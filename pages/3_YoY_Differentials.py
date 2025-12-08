"""
YoY Differentials - Compare team performance vs last season.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import get_team_stats
from src.config import LEAGUE_DISPLAY_NAMES, CURRENT_SEASON, SEASONS

st.set_page_config(
    page_title="YoY Differentials | Gaffer's Notebook",
    page_icon="📊",
    layout="wide"
)

st.title("📊 YoY Differentials")
st.markdown("Compare team performance against the same fixtures from last season.")

st.divider()


@st.cache_data(ttl=3600)
def load_team_stats():
    return get_team_stats()


# Load data
team_stats_df = load_team_stats()

if len(team_stats_df) == 0:
    st.warning("No team stats data available")
    st.stop()

# Add display names
team_stats_df['league_display'] = team_stats_df['league'].map(LEAGUE_DISPLAY_NAMES)

# Handle reset
if "reset_yoy_filters" in st.session_state and st.session_state["reset_yoy_filters"]:
    st.session_state["reset_yoy_filters"] = False
    st.session_state["yoy_league"] = None
    st.session_state["yoy_teams"] = []
    st.session_state["yoy_seasons"] = [CURRENT_SEASON]

# --- Filters ---
col1, col2, col3, col4 = st.columns([1, 2, 1, 0.5])

with col1:
    # League filter
    leagues = sorted(team_stats_df['league_display'].unique().tolist())
    selected_league = st.selectbox(
        "League",
        options=leagues,
        index=None,
        placeholder="Select league...",
        key="yoy_league"
    )

with col2:
    # Team multiselect (max 3) - filtered by league
    if selected_league:
        available_teams = sorted(team_stats_df[team_stats_df['league_display'] == selected_league]['team_name'].unique().tolist())
    else:
        available_teams = sorted(team_stats_df['team_name'].unique().tolist())
    
    selected_teams = st.multiselect(
        "Teams (max 3)",
        options=available_teams,
        max_selections=3,
        placeholder="Select teams...",
        key="yoy_teams"
    )

with col3:
    # Season multiselect
    available_seasons = sorted(team_stats_df['season'].unique().tolist(), reverse=True)
    selected_seasons = st.multiselect(
        "Seasons",
        options=available_seasons,
        default=[CURRENT_SEASON] if CURRENT_SEASON in available_seasons else [],
        key="yoy_seasons"
    )

with col4:
    st.write("")
    st.write("")
    if st.button("Reset", key="reset_yoy_btn"):
        load_team_stats.clear()
        st.session_state["reset_yoy_filters"] = True
        st.rerun()

# Check if we have selections
if not selected_teams:
    st.info("👆 Select a league and team(s) to view their YoY performance")
    st.stop()

if not selected_seasons:
    st.warning("Please select at least one season")
    st.stop()

# Filter data
filtered_df = team_stats_df[
    (team_stats_df['team_name'].isin(selected_teams)) &
    (team_stats_df['season'].isin(selected_seasons))
].copy()

if len(filtered_df) == 0:
    st.warning("No data found for selected filters")
    st.stop()

# Create label for chart legend
filtered_df['label'] = filtered_df['team_name'] + ' (' + filtered_df['season'] + ')'

st.divider()

# --- Line Chart ---
st.subheader("Cumulative Differential Over Season")

fig = px.line(
    filtered_df.sort_values(['label', 'match_number']),
    x='match_number',
    y='cumulative_differential',
    color='label',
    markers=True,
    labels={
        'match_number': 'Match Number',
        'cumulative_differential': 'Cumulative Differential',
        'label': 'Team (Season)'
    }
)

# Add zero line
fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

fig.update_layout(
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Heatmap Table ---
st.subheader("Match-by-Match Details")

# Show table for each team/season combo
for team in selected_teams:
    for season in selected_seasons:
        team_season_df = filtered_df[
            (filtered_df['team_name'] == team) & 
            (filtered_df['season'] == season)
        ].sort_values('match_number')
        
        if len(team_season_df) == 0:
            continue
        
        st.markdown(f"**{team}** ({season})")
        
        # Prepare display dataframe
        display_df = team_season_df[[
            'match_number', 'opponent', 'venue', 'result',
            'points_current', 'points_previous', 'differential', 'cumulative_differential'
        ]].copy()
        
        display_df.columns = ['Match', 'Opponent', 'Venue', 'Result', 'Pts (Now)', 'Pts (Last)', 'Diff', 'Cumulative']
        
        # Style function for cumulative column
        def color_cumulative(val):
            """Color based on cumulative differential value."""
            if pd.isna(val):
                return ''
            
            # Normalize to -1 to 1 range (assuming max ~15)
            intensity = min(abs(val) / 12, 1)
            
            if val > 0:
                # Green shades
                r = int(255 * (1 - intensity * 0.7))
                g = int(255 * (1 - intensity * 0.2))
                b = int(255 * (1 - intensity * 0.7))
                return f'background-color: rgb({r}, {g}, {b}); color: {"white" if intensity > 0.5 else "black"}'
            elif val < 0:
                # Red shades
                r = int(255 * (1 - intensity * 0.2))
                g = int(255 * (1 - intensity * 0.7))
                b = int(255 * (1 - intensity * 0.7))
                return f'background-color: rgb({r}, {g}, {b}); color: {"white" if intensity > 0.5 else "black"}'
            else:
                return 'background-color: white; color: black'
        
        # Style function for diff column
        def color_diff(val):
            """Color based on single match differential."""
            if pd.isna(val):
                return ''
            if val > 0:
                return 'color: green; font-weight: bold'
            elif val < 0:
                return 'color: red; font-weight: bold'
            return ''
        
        # Apply styling
        styled_df = display_df.style.applymap(
            color_cumulative, subset=['Cumulative']
        ).applymap(
            color_diff, subset=['Diff']
        ).format({
            'Diff': lambda x: f"+{x:.0f}" if x > 0 else f"{x:.0f}",
            'Cumulative': lambda x: f"+{x:.0f}" if x > 0 else f"{x:.0f}"
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        st.write("")  # Spacing between tables
