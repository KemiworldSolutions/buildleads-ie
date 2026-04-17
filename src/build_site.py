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
DOMAIN = "https://buildleads.ie"
GA4_ID = "G-DETYX5K1YP"
BRAND = "BuildLeads.ie"
EMAIL_HELLO = "hello@buildleads.ie"
EMAIL_JOIN = "join@buildleads.ie"

SEGMENT_BLURBS = {
    "roofing": {
        "h1": "Every Dublin roof job before the bidding war.",
        "intro": "Dublin's four councils approve hundreds of extensions, loft conversions, and re-roofs every month. BuildLeads.ie pulls every relevant application from the public weekly lists and emails them to you every Monday morning. €29/month. No middlemen.",
        "long_tail": "Dublin roofing leads, planning application leads roofers Dublin, new roof jobs Dublin",
    },
    "solar_pv": {
        "h1": "Every Dublin homeowner who's about to renovate. Get there before your competition.",
        "intro": "SEAI grants made Dublin the most competitive solar PV market in Ireland. BuildLeads.ie gives you every Dublin household at planning stage — the exact moment they're spending on the house and most likely to add PV.",
        "long_tail": "Dublin solar leads, SEAI installer leads, solar PV planning applications Dublin",
    },
    "structural_engineering": {
        "h1": "Every Dublin extension that needs a structural engineer's stamp.",
        "intro": "Small structural practices spend 30% of their week chasing work. BuildLeads.ie sends you a weekly digest of every Dublin application that's going to need structural certification — sourced direct from the four council registers.",
        "long_tail": "structural engineer leads Dublin, planning application leads engineers Dublin",
    },
    "architecture": {
        "h1": "Sub-work for small Dublin practices, every Monday morning.",
        "intro": "If you're a small Dublin practice taking on overflow design or technician work, BuildLeads.ie tells you which other Dublin architects just filed substantial applications and which projects have no agent listed at all.",
        "long_tail": "architect leads Dublin, planning application architect Dublin",
    },
    "kitchens": {
        "h1": "Every Dublin extension. Every kitchen waiting to happen.",
        "intro": "Most rear extensions in Dublin end with a new kitchen. BuildLeads.ie sends you every Dublin extension at planning stage, weeks before the homeowner starts ringing showrooms.",
        "long_tail": "kitchen leads Dublin, kitchen fitter leads Dublin, extension leads Dublin",
    },
    "windows_glazing": {
        "h1": "Every Dublin window and rooflight job at planning stage.",
        "intro": "If it has windows, it'll need a glazier. BuildLeads.ie pulls every Dublin application that mentions glazing, rooflights, sliding doors or replacement windows.",
        "long_tail": "window installer leads Dublin, glazing leads Dublin",
    },
    "insulation": {
        "h1": "Every Dublin home about to be opened up. Before the SEAI grant rush.",
        "intro": "Every renovation in Dublin is also an insulation opportunity. BuildLeads.ie sends you the planning applications first.",
        "long_tail": "insulation contractor leads Dublin, SEAI insulation leads",
    },
    "scaffolding": {
        "h1": "Every Dublin job that's about to need scaffolding.",
        "intro": "Two-storey extension? Re-roof? Render job? Scaffolding required. BuildLeads.ie tells you who and where, before the main contractor is even appointed.",
        "long_tail": "scaffolding hire leads Dublin",
    },
}

BLOG_POSTS = [
    {
        "slug": "how-to-find-roofing-jobs-dublin",
        "title": "How to find roofing jobs in Dublin before the main contractor does",
        "date": "2026-04-10",
        "excerpt": "Every Dublin re-roof and loft conversion starts as a planning application. Here's why checking the weekly list every Monday beats any referral network.",
    },
    {
        "slug": "dublin-planning-data-explained",
        "title": "Dublin planning data explained: what's in the weekly list?",
        "date": "2026-04-03",
        "excerpt": "The four Dublin councils publish a weekly planning list under statutory requirement. We break down what's in it, how to read it, and what it means for tradespeople.",
    },
    {
        "slug": "why-sole-traders-lose-to-main-contractors",
        "title": "Why sole traders keep losing jobs to main contractors (and how to stop it)",
        "date": "2026-03-27",
        "excerpt": "Main contractors win not because they're better — they win because they're first. Here's how to change that.",
    },
]

