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

## 🚀 CURRENT: Streamlit Dashboard

> **Design Principle:** Design for the end state, iterate towards it — not through disposable versions.
> Build the architecture that supports future growth from day one.

**Final Vision:** Multi-page analytics dashboard with ELO, YoY, player stats, and future xG/advanced metrics.

### Target Architecture
```
gaffers-notebook/
├── app.py                      ← Home/Overview (landing page)
├── pages/
│   ├── 1_ELO_Rankings.py       ← Cross-league leaderboard
│   ├── 2_ELO_History.py        ← Team rating progression over time
│   ├── 3_YoY_Differentials.py  ← Cumulative differential charts
│   ├── 4_Player_Stats.py       ← Contributions, top scorers
│   └── (future: xG, opponent difficulty, predictions)
└── src/
    └── database.py             ← Shared data layer (already exists)
```

### Build Order (iterate towards final vision)

**Phase 1: Foundation**
- [ ] Create `app.py` (home page with overview/navigation)
- [ ] Create `pages/` directory
- [ ] Add streamlit + plotly to requirements.txt

**Phase 2: Core Pages**
- [ ] `1_ELO_Rankings.py` — Query `elo_ratings`, sortable table, league filter
- [ ] `2_ELO_History.py` — Query `elo_match_history`, line chart per team
- [ ] `3_YoY_Differentials.py` — Query `team_stats`, cumulative line chart
- [ ] `4_Player_Stats.py` — Query `player_stats`, top contributors table

**Phase 3: Polish & Deploy**
- [ ] Add consistent styling/theme across pages
- [ ] Add caching with `@st.cache_data` for DB queries
- [ ] Deploy to Streamlit Cloud (free for public apps)
- [ ] Add secrets: SUPABASE_URL, SUPABASE_KEY

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
| `team_stats` | league, season, team, match_number, cumulative | YoY charts |
| `player_stats` | league, season, player, team, goals, assists, contribution_pct | Player analysis |
| `raw_matches` | All match data | Deep dives |

### Reference: Existing DB Functions (src/database.py)
- `get_elo_ratings()` — Returns DataFrame of all team ratings
- `get_raw_matches(league, season)` — Returns match data
- `get_matches_for_analysis(league, season)` — Returns formatted for analysis

---

## 📋 Future Enhancements

### Analytics
- [ ] **xG Differentials** — "Are they winning lucky, or playing better?"
- [ ] **Player YoY Tracking** — Compare player output season-over-season
- [ ] **Opponent Difficulty** — Weight differentials by opponent ELO

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
