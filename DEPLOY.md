# Deployment

Two pieces deploy separately:
1. The static landing site (`site/`) → free, on Cloudflare Pages
2. The pipeline cron (`src/pipeline.py`) → €4/mo Hetzner CX11 VPS, or run on your own laptop initially

## 1. Static site → Cloudflare Pages (free, 5 minutes)

```
cd E:/Work/OPENCLAW
python -m src.build_site
npm install -g wrangler
wrangler login
wrangler pages deploy site --project-name=planradar
```

You'll get a `planradar.pages.dev` URL immediately. Then:
1. Buy `planradar.ie` from blacknight.ie or namecheap (~€15/yr — pick a name that's actually free; this is illustrative)
2. Cloudflare Dashboard → Pages → planradar → Custom domains → Set up
3. Add DNS records as instructed (Cloudflare can be your DNS provider too — easier)
4. Site is live on your real domain in under an hour

Re-deploy after edits: `python -m src.build_site && wrangler pages deploy site --project-name=planradar`

## 2. Pipeline cron — run locally for the first 4 weeks

You don't need a VPS until you have paying customers. For the first month, run the pipeline on your own laptop every Monday morning:

```bash
python -m src.pipeline
python -m src.outreach roofing 30      # if you're still in cold-outreach mode
```

That's it. 10 minutes a week.

## 3. Pipeline cron — Hetzner VPS (when you have ≥3 paying customers)

1. Sign up at hetzner.com → CX11 instance (€4.51/mo), Ubuntu 22.04, Helsinki or Falkenstein
2. SSH in, install Python 3.11 + git
3. `git clone` your repo (or `rsync` it)
4. Set up `.env` with DEEPSEEK_API_KEY and SMTP creds
5. Add a cron entry:

```
# Every Monday at 06:30 Dublin time
30 6 * * 1 cd /home/planradar && /usr/bin/python3 -m src.pipeline >> logs/pipeline.log 2>&1

# Send the digest emails to subscribers at 07:00
0 7 * * 1 cd /home/planradar && /usr/bin/python3 -m src.deliver_subscribers >> logs/deliver.log 2>&1
```

(`src/deliver_subscribers.py` is the next thing to build once you have your first paying customer — it reads `subscribers/active.csv` and emails the relevant per-segment digest to each.)

## 4. SMTP for sending email

Don't use Gmail. Don't use your existing personal mailbox. Set up a real sending infrastructure:

**Option A (cheapest, recommended for first 100 subscribers):**
- Fastmail: €5/mo, custom domain, decent reputation
- Set up SPF, DKIM, DMARC (Fastmail provides the DNS records)

**Option B (when scaling):**
- Postmark or AWS SES — both have transactional reputation, both ~€0.001/email

Whatever you do, **warm up the domain**: send 5 emails on day 1, 10 on day 2, 20 on day 3, etc. for the first two weeks. Cold-blasting from a brand-new domain is the fastest way to get blacklisted.

## 5. Monitoring (skip until you have paying customers)

For now: weekly run, you check the output by hand. When you have ≥10 customers, add:
- A Discord webhook from `pipeline.py` so you get a ping if extraction fails
- Daily Stripe digest email (built-in to Stripe)
