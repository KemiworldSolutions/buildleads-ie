"""
Offline end-to-end smoke test.

Runs the extraction + classification + digest pipeline against the bundled
fixture so you can verify everything works before touching live council URLs
or paying for DeepSeek credit (well — extraction still costs ~€0.01 for the
fixture, which is fine).

Usage:
    python -m src.test_offline
"""

from __future__ import annotations

import json
from pathlib import Path

from .digest import build_digest
from .extract import RawEntry, extract_one


def run() -> None:
    fixture = Path("fixtures/sample_dcc_week.txt")
    if not fixture.exists():
        print("Missing fixture file.")
        return

    text = fixture.read_text(encoding="utf-8")

    # Naive split on the application reference pattern
    import re
    parts = re.split(r"(?=\b\d{4}/\d{2}\b\s+Received)", text)
    entries = [RawEntry(council_code="dcc", text=p.strip()) for p in parts if "Received" in p]

    print(f"[fixture] {len(entries)} entries to extract")

    out = Path("out/structured/fixture.dcc.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, e in enumerate(entries, 1):
        print(f"  [{i}/{len(entries)}] extracting...")
        row = extract_one(e)
        if row:
            rows.append(row)

    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[wrote] {out} ({len(rows)} rows)")

    print("\n[digests]")
    for seg in ["roofing", "solar_pv", "structural_engineering", "architecture", "kitchens"]:
        build_digest(seg)

    print("\nDone. Open out/digests/ to see the artifacts.")


if __name__ == "__main__":
    run()
