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

**Goal:** Build an interactive web app to visualize ELO rankings, YoY differentials, and player stats.

### Step 1: Setup (Do First)
```bash
pip install streamlit plotly
echo "streamlit" >> requirements.txt
echo "plotly" >> requirements.txt
```

Create `app.py` in project root (Streamlit convention).

### Step 2: Core Pages to Build

**Page 1: ELO Leaderboard**
- Query `elo_ratings` table from Supabase
- Display sortable table: Rank, Team, League, ELO, Matches Played
- Add league filter dropdown
- Use existing `get_elo_ratings()` from `src/database.py`

**Page 2: YoY Differentials**
- Query `team_stats` table from Supabase
- Line chart: Cumulative differential over match number
- Team selector dropdown
- Season selector (default: current 2526)

**Page 3: ELO History (Optional)**
- Query `elo_match_history` for a specific team
- Show rating progression over time

### Step 3: Supabase Connection
```python
# In app.py, reuse existing database.py
from src.database import get_db, get_elo_ratings

# Or use st.connection for caching:
# https://docs.streamlit.io/develop/api-reference/connections
```

### Step 4: Deploy to Streamlit Cloud
1. Push `app.py` to GitHub
2. Go to share.streamlit.io
3. Connect repo, set main file to `app.py`
4. Add secrets: SUPABASE_URL, SUPABASE_KEY
5. Deploy (free for public apps)

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
