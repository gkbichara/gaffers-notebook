# Project To-Do List

## 🚨 High Priority: Database-First Architecture

*Goal:* Make Supabase the single source of truth. Scrape → Upload to DB → Query from DB for analysis.

### Phase 1: Database Schema ✅
- [x] Create raw_matches table in Supabase (core columns + betting_odds JSONB)
- [x] Create elo_ratings table (current ELO per team)
- [x] Create elo_match_history table (every match with before/after ELO for ML)
- [x] Verify existing team_stats and player_stats tables are correct
- [x] Add upload functions: upload_raw_matches, upload_elo_ratings, upload_elo_match_history
- [x] Seed existing ELO data to database

### Phase 2: Scrape Pipeline (Pipeline 1) ✅
- [x] Update src/scrapers/matches.py to return DataFrame with league/season columns
- [x] Add upload_raw_matches call in matches.py main()
- [x] Update src/scrapers/understat.py to upload player contributions to player_stats
- [x] Seed raw_matches with all historical data (9322 matches)

### Phase 3: Analysis Pipeline (Pipeline 2) ✅
- [x] Add DB query functions to src/database.py:
  - [x] get_raw_matches(league, season) - with pagination
  - [x] get_elo_ratings() - query current ELO state
  - [x] get_elo_match_history(league) - query history
  - [x] get_last_processed_match_date() - for incremental ELO
- [x] Refactor src/analysis/elo.py for incremental updates:
  - [x] load_from_db() - load existing ratings from DB
  - [x] process_new_matches() - process only new matches
- [ ] Update src/analysis/teams.py to query from DB instead of local CSV
- [x] Create run_incremental_elo() wrapper function
- [x] Wire into main.py

### Phase 4: Pipeline Orchestration ✅
- [x] Update src/main.py to use incremental ELO from DB
- [ ] Update GitHub Action to trigger chained pipelines
- [x] Add data/ to .gitignore

### Phase 5: Migration & Testing
- [x] Seed raw_matches with all historical data (9322 matches)
- [x] Seed elo_match_history from existing CSV (8099 records)
- [x] Seed elo_ratings from existing CSVs (96 teams)
- [x] Verify incremental mode works (tested - correctly found 0 new matches)
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