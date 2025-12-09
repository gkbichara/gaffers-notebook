# Project To-Do List

## ✅ Database-First Architecture — COMPLETE

All phases complete. Supabase is now the single source of truth.

| Phase | Status |
|-------|--------|
| 1. Database Schema | ✅ raw_matches, elo_ratings, elo_match_history |
| 2. Scrape Pipeline | ✅ Scrape → Upload to DB |
| 3. Analysis Pipeline | ✅ Query DB → ELO/YoY → Upload |
| 4. Pipeline Orchestration | ✅ main.py + GitHub Action |
| 5. Migration & Testing | ✅ 9322 matches, 136 teams, 28 tests |

---

## ✅ Streamlit Dashboard — COMPLETE

> **Design Principle:** Design for the end state, iterate towards it — not through disposable versions.

**Current Status:** All core pages complete with xG analysis.

### Architecture (Implemented)
```
gaffers-notebook/
├── Home.py                     ← Home/Overview (landing page) ✅
├── pages/
│   ├── 1_ELO_Rankings.py       ← Rankings + History ✅
│   ├── 2_ELO_Snapshot.py       ← Historical ELO at specific points ✅
│   ├── 3_YoY_Differentials.py  ← Cumulative differential charts ✅
│   ├── 4_Player_Stats.py       ← Player comparison with charts ✅
│   └── 5_xG_Analysis.py        ← xG trends & over/underperformance ✅
└── src/
    └── database.py             ← Shared data layer with pagination ✅
```

### Build Progress

**Phase 1: Foundation** ✅
- [x] Create `app.py` (home page with overview stats)
- [x] Create `pages/` directory
- [x] Add streamlit + plotly + streamlit-searchbox to requirements.txt

**Phase 2: Core Pages** ✅
- [x] `1_ELO_Rankings.py` — Rankings table + history chart when team selected
- [x] `2_YoY_Differentials.py` — Multi-team comparison, line chart, heatmap table, Roma default
- [x] `3_Player_Stats.py` — Accent-insensitive search, 10-player comparison, stacked bar chart

**Phase 3: Polish & Deploy**
- [x] Add caching with `@st.cache_data` for DB queries
- [x] Add consistent styling/theme across pages
- [x] Deploy to Streamlit Cloud (free for public apps)
- [x] Add secrets: SUPABASE_URL, SUPABASE_KEY

### Supabase Connection Pattern
```python
# Reuse existing database.py functions
from src.database import get_elo_ratings, get_raw_matches

# Add caching in Streamlit:
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_elo_ratings():
    return get_elo_ratings()
```

### Reference: Database Tables Available
| Table | Key Columns | Use For |
|-------|-------------|---------|
| `elo_ratings` | team, league, elo_rating, matches_played | Leaderboard |
| `elo_match_history` | date, home_team, away_team, home_rating_after, away_rating_after | Rating trends |
| `team_stats` | league, season, team, match_number, cumulative | YoY charts (points) |
| `player_stats` | league, season, player, team, goals, assists, xg, xa, npxg, goals_minus_xg | Player analysis |
| `understat_team_matches` | league, season, team, opponent, xg_for, xg_against | xG Analysis |
| `raw_matches` | All match data | Deep dives |

### Reference: Existing DB Functions (src/database.py)
- `get_elo_ratings()` — Returns DataFrame of all team ratings
- `get_raw_matches(league, season)` — Returns match data
- `get_matches_for_analysis(league, season)` — Returns formatted for analysis

---

## ✅ xG Analysis — COMPLETE (All Phases)

### Phase 1: Data Foundation ✅
- [x] Create `understat_team_matches` table in Supabase
- [x] Add RLS policies for public read + service write
- [x] Build scraper: `get_team_match_xg()` in understat.py (using JSON API with dates)
- [x] Build uploader: `update_understat_team_matches()` in database.py
- [x] Test upload (Serie A 2526)
- [x] Backfill all 5 leagues × 6 seasons (19,352 records)
- [x] Add team name mapping (TEAM_NAME_MAP) for cross-source joins

### Phase 2: xG Analysis Page (`pages/5_xG_Analysis.py`) ✅
- [x] Season(s) multiselect (with auto-fill gaps)
- [x] All Leagues default with teams showing "(League)" labels
- [x] Team(s) multiselect (max 2, Roma default)
- [x] Match range (From/To)
- [x] Goals vs xG cumulative chart with dynamic red/green fills
- [x] Defensive xGA chart with dynamic fills
- [x] Summary cards (Goals, xG, GA, xGA with status)
- [x] xG YoY comparison (expandable section)
- [x] Match-by-match details table

### Phase 3: Player Stats Enhancement ✅
- [x] Add columns to `player_stats`: xg, xa, npxg, xg_pct, shots, minutes, goals_minus_xg
- [x] Update player scraper to extract xG/xA from Understat (via API)
- [x] Backfill all leagues/seasons with xG data (16,000+ players)
- [x] Add "Most Clinical" metric on Home page (highest Goals - xG, >5 goals)
- [x] Add "Most Creative" metric on Home page (highest xA)

### Phase 4: Future Pages (Planned)
- [ ] **Team Deep Dive** — Player reliance, attack/defense profiles, form trends
- [ ] **Predictions** — ELO + xG model for match predictions

---

## 📋 Future Enhancements

### Analytics
- [ ] **Player YoY Tracking** — Compare player output season-over-season
- [ ] **Opponent Difficulty** — Weight differentials by opponent ELO
- [ ] **Set Piece Analysis** — Find additional data source

### Infrastructure
- [ ] **Error Monitoring** — Slack/Discord alerts on pipeline failure
- [ ] **Type Hinting** — Add strict mypy types
- [ ] **Async Scraping** — Use aiohttp for faster downloads

---

## ✅ Completed

### Database-First Migration
- [x] Create raw_matches table (core columns + betting_odds JSONB)
- [x] Create elo_ratings and elo_match_history tables
- [x] Seed historical data (9322 matches, 136 teams)
- [x] Incremental ELO updates (only process new matches)
- [x] Home advantage calibrated to 40 (based on 9322 matches analysis)
- [x] YoY analysis queries from DB
- [x] GitHub Action uploads to DB (no git commits)
- [x] data/ folder gitignored (local cache only)
- [x] Full pipeline tested end-to-end

### Code Quality
- [x] 28 unit tests (database + ELO logic)
- [x] Modular architecture (scrapers/, analysis/)
- [x] Centralized config.py
