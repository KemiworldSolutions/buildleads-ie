.PHONY: install test discover fetch extract digest site harvest drafts send dry-send deliver welcome replies all clean

install:
	pip install -r requirements.txt

test:
	python -m src.test_offline

discover:
	python -m src.discover_weekly_urls

fetch:
	python -m src.scraper

extract:
	python -m src.pipeline

digest:
	python -m src.digest roofing
	python -m src.digest solar_pv
	python -m src.digest structural_engineering

site:
	python -m src.build_site

harvest:
	python -m src.buyer_harvester

drafts:
	python -m src.outreach roofing 30
	python -m src.outreach solar_pv 30
	python -m src.outreach structural_engineering 30

dry-send:
	python -m src.sender --dry-run

send:
	python -m src.sender --confirm --limit 10

deliver:
	python -m src.deliver_subscribers

welcome:
	python -m src.send_welcome

replies:
	python -m src.track_responses

all: extract site

clean:
	rm -rf out/structured out/digests
