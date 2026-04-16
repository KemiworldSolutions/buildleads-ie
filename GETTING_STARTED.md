# Getting started — first 60 minutes

Do these in order. Don't skip ahead.

## 0. Prereqs
- Python 3.11+ installed
- A DeepSeek account at https://platform.deepseek.com (top up €10)
- A domain registrar account (you'll buy a domain later, not now)

## 1. Install (3 minutes)
```powershell
cd E:\Work\OPENCLAW
.\run.ps1 install
copy .env.example .env
notepad .env       # paste your DeepSeek API key
```

## 2. Offline smoke test (5 minutes, ~€0.01 of API spend)
This runs the extraction pipeline against a bundled fixture so you can verify
everything works without touching live council URLs.

```powershell
.\run.ps1 test
```

You should see:
- 8 entries extracted from `fixtures/sample_dcc_week.txt`
- A digest written to `out/digests/roofing_<today>.md` etc.

Open one of the digest files. If it looks like a clean per-trade list, the
core pipeline works.

## 3. Build the static site (1 minute)
```powershell
.\run.ps1 site
```
Open `site\index.html` in a browser. You should see a real landing page with
a nav, pricing, FAQ, and per-segment pages under `site\r\`.

## 4. Wire up the live council URLs (15 minutes)
Open each URL below in a browser, find the most recent "Weekly List" PDF link,
and paste it into `src/sources.py`:

- https://www.dublincity.ie/residential/planning/planning-applications/weekly-planning-lists
- https://www.fingal.ie/council/service/planning-application-weekly-lists
- https://www.dlrcoco.ie/en/planning/weekly-lists
- https://www.sdcc.ie/en/services/planning/planning-applications/weekly-lists/

Then run:
```powershell
.\run.ps1 fetch
.\run.ps1 extract
```

You now have real Dublin planning data, classified by trade, in `out/digests/`.

## 5. Harvest your first buyer list (10 minutes)
```powershell
.\run.ps1 harvest
```

This will probably FAIL on the first run because the CSS selectors in
`src/buyer_harvester.py` need to be checked against the live page structure.
Open the SEAI installer page in a browser, right-click an installer card,
"Inspect", and update the selectors in `SOURCES`. Re-run.

You should end up with `buyers/solar_pv.csv`, `buyers/roofing.csv`, etc.

## 6. Generate outreach drafts (5 minutes, ~€0.05 of API spend)
```powershell
python -m src.outreach solar_pv 30
```

30 personalised cold emails get written to `outreach\drafts\`. Open every
single one and read it. Edit any that are awkward. Delete any that don't
make sense for the recipient.

## 7. Buy a domain + set up email (20 minutes)
- Buy a domain at blacknight.ie or namecheap (~€15/yr)
- Sign up for Fastmail with that domain (€5/mo)
- Add SPF, DKIM, DMARC DNS records (Fastmail tells you what to add)
- Wait an hour for DNS to propagate
- Send yourself a test email through Fastmail's web UI

## 8. Stripe (30 minutes)
Follow STRIPE.md.

## 9. Deploy the site (5 minutes)
Follow DEPLOY.md section 1.

## 10. Send the first 10 emails (60 minutes elapsed, ~15 min hands-on)
```powershell
.\run.ps1 dry-send
```
Read the output. If the queue looks right:
```powershell
.\run.ps1 send
```
This sends 10 emails over 15 minutes (90s gap each). Watch the log. Stop
with Ctrl-C if anything looks wrong.

## 11. The next 7 days
- Day 2-4: send 10 more per day, switching segments
- Watch responses in your inbox
- Convert at least 1 sample request → paying subscriber by the end of week 1
- If 0 conversions after 30 sends in a segment, switch segments before changing the product

## What you have at this point
- A working extraction pipeline against real council data
- A real deployable landing site with one page per segment (programmatic SEO)
- A buyer-harvesting framework you can extend to any new directory
- A draft-generator + human-gated sender with rate limiting and audit trail
- A clear path from 0 to first paying customer

## What you still have to do yourself
- Pick the right buyer segment for *your* situation in Dublin
- Read every draft email before sending
- Reply to every response personally for the first 50 customers
- Decide when to expand to Cork / Galway / Limerick
