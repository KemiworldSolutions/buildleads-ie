"""
Minimal Stripe webhook handler.

Runs as a tiny Flask app on your VPS. Appends new subscribers to
subscribers/active.csv on subscription creation, marks them cancelled on
subscription deletion.

Deliberately minimal — no database, no ORM. The subscribers file IS the
source of truth until you cross ~200 customers. Then migrate to SQLite.

Setup:
    pip install flask stripe
    # in .env add: STRIPE_WEBHOOK_SECRET=whsec_...
    flask --app src.stripe_webhook run --host 0.0.0.0 --port 8080

Expose with:
    # Quick and dirty: cloudflared tunnel
    cloudflared tunnel --url http://localhost:8080
    # Production: nginx reverse proxy + systemd service

In Stripe dashboard:
    Webhooks → Add endpoint
    URL: https://your-tunnel-or-domain/stripe-webhook
    Events: customer.subscription.created, customer.subscription.deleted, customer.subscription.updated
    Copy the signing secret into .env
"""

from __future__ import annotations

import csv
import datetime as dt
import os
from pathlib import Path

try:
    from flask import Flask, request, abort
    import stripe
except ImportError:
    print("Install flask and stripe first:  pip install flask stripe")
    raise

from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

SUBSCRIBERS_FILE = Path("subscribers/active.csv")
WEBHOOK_LOG = Path("subscribers/webhook_log.csv")

# Map Stripe product/price metadata → segment
# When you create the Stripe product, add a metadata field `segment` with value e.g. "roofing"
# This handler reads that field to know which digest to send.

app = Flask(__name__)


def _ensure_subscribers_file() -> None:
    if SUBSCRIBERS_FILE.exists():
        return
    SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SUBSCRIBERS_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "segment", "stripe_customer_id", "joined", "status"])


def _log_event(event_type: str, customer_id: str, email: str, detail: str) -> None:
    new = not WEBHOOK_LOG.exists()
    WEBHOOK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with WEBHOOK_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "event", "customer_id", "email", "detail"])
        w.writerow([dt.datetime.utcnow().isoformat(), event_type, customer_id, email, detail])


def _add_subscriber(email: str, segment: str, customer_id: str) -> None:
    _ensure_subscribers_file()
    rows = list(csv.DictReader(SUBSCRIBERS_FILE.open(encoding="utf-8")))
    for r in rows:
        if r["email"] == email:
            r["status"] = "active"
            r["segment"] = segment or r["segment"]
            break
    else:
        rows.append({
            "email": email,
            "segment": segment,
            "stripe_customer_id": customer_id,
            "joined": dt.date.today().isoformat(),
            "status": "active",
        })
    with SUBSCRIBERS_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["email", "segment", "stripe_customer_id", "joined", "status"])
        w.writeheader()
        w.writerows(rows)


def _cancel_subscriber(customer_id: str) -> None:
    if not SUBSCRIBERS_FILE.exists():
        return
    rows = list(csv.DictReader(SUBSCRIBERS_FILE.open(encoding="utf-8")))
    for r in rows:
        if r["stripe_customer_id"] == customer_id:
            r["status"] = "cancelled"
    with SUBSCRIBERS_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["email", "segment", "stripe_customer_id", "joined", "status"])
        w.writeheader()
        w.writerows(rows)


@app.post("/stripe-webhook")
def webhook() -> tuple[str, int]:
    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        _log_event("signature_error", "", "", str(e))
        abort(400)

    t = event["type"]
    obj = event["data"]["object"]

    if t == "customer.subscription.created":
        customer_id = obj.get("customer", "")
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.get("email", "")
        # Pull segment from price metadata
        items = obj.get("items", {}).get("data", [])
        segment = ""
        if items:
            segment = items[0].get("price", {}).get("metadata", {}).get("segment", "")
        _add_subscriber(email, segment, customer_id)
        _log_event(t, customer_id, email, f"segment={segment}")

    elif t in ("customer.subscription.deleted", "customer.subscription.updated"):
        customer_id = obj.get("customer", "")
        status = obj.get("status", "")
        if t == "customer.subscription.deleted" or status in ("canceled", "incomplete_expired", "unpaid"):
            _cancel_subscriber(customer_id)
            _log_event(t, customer_id, "", f"status={status}")

    return "", 200


@app.get("/health")
def health() -> tuple[str, int]:
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
