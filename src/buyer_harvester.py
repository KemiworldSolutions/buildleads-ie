"""
Buyer harvester — hands-free DuckDuckGo-based version.

Strategy:
  1. For each segment, run a handful of Dublin-scoped DDG searches.
  2. Extract organic result domains (skip ads and known directories).
  3. Visit each domain's homepage + /contact variants.
  4. Extract public emails whose domain matches the company's own website.
  5. Write buyers/{segment}.csv.

Why DDG HTML:
  - No API key, no Cloudflare on DDG itself.
  - Returns real SERP links in a stable `.result__a` structure.
  - Links are wrapped as /l/?uddg=<url-encoded target> — we unwrap them.

Hard rules:
  - Only visits public homepages + contact pages.
  - Rate-limited (1s between DDG queries, 0.4s between site fetches).
  - Skips personal email domains and template placeholders.
  - Only accepts emails whose domain matches the company's own site root —
    kills tracking pixels, CDN noise, stock "example@wordpress" garbage.
  - Skips known aggregator/directory domains so we harvest operators,
    not middlemen.

Run:
    python -m src.buyer_harvester               # all segments
    python -m src.buyer_harvester roofing       # one segment
"""

from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

BUYERS_DIR = Path("buyers")
DEEPSEEK_MODEL = "deepseek-chat"
SEED_COUNT_PER_SEGMENT = 50  # ask DeepSeek for this many real companies

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.ie", "hotmail.com", "hotmail.ie",
    "outlook.com", "outlook.ie", "live.ie", "live.com", "eircom.net",
    "icloud.com", "me.com", "aol.com",
}

# Skip aggregators and directories — we want operators, not middlemen.
SKIP_DOMAINS = {
    "tradesmen.ie", "myhammer.ie", "rated-people.com", "ratedpeople.com",
    "goldenpages.ie", "yelp.com", "yelp.ie", "facebook.com", "linkedin.com",
    "instagram.com", "twitter.com", "x.com", "youtube.com", "tiktok.com",
    "pinterest.com", "google.com", "bing.com", "wikipedia.org", "reddit.com",
    "indeed.com", "indeed.ie", "jobs.ie", "irishjobs.ie", "thejournal.ie",
    "rte.ie", "independent.ie", "irishtimes.com", "boards.ie",
    "checkatrade.com", "trustpilot.com", "yell.com", "houzz.com", "bark.com",
    "seai.ie", "engineersireland.ie", "riai.ie", "citizensinformation.ie",
    "dublincity.ie", "fingal.ie", "dlrcoco.ie", "sdcc.ie",
    "duckduckgo.com", "wordpress.com", "wix.com", "squarespace.com",
    "amazon.com", "amazon.co.uk", "ebay.ie", "ebay.co.uk", "diy.com",
    "woodiesdiy.com",
}

