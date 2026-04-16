# PlanRadar runner (Windows PowerShell equivalent of the Makefile)
#
# Usage:
#   .\run.ps1 install    # install python deps
#   .\run.ps1 test       # offline end-to-end smoke test against the fixture
#   .\run.ps1 fetch      # download council weekly lists
#   .\run.ps1 extract    # run extraction + digests
#   .\run.ps1 site       # rebuild the static site
#   .\run.ps1 harvest    # harvest buyer lists
#   .\run.ps1 drafts     # generate outreach drafts (review before sending!)
#   .\run.ps1 dry-send   # show what would be sent, send nothing
#   .\run.ps1 send       # actually send up to 10 emails

param([string]$cmd = "test")

switch ($cmd) {
    "install"   { pip install -r requirements.txt }
    "test"      { python -m src.test_offline }
    "discover"  { python -m src.discover_weekly_urls }
    "fetch"     { python -m src.scraper }
    "extract"   { python -m src.pipeline }
    "digest"    { python -m src.digest roofing; python -m src.digest solar_pv; python -m src.digest structural_engineering }
    "site"      { python -m src.build_site }
    "harvest"   { python -m src.buyer_harvester }
    "drafts"    { python -m src.outreach roofing 30; python -m src.outreach solar_pv 30 }
    "dry-send"  { python -m src.sender --dry-run }
    "send"      { python -m src.sender --confirm --limit 10 }
    "deliver"   { python -m src.deliver_subscribers }
    "deliver-dry" { python -m src.deliver_subscribers --dry-run }
    "welcome"   { python -m src.send_welcome }
    "replies"   { python -m src.track_responses }
    default     { Write-Host "Unknown command: $cmd"; Write-Host "Try: install | test | discover | fetch | extract | site | harvest | drafts | dry-send | send | deliver | deliver-dry | welcome | replies" }
}
