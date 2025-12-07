# Project To-Do List

## 🚨 High Priority: Database-First Architecture

*Goal:* Make Supabase the single source of truth. Scrape → Upload to DB → Query from DB for analysis.

### Phase 1: Database Schema
- [ ] Create raw_matches table in Supabase (all columns from football-data.co.uk)
- [ ] Create elo_ratings table (current ELO per team)
- [ ] Create elo_match_history table (every match with before/after ELO for ML)
- [ ] Verify existing team_stats and player_stats tables are correct

### Phase 2: Scrape Pipeline (Pipeline 1)
- [ ] Update src/scrapers/matches.py to upload raw match data to raw_matches table
- [ ] Update src/scrapers/understat.py to upload player contributions to player_stats (already done, verify)
- [ ] Create src/pipelines/scrape.py - orchestrates scraping and uploading raw data

### Phase 3: Analysis Pipeline (Pipeline 2)
- [ ] Add DB query functions to src/database.py:
  - [ ] get_raw_matches(league, season) - query raw match data
  - [ ] get_elo_ratings() - query current ELO state
  - [ ] get_last_processed_match() - for incremental ELO
- [ ] Refactor src/analysis/elo.py for incremental updates:
  - [ ] Load current ratings from DB on init
  - [ ] Process only new matches (not in elo_match_history)
  - [ ] Upload results to elo_ratings and elo_match_history
- [ ] Update src/analysis/teams.py to query from DB instead of local CSV
- [ ] Create src/pipelines/analysis.py - orchestrates querying and analysis

### Phase 4: Pipeline Orchestration
- [ ] Update src/main.py to run both pipelines (scrape → analysis)
- [ ] Update GitHub Action to trigger chained pipelines
- [ ] Add data/ to .gitignore

### Phase 5: Migration & Testing
- [ ] Run full scrape of all seasons (2021 → 2526) to seed raw_matches
- [ ] Run full ELO calculation to seed elo_ratings and elo_match_history
- [ ] Verify incremental mode works (run again, should only process new matches)
- [ ] Test end-to-end pipeline

---

## ✅ Completed Refactoring
- [x] *Fix "God Object" Scrapers*: Split scraper.py and understat_scraper.py into distinct extraction and analysis modules.
  - [x] Create src/scrapers/ and src/analysis/
  - [x] Refactor scraper.py → src/scrapers/matches.py
  - [x] Refactor understat_scraper.py → src/scrapers/understat.py + src/analysis/players.py
  - [x] Update src/analysis.py → src/analysis/teams.py
- [x] *Modularize Main*: Update main.py to use the new modular structure.
- [x] *Fix Virtual Environment*: Recreate venv to handle project folder rename.
- [x] *Update Documentation*: Ensure README and scripts reflect "Gaffer's Notebook" name.

## 📈 Analytics & Metrics
- [ ] *xG Differentials*: Incorporate Expected Goals (xG) into the YoY comparison.
  - Goal: "Are they winning lucky, or playing better?"
- [ ] *Player YoY Tracking*: Compare player output this season vs last season.
- [ ] *Opponent Difficulty*: Weight differentials based on opponent strength (e.g., beating City away is worth more than beating Luton at home).

## 🛠️ Infrastructure & Ops
- [x] *GitHub Actions*: Setup daily automated scraping.
- [x] *Supabase Integration (Basic)*: Push player/team stats to cloud database.
- [ ] *Supabase Integration (Full)*: See "Database-First Architecture" above.
- [ ] *Error Monitoring*: Add Slack/Discord webhook alerts on pipeline failure.

## 📊 Visualization / Frontend
- [ ] *Streamlit Dashboard*: Build a simple interactive web app to browse results.
- [ ] *Trend Plots*: Visualize the Cumulative differential over time (line chart).
- [ ] *Scatter Plots*: Plot "Goals Scored vs xG" for player analysis.

## 🧹 Tech Debt / Clean Code
- [ ] *Type Hinting*: Add strict mypy types to all functions.
- [ ] *Unit Tests*: Add pytest coverage for the calculation logic in src/analysis/.
- [ ] *Async Scraping*: Use aiohttp if we expand to more leagues/seasons to speed up downloads.