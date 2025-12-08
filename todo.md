# Project To-Do List

## ✅ Database-First Architecture — COMPLETE

All phases complete. Supabase is now the single source of truth.

| Phase | Status |
|-------|--------|
| 1. Database Schema | ✅ raw_matches, elo_ratings, elo_match_history |
| 2. Scrape Pipeline | ✅ Scrape → Upload to DB |
| 3. Analysis Pipeline | ✅ Query DB → ELO/YoY → Upload |
| 4. Pipeline Orchestration | ✅ main.py + GitHub Action |
| 5. Migration & Testing | ✅ 9322 matches, 8099 ELO records, 28 tests |

---

## 🚀 What's Next?

### Immediate
- [ ] **Test end-to-end pipeline** — Run `python -m src.main` and verify full flow
- [ ] **Push changes** — `git push` to trigger GitHub Action

### Analytics & Metrics
- [ ] **xG Differentials** — "Are they winning lucky, or playing better?"
- [ ] **Player YoY Tracking** — Compare player output season-over-season
- [ ] **Opponent Difficulty** — Weight differentials by opponent ELO

### Visualization / Frontend
- [ ] **Streamlit Dashboard** — Interactive web app to browse results
- [ ] **Trend Plots** — Cumulative differential over time
- [ ] **ELO Leaderboard** — Cross-league ELO rankings

### Infrastructure
- [ ] **Error Monitoring** — Slack/Discord alerts on pipeline failure
- [ ] **Type Hinting** — Add strict mypy types
- [ ] **Async Scraping** — Use aiohttp for faster downloads

---

## ✅ Completed

### Database-First Migration
- [x] Create raw_matches table (core columns + betting_odds JSONB)
- [x] Create elo_ratings and elo_match_history tables
- [x] Seed historical data (9322 matches, 96 teams)
- [x] Incremental ELO updates (only process new matches)
- [x] YoY analysis queries from DB
- [x] GitHub Action uploads to DB (no git commits)
- [x] data/ folder gitignored (local cache only)

### Code Quality
- [x] 28 unit tests (database + ELO logic)
- [x] Modular architecture (scrapers/, analysis/)
- [x] Centralized config.py