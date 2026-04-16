"""
Read the IMAP inbox, find replies to cold outreach, and classify each
reply via DeepSeek into one of:
    sample_request | remove | interested | not_interested | question | other

Writes results to outreach/replies.csv for your morning review.

Uses read-only IMAP (no mark-as-seen, no delete) so you can also handle
replies in your normal mail client.

Config in .env:
    IMAP_HOST=imap.fastmail.com
    IMAP_PORT=993
    IMAP_USER=you@yourdomain.ie
    IMAP_PASS=app_password
"""

from __future__ import annotations

import csv
import datetime as dt
import email
import imaplib
import os
from email.header import decode_header
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

REPLIES_FILE = Path("outreach/replies.csv")

CLASSIFY_PROMPT = """You classify short replies to a cold B2B email about an Irish lead-gen service.

Output STRICT JSON only:
{
  "category": "sample_request" | "remove" | "interested" | "not_interested" | "question" | "other",
  "summary": string (one sentence),
  "urgency": "high" | "medium" | "low"
}

Categories:
- "sample_request": they want a free sample of the weekly digest
- "remove": they want to be removed from the list — HIGHEST priority, must be handled within 24h
- "interested": positive signal, wants to know more, wants to talk
- "not_interested": polite no
- "question": they have a specific question to answer
- "other": anything else

Output JSON only, no prose."""


def _decode(s: str | bytes | None) -> str:
    if s is None:
        return ""
    if isinstance(s, bytes):
        try:
            return s.decode()
        except Exception:
            return s.decode("latin-1", errors="replace")
    parts = decode_header(s)
    return "".join(
        (p.decode(c or "utf-8", errors="replace") if isinstance(p, bytes) else p)
        for p, c in parts
    )


def _body_from_msg(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(errors="replace")
                except Exception:
                    continue
        return ""
    try:
        return msg.get_payload(decode=True).decode(errors="replace")
    except Exception:
        return str(msg.get_payload())


def classify(body: str) -> dict:
    import json
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": CLASSIFY_PROMPT},
            {"role": "user", "content": body[:4000]},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"category": "other", "summary": "(classification failed)", "urgency": "medium"}


def scan_inbox(days: int = 7) -> None:
    host = os.environ["IMAP_HOST"]
    port = int(os.environ["IMAP_PORT"])
    user = os.environ["IMAP_USER"]
    pw = os.environ["IMAP_PASS"]

    since = (dt.date.today() - dt.timedelta(days=days)).strftime("%d-%b-%Y")

    m = imaplib.IMAP4_SSL(host, port)
    m.login(user, pw)
    m.select("INBOX", readonly=True)
    status, data = m.search(None, f'(SINCE "{since}")')
    ids = data[0].split()
    print(f"[imap] {len(ids)} messages since {since}")

    REPLIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_file = not REPLIES_FILE.exists()
    with REPLIES_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "from", "subject", "category", "urgency", "summary"])
        if new_file:
            w.writeheader()

        for msg_id in ids:
            status, data = m.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(data[0][1])
            subj = _decode(msg.get("Subject"))
            frm = _decode(msg.get("From"))
            date = _decode(msg.get("Date"))
            if "re:" not in subj.lower() and "planradar" not in subj.lower():
                continue
            body = _body_from_msg(msg)
            if not body.strip():
                continue
            result = classify(body)
            w.writerow({
                "date": date,
                "from": frm,
                "subject": subj,
                "category": result.get("category", "other"),
                "urgency": result.get("urgency", "medium"),
                "summary": result.get("summary", ""),
            })
            print(f"  [{result.get('category'):16}] {frm[:40]:40} — {subj[:50]}")

    m.logout()
    print(f"\nWrote results to {REPLIES_FILE}")
    print("Act on 'remove' replies first, then 'sample_request', then 'interested'.")


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    scan_inbox(days)
