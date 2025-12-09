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

## ✅ Streamlit Dashboard — IN PROGRESS

> **Design Principle:** Design for the end state, iterate towards it — not through disposable versions.

**Current Status:** Core pages complete. Adding xG analysis features.

### Architecture (Implemented)
```
gaffers-notebook/
├── app.py                      ← Home/Overview (landing page) ✅
├── pages/
│   ├── 1_ELO_Rankings.py       ← Rankings + History ✅
│   ├── 2_ELO_Snapshot.py       ← Historical ELO at specific points ✅
│   ├── 3_YoY_Differentials.py  ← Cumulative differential charts ✅
│   ├── 4_Player_Stats.py       ← Player comparison with charts ✅
│   └── 5_xG_Analysis.py        ← xG trends & over/underperformance 🔄
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
| `player_stats` | league, season, player, team, goals, assists, contribution_pct | Player analysis |
| `understat_team_matches` | league, season, team, opponent, xg_for, xg_against | xG Analysis |
| `raw_matches` | All match data | Deep dives |

### Reference: Existing DB Functions (src/database.py)
- `get_elo_ratings()` — Returns DataFrame of all team ratings
- `get_raw_matches(league, season)` — Returns match data
- `get_matches_for_analysis(league, season)` — Returns formatted for analysis

---

## 🔄 xG Analysis — IN PROGRESS

### Phase 1: Data Foundation ✅
- [x] Create `understat_team_matches` table in Supabase
- [x] Add RLS policies for public read + service write
- [x] Build scraper: `get_team_match_xg()` in understat.py (using JSON API)
- [x] Build uploader: `update_understat_team_matches()` in database.py
- [x] Test upload (Serie A 2526)
- [x] Backfill all 5 leagues × 6 seasons (19,352 records)

### Phase 2: xG Analysis Page (`pages/5_xG_Analysis.py`)

**Filters:**
- Season(s) multiselect (with auto-fill gaps)
- League dropdown
- Team(s) multiselect (max 2)
- Match range (From/To)

**Section 1: Goals vs xG Chart**
- Filled area chart showing over/underperformance
- Green area = Goals > xG (clinical)
- Red area = Goals < xG (wasteful)
- If 2 teams selected: Show 2 stacked charts (one per team)
- Multi-season support (like ELO Snapshot)

**Section 2: xG YoY Differentials**
- Same fixture comparison (like current YoY page)
- Table: Match, Opponent, Venue, xG (Now), xG (Last), Diff, Cumulative
- Color-coded heatmap
- Line chart: Cumulative xG differential

**Section 3: Defensive xG (xGA)**
- Same as above but for xG Against
- Lower xGA = defensive improvement (green)

**Section 4: Summary Cards**
- Total Goals vs Total xG
- Over/underperformance status (Clinical/Wasteful)
- Goals Against vs xGA

### Phase 3: Player Stats Enhancement
- [ ] Add columns to `player_stats`: xg, xa, xg_pct, xa_pct, goals_minus_xg
- [ ] Update player scraper to extract xG/xA from Understat
- [ ] Add xG columns to Player Stats page table
- [ ] Add "Most Clinical" metric (highest Goals - xG)

### Phase 4: Future Tabs (Deferred)
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