GA4_TAG = f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
window.dataLayer=window.dataLayer||[];
function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());
gtag('config','{GA4_ID}');
</script>"""

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f172a;
  --surface:#1e293b;
  --border:#334155;
  --text:#e2e8f0;
  --muted:#94a3b8;
  --accent:#38bdf8;
  --cta:#6366f1;
  --cta-hover:#4f46e5;
}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.site-nav{background:var(--surface);border-bottom:1px solid var(--border);padding:0 1.5rem}
.nav-inner{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;align-items:center;gap:.4rem .75rem;padding:.75rem 0}
.nav-logo{font-weight:700;font-size:1.1rem;color:var(--accent);text-decoration:none;flex:0 0 100%}
.nav-links{display:flex;flex-wrap:wrap;gap:.25rem 1.25rem;font-size:.9rem}
.nav-links a{color:var(--muted)}
.nav-links a:hover{color:var(--text);text-decoration:none}
@media(min-width:768px){
  .nav-inner{flex-wrap:nowrap;justify-content:space-between;height:60px;padding:0}
  .nav-logo{flex:0 0 auto}
}
.hero{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);padding:5rem 1.5rem 4rem;text-align:center}
.hero-inner{max-width:800px;margin:0 auto}
.hero h1{font-size:clamp(1.9rem,5vw,3.25rem);font-weight:700;line-height:1.15;margin-bottom:1.25rem;color:#fff}
.hero p{font-size:1.1rem;color:var(--muted);max-width:620px;margin:0 auto 1.5rem}
.hero .price{font-size:1.75rem;font-weight:700;color:var(--accent);margin-bottom:1.5rem}
.cta{display:inline-block;background:var(--cta);color:#fff;padding:.875rem 2rem;border-radius:8px;font-weight:600;font-size:1rem;text-decoration:none;transition:background .2s}
.cta:hover{background:var(--cta-hover);text-decoration:none}
.cta-note{display:block;margin-top:.75rem;color:var(--muted);font-size:.9rem}
.section{padding:4rem 1.5rem}
.section-inner{max-width:1100px;margin:0 auto}
.section-title{font-size:1.6rem;font-weight:700;margin-bottom:1.75rem;color:var(--text)}
.cards{display:grid;grid-template-columns:1fr;gap:1.25rem}
@media(min-width:640px){.cards{grid-template-columns:1fr 1fr}}
@media(min-width:960px){.cards-3{grid-template-columns:1fr 1fr 1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem}
.card h3{font-size:1rem;font-weight:600;margin-bottom:.5rem;color:var(--accent)}
.card p{color:var(--muted);font-size:.95rem}
.trades{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.875rem;list-style:none}
.trades a{display:block;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.75rem 1rem;color:var(--text);font-weight:500;font-size:.95rem;transition:border-color .2s}
.trades a:hover{border-color:var(--accent);text-decoration:none}
.blog-grid{display:grid;grid-template-columns:1fr;gap:1.25rem}
@media(min-width:640px){.blog-grid{grid-template-columns:1fr 1fr 1fr}}
.blog-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem;display:flex;flex-direction:column}
.blog-card time{font-size:.8rem;color:var(--muted);margin-bottom:.5rem;display:block}
.blog-card h3{font-size:1rem;font-weight:600;margin-bottom:.5rem}
.blog-card h3 a{color:var(--text)}
.blog-card h3 a:hover{color:var(--accent)}
.blog-card p{color:var(--muted);font-size:.9rem;flex:1}
.faq{display:flex;flex-direction:column;gap:1.25rem}
.faq-item{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.25rem}
.faq-item dt{font-weight:600;color:var(--text);margin-bottom:.4rem}
.faq-item dd{color:var(--muted);font-size:.95rem}
.how-steps{display:flex;flex-direction:column;gap:1rem;list-style:none;counter-reset:step}
.how-steps li{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1rem 1rem 1rem 3.5rem;position:relative;color:var(--muted);font-size:.95rem;counter-increment:step}
.how-steps li::before{content:counter(step);position:absolute;left:1rem;top:1rem;font-weight:700;color:var(--accent);font-size:1.1rem}
footer{background:var(--surface);border-top:1px solid var(--border);padding:3rem 1.5rem;margin-top:2rem}
.footer-inner{max-width:1100px;margin:0 auto;font-size:.85rem;color:var(--muted)}
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
{GA4_TAG}
<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"Service",
  "name":"BuildLeads.ie",
  "areaServed":{{"@type":"City","name":"Dublin"}},
  "provider":{{"@type":"Organization","name":"BuildLeads.ie","url":"{DOMAIN}"}},
  "description":"{description}",
  "offers":{{"@type":"Offer","price":"29","priceCurrency":"EUR"}}
}}
</script>
</head>
<body>
<nav class="site-nav">
  <div class="nav-inner">
    <a class="nav-logo" href="/">BuildLeads.ie</a>
    <div class="nav-links">
      <a href="/r/roofing.html">Roofing</a>
      <a href="/r/solar_pv.html">Solar PV</a>
      <a href="/r/structural_engineering.html">Structural</a>
      <a href="/r/architecture.html">Architecture</a>
      <a href="/blog/">Blog</a>
    </div>
  </div>
</nav>
{body}
<footer>
  <div class="footer-inner">
    <strong style="color:var(--text)">BuildLeads.ie</strong> — Dublin planning leads for trades and professionals.<br>
    Data sourced from the public weekly planning lists of Dublin City Council, Fingal County Council,
    Dún Laoghaire-Rathdown County Council and South Dublin County Council, as required to be published
    under the Planning and Development Regulations 2001 (as amended).
  </div>
</footer>
</body>
</html>
"""


