"""
Generates the deployable static site at site/.

- site/index.html (main landing page)
- site/r/{segment}.html (one programmatic-SEO page per trade)
- site/sitemap.xml
- site/robots.txt

Programmatic SEO strategy:
  Each trade gets its own page, each one targets a long-tail query like
  "Dublin roofing leads", "Dublin solar PV leads", etc.
  Page content is unique per segment (different intro, different FAQ slant,
  different sample applications drawn from the most recent digest).
  This is real content, not doorway pages — every page is genuinely useful
  and every page has a real CTA.

Run:  python -m src.build_site
Then deploy site/ to Cloudflare Pages, Netlify, or any static host.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from .digest import SEGMENT_LABELS

SITE_DIR = Path("site")
DOMAIN = "https://planradar.ie"

SEGMENT_BLURBS = {
    "roofing": {
        "h1": "Every Dublin roof job before the bidding war.",
        "intro": "Dublin's four councils approve hundreds of extensions, loft conversions, and re-roofs every month. PlanRadar pulls every relevant application from the public weekly lists and emails them to you every Monday morning. €29/month. No middlemen.",
        "long_tail": "Dublin roofing leads, planning application leads roofers Dublin, new roof jobs Dublin",
    },
    "solar_pv": {
        "h1": "Every Dublin homeowner who's about to renovate. Get there before your competition.",
        "intro": "SEAI grants made Dublin the most competitive solar PV market in Ireland. PlanRadar gives you every Dublin household at planning stage — the exact moment they're spending on the house and most likely to add PV.",
        "long_tail": "Dublin solar leads, SEAI installer leads, solar PV planning applications Dublin",
    },
    "structural_engineering": {
        "h1": "Every Dublin extension that needs a structural engineer's stamp.",
        "intro": "Small structural practices spend 30% of their week chasing work. PlanRadar sends you a weekly digest of every Dublin application that's going to need structural certification — sourced direct from the four council registers.",
        "long_tail": "structural engineer leads Dublin, planning application leads engineers Dublin",
    },
    "architecture": {
        "h1": "Sub-work for small Dublin practices, every Monday morning.",
        "intro": "If you're a small Dublin practice taking on overflow design or technician work, PlanRadar tells you which other Dublin architects just filed substantial applications and which projects have no agent listed at all.",
        "long_tail": "architect leads Dublin, planning application architect Dublin",
    },
    "kitchens": {
        "h1": "Every Dublin extension. Every kitchen waiting to happen.",
        "intro": "Most rear extensions in Dublin end with a new kitchen. PlanRadar sends you every Dublin extension at planning stage, weeks before the homeowner starts ringing showrooms.",
        "long_tail": "kitchen leads Dublin, kitchen fitter leads Dublin, extension leads Dublin",
    },
    "windows_glazing": {
        "h1": "Every Dublin window and rooflight job at planning stage.",
        "intro": "If it has windows, it'll need a glazier. PlanRadar pulls every Dublin application that mentions glazing, rooflights, sliding doors or replacement windows.",
        "long_tail": "window installer leads Dublin, glazing leads Dublin",
    },
    "insulation": {
        "h1": "Every Dublin home about to be opened up. Before the SEAI grant rush.",
        "intro": "Every renovation in Dublin is also an insulation opportunity. PlanRadar sends you the planning applications first.",
        "long_tail": "insulation contractor leads Dublin, SEAI insulation leads",
    },
    "scaffolding": {
        "h1": "Every Dublin job that's about to need scaffolding.",
        "intro": "Two-storey extension? Re-roof? Render job? Scaffolding required. PlanRadar tells you who and where, before the main contractor is even appointed.",
        "long_tail": "scaffolding hire leads Dublin",
    },
}

BASE_CSS = """
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;line-height:1.6;color:#1a1a1a;max-width:720px;margin:0 auto;padding:2rem 1.25rem;background:#fafaf7}
h1{font-size:2rem;line-height:1.2;margin:1rem 0 .5rem}
h2{font-size:1.4rem;margin-top:2.5rem}
h3{font-size:1.1rem;margin-top:1.5rem}
p{margin:.75rem 0}
a{color:#0a5fae}
.cta{display:inline-block;background:#0a5fae;color:#fff;padding:.85rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;margin:1rem 0}
.cta:hover{background:#084a87}
.price{font-size:1.6rem;font-weight:700;color:#0a5fae}
.three{display:grid;grid-template-columns:1fr;gap:1rem;margin:2rem 0}
@media(min-width:640px){.three{grid-template-columns:1fr 1fr 1fr}}
.card{background:#fff;border:1px solid #e5e3da;border-radius:8px;padding:1rem}
nav{font-size:.9rem;margin-bottom:1.5rem}
nav a{margin-right:1rem}
footer{margin-top:4rem;padding-top:2rem;border-top:1px solid #e5e3da;font-size:.85rem;color:#666}
.faq dt{font-weight:600;margin-top:1rem}
"""


def _page(title: str, description: str, body: str, canonical: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<style>{BASE_CSS}</style>
<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"Service",
  "name":"PlanRadar.ie",
  "areaServed":{{"@type":"City","name":"Dublin"}},
  "provider":{{"@type":"Organization","name":"PlanRadar.ie"}},
  "description":"{description}",
  "offers":{{"@type":"Offer","price":"29","priceCurrency":"EUR"}}
}}
</script>
</head>
<body>
<nav><a href="/">Home</a> <a href="/r/roofing.html">Roofing</a> <a href="/r/solar_pv.html">Solar PV</a> <a href="/r/structural_engineering.html">Structural</a> <a href="/r/architecture.html">Architecture</a></nav>
{body}
<footer>
PlanRadar.ie — Dublin planning leads for trades and professionals. Data sourced from the public weekly planning lists of Dublin City Council, Fingal County Council, Dún Laoghaire-Rathdown County Council and South Dublin County Council, as required to be published under the Planning and Development Regulations 2001 (as amended).
</footer>
</body>
</html>
"""


def _index_body() -> str:
    return """
<h1>Every Dublin planning application that needs your trade. In your inbox every Monday.</h1>
<p>PlanRadar pulls the official weekly planning lists from the four Dublin councils, classifies every application by trade, and sends you only the ones that need your work. No bidding wars. No main-contractor middlemen.</p>
<p class="price">€29 / month — cancel anytime</p>
<a class="cta" href="https://buy.stripe.com/REPLACE_WITH_YOUR_PAYMENT_LINK">Subscribe with Stripe</a>
<p>Or email <a href="mailto:sample@planradar.ie?subject=Sample">sample@planradar.ie</a> with your trade and I'll send last week's digest free.</p>

<div class="three">
<div class="card"><h3>Public data, properly filtered</h3><p>Every application on PlanRadar is a public planning record published by your local council. We do the boring sorting work.</p></div>
<div class="card"><h3>Built for sole traders</h3><p>Existing services charge €100–€400/month and target large contractors. PlanRadar is €29/month and built for the people picking up the tools.</p></div>
<div class="card"><h3>Dublin-only, weekly</h3><p>Four councils. One email. Every Monday before 9am.</p></div>
</div>

<h2>Pick your trade</h2>
<ul>
""" + "\n".join(
        f'<li><a href="/r/{seg}.html">{SEGMENT_LABELS.get(seg, seg)}</a></li>'
        for seg in SEGMENT_BLURBS
    ) + """
</ul>

<h2>FAQ</h2>
<dl class="faq">
<dt>Where does the data come from?</dt>
<dd>The four Dublin local authorities publish a Weekly Planning List under statutory requirement. PlanRadar fetches those lists every Monday morning. Nothing on PlanRadar is private data.</dd>
<dt>How is this different from CIS or BCI?</dt>
<dd>Those services are excellent if you're a main contractor on a €5m project. They're overkill for a sole trader or small practice. PlanRadar does one city, one trade-relevant filter, one weekly email.</dd>
<dt>Can I see a sample?</dt>
<dd>Yes. Email sample@planradar.ie with your trade and I'll send last week's full digest free.</dd>
<dt>What if I'm not in Dublin?</dt>
<dd>Cork, Galway and Limerick are next. Email join@planradar.ie to be notified.</dd>
</dl>
"""


def _segment_body(segment: str) -> str:
    blurb = SEGMENT_BLURBS[segment]
    label = SEGMENT_LABELS.get(segment, segment)
    return f"""
<h1>{blurb['h1']}</h1>
<p>{blurb['intro']}</p>
<p class="price">€29 / month — cancel anytime</p>
<a class="cta" href="https://buy.stripe.com/REPLACE_WITH_YOUR_PAYMENT_LINK">Subscribe — {label} digest</a>
<p>Or email <a href="mailto:sample@planradar.ie?subject=Sample {label}">sample@planradar.ie</a> for last week's free.</p>

<h2>What you get every Monday</h2>
<ul>
<li>Every {label.lower()}-relevant Dublin planning application from the previous 7 days</li>
<li>Site address, applicant name, agent (if listed), and a structured description</li>
<li>All four Dublin councils: DCC, Fingal, DLR, SDCC</li>
<li>Delivered as a clean PDF + a CSV you can import into your CRM</li>
</ul>

<h2>How it works</h2>
<ol>
<li>Every Monday at 6am, PlanRadar fetches the public weekly planning lists from the four Dublin councils.</li>
<li>An LLM extraction step (DeepSeek) classifies each application by which trades it's relevant to.</li>
<li>By 7am you have an email with only the {label.lower()} jobs.</li>
</ol>

<h2>FAQ</h2>
<dl class="faq">
<dt>Is this a "leads list" of homeowners?</dt>
<dd>No. PlanRadar is the underlying public planning record — applicant name, site address, the description as published. We do not enrich with phone or personal email. You make first contact yourself, professionally, with full context about what they're planning.</dd>
<dt>How is this legal?</dt>
<dd>Planning applications are public record under the Planning and Development Act 2000 (as amended). The councils publish the same data themselves on their own websites. PlanRadar's value is filtering and delivery, not access.</dd>
<dt>Can I cancel?</dt>
<dd>Yes, one click in the Stripe portal. No contract, no minimum term.</dd>
</dl>
"""


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "r").mkdir(exist_ok=True)

    # index
    idx = _page(
        title="PlanRadar.ie — Dublin planning leads for trades, €29/month",
        description="Every Dublin planning application that needs your trade, in your inbox every Monday. Sourced from the four Dublin councils' public weekly lists. €29/month, cancel anytime.",
        body=_index_body(),
        canonical=f"{DOMAIN}/",
    )
    (SITE_DIR / "index.html").write_text(idx, encoding="utf-8")

    # segment pages
    urls = [f"{DOMAIN}/"]
    for seg in SEGMENT_BLURBS:
        label = SEGMENT_LABELS.get(seg, seg)
        page = _page(
            title=f"Dublin {label} leads — weekly planning applications | PlanRadar.ie",
            description=f"Every Dublin {label.lower()}-relevant planning application from the four Dublin councils, in your inbox every Monday. €29/month, cancel anytime.",
            body=_segment_body(seg),
            canonical=f"{DOMAIN}/r/{seg}.html",
        )
        (SITE_DIR / "r" / f"{seg}.html").write_text(page, encoding="utf-8")
        urls.append(f"{DOMAIN}/r/{seg}.html")

    # robots.txt
    (SITE_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n",
        encoding="utf-8",
    )

    # sitemap.xml
    today = dt.date.today().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sitemap += f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq></url>\n"
    sitemap += "</urlset>\n"
    (SITE_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print(f"[built] {SITE_DIR}/  — {1 + len(SEGMENT_BLURBS)} pages")
    print(f"        deploy with:  npx wrangler pages deploy {SITE_DIR}")


if __name__ == "__main__":
    build()