BAD_LOCAL_PARTS = {"example", "test", "noreply", "no-reply", "donotreply", "sentry"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Irish phone numbers: +353, 00353, or leading 0 then 1-9 digit prefix.
# Accepts spaces, dashes, parentheses, dots as separators. 7–11 total digits after prefix.
PHONE_RE = re.compile(
    r"(?:\+353|00353|\(0\)|\b0)\s*[\-\.\(\)\s]*\d{1,3}[\-\.\(\)\s]*\d{3,4}[\-\.\(\)\s]*\d{3,4}"
)


@dataclass
class Segment:
    name: str
    description: str  # plain-English brief for DeepSeek


SEGMENTS: list[Segment] = [
    Segment("roofing", "roofing contractors and roof repair companies in Dublin (slate, tile, flat roofs, gutters)"),
    Segment("solar_pv", "solar PV and battery storage installers in Dublin (SEAI-registered where possible)"),
    Segment("structural_engineering", "chartered structural engineering practices in Dublin offering residential and commercial structural design"),
    Segment("architecture", "RIAI-registered architecture practices in Dublin working on residential extensions, renovations, and new builds"),
    Segment("kitchens", "bespoke kitchen design and installation companies in Dublin"),
    Segment("windows_glazing", "window, glazing and double-glazing installation companies in Dublin"),
    Segment("insulation", "insulation contractors in Dublin (cavity wall, external wall, attic insulation)"),
    Segment("scaffolding", "scaffolding hire and erection companies in Dublin"),
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _get(client: httpx.Client, url: str) -> httpx.Response:
    r = client.get(url)
    r.raise_for_status()
    return r


def _unwrap_ddg(href: str) -> str | None:
    """DDG wraps links as //duckduckgo.com/l/?uddg=<encoded>. Unwrap to real URL."""
    if href.startswith("//"):
        href = "https:" + href
    try:
        qs = parse_qs(urlparse(href).query)
    except Exception:
        return None
    target = qs.get("uddg", [None])[0]
    if not target:
        return None
    target = unquote(target)
    # DDG y.js ad redirects look like https://duckduckgo.com/y.js?ad_domain=...
    if "duckduckgo.com/y.js" in target or "ad_domain=" in target:
        return None
    return target


def _root_domain(host: str) -> str:
    host = host.lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    # Naive root: last two labels (handles .ie, .com; imperfect for .co.uk)
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "com", "org", "gov", "ac"} and parts[-1] == "uk":
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def deepseek_seed(segment_name: str, description: str, n: int = SEED_COUNT_PER_SEGMENT) -> list[str]:
    """Ask DeepSeek for ~n real Dublin companies in this segment, return root domains."""
    from .extract import _get_client
    client = _get_client()
    system = (
        "You are a local-business research assistant for Dublin, Ireland. "
        "When asked for companies in a trade, return ONLY real, currently-operating "
        "Dublin-based businesses that you are highly confident exist. Never invent. "
        "If you are unsure a company is real, skip it. Prefer SMEs over large chains."
    )
    user = (
        f"List {n} real Dublin, Ireland businesses in this category: {description}.\n"
        "Return STRICT JSON, no prose, matching:\n"
        '{"companies": [{"name": "...", "website": "https://..."}]}\n'
        "Rules:\n"
        "- Only include businesses whose website you are confident is real and correct.\n"
        "- website must be the full https:// URL to their own site (not Facebook, not directories).\n"
        "- Skip anything you are unsure about rather than guessing.\n"
        "- Prefer independent Dublin operators over national chains.\n"
    )
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    import json as _json
    try:
        data = _json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"  [deepseek] parse failed: {e}")
        return []
    domains: list[str] = []
    seen: set[str] = set()
    for c in data.get("companies", []):
        site = (c.get("website") or "").strip()
        if not site:
            continue
        if not site.startswith(("http://", "https://")):
            site = "https://" + site
        host = urlparse(site).netloc.lower()
        root = _root_domain(host)
        if not root or root in SKIP_DOMAINS or root in seen:
            continue
        seen.add(root)
        domains.append(root)
    return domains


def _is_business_email(email: str, site_root: str) -> bool:
    email = email.lower()
    local, _, domain = email.partition("@")
    if domain in PERSONAL_EMAIL_DOMAINS:
        return False
    if local in BAD_LOCAL_PARTS or local.startswith("wordpress") or "sentry" in local:
        return False
    # Email domain root must match site domain root
    return _root_domain(domain) == site_root


def _extract_emails(html: str, site_root: str) -> list[str]:
    found = set()
    for raw in EMAIL_RE.findall(html):
        if _is_business_email(raw, site_root):
            found.add(raw.lower())
    return sorted(found)


def _normalise_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("00353"):
        digits = "+353" + digits[5:]
    elif digits.startswith("0") and not digits.startswith("+"):
        digits = "+353" + digits[1:]
    return digits


def _extract_phones(html: str) -> list[str]:
    # Strip tracking-ID / date-looking strings by requiring the match to come
    # from text that doesn't look like a filename or a CSS class.
    # Crude: ignore matches inside <script> and <style> blocks.
    cleaned = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", " ", cleaned, flags=re.I | re.S)
    found = set()
    for raw in PHONE_RE.findall(cleaned):
        norm = _normalise_phone(raw)
        # Irish numbers are +353 followed by 7–10 digits
        digits_only = re.sub(r"\D", "", norm)
        if 10 <= len(digits_only) <= 13 and norm.startswith("+353"):
            found.add(norm)
    return sorted(found)


def _find_contact_form_url(html: str, base_url: str) -> str:
    """Find a link to a contact page (fallback if no email/phone)."""
    # Look for any anchor whose href or text mentions 'contact'
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{0,80})</a>', html, re.I):
        href, text = m.group(1), m.group(2)
        if "contact" in href.lower() or "contact" in text.lower():
            return urljoin(base_url, href)
    return ""


