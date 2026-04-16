"""
Council source configuration — verified working against live council sites
on 2026-04-14.

Each council has a `landing_page` (the human-facing weekly-lists index) and a
`discover()` function that returns (url, filename, format) tuples for the
most recent week's downloadable files. Format is one of: "pdf", "docx", "doc".

Why one discover function per council: each council publishes differently
(DCC has 5 electoral-area docx files, Fingal has multiple per-type .doc
files, DLR has a single PDF, SDCC has numeric IDs behind a listing page).
Trying to unify them behind a single URL template is brittle — so we keep
the council-specific logic small and honest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "PlanRadar/0.1 (+contact: you@example.ie)"}


@dataclass
class DiscoveredFile:
    council_code: str
    url: str
    filename: str
    format: str  # "pdf" | "docx" | "doc"
    note: str = ""  # e.g. "Electoral Area 1" for DCC


def _get(url: str) -> httpx.Response:
    with httpx.Client(timeout=30, follow_redirects=True, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return r


# ---------- Dublin City Council ----------
# Lists 5 electoral-area DOCX files per week. Filenames look like:
#   a1-wpl-14-26.docx   (Area 1, Week 14, Year 26)
# The listing page has all recent weeks linked. We take the five most recent
# a1..a5 files from the current week (highest week number).

DCC_LANDING = "https://www.dublincity.ie/planning-and-land-use/find-planning-application/weeks-planning-applications-and-decisions"


def discover_dcc() -> list[DiscoveredFile]:
    r = _get(DCC_LANDING)
    soup = BeautifulSoup(r.text, "html.parser")
    pattern = re.compile(r"/sites/default/files/\d{4}-\d{2}/a(\d)-wpl-(\d{1,2})-(\d{2})\.docx", re.I)
    by_area: dict[int, tuple[int, str]] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = pattern.search(href)
        if not m:
            continue
        area, week, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        prev = by_area.get(area)
        if prev is None or (yr, week) > prev[0:2]:  # keep highest year/week
            by_area[area] = (yr, week, href)
    out = []
    for area in sorted(by_area):
        yr, week, href = by_area[area]
        abs_url = urljoin(DCC_LANDING, href)
        out.append(DiscoveredFile(
            council_code="dcc",
            url=abs_url,
            filename=f"dcc_area{area}_w{week}_y{yr}.docx",
            format="docx",
            note=f"Electoral Area {area}",
        ))
    return out


# ---------- Fingal County Council ----------
# Lists 4 legacy .doc files per week: applications-received, decisions-made,
# appeals-lodged, appeals-decided. Folder names vary:
#   .../2026%20Week%2014/applications-received.doc
#   .../2026%2C%2010/applications-received.doc  (older weeks use comma)
# We only care about "applications-received" for lead gen.

FINGAL_LANDING = "https://www.fingal.ie/council/service/planning-weekly-lists"


def discover_fingal() -> list[DiscoveredFile]:
    r = _get(FINGAL_LANDING)
    soup = BeautifulSoup(r.text, "html.parser")
    # Grab the first "applications-received.doc" link — the page is ordered newest first.
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "applications-received" in href.lower() and href.lower().endswith(".doc"):
            abs_url = urljoin(FINGAL_LANDING, href)
            # Pull a rough week id out of the href for filenaming
            m = re.search(r"(\d{4}).{1,5}(\d{1,2})", href)
            label = f"{m.group(1)}w{m.group(2)}" if m else "latest"
            return [DiscoveredFile(
                council_code="fingal",
                url=abs_url,
                filename=f"fingal_{label}.doc",
                format="doc",
            )]
    return []


# ---------- Dún Laoghaire-Rathdown County Council ----------
# Single PDF per week. Filename pattern: "Weekly List no {N}.pdf" (sometimes "No").

DLR_LANDING = "https://www.dlrcoco.ie/weekly-planning-lists/weekly-planning-lists"


def discover_dlr() -> list[DiscoveredFile]:
    r = _get(DLR_LANDING)
    soup = BeautifulSoup(r.text, "html.parser")
    pattern = re.compile(r"Weekly%20List%20[Nn]o\.?%20(\d{1,2})", re.I)
    best: tuple[int, str] | None = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = pattern.search(href)
        if not m:
            continue
        week = int(m.group(1))
        # Only take files from the most recent YYYY-MM folder we see
        year_m = re.search(r"/files/(\d{4})-(\d{2})/", href)
        rank = (int(year_m.group(1)), int(year_m.group(2)), week) if year_m else (0, 0, week)
        if best is None or rank > best[0]:
            best = (rank, href)
    if not best:
        return []
    href = best[1]
    abs_url = urljoin(DLR_LANDING, href)
    m = re.search(r"no\.?%20(\d+)", href, re.I)
    week = m.group(1) if m else "latest"
    return [DiscoveredFile(
        council_code="dlr",
        url=abs_url,
        filename=f"dlr_w{week}.pdf",
        format="pdf",
    )]


# ---------- South Dublin County Council ----------
# Listing page has rows per week with 4 links (Applications Received /
# Decisions Made / Appeals Notified / Appeal Decisions), each a numeric ID.
# Top row = most recent week. We only want "Applications Received".

SDCC_LANDING = "https://planning.southdublin.ie/Home/WeeklyLists"
SDCC_DOC_PREFIX = "https://planning.southdublin.ie/Home/ViewWeeklyListDocument/"


def discover_sdcc() -> list[DiscoveredFile]:
    r = _get(SDCC_LANDING)
    soup = BeautifulSoup(r.text, "html.parser")
    # Find the first link whose text starts with "1 Applications Received"
    for a in soup.find_all("a", href=True):
        txt = a.get_text(" ", strip=True)
        if txt.lower().startswith("1 applications received"):
            abs_url = urljoin(SDCC_LANDING, a["href"])
            doc_id = abs_url.rsplit("/", 1)[-1]
            return [DiscoveredFile(
                council_code="sdcc",
                url=abs_url,
                filename=f"sdcc_id{doc_id}.pdf",
                format="pdf",
            )]
    return []


# ---------- Cork City Council ----------
# 2026 weekly lists index page lists all weeks of the current year. PDFs sit
# at /media/{opaque-slug}/report-weekly-lists-planning-applications-received.pdf
# Multiple files share that filename (one per week) — we take the first match,
# which is the most recent on the page.

CORKCITY_LANDING = "https://www.corkcity.ie/en/council-services/services/planning/planning-lists/planning-lists-2026/"


def discover_corkcity() -> list[DiscoveredFile]:
    r = _get(CORKCITY_LANDING)
    # Find all "received" PDFs; first match = most recent
    matches = re.findall(
        r'href="(/media/[^"]+report[- ]?weekly[- ]?lists[- ]?planning[- ]?applications[- ]?received\.pdf)"',
        r.text, re.I,
    )
    if not matches:
        return []
    url = urljoin(CORKCITY_LANDING, matches[0])
    # Synthesize a stable filename including current ISO week
    import datetime as dt
    w = dt.date.today().isocalendar().week
    return [DiscoveredFile(
        council_code="corkcity",
        url=url,
        filename=f"corkcity_w{w}.pdf",
        format="pdf",
        note="Cork City received applications",
    )]


# ---------- Cork County Council ----------
# Drupal site. Weekly PDFs at /system/files/planning-weekly-lists/Week%20{NN}/
# weekly-list-of-planning-applications-received-from-DD-MM-YYYY-to-DD-MM-YYYY-pdf.pdf

CORKCOCO_LANDING = "https://www.corkcoco.ie/en/resident/planning-and-development/planning-weekly-lists"


def discover_corkcoco() -> list[DiscoveredFile]:
    r = _get(CORKCOCO_LANDING)
    # Find all "applications-received" links; first match on the page is the
    # most recent week.
    matches = re.findall(
        r'href="(/system/files/[^"]*weekly-list-of-planning-applications-received[^"]*\.pdf)"',
        r.text, re.I,
    )
    if not matches:
        return []
    url = urljoin(CORKCOCO_LANDING, matches[0])
    # Extract week number from the URL if present, else fall back to ISO week
    m = re.search(r"Week%20(\d{1,2})", matches[0])
    if m:
        week = m.group(1)
    else:
        import datetime as dt
        week = str(dt.date.today().isocalendar().week)
    return [DiscoveredFile(
        council_code="corkcoco",
        url=url,
        filename=f"corkcoco_w{week}.pdf",
        format="pdf",
        note="Cork County received applications",
    )]


COUNCIL_DISCOVERERS = {
    "dcc": discover_dcc,
    "fingal": discover_fingal,
    "dlr": discover_dlr,
    "sdcc": discover_sdcc,
    "corkcity": discover_corkcity,
    "corkcoco": discover_corkcoco,
}

COUNCIL_NAMES = {
    "dcc": "Dublin City Council",
    "fingal": "Fingal County Council",
    "dlr": "Dún Laoghaire-Rathdown County Council",
    "sdcc": "South Dublin County Council",
    "corkcity": "Cork City Council",
    "corkcoco": "Cork County Council",
}


def discover_all() -> list[DiscoveredFile]:
    out: list[DiscoveredFile] = []
    for code, fn in COUNCIL_DISCOVERERS.items():
        try:
            files = fn()
            out.extend(files)
            print(f"[discover] {code}: {len(files)} file(s)")
            for f in files:
                print(f"    -> {f.filename} ({f.format}) {f.note}")
        except Exception as e:
            print(f"[discover] {code}: ERROR {e}")
    return out


if __name__ == "__main__":
    discover_all()
