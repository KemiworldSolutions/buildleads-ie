# Dublin Planning Leads (working name: PlanRadar.ie)

A weekly lead-gen feed of Dublin planning applications, classified and routed
to the trades and professionals who care about each one.

**One-line pitch:** "Every new Dublin planning application that needs your trade, in your inbox every Monday. €29/mo. No login. Cancel anytime."

## Why this exists

Dublin's four local authorities (DCC, Fingal, DLR, SDCC) publish weekly
planning lists by statutory requirement. The lists are public PDFs/HTML
with messy free-text descriptions. Existing aggregators (CIS, BCI, Build Info)
charge €100–€400/month and target large contractors. There is no cheap,
focused, sole-trader-friendly product in this space.

The arbitrage:
- Source data: free + statutorily published
- Extraction cost: ~€0.001 per application via DeepSeek (cache-hit prompt)
- Buyer willingness to pay: €29–€49/month for ~50–150 relevant leads
- Buyer pool in Dublin: thousands of registered tradespeople and professionals

## Pipeline

```
[4 council weekly lists]  --fetch-->  raw/{council}/{date}.{pdf|html}
                              |
                              v
                    [DeepSeek extraction]
                              |
                              v
                  structured/applications.jsonl
                              |
                              v
              [classify by trade interest]
                              |
                              v
            per-trade weekly digest emails
```

## Files

- `src/sources.py` — council endpoints + fetch instructions (config, edit me)
- `src/scraper.py` — pulls the latest weekly lists from each council
- `src/extract.py` — DeepSeek extraction with a cache-friendly system prompt
- `src/classify.py` — assigns each application to one or more trade buckets
- `src/pipeline.py` — runs the whole thing end-to-end
- `src/digest.py` — builds per-trade weekly markdown/HTML digests
- `outreach/cold_email.md` — first-30-buyers outreach template
- `landing/copy.md` — Carrd / one-page landing copy
- `buyers/buyer_segments.md` — who to email, why, where to find them
- `requirements.txt` — Python deps
- `.env.example` — copy to `.env` and fill in DEEPSEEK_API_KEY

## Runbook (first 7 days)

**Day 1 — set up**
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`, paste DeepSeek API key (sign up at platform.deepseek.com, $10 of credit is enough for the first month)
3. Open `src/sources.py` and confirm/fix the four council URLs by visiting each council's planning page (URLs drift; verify before first run)
4. `python -m src.pipeline --once` — pulls last week's lists from all 4 councils, extracts, classifies, writes `out/digests/*.md`

**Day 2 — build the buyer list**
1. Open `buyers/buyer_segments.md`
2. For the top 3 segments (roofers, solar installers, structural engineers), find 30 names with public emails. Sources: goldenpages.ie, Engineers Ireland directory, SEAI registered installer list, Construction Industry Federation member directory.
3. Save to `buyers/dublin_30.csv` (name, email, segment, source)

**Day 3 — landing page**
1. Sign up for Carrd ($19/yr) or use a free Cloudflare Pages static site
2. Paste `landing/copy.md` into the page
3. Add a Stripe payment link (€29/mo subscription) — Stripe Ireland onboarding is same-day for most sole traders
4. Live URL goes in the email

**Day 4 — first 30 emails**
1. Generate the previous week's digest for each segment with `python -m src.digest --segment roofing --week last`
2. Use `outreach/cold_email.md` as the template; attach the relevant segment digest as proof
3. Send 30 personalised emails (do not blast; CAN-SPAM/GDPR — see notes in cold_email.md)

**Day 5–6 — respond, iterate**
- Conversions: aim for 1–3 paying. If 0, the *segment* is wrong, not the product. Try a different segment before changing the product.

**Day 7 — decide**
- If ≥1 paying customer: continue, expand to Cork (copy `sources.py` block, change URLs)
- If 0 after talking to ≥10 humans: change the buyer segment, not the strategy
- If 0 after trying 3 segments: the underlying assumption is wrong — stop and reassess

## What this project deliberately does NOT do

- No autonomous purchasing, hiring, or contract-signing
- No crypto wallet hookup
- No "agent in a loop spending money"
- No scraping behind logins
- No personal data beyond what councils already publish (applicant names appear on planning lists by law; we do not enrich with phone/email lookups)

The agent extracts and formats. The human (you) sells.

## Cost ceiling

- DeepSeek: under €5/mo at 4 councils × ~200 applications/week
- VPS (optional, for cron): €5/mo Hetzner CX11
- Carrd: €19/yr
- Stripe: 1.5% + €0.25 per EU charge
- **Total monthly burn: under €15.** $100 of API credit is roughly 18 months of runway at full Dublin volume.

## Legal notes (read before launching)

1. Planning application data is public record under the Planning and Development Act 2000 (as amended). Aggregating and reselling it is established practice (CIS, BCI, etc. have done so for 20+ years).
2. Applicant names appear on the public register. Do NOT enrich with phone/email from third-party sources without consent — that crosses into GDPR territory.
3. Cold B2B email in Ireland is permitted to corporate addresses (info@, sales@, named role addresses at registered companies) under the ePrivacy Regulations 2011 SI 336, with an opt-out in every message. Personal Gmail/Yahoo addresses of sole traders are a grey area — when in doubt, use LinkedIn instead.
4. This is not legal advice. If you reach 50+ paying customers, talk to a solicitor about your privacy notice.