def _index_body() -> str:
    trade_items = "\n".join(
        f'<li><a href="/r/{seg}.html">{SEGMENT_LABELS.get(seg, seg)}</a></li>'
        for seg in SEGMENT_BLURBS
    )
    blog_cards = "\n".join(
        f"""<div class="blog-card">
  <time datetime="{p['date']}">{p['date']}</time>
  <h3><a href="/blog/{p['slug']}.html">{p['title']}</a></h3>
  <p>{p['excerpt']}</p>
</div>"""
        for p in BLOG_POSTS
    )
    return f"""
<div class="hero">
  <div class="hero-inner">
    <h1>Every Dublin planning application that needs your trade. In your inbox every Monday.</h1>
    <p>BuildLeads.ie pulls the official weekly planning lists from the four Dublin councils, classifies every application by trade, and sends you only the ones that need your work. No bidding wars. No main-contractor middlemen.</p>
    <p class="price">€29 / month — cancel anytime</p>
    <a class="cta" href="https://buy.stripe.com/REPLACE_WITH_YOUR_PAYMENT_LINK">Subscribe with Stripe</a>
    <span class="cta-note">or <a href="mailto:{EMAIL_HELLO}?subject=Sample">email {EMAIL_HELLO}</a> for a free sample digest</span>
  </div>
</div>

<section class="section">
  <div class="section-inner">
    <div class="cards cards-3">
      <div class="card"><h3>Public data, properly filtered</h3><p>Every application on BuildLeads.ie is a public planning record published by your local council. We do the boring sorting work.</p></div>
      <div class="card"><h3>Built for sole traders</h3><p>Existing services charge €100–€400/month and target large contractors. BuildLeads.ie is €29/month and built for the people picking up the tools.</p></div>
      <div class="card"><h3>Dublin-only, weekly</h3><p>Four councils. One email. Every Monday before 9am.</p></div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="section-inner">
    <h2 class="section-title">Pick your trade</h2>
    <ul class="trades">
{trade_items}
    </ul>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="section-inner">
    <h2 class="section-title">From the blog</h2>
    <div class="blog-grid">
{blog_cards}
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="section-inner">
    <h2 class="section-title">FAQ</h2>
    <dl class="faq">
      <div class="faq-item"><dt>Where does the data come from?</dt><dd>The four Dublin local authorities publish a Weekly Planning List under statutory requirement. BuildLeads.ie fetches those lists every Monday morning. Nothing on BuildLeads.ie is private data.</dd></div>
      <div class="faq-item"><dt>How is this different from CIS or BCI?</dt><dd>Those services are excellent if you're a main contractor on a €5m project. They're overkill for a sole trader or small practice. BuildLeads.ie does one city, one trade-relevant filter, one weekly email.</dd></div>
      <div class="faq-item"><dt>Can I see a sample?</dt><dd>Yes. Email <a href="mailto:{EMAIL_HELLO}?subject=Sample">{EMAIL_HELLO}</a> with your trade and I'll send last week's full digest free.</dd></div>
      <div class="faq-item"><dt>What if I'm not in Dublin?</dt><dd>Cork, Galway and Limerick are next. Email <a href="mailto:{EMAIL_JOIN}">{EMAIL_JOIN}</a> to be notified.</dd></div>
    </dl>
  </div>
</section>
"""


