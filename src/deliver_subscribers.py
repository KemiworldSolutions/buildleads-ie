"""
Deliver the weekly digest to paying subscribers.

Reads subscribers/active.csv, looks up the right per-segment digest from
out/digests/, and emails each subscriber their digest via the same SMTP
config that sender.py uses.

This is the core product fulfilment. Run it every Monday after pipeline.py.

Usage:
    python -m src.deliver_subscribers                # sends to everyone
    python -m src.deliver_subscribers --dry-run      # shows what would be sent
    python -m src.deliver_subscribers --only you@x   # send to one address (test)
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

SUBSCRIBERS_FILE = Path("subscribers/active.csv")
DIGEST_DIR = Path("out/digests")
DELIVERY_LOG = Path("subscribers/delivery_log.csv")


def _latest_digest(segment: str) -> Path | None:
    files = sorted(DIGEST_DIR.glob(f"{segment}_*.md"), reverse=True)
    return files[0] if files else None


def _load_subscribers() -> list[dict]:
    if not SUBSCRIBERS_FILE.exists():
        print(f"[error] {SUBSCRIBERS_FILE} not found. Create it with headers: email,segment,stripe_customer_id,joined,status")
        return []
    with SUBSCRIBERS_FILE.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("status", "active") == "active"]


def _log_delivery(row: dict) -> None:
    new = not DELIVERY_LOG.exists()
    DELIVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DELIVERY_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "email", "segment", "digest_file", "status"])
        if new:
            w.writeheader()
        w.writerow(row)


def _send(to_addr: str, subject: str, body: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    user = os.environ["SMTP_USER"]
    pw = os.environ["SMTP_PASS"]
    from_name = os.environ.get("FROM_NAME", "PlanRadar")
    from_addr = os.environ.get("FROM_ADDRESS", user)

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Reply-To"] = from_addr
    msg["List-Unsubscribe"] = f"<mailto:{from_addr}?subject=unsubscribe>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as s:
        s.login(user, pw)
        s.send_message(msg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", default=None, help="Only send to this one address")
    args = parser.parse_args()

    subs = _load_subscribers()
    if args.only:
        subs = [s for s in subs if s["email"] == args.only]
    if not subs:
        print("No active subscribers to deliver to.")
        return 0

    today = dt.date.today().isoformat()
    print(f"[deliver] {len(subs)} active subscribers for week of {today}")

    for i, sub in enumerate(subs, 1):
        seg = sub["segment"]
        digest = _latest_digest(seg)
        if not digest:
            print(f"  [skip] {sub['email']}: no digest for segment {seg}")
            _log_delivery({"timestamp": dt.datetime.utcnow().isoformat(), "email": sub["email"], "segment": seg, "digest_file": "", "status": "skip_no_digest"})
            continue

        body = digest.read_text(encoding="utf-8") + "\n\n---\nPlanRadar.ie — Dublin weekly planning leads\nManage or cancel: https://billing.stripe.com/p/login/REPLACE_WITH_YOUR_PORTAL_LINK\nReply 'unsubscribe' to stop permanently.\n"
        subject = f"PlanRadar — Dublin {seg.replace('_', ' ')} leads, week of {today}"

        print(f"  [{i}/{len(subs)}] -> {sub['email']} ({seg}) using {digest.name}")
        if args.dry_run:
            continue

        try:
            _send(sub["email"], subject, body)
            _log_delivery({"timestamp": dt.datetime.utcnow().isoformat(), "email": sub["email"], "segment": seg, "digest_file": digest.name, "status": "sent"})
        except Exception as e:
            print(f"    ERROR: {e}")
            _log_delivery({"timestamp": dt.datetime.utcnow().isoformat(), "email": sub["email"], "segment": seg, "digest_file": digest.name, "status": f"error: {e}"})

        if i < len(subs):
            time.sleep(2)  # SMTP politeness, much shorter than cold outreach

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
