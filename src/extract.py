"""
DeepSeek extraction of structured planning applications from raw files.

Key design points:
- Large stable system prompt → DeepSeek prompt-cache hit → 90% discount.
- One application per API call. Cheap (~€0.003 uncached, ~€0.0007 cached)
  and isolates failures so one bad entry doesn't poison a batch.
- Strict-JSON response format + schema validation. Bad rows dropped.
- DEEPSEEK_API_KEY is resolved lazily, at the first API call. This lets
  other modules import this one without needing the key just to use the
  chunk splitter or read functions.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_client = None  # lazy


def _get_client():
    global _client
    if _client is not None:
        return _client
    from openai import OpenAI
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key or key == "sk-replace-me":
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. Put a real key in .env — copy .env.example to .env and edit."
        )
    _client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    return _client


MODEL = "deepseek-chat"

SYSTEM_PROMPT = """You are an expert Irish planning-application classifier.

You will receive ONE planning application entry from a Dublin council weekly
list. Your job is to extract structured fields and classify which trades and
professionals would be commercially interested in this application as a lead.

Return STRICT JSON matching this schema, with no prose, no markdown, no code fence:

{
  "application_ref": string,            // council reference number, e.g. "3456/24"
  "council": string,                    // one of: "DCC", "Fingal", "DLR", "SDCC", "CorkCity", "CorkCoCo"
  "received_date": string,              // ISO date if present, else ""
  "applicant_name": string,             // as printed; if a company, the company name
  "agent_name": string,                 // architect/agent if listed, else ""
  "site_address": string,               // full address as printed
  "eircode": string,                    // if present, else ""
  "description": string,                // verbatim free-text description, trimmed
  "work_type": string,                  // one of: "new_build", "extension", "renovation", "demolition", "change_of_use", "commercial_fitout", "infrastructure", "other"
  "scale": string,                      // one of: "small", "medium", "large"
  "est_value_band_eur": string,         // one of: "under_50k", "50k_to_250k", "250k_to_1m", "over_1m", "unknown"
  "trades_relevant": [string],          // any of: "roofing", "solar_pv", "scaffolding", "structural_engineering", "architecture", "kitchens", "windows_glazing", "insulation", "groundworks", "electrical", "plumbing_heating", "plastering", "painting", "landscaping", "demolition", "surveying", "fire_safety", "ber_assessment", "planning_consulting", "solicitor_objections"
  "professionals_relevant": [string],   // any of: "insurance_broker", "mortgage_broker", "estate_agent", "solicitor_conveyancing", "quantity_surveyor"
  "confidence": number                  // 0.0 to 1.0
}

Rules:
- If a field is not present in the input, use "" (not null).
- Never invent data.
- trades_relevant should be the trades whose phone you would expect to ring if they saw this application — be generous but not absurd.
- A small rear extension is "extension" + "small" + ["architecture", "structural_engineering", "groundworks", "windows_glazing"] at minimum.
- Change of use alone (no construction) skips most trades but is gold for solicitors and BER assessors.
- Solar PV / battery installs go in "solar_pv".
- Output STRICT JSON only. No explanations.
"""


@dataclass
class RawEntry:
    council_code: str
    text: str


# Matches an Irish council planning reference across multiple councils:
#   Dublin:      3456/24, F25A/0777, D21A/0297/E, SDZ25A/0046W, SD25A/0156W, LRD000123
#   Cork City:   26/44469       (YY/NNNNN — year first)
#   Cork County: 120000089807   (12 consecutive digits)
REF_PATTERN = re.compile(
    r"\b("
    r"(?:SDZ|LRD|F|D|SD|ABP)[A-Z]{0,3}\d{2,5}[A-Z]?/\d{2,4}(?:/[A-Z])?"
    r"|\d{3,5}/\d{2}"          # Dublin-style: 3456/24
    r"|\d{2}/\d{5,6}"          # Cork City:    26/44469  (5-6 digits excludes MM/YYYY dates)
    r"|\b1\d{11}\b"            # Cork County:  120000089807 (12 digits starting with 1)
    r")\b"
)


def split_into_entries(full_text: str, council_code: str) -> list[RawEntry]:
    """Split a council weekly-list raw text into one chunk per application.

    Strategy: find every reference-number match, use each as a split boundary.
    Entries shorter than 80 chars are discarded as noise (headers, footers).
    """
    matches = list(REF_PATTERN.finditer(full_text))
    if not matches:
        return []
    entries: list[RawEntry] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        chunk = full_text[start:end].strip()
        if len(chunk) >= 80:
            entries.append(RawEntry(council_code=council_code, text=chunk))
    return entries


def extract_one(entry: RawEntry) -> Optional[dict]:
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Council: {entry.council_code}\n\n{entry.text}"},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return None
    required = {"application_ref", "council", "site_address", "description", "work_type", "trades_relevant"}
    if not required.issubset(data.keys()):
        return None
    return data


def extract_file(path: Path, council_code: str, fmt: str, limit: int | None = None) -> list[dict]:
    from .readers import read_any
    text = read_any(path, fmt)
    entries = split_into_entries(text, council_code)
    if limit:
        entries = entries[:limit]
    print(f"[extract] {path.name}: {len(entries)} candidate entries")
    results: list[dict] = []
    for i, e in enumerate(entries, 1):
        try:
            row = extract_one(e)
            if row:
                results.append(row)
                if i % 10 == 0:
                    print(f"  [{i}/{len(entries)}] {len(results)} good rows so far")
        except Exception as ex:
            print(f"  [error] entry {i}: {ex}")
    print(f"[extract] {path.name}: {len(results)}/{len(entries)} valid applications")
    return results


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1])
    code = sys.argv[2] if len(sys.argv) > 2 else path.parent.name
    fmt = sys.argv[3] if len(sys.argv) > 3 else path.suffix.lstrip(".")
    rows = extract_file(path, code, fmt)
    out = Path("out/structured") / f"{path.stem}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[wrote] {out}")