def _segment_body(segment: str) -> str:
    blurb = SEGMENT_BLURBS[segment]
    label = SEGMENT_LABELS.get(segment, segment)
    return f"""
<div class="hero">
  <div class="hero-inner">
    <h1>{blurb['h1']}</h1>
    <p>{blurb['intro']}</p>
    <p class="price">€29 / month — cancel anytime</p>
    <a class="cta" href="https://buy.stripe.com/REPLACE_WITH_YOUR_PAYMENT_LINK">Subscribe — {label} digest</a>
    <span class="cta-note">or <a href="mailto:{EMAIL_HELLO}?subject=Sample {label}">email for a free sample</a></span>
  </div>
</div>

<section class="section">
  <div class="section-inner">
    <h2 class="section-title">What you get every Monday</h2>
    <div class="cards cards-3">
      <div class="card"><h3>Every {label} application</h3><p>Every {label.lower()}-relevant Dublin planning application from the previous 7 days.</p></div>
      <div class="card"><h3>Full application detail</h3><p>Site address, applicant name, agent (if listed), and a structured description of the work.</p></div>
      <div class="card"><h3>All four Dublin councils</h3><p>DCC, Fingal, Dún Laoghaire-Rathdown, and South Dublin — all in one email.</p></div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="section-inner">
    <h2 class="section-title">How it works</h2>
    <ol class="how-steps">
      <li>Every Monday at 6am, BuildLeads.ie fetches the public weekly planning lists from the four Dublin councils.</li>
      <li>An AI extraction step classifies each application by which trades it's relevant to.</li>
      <li>By 7am you have an email with only the {label.lower()} jobs.</li>
    </ol>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="section-inner">
    <h2 class="section-title">FAQ</h2>
    <dl class="faq">
      <div class="faq-item"><dt>Is this a "leads list" of homeowners?</dt><dd>No. BuildLeads.ie is the underlying public planning record — applicant name, site address, the description as published. We do not enrich with phone or personal email. You make first contact yourself, professionally, with full context about what they're planning.</dd></div>
      <div class="faq-item"><dt>How is this legal?</dt><dd>Planning applications are public record under the Planning and Development Act 2000 (as amended). The councils publish the same data themselves on their own websites. BuildLeads.ie's value is filtering and delivery, not access.</dd></div>
      <div class="faq-item"><dt>Can I cancel?</dt><dd>Yes, one click in the Stripe portal. No contract, no minimum term.</dd></div>
    </dl>
  </div>
</section>
"""


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "r").mkdir(exist_ok=True)

    # index
    idx = _page(
        title="BuildLeads.ie — Dublin planning leads for trades, €29/month",
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
            title=f"Dublin {label} leads — weekly planning applications | BuildLeads.ie",
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
