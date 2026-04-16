"""
Outreach draft generator.

Reads buyers/{segment}.csv and out/digests/{segment}_*.md, then asks DeepSeek
to write ONE personalised cold email per buyer. Drafts go to outreach/drafts/.

Drafts are NEVER sent automatically. The human reviews each one and runs
sender.py with explicit confirmation. This is the human-in-the-loop gate.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from .extract import _get_client  # lazy DeepSeek client

DRAFTS_DIR = Path("outreach/drafts")
BUYERS_DIR = Path("buyers")
DIGESTS_DIR = Path("out/digests")

SYSTEM_PROMPT = """You write short, specific, non-sleazy B2B cold emails for an Irish lead-gen service called PlanRadar.

PlanRadar sends Dublin tradespeople a weekly digest of new planning applications relevant to their trade, sourced from the four Dublin local authorities' public weekly planning lists. €29/month, cancel anytime.

You will be given:
1. The recipient's company name and segment (e.g. "roofing")
2. A short snippet from this week's actual digest for that segment

Your job: write ONE email under 130 words that:
- Opens with a specific, plausible reference to the recipient's trade in Dublin (no fake compliments, no "I came across your website" cliches)
- States in one sentence what PlanRadar is and where the data comes from
- Quotes one or two specific applications from the digest snippet as proof
- Names the price (€29/month) and the cancel-anytime
- Ends with a soft CTA ("reply 'sample' and I'll send last week's full list free")
- Includes a one-line opt-out: "Reply 'remove' and you're off the list permanently."

Output ONLY the email body. No subject line, no signature block — those are added by the sender. No markdown, no headers."""


def _load_digest_snippet(segment: str) -> str:
    files = sorted(DIGESTS_DIR.glob(f"{segment}_*.md"), reverse=True)
    if not files:
        return ""
    text = files[0].read_text(encoding="utf-8")
    # Take the first 3 application entries (everything up to the third "---" divider after the header)
    parts = text.split("\n---\n")
    return "\n---\n".join(parts[:4])[:2000]


def draft_email(company: str, segment: str, digest_snippet: str) -> str:
    client = _get_client()
    user_msg = f"Recipient company: {company}\nSegment: {segment}\n\nThis week's digest snippet:\n\n{digest_snippet}"
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


def draft_segment(segment: str, limit: int = 30) -> None:
    buyer_file = BUYERS_DIR / f"{segment}.csv"
    if not buyer_file.exists():
        print(f"[error] no buyer file at {buyer_file}. Run buyer_harvester.py first or drop a CSV in by hand.")
        return

    snippet = _load_digest_snippet(segment)
    if not snippet:
        print(f"[error] no digest for {segment}. Run pipeline.py first.")
        return

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()

    with buyer_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        buyers = list(reader)[:limit]

    for buyer in buyers:
        company = buyer["company"]
        email = buyer["email"]
        safe = "".join(c if c.isalnum() else "_" for c in company)[:60]
        out = DRAFTS_DIR / f"{today}_{segment}_{safe}.md"
        if out.exists():
            print(f"[skip] {out.name} (exists)")
            continue
        body = draft_email(company, segment, snippet)
        out.write_text(
            f"---\nto: {email}\ncompany: {company}\nsegment: {segment}\nsubject: Dublin {segment.replace('_', ' ')} leads — week of {today}\nstatus: draft\n---\n\n{body}\n",
            encoding="utf-8",
        )
        print(f"[draft] {out.name}")

    print(f"\n{len(buyers)} drafts written to {DRAFTS_DIR}/")
    print("Review each one. Then run: python -m src.sender --confirm")


def draft_all(limit: int = 30) -> None:
    """Generate drafts for every segment that has a buyer CSV."""
    if not BUYERS_DIR.exists():
        print("[error] buyers/ directory missing")
        return
    segments = sorted(p.stem for p in BUYERS_DIR.glob("*.csv"))
    for seg in segments:
        print(f"\n=== {seg} ===")
        draft_segment(seg, limit)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        seg = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        draft_segment(seg, limit)
    else:
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        draft_all(limit)
