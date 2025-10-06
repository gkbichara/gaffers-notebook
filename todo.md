# 🧾 TODO — Season Differentials Project

A running list of features, improvements, and checkpoints for the project.

---

## ✅ Phase 1 — Setup & One-Team Prototype
- [ ] Create initial project structure (`data/`, `scripts/`, `notebooks/`, `output/`)
- [ ] Load Premier League 2024/25 and 2025/26 data (from FBref or similar)
- [ ] Normalize team names (aliases lookup)
- [ ] Write helper to compute result → points (3/1/0)
- [ ] Implement function to find equivalent fixtures (same opponent + venue)
- [ ] Exclude promoted and relegated teams from comparison
- [ ] Compute per-fixture differentials (points_25_26 – points_24_25)
- [ ] Build cumulative differential by GW for one team
- [ ] Visualize line plot (cumulative diff vs GW)
- [ ] Verify output manually for 1–2 teams

---

## 🧩 Phase 2 — League-Wide Extension
- [ ] Generalize logic for all Premier League teams
- [ ] Create per-league leaderboard: overperformers vs underperformers
- [ ] Plot cumulative differentials for all teams on one chart
- [ ] Export CSV summaries (`per_fixture_differentials.csv`, `cumulative_differentials.csv`)
- [ ] Add league-level summary bar chart for latest GW

---

## 🌍 Phase 3 — Multi-League Expansion (Top 5 Leagues)
- [ ] Collect datasets for La Liga, Serie A, Bundesliga, Ligue 1 (2024/25–2025/26)
- [ ] Apply normalization across leagues (consistent naming)
- [ ] Run comparison logic for all leagues
- [ ] Merge into one global dashboard/table
- [ ] Add simple filter for league/team in notebooks or Streamlit app

---

## 📈 Phase 4 — Advanced Metrics
- [ ] Integrate goal difference differential
- [ ] Add expected goals (xG) differential (Understat API)
- [ ] Include Strength of Schedule adjustment (last-season finish or ELO)
- [ ] Highlight fixtures with biggest point swings (+3 or –3)
- [ ] Add rolling chart to show trend per team over recent GWs

---

## 🧠 Phase 5 — Automation & Deployment
- [ ] Automate weekly data updates (via GitHub Actions or cron job)
- [ ] Automatically pull new results and recompute metrics
- [ ] Publish updated charts weekly (e.g., `/plots/week_X.png`)
- [ ] Optional: post summary chart to X/Twitter

---

## 💄 Phase 6 — Documentation & Polish
- [ ] Write detailed docstrings for each function
- [ ] Add setup instructions in `requirements.txt` or `environment.yml`
- [ ] Refine README with latest plots and results
- [ ] Add references section (data sources, credits)
- [ ] Final QA pass before sharing or publishing results

---

## 🧩 Optional Stretch Ideas
- [ ] Create an interactive Streamlit dashboard (filters by team, league, GW)
- [ ] Compare goal differentials and xG swings side-by-side
- [ ] Add support for domestic cups or continental competitions
- [ ] Historical mode (compare 3–5 past seasons instead of just 2)
- [ ] “Manager impact” mode — show differential before and after manager changes

---

## 📅 Progress Tracker
| Date | Milestone | Status |
|------|------------|--------|
| 2025-10 | Initial repo setup | ⏳ In progress |
| 2025-10 | One-team prototype complete | ☐ |
| 2025-11 | Full Premier League rollout | ☐ |
| 2025-12 | Top 5 leagues integration | ☐ |
| 2026-01 | Automation & dashboard | ☐ |

---

**Author:** Galal Bichara  
**Inspiration:** [@DrRitzyy](https://x.com/DrRitzyy/status/1972362982484271109) — “same fixtures, new season” analytics  
