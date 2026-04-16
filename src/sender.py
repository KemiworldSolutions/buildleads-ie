"""
Human-gated email sender.

- Reads outreach/drafts/*.md
- Refuses to run without --confirm flag
- Refuses to send more than --limit per invocation (default 10)
- Sleeps 90 seconds between sends (so you stay under any rate limit and
  have time to ctrl-c if a draft is wrong)
- Logs every send to outreach/log.csv
- Marks status: sent in the draft frontmatter

This script intentionally does NOT auto-send on a schedule. You run it,
you watch it, you stop it.

Configure SMTP in .env:
    SMTP_HOST=smtp.fastmail.com
    SMTP_PORT=465
    SMTP_USER=you@yourdomain.ie
    SMTP_PASS=app_password
    FROM_NAME=Your Name
    FROM_ADDRESS=you@yourdomain.ie

Use a real domain you own. Set up SPF, DKIM and DMARC before sending anything
or your emails go to spam and your domain reputation tanks. Fastmail and
MXroute both support custom domains and have decent IP reputation.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DRAFTS_DIR = Path("outreach/drafts")
LOG_FILE = Path("outreach/log.csv")
SLEEP_SECONDS = 90


def _parse_draft(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing frontmatter")
    _, fm, body = text.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body.strip()


def _write_log(row: dict) -> None:
    new = not LOG_FILE.exists()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "to", "company", "segment", "subject", "status", "draft_file"])
        if new:
            w.writeheader()
        w.writerow(row)


def _mark_sent(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("status: draft", "status: sent")
    path.write_text(text, encoding="utf-8")


def send_one(meta: dict, body: str, draft_path: Path) -> bool:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    user = os.environ["SMTP_USER"]
    pw = os.environ["SMTP_PASS"]
    from_name = os.environ.get("FROM_NAME", "PlanRadar")
    from_addr = os.environ.get("FROM_ADDRESS", user)

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = meta["to"]
    msg["Subject"] = meta["subject"]
    msg["Reply-To"] = from_addr
    # Add list-unsubscribe so Gmail/Outlook show the one-click unsubscribe button
    msg["List-Unsubscribe"] = f"<mailto:{from_addr}?subject=remove>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(body + f"\n\n---\nReply 'remove' to {from_addr} and you are off this list permanently.\nPlanRadar.ie")

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as s:
        s.login(user, pw)
        s.send_message(msg)

    _mark_sent(draft_path)
    _write_log({
        "timestamp": dt.datetime.utcnow().isoformat(),
        "to": meta["to"],
        "company": meta.get("company", ""),
        "segment": meta.get("segment", ""),
        "subject": meta["subject"],
        "status": "sent",
        "draft_file": draft_path.name,
    })
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Required to actually send")
    parser.add_argument("--limit", type=int, default=10, help="Max sends per invocation")
    parser.add_argument("--segment", default=None, help="Only send drafts for this segment")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent, don't send")
    args = parser.parse_args()

    drafts = sorted(DRAFTS_DIR.glob("*.md"))
    queue = []
    for d in drafts:
        meta, body = _parse_draft(d)
        if meta.get("status") != "draft":
            continue
        if args.segment and meta.get("segment") != args.segment:
            continue
        queue.append((d, meta, body))
        if len(queue) >= args.limit:
            break

    if not queue:
        print("Nothing to send.")
        return 0

    print(f"Queue: {len(queue)} drafts (limit {args.limit})")
    for d, meta, _ in queue:
        print(f"  - {meta['to']} ({meta.get('company', '')}) [{d.name}]")

    if args.dry_run:
        print("\nDRY RUN — not sending.")
        return 0

    if not args.confirm:
        print("\nRefusing to send without --confirm. Re-run with --confirm to actually send.")
        return 1

    print(f"\nSending with {SLEEP_SECONDS}s between messages. Ctrl-C to stop at any time.\n")
    for i, (d, meta, body) in enumerate(queue, 1):
        try:
            print(f"[{i}/{len(queue)}] -> {meta['to']}")
            send_one(meta, body, d)
            print("  sent.")
        except Exception as e:
            print(f"  ERROR: {e}")
            _write_log({
                "timestamp": dt.datetime.utcnow().isoformat(),
                "to": meta["to"],
                "company": meta.get("company", ""),
                "segment": meta.get("segment", ""),
                "subject": meta["subject"],
                "status": f"error: {e}",
                "draft_file": d.name,
            })
        if i < len(queue):
            time.sleep(SLEEP_SECONDS)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
