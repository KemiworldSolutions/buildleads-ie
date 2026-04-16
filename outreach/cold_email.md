# Cold email template — first 30 buyers

## Rules before you send a single one

1. **Personalise the first line.** Mention something specific about their business that you confirmed by visiting their website. No "Hi {first_name}" mail merge.
2. **Attach the actual digest** for their segment as a PDF or paste the top 5 entries inline. The proof IS the pitch.
3. **One-click unsubscribe** at the bottom of every message. This is legally required (SI 336/2011) and is also the right thing to do.
4. **Email business addresses only** (info@, your-name@registered-business.ie). No Gmail/Yahoo of sole traders unless they've published it on their own website as a contact method.
5. **Send in batches of 10**, not 30 at once. Wait 24 hours between batches so you can read replies and adjust.
6. **Do not buy a list.** You are building this from public registers (SEAI installer list, Engineers Ireland, RIAI, Golden Pages). Each address has a defensible source you can cite if asked.

---

## Template (roofing segment example — adapt per segment)

**Subject:** 14 Dublin extensions filed this week that'll need a roofer

Hi {first_name},

I noticed {company} does pitched-roof work across north Dublin — your job at {specific_estate_or_project_you_saw_on_their_site} is exactly the kind of thing this list is built around.

I run a small service called PlanRadar.ie. Every Monday I pull the official weekly planning lists from all four Dublin councils, classify them, and send each trade only the applications that actually need their work. No bidding war, no main-contractor middleman.

This week's roofing-relevant Dublin filings (attached as a PDF) include 14 extensions, 3 loft conversions, and 2 new dwellings. Every one is a public record, every one is at the planning stage right now, and every one has the applicant name and site address as published on the council register.

It's €29/month, weekly delivery, cancel anytime: planradar.ie

If it's not for you, no worries — and if you'd rather not hear from me again, just reply "remove" and you're off the list permanently.

Best,
{your_name}

---

PlanRadar.ie • {your_address} • One-click unsubscribe: planradar.ie/u/{token}

---

## What to track

In `outreach/log.csv` record for every email:
- `date_sent, segment, company, email, opened, replied, reply_sentiment, converted`

After 30 sent in a segment, look at:
- Reply rate (target: ≥10%)
- Conversion to free trial or paid (target: ≥1 paying out of 30)

If reply rate is high but conversion is 0, the **price or product** is wrong.
If reply rate is 0, the **segment or pitch** is wrong.
If both are 0, change segment before changing the product.
