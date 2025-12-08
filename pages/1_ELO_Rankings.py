"""
ELO Rankings - Cross-league team rankings by ELO rating.
"""
import streamlit as st
import pandas as pd

from src.database import get_elo_ratings
from src.config import LEAGUE_DISPLAY_NAMES

st.set_page_config(
    page_title="ELO Rankings | Gaffer's Notebook",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 ELO Rankings")
st.markdown("Cross-league team rankings based on match results. Higher ELO = stronger team.")

st.divider()


@st.cache_data(ttl=3600)
def load_elo_ratings():
    return get_elo_ratings()


# Load data
elo_df = load_elo_ratings()

if len(elo_df) == 0:
    st.warning("No ELO data available")
    st.stop()

# Add display names
elo_df['league_display'] = elo_df['league'].map(LEAGUE_DISPLAY_NAMES)

# Handle reset - must happen BEFORE widgets are created
if "reset_filters" in st.session_state and st.session_state["reset_filters"]:
    st.session_state["reset_filters"] = False
    st.session_state["league_filter"] = None
    st.session_state["team_select"] = None

# --- Filters ---
col1, col2, col3 = st.columns([1, 2, 0.5])

with col1:
    # League filter
    display_names = sorted(elo_df['league_display'].unique().tolist())
    selected_display = st.selectbox(
        "Filter by League",
        options=display_names,
        index=None,
        placeholder="All Leagues",
        key="league_filter"
    )

with col2:
    # Team dropdown - filtered by selected league
    if selected_display:
        available_teams = sorted(elo_df[elo_df['league_display'] == selected_display]['team'].tolist())
    else:
        available_teams = sorted(elo_df['team'].unique().tolist())
    
    selected_team = st.selectbox(
        "Select Team",
        options=available_teams,
        index=None,
        placeholder="Search teams...",
        key="team_select"
    )

with col3:
    st.write("")  # Spacing
    st.write("")  # Align with dropdowns
    if st.button("Reset", key="reset_btn"):
        st.session_state["reset_filters"] = True
        st.rerun()

# Apply filters
filtered_df = elo_df.copy()

if selected_display:
    filtered_df = filtered_df[filtered_df['league_display'] == selected_display]

if selected_team:
    filtered_df = filtered_df[filtered_df['team'] == selected_team]

# Sort by ELO and add rank
filtered_df = filtered_df.sort_values('elo_rating', ascending=False).reset_index(drop=True)
filtered_df['rank'] = range(1, len(filtered_df) + 1)

# --- Display Table ---
st.subheader(f"Rankings ({len(filtered_df)} teams)")

# Format for display
display_df = filtered_df[['rank', 'team', 'league_display', 'elo_rating', 'matches_played']].copy()
display_df.columns = ['Rank', 'Team', 'League', 'ELO Rating', 'Matches']
display_df['ELO Rating'] = display_df['ELO Rating'].apply(lambda x: f"{x:.0f}")

# Display with nice formatting
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(width="small"),
        "Team": st.column_config.TextColumn(width="medium"),
        "League": st.column_config.TextColumn(width="medium"),
        "ELO Rating": st.column_config.TextColumn(width="small"),
        "Matches": st.column_config.NumberColumn(width="small"),
    }
)

st.divider()

# --- League Summary Stats ---
st.subheader("League Averages")

league_stats = elo_df.groupby('league_display').agg({
    'elo_rating': ['mean', 'max', 'min', 'count']
}).round(0)
league_stats.columns = ['Avg ELO', 'Highest', 'Lowest', 'Teams']
league_stats = league_stats.sort_values('Avg ELO', ascending=False)
league_stats = league_stats.reset_index()
league_stats.columns = ['League', 'Avg ELO', 'Highest', 'Lowest', 'Teams']

# Put selected league at top if filtered
if selected_display:
    selected_row = league_stats[league_stats['League'] == selected_display]
    other_rows = league_stats[league_stats['League'] != selected_display]
    league_stats = pd.concat([selected_row, other_rows], ignore_index=True)

st.dataframe(league_stats, use_container_width=True, hide_index=True)
