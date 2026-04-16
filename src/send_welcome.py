"""
Send a personal welcome email to the newest subscriber(s).

Reads subscribers/active.csv, finds rows joined today that haven't had a
welcome sent yet (tracked via subscribers/welcomed.csv), and sends each
one a short personal email via DeepSeek-drafted copy tailored to their segment.

Run manually whenever Stripe notifies you of a new subscriber, or from cron
every 15 minutes if you have a VPS:
    */15 * * * * cd /home/planradar && python3 -m src.send_welcome
"""

from __future__ import annotations

import csv
import datetime as dt
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SUBSCRIBERS_FILE = Path("subscribers/active.csv")
WELCOMED_FILE = Path("subscribers/welcomed.csv")

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

WELCOME_PROMPT = """Write a short personal welcome email (under 120 words) from the founder of PlanRadar.ie to a new paying subscriber.

Tone: warm, specific, human — like an indie maker, not a corporation. No "we at PlanRadar". First person, singular.

Structure:
- Thank them personally
- Mention their segment specifically and one concrete thing about that trade in Dublin
- Tell them the first digest arrives next Monday at 7am
- Ask ONE question: their specific catchment area or the one job type they want more of
- Sign off with first name only

Output ONLY the email body. No subject, no signature block."""


def _load_welcomed() -> set[str]:
    if not WELCOMED_FILE.exists():
        return set()
    with WELCOMED_FILE.open(encoding="utf-8") as f:
        return {row["email"] for row in csv.DictReader(f)}


def _mark_welcomed(email: str) -> None:
    new = not WELCOMED_FILE.exists()
    WELCOMED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with WELCOMED_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["email", "timestamp"])
        w.writerow([email, dt.datetime.utcnow().isoformat()])


def _draft_welcome(segment: str) -> str:
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": WELCOME_PROMPT},
            {"role": "user", "content": f"New subscriber's segment: {segment}"},
        ],
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()


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
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as s:
        s.login(user, pw)
        s.send_message(msg)


def main() -> None:
    if not SUBSCRIBERS_FILE.exists():
        print("No subscribers file yet.")
        return
    welcomed = _load_welcomed()
    with SUBSCRIBERS_FILE.open(encoding="utf-8") as f:
        subs = [r for r in csv.DictReader(f) if r.get("status", "active") == "active"]
    new = [s for s in subs if s["email"] not in welcomed]
    if not new:
        print("No new subscribers to welcome.")
        return
    print(f"[welcome] {len(new)} new subscribers")
    for s in new:
        body = _draft_welcome(s["segment"])
        subject = "Welcome to PlanRadar"
        try:
            _send(s["email"], subject, body)
            _mark_welcomed(s["email"])
            print(f"  sent -> {s['email']}")
        except Exception as e:
            print(f"  ERROR -> {s['email']}: {e}")


if __name__ == "__main__":
    main()
