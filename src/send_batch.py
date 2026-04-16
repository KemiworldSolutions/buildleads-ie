"""
Batch send outreach emails via Gmail SMTP.
From: hello@buildleads.ie (Send As alias on kemiworldsolutions@gmail.com)
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "kemiworldsolutions@gmail.com"
SMTP_PASS = "pxkm gfdn vesv iwnx"   # app password (spaces OK)
FROM_ADDR = "BuildLeads <hello@buildleads.ie>"

EMAILS = [
    # ── ARCHITECTURE ─────────────────────────────────────────────────────────
    {
        "to": "info@ardmac.com",
        "subject": "Dublin architecture leads \u2014 week of 2026-04-15",
        "body": (
            "Ardmac, as an architecture firm focused on precision-built spaces, "
            "you know Dublin\u2019s planning lists are a key source of potential leads.\n\n"
            "PlanRadar sends a weekly digest of new planning applications from the four "
            "Dublin local authorities directly to your inbox.\n\n"
            "For example, this week\u2019s list included a new two-storey mews dwelling on "
            "Tritonville Road (DCC ref 3759/20/X1) and a change-of-use for a hotel "
            "extension to restaurant use on Avenue Road (DCC ref 4018/24).\n\n"
            "The service costs \u20ac29/month and you can cancel anytime.\n\n"
            "If you\u2019d like to see the full list from last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@dta.ie",
        "subject": "Dublin architecture leads \u2014 week of 2026-04-15",
        "body": (
            "DTA, as an architecture practice in Dublin, you know the value of early "
            "visibility on new projects. PlanRadar sends a weekly digest of every new "
            "planning application from the four Dublin councils directly to your inbox.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling at "
            "Herbert Mews in Sandymount (ref 3759/20/X1) and a change-of-use for a hotel "
            "extension to restaurant use on Avenue Road (ref 4018/24).\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. If you\u2019d like to see the full list from "
            "last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "mail@dmod.ie",
        "subject": "Dublin architecture leads \u2014 week of 2026-04-15",
        "body": (
            "As an architect in Dublin, you know new planning applications are the "
            "lifeblood of potential work. PlanRadar sends a weekly digest of every new "
            "application from the four Dublin councils.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling at "
            "Herbert Mews in Sandymount (3759/20/X1) and a change of use to a restaurant "
            "on the 7th floor of a Portobello hotel (4018/24).\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. If you\u2019d like to see the full list from "
            "last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@johnpaul.ie",
        "subject": "Dublin architecture leads \u2014 week of 2026-04-15",
        "body": (
            "John Paul Construction, as an architecture firm in Dublin, you know the "
            "value of early visibility on new projects.\n\n"
            "PlanRadar sends a weekly digest of every new planning application from the "
            "four Dublin councils.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling on "
            "Tritonville Road (DCC ref 3759/20/X1) and a change of use to a restaurant "
            "on the 7th floor at 36/37 Avenue Road (DCC ref 4018/24).\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. Reply \u2018sample\u2019 and I\u2019ll send last week\u2019s "
            "full architecture list free.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@kennedyfitzgerald.ie",
        "subject": "Dublin architecture leads \u2014 week of 2026-04-15",
        "body": (
            "Kennedy Fitzgerald LLP, as an architecture practice in Dublin, you know how "
            "quickly new planning applications move. PlanRadar sends a weekly digest of "
            "every new application from the four Dublin councils, so you see opportunities "
            "first.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling at "
            "Herbert Mews in Sandymount (DCC/3759/20/X1) and a change of use for a hotel "
            "extension to restaurant use on Avenue Road (DCC/4018/24).\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. If you\u2019d like to see the full list from "
            "last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    # ── STRUCTURAL ENGINEERING ────────────────────────────────────────────────
    {
        "to": "info@rod.ie",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Your structural engineering expertise in Dublin will be needed for projects "
            "like the new two-storey mews dwelling at 141 Tritonville Road, Sandymount, "
            "which requires demolition and new construction.\n\n"
            "PlanRadar sends a weekly digest of new planning applications from the four "
            "Dublin councils. For example, this week also includes a hotel extension "
            "change-of-use at 36/37 Avenue Road, Portobello, involving significant "
            "structural alterations.\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. Reply \u2018sample\u2019 and I\u2019ll send last week\u2019s "
            "full list free.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "media@burohappold.com",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Your team at Buro Happold handles structural design for Dublin\u2019s built "
            "environment. PlanRadar sends a weekly list of new planning applications from "
            "the four Dublin councils directly to your inbox.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling with "
            "undercroft parking at Herbert Mews in Sandymount (DCC/3759/20/X1) and a "
            "hotel extension change-of-use to a restaurant with a new terrace on Avenue "
            "Road (DCC/4018/24).\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. If you\u2019d like to see the full list from "
            "last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "dublin@mottmac.com",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Your team in Dublin likely handles structural assessments for projects like "
            "the new two-storey mews dwelling at 141 Tritonville Road or the hotel "
            "extension change-of-use at 36/37 Avenue Road.\n\n"
            "PlanRadar sends a weekly digest of every new planning application from the "
            "four Dublin councils. This week\u2019s list had 196 relevant to structural "
            "engineering.\n\n"
            "For example, the Sandymount application seeks permission for demolition and "
            "a new build with undercroft parking, while the Portobello project involves "
            "converting a 7th floor to restaurant use with a new terrace.\n\n"
            "It\u2019s \u20ac29/month, cancel anytime. If you\u2019d like to see the full list from "
            "last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@sweco.ie",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Sweco\u2019s structural engineering teams in Dublin will be reviewing new builds "
            "and change-of-use applications like the two-storey mews dwelling at 141 "
            "Tritonville Road (DCC ref. 3759/20/X1) or the hotel extension conversion at "
            "36/37 Avenue Road (DCC ref. 4018/24) filed last week.\n\n"
            "PlanRadar sends a weekly digest of every new planning application from the "
            "four Dublin councils. It\u2019s \u20ac29/month, cancel anytime.\n\n"
            "Reply \u2018sample\u2019 and I\u2019ll send last week\u2019s full structural engineering list free. "
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@ryanhanley.ie",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Ryan Hanley, as structural engineering consultants in Dublin, you know new "
            "planning applications mean potential project leads.\n\n"
            "PlanRadar sends a weekly digest of every new planning application from the "
            "four Dublin councils, directly to your inbox.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling in "
            "Sandymount (3759/20/X1) and a hotel extension change-of-use in Portobello "
            "(4018/24), both requiring structural input.\n\n"
            "The service costs \u20ac29/month, cancel anytime.\n\n"
            "If you\u2019d like to see the full list from last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "mail@meehangreen.ie",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Meehan Green, as a structural engineering firm in Dublin, you know early "
            "visibility on upcoming projects is key. PlanRadar sends a weekly digest of "
            "new planning applications from the four Dublin local authorities.\n\n"
            "For example, this week\u2019s list includes a new two-storey mews dwelling in "
            "Sandymount (3759/20/X1) and a hotel extension change-of-use on Avenue Road "
            "(4018/24), both requiring structural input.\n\n"
            "The service is \u20ac29/month, cancel anytime. If you\u2019d like to see the full "
            "list from last week free, just reply \u2018sample\u2019.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
    {
        "to": "info@tpa.ie",
        "subject": "Dublin structural engineering leads \u2014 week of 2026-04-15",
        "body": (
            "Tom, structural engineering in Dublin means foundations, load-bearing "
            "changes, and new builds \u2014 like the two-storey mews on Tritonville Road "
            "(DCC ref 3759/20/X1) or the hotel extension change-of-use on Avenue Road "
            "(DCC ref 4018/24) filed last week.\n\n"
            "PlanRadar sends Dublin engineers a weekly digest of every new planning "
            "application from the four Dublin councils.\n\n"
            "We spotted 196 relevant applications last week. For \u20ac29/month (cancel "
            "anytime) you get the full list every Monday.\n\n"
            "Reply \u2018sample\u2019 and I\u2019ll send last week\u2019s full structural engineering list free.\n\n"
            "Reply \u2018remove\u2019 and you\u2019re off the list permanently."
        ),
    },
]


def send_email(smtp, msg_data):
    msg = MIMEMultipart("alternative")
    msg["From"] = FROM_ADDR
    msg["To"] = msg_data["to"]
    msg["Subject"] = msg_data["subject"]
    msg.attach(MIMEText(msg_data["body"], "plain", "utf-8"))
    smtp.sendmail("hello@buildleads.ie", msg_data["to"], msg.as_string())


def main():
    print(f"Connecting to {SMTP_HOST}:{SMTP_PORT} ...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS.replace(" ", ""))
        print("Logged in. Sending...\n")

        ok, fail = [], []
        for i, em in enumerate(EMAILS, 1):
            try:
                send_email(smtp, em)
                print(f"[{i:02d}] OK  -> {em['to']}")
                ok.append(em["to"])
            except Exception as e:
                print(f"[{i:02d}] ERR -> {em['to']}  ({e})")
                fail.append(em["to"])
            time.sleep(2)   # be polite to Gmail rate limits

    print(f"\nDone. Sent: {len(ok)}  Failed: {len(fail)}")
    if fail:
        print("Failed:", fail)


if __name__ == "__main__":
    main()
