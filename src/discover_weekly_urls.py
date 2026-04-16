"""
Best-effort auto-discovery of the latest weekly planning list URL for each
council. Prints what it found so YOU can paste the correct URL into
sources.py — it does not auto-write to avoid silently choosing the wrong link.

Each council's landing page lists their weekly files. This script fetches the
landing page and picks the link whose text/filename looks most like the most
recent weekly list.
"""

from __future__ import annotations

import datetime as dt
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .sources import COUNCILS

WEEK_PATTERN = re.compile(r"week[\s_-]*(\d{1,2})", re.I)
YEAR_PATTERN = re.compile(r"20(\d{2})")


def _score(link_text: str, href: str) -> int:
    """Higher score = more likely to be the most recent weekly list."""
    s = 0
    combo = f"{link_text} {href}".lower()
    if ".pdf" in combo:
        s += 10
    if "week" in combo:
        s += 20
    if "202" in combo:  # contains a year
        s += 15
    # Prefer higher week numbers
    m = WEEK_PATTERN.search(combo)
    if m:
        s += int(m.group(1))
    # Prefer current year
    y = YEAR_PATTERN.search(combo)
    if y and int("20" + y.group(1)) == dt.date.today().year:
        s += 30
    return s


def discover_one(landing_url: str) -> list[tuple[int, str, str]]:
    headers = {"User-Agent": "PlanRadar/0.1 (+contact: you@example.ie)"}
    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        r = client.get(landing_url)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    candidates: list[tuple[int, str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        abs_url = urljoin(landing_url, href)
        score = _score(text, abs_url)
        if score >= 25:
            candidates.append((score, text, abs_url))
    candidates.sort(reverse=True)
    return candidates[:5]


def main() -> None:
    print("Candidate weekly-list URLs (highest score = most likely the current week):\n")
    for c in COUNCILS:
        print(f"=== {c.code} — {c.name} ===")
        print(f"Landing: {c.landing_page}")
        try:
            cands = discover_one(c.landing_page)
        except Exception as e:
            print(f"  [error] {e}\n")
            continue
        if not cands:
            print("  [none] no candidates — the landing page may be JS-rendered or the structure changed.\n")
            continue
        for score, text, url in cands:
            print(f"  [{score:3d}] {text[:60]!r}")
            print(f"        {url}")
        print(f"\n  -> If the top candidate is correct, paste its URL into sources.py as {c.code}.weekly_list_url\n")


if __name__ == "__main__":
    main()
