"""
Build per-segment weekly markdown digests.

Output goes to out/digests/{segment}_{date}.md and is the artifact you
attach (or paste) into a cold email or send to a paying subscriber.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from .classify import bucket_by_trade, load_all_structured

DIGEST_DIR = Path("out/digests")

SEGMENT_LABELS = {
    "roofing": "Roofing",
    "solar_pv": "Solar PV & Battery",
    "scaffolding": "Scaffolding",
    "structural_engineering": "Structural Engineering",
    "architecture": "Architecture",
    "kitchens": "Kitchens & Joinery",
    "windows_glazing": "Windows & Glazing",
    "insulation": "Insulation",
    "groundworks": "Groundworks",
    "electrical": "Electrical",
    "plumbing_heating": "Plumbing & Heating",
    "plastering": "Plastering",
    "painting": "Painting & Decorating",
    "landscaping": "Landscaping",
    "demolition": "Demolition",
    "surveying": "Surveying",
    "fire_safety": "Fire Safety",
    "ber_assessment": "BER Assessment",
    "planning_consulting": "Planning Consulting",
    "solicitor_objections": "Solicitors (Planning Objections)",
    "insurance_broker": "Insurance Brokers",
    "mortgage_broker": "Mortgage Brokers",
    "estate_agent": "Estate Agents",
    "solicitor_conveyancing": "Solicitors (Conveyancing)",
    "quantity_surveyor": "Quantity Surveyors",
}


def build_digest(segment: str) -> Path:
    rows = load_all_structured()
    buckets = bucket_by_trade(rows)
    items = buckets.get(segment, [])

    label = SEGMENT_LABELS.get(segment, segment)
    today = dt.date.today().isoformat()

    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    out = DIGEST_DIR / f"{segment}_{today}.md"

    lines = [
        f"# Dublin Planning Leads — {label}",
        f"_Week of {today}. {len(items)} relevant applications across DCC, Fingal, DLR, SDCC._",
        "",
        "Every application below is a public planning record. Filed in the last 7 days.",
        "Applicant and agent names are as published on the council register.",
        "",
        "---",
        "",
    ]

    for r in items:
        lines.append(f"### {r.get('application_ref', '?')} — {r.get('council', '?')}")
        lines.append(f"**Site:** {r.get('site_address', '')}")
        if r.get("eircode"):
            lines.append(f"**Eircode:** {r['eircode']}")
        lines.append(f"**Applicant:** {r.get('applicant_name', '')}")
        if r.get("agent_name"):
            lines.append(f"**Agent / Architect:** {r['agent_name']}")
        lines.append(f"**Type:** {r.get('work_type', '')} ({r.get('scale', '')})")
        lines.append(f"**Estimated value band:** {r.get('est_value_band_eur', 'unknown')}")
        lines.append("")
        lines.append(f"> {r.get('description', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[digest] wrote {out} ({len(items)} items)")
    return out


if __name__ == "__main__":
    import sys
    segment = sys.argv[1] if len(sys.argv) > 1 else "roofing"
    build_digest(segment)
