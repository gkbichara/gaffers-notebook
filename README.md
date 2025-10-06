# ⚽ Season Differentials — Real-Time Team Over/Underperformance Tracker

## Overview

**Season Differentials** is a data project that compares how every football (soccer) team is performing this season versus the same stage last season.

Instead of just showing current league tables, this tool measures *how much better or worse* each team is doing **against the same opponents and venues** they faced last year.

For example:
> Arsenal drew 1–1 at Anfield last year but won 2–0 there this season — that fixture is worth **+2 points differential**.

By computing this for every team and aggregating across gameweeks, the project reveals which clubs are the biggest **overperformers** and **underperformers** relative to last year.

---

## 🔍 What It Does

For each team and gameweek:

1. **Match equivalence:** Find this season’s fixtures that have an exact equivalent last season (same opponent + same venue).
2. **Compute points:** Assign 3/1/0 for win/draw/loss for both seasons.
3. **Per-fixture differential:**  
   \[
   \text{Differential} = \text{Points}_{25/26} - \text{Points}_{24/25}
   \]
4. **Cumulative differential:** Track the running total through each gameweek.
5. **League-wide view:** Identify biggest over- and underperformers week by week.

Fixtures involving newly promoted or relegated teams are **excluded** to avoid biasing comparisons.

---

## 🧩 Example

| Opponent | Venue | 24/25 Result | 25/26 Result | 24/25 Pts | 25/26 Pts | Diff |
|-----------|--------|--------------|--------------|------------|------------|------|
| Newcastle | A | D | W | 1 | 3 | +2 |
| Liverpool | H | L | D | 0 | 1 | +1 |
| Fulham    | A | W | L | 3 | 0 | -3 |

**Cumulative Differential:** **0** after 3 GWs (overperformers and underperformers cancel out)

---

## 🛠️ Data Requirements

Each season’s matches should be in a single CSV or dataframe with these columns:

| Column | Description |
|--------|--------------|
| `season` | Season identifier (e.g., 2024/25, 2025/26) |
| `gw` | Gameweek number |
| `date` | Match date |
| `home_team` | Home team name |
| `away_team` | Away team name |
| `home_goals` | Home team goals |
| `away_goals` | Away team goals |

The script will automatically:
- Compute points for both home and away sides.
- Normalize team names (aliases handled via a small lookup).
- Skip promoted/relegated teams when comparing.

---

## 🧮 Outputs

- `per_fixture_differentials.csv`:  
  Fixture-by-fixture comparison with points and differentials.  
- `cumulative_differentials.csv`:  
  Cumulative per-team differential by gameweek.  
- Optional `plots/` folder with:
  - Line chart of cumulative differential by team.
  - League-wide bar chart (biggest over/underperformers after latest GW).

---

## 🚀 How to Use

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/season-differentials.git
   cd season-differentials
