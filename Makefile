PYTHON := python

.PHONY: run scrape analyze lint format setup

run:
	$(PYTHON) -m src.main

scrape-teams:
	$(PYTHON) -m src.scraper

analyze-teams:
	$(PYTHON) -m src.analysis

scrape-players:
	$(PYTHON) -m src.understat_scraper

lint:
	ruff check src

format:
	black src

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

