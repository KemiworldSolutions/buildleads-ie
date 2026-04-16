# Stripe setup (Dublin / EU, ~30 minutes)

You don't need a registered company to start. A sole trader (Self-Employed) Stripe account works for the first stage.

## 1. Create the account
1. Go to https://dashboard.stripe.com/register
2. Pick **Ireland** as country
3. Account type: **Individual / Sole Trader** (you can upgrade to Limited Company later)
4. You'll need: PPS number, IBAN, mobile number, photo ID, proof of address
5. Activation usually takes a few hours to one business day

## 2. Create the product
1. Dashboard → Products → Add product
2. Name: `PlanRadar — Dublin Weekly`
3. Pricing: **€29.00 / month, recurring**
4. Save

## 3. Create a Payment Link (this is what goes on the landing page)
1. Dashboard → Payment links → New
2. Pick the product you just created
3. Enable **customer email collection**
4. Enable **promotion codes** (you'll want these for first-month-free)
5. After-payment behaviour: redirect to `https://planradar.ie/welcome.html`
6. Copy the resulting `https://buy.stripe.com/...` URL
7. Replace `REPLACE_WITH_YOUR_PAYMENT_LINK` everywhere in `src/build_site.py` and rebuild

## 4. Customer portal (for self-service cancel)
1. Dashboard → Settings → Billing → Customer portal
2. Enable: cancel subscription, update payment method, view invoices
3. Save
4. The portal URL is the same for every customer; share it in your welcome email

## 5. Webhooks (later, when you automate fulfilment)
For the first 20 customers do fulfilment by hand: when Stripe emails you about a new subscription, manually add the email to a list in `subscribers/active.csv` and your Monday cron picks it up.

When you cross 20 customers, set up a webhook:
- Endpoint: `https://your-vps/stripe-webhook`
- Events: `customer.subscription.created`, `customer.subscription.deleted`, `invoice.payment_failed`
- The handler appends/removes from `subscribers/active.csv`

## 6. VAT
Until you cross €40,000/year of EU-customer sales (the Irish small-business threshold), you don't need to register for VAT. Track revenue and re-evaluate when you hit ~€30k. At that point talk to an accountant — €200 once is cheaper than getting it wrong.
