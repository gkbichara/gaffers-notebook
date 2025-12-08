"""
Gaffer's Notebook - Football Analytics Dashboard
Home page with key stats overview.
"""
import streamlit as st
import pandas as pd

from src.database import get_elo_ratings, get_team_stats, get_player_stats
from src.config import CURRENT_SEASON, LEAGUE_DISPLAY_NAMES

# Page config
st.set_page_config(
    page_title="Gaffer's Notebook",
    layout="wide"
)

# Title
st.title("Gaffer's Notebook")
st.markdown("**European Football Intelligence** — ELO ratings, YoY performance, and player analytics across the Top 5 leagues.")

st.divider()


# Cache data queries
@st.cache_data(ttl=3600)
def load_elo_ratings():
    return get_elo_ratings()


@st.cache_data(ttl=3600)
def load_team_stats():
    return get_team_stats(season=CURRENT_SEASON)


@st.cache_data(ttl=3600)
def load_player_stats():
    return get_player_stats(season=CURRENT_SEASON)


# Load data
elo_df = load_elo_ratings()
team_stats_df = load_team_stats()
player_stats_df = load_player_stats()

# --- ELO Rankings Section ---
st.header("ELO Rankings")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 5 Teams")
    if len(elo_df) > 0:
        top_5 = elo_df.nlargest(5, 'elo_rating')[['team', 'league', 'elo_rating', 'matches_played']].copy()
        top_5['league'] = top_5['league'].map(LEAGUE_DISPLAY_NAMES)
        top_5.columns = ['Team', 'League', 'ELO', 'Matches']
        top_5 = top_5.reset_index(drop=True)
        top_5.index = top_5.index + 1
        st.dataframe(top_5, width='stretch')
    else:
        st.info("No ELO data available")

with col2:
    st.subheader("Bottom 5 Teams")
    if len(elo_df) > 0:
        bottom_5 = elo_df.nsmallest(5, 'elo_rating')[['team', 'league', 'elo_rating', 'matches_played']].copy()
        bottom_5['league'] = bottom_5['league'].map(LEAGUE_DISPLAY_NAMES)
        bottom_5.columns = ['Team', 'League', 'ELO', 'Matches']
        bottom_5 = bottom_5.reset_index(drop=True)
        bottom_5.index = bottom_5.index + 1
        st.dataframe(bottom_5, width='stretch')
    else:
        st.info("No ELO data available")

st.divider()

# --- YoY Performance Section ---
st.header("Season Performance (YoY)")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Biggest Overperformers")
    if len(team_stats_df) > 0:
        # Get the latest cumulative for each team
        latest = team_stats_df.sort_values('match_number').groupby(['league', 'team_name']).last().reset_index()
        top_performers = latest.nlargest(5, 'cumulative_differential')[['team_name', 'league', 'cumulative_differential', 'match_number']].copy()
        top_performers['league'] = top_performers['league'].map(LEAGUE_DISPLAY_NAMES)
        top_performers.columns = ['Team', 'League', 'Differential', 'Matches']
        top_performers = top_performers.reset_index(drop=True)
        top_performers.index = top_performers.index + 1
        top_performers['Differential'] = top_performers['Differential'].apply(lambda x: f"+{x:.0f}" if x > 0 else f"{x:.0f}")
        st.dataframe(top_performers, width='stretch')
    else:
        st.info("No YoY data available")

with col4:
    st.subheader("Biggest Underperformers")
    if len(team_stats_df) > 0:
        latest = team_stats_df.sort_values('match_number').groupby(['league', 'team_name']).last().reset_index()
        bottom_performers = latest.nsmallest(5, 'cumulative_differential')[['team_name', 'league', 'cumulative_differential', 'match_number']].copy()
        bottom_performers['league'] = bottom_performers['league'].map(LEAGUE_DISPLAY_NAMES)
        bottom_performers.columns = ['Team', 'League', 'Differential', 'Matches']
        bottom_performers = bottom_performers.reset_index(drop=True)
        bottom_performers.index = bottom_performers.index + 1
        bottom_performers['Differential'] = bottom_performers['Differential'].apply(lambda x: f"+{x:.0f}" if x > 0 else f"{x:.0f}")
        st.dataframe(bottom_performers, width='stretch')
    else:
        st.info("No YoY data available")

st.divider()

# --- Player Contributions Section ---
st.header("Top Player Contributions")

if len(player_stats_df) > 0:
    top_players = player_stats_df.nlargest(10, 'contribution_pct')[
        ['player_name', 'team', 'league', 'goals', 'assists', 'contribution_pct']
    ].copy()
    top_players['league'] = top_players['league'].map(LEAGUE_DISPLAY_NAMES)
    top_players.columns = ['Player', 'Team', 'League', 'Goals', 'Assists', 'Contribution %']
    top_players = top_players.reset_index(drop=True)
    top_players.index = top_players.index + 1
    top_players['Contribution %'] = top_players['Contribution %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(top_players, width='stretch')
else:
    st.info("No player data available")

st.divider()

# --- Quick Stats ---
st.header("Quick Stats")

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric("Total Teams", len(elo_df) if len(elo_df) > 0 else 0)

with col6:
    st.metric("Leagues", 5)

with col7:
    if len(elo_df) > 0:
        top_team = elo_df.nlargest(1, 'elo_rating').iloc[0]
        st.metric("Top ELO", f"{top_team['elo_rating']:.0f}", top_team['team'])
    else:
        st.metric("Top ELO", "N/A")

with col8:
    if len(team_stats_df) > 0:
        latest = team_stats_df.sort_values('match_number').groupby(['league', 'team_name']).last().reset_index()
        top_perf = latest.nlargest(1, 'cumulative_differential').iloc[0]
        st.metric("Best YoY", f"+{top_perf['cumulative_differential']:.0f}", top_perf['team_name'])
    else:
        st.metric("Best YoY", "N/A")

# Footer
st.divider()
st.caption(f"Data: football-data.co.uk & Understat.com | Season: {CURRENT_SEASON}")