def enrich_domain(root: str) -> dict | None:
    """Visit root domain's homepage + contact variants.
    Returns a row if we found email OR phone OR contact form URL, else None."""
    candidate_urls = [
        f"https://{root}/",
        f"https://www.{root}/",
        f"https://{root}/contact",
        f"https://{root}/contact-us",
        f"https://www.{root}/contact",
        f"https://www.{root}/contact-us",
        f"https://{root}/get-in-touch",
        f"https://www.{root}/get-in-touch",
    ]
    emails: set[str] = set()
    phones: set[str] = set()
    contact_form_url = ""
    company_name = ""
    headers = {"User-Agent": BROWSER_UA}
    with httpx.Client(timeout=12, follow_redirects=True, headers=headers) as c:
        for url in candidate_urls:
            try:
                r = c.get(url)
                if r.status_code >= 400:
                    continue
            except Exception:
                continue
            if not company_name:
                m = re.search(r"<title[^>]*>([^<]{3,120})</title>", r.text, re.I)
                if m:
                    company_name = re.sub(r"\s+", " ", m.group(1)).strip()
            for e in _extract_emails(r.text, root):
                emails.add(e)
            for p in _extract_phones(r.text):
                phones.add(p)
            if not contact_form_url:
                contact_form_url = _find_contact_form_url(r.text, str(r.url))
            if emails and phones:
                break  # got both, no need to keep crawling
            time.sleep(0.3)

    # Accept if we have at least one reachable channel
    if not emails and not phones and not contact_form_url:
        return None

    return {
        "company": company_name or root,
        "email": sorted(emails)[0] if emails else "",
        "all_emails": ";".join(sorted(emails)),
        "phone": sorted(phones)[0] if phones else "",
        "all_phones": ";".join(sorted(phones)),
        "contact_form_url": contact_form_url,
        "website": f"https://{root}",
        "source": "deepseek",
    }


def harvest_segment(seg: Segment) -> list[dict]:
    print(f"[harvest] {seg.name}")
    try:
        all_domains = deepseek_seed(seg.name, seg.description)
    except Exception as e:
        print(f"  [deepseek] seed failed: {e}")
        return []
    print(f"  [deepseek] {len(all_domains)} candidate domains")

    rows: list[dict] = []
    for i, root in enumerate(all_domains, 1):
        try:
            row = enrich_domain(root)
        except Exception as e:
            print(f"  [skip] {root}: {e}")
            continue
        if row:
            row["segment"] = seg.name
            rows.append(row)
        if i % 10 == 0:
            print(f"  [{i}/{len(all_domains)}] {len(rows)} with emails")
        time.sleep(0.4)
    with_email = sum(1 for r in rows if r.get("email"))
    with_phone = sum(1 for r in rows if r.get("phone"))
    print(f"[harvest] {seg.name}: {len(rows)}/{len(all_domains)} reachable "
          f"({with_email} email, {with_phone} phone)")
    return rows


def write_csv(seg_name: str, rows: list[dict]) -> Path:
    BUYERS_DIR.mkdir(parents=True, exist_ok=True)
    out = BUYERS_DIR / f"{seg_name}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "segment", "company", "email", "all_emails",
            "phone", "all_phones", "contact_form_url",
            "website", "source",
        ])
        writer.writeheader()
        writer.writerows(rows)
    return out


def harvest_all(skip_existing: bool = True) -> None:
    BUYERS_DIR.mkdir(parents=True, exist_ok=True)
    for seg in SEGMENTS:
        out = BUYERS_DIR / f"{seg.name}.csv"
        if skip_existing and out.exists() and out.stat().st_size > 100:
            print(f"[skip] {seg.name}: {out} already exists")
            continue
        rows = harvest_segment(seg)
        if rows:
            p = write_csv(seg.name, rows)
            print(f"[wrote] {p}")
        # Cool-off between segments to avoid DDG rate limiting
        print("  [cooldown] sleeping 20s before next segment")
        time.sleep(20)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        wanted = sys.argv[1]
        for s in SEGMENTS:
            if s.name == wanted:
                rows = harvest_segment(s)
                if rows:
                    p = write_csv(s.name, rows)
                    print(f"[wrote] {p}")
                break
    else:
        harvest_all()
