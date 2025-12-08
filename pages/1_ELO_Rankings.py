"""
ELO Ratings - Cross-league team rankings and rating history.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from src.database import get_elo_ratings, get_team_elo_history
from src.config import LEAGUE_DISPLAY_NAMES, CHART_COLORS, PLOTLY_COLOR_SEQUENCE

st.set_page_config(
    page_title="ELO Ratings | Gaffer's Notebook",
    layout="wide"
)

st.title("ELO Ratings")
st.markdown("Cross-league team rankings and rating progression over time.")

col1, col2 = st.columns([3, 1])
with col2:
    st.page_link("pages/2_ELO_Snapshot.py", label="ELO Snapshot →")

st.divider()


@st.cache_data(ttl=3600)
def load_elo_ratings():
    return get_elo_ratings()

@st.cache_data(ttl=3600)
def load_team_history(team):
    return get_team_elo_history(team=team)


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
    st.session_state["team_select"] = []

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
    # Team multiselect - filtered by selected league
    if selected_display:
        available_teams = sorted(elo_df[elo_df['league_display'] == selected_display]['team'].tolist())
    else:
        available_teams = sorted(elo_df['team'].unique().tolist())
    
    selected_teams = st.multiselect(
        "Compare Teams (max 5)",
        options=available_teams,
        max_selections=5,
        placeholder="Select teams to compare...",
        key="team_select"
    )

with col3:
    st.write("")  # Spacing
    st.write("")  # Align with dropdowns
    if st.button("Reset", key="reset_btn"):
        st.session_state["reset_filters"] = True
        st.rerun()

# Apply filters for rankings table
filtered_df = elo_df.copy()

if selected_display:
    filtered_df = filtered_df[filtered_df['league_display'] == selected_display]

if selected_teams:
    filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]

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
    width='stretch',
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(width="small"),
        "Team": st.column_config.TextColumn(width="medium"),
        "League": st.column_config.TextColumn(width="medium"),
        "ELO Rating": st.column_config.TextColumn(width="small"),
        "Matches": st.column_config.NumberColumn(width="small"),
    }
)

# --- ELO History Chart (when teams selected) ---
if selected_teams:
    st.divider()
    if len(selected_teams) == 1:
        st.subheader(f"ELO History: {selected_teams[0]}")
    else:
        st.subheader("ELO History Comparison")
    
    # Load history for all selected teams
    all_history = []
    for team in selected_teams:
        team_history = load_team_history(team)
        if len(team_history) > 0:
            all_history.append(team_history)
    
    if all_history:
        combined_history = pd.concat(all_history, ignore_index=True)
        
        # Create stable color mapping based on selection order
        color_map = {team: PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)] 
                     for i, team in enumerate(selected_teams)}
        
        fig = px.line(
            combined_history.sort_values(['team', 'match_number']),
            x='match_number',
            y='elo_rating',
            color='team',
            markers=True,
            color_discrete_map=color_map,
            labels={
                'match_number': 'Match Number',
                'elo_rating': 'ELO Rating',
                'team': 'Team'
            }
        )
        
        # Add reference line at 1500 (starting ELO)
        fig.add_hline(y=1500, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Starting ELO (1500)")
        
        fig.update_layout(
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Show recent matches table for each team
        for team in selected_teams:
            team_history = combined_history[combined_history['team'] == team]
            if len(team_history) > 0:
                st.markdown(f"**Recent Matches: {team}**")
                recent = team_history.tail(10).sort_values('match_number', ascending=False)
                recent_display = recent[['date', 'opponent', 'venue', 'team_result', 'goals_for', 'goals_against', 'elo_rating']].copy()
                recent_display.columns = ['Date', 'Opponent', 'Venue', 'Result', 'GF', 'GA', 'ELO After']
                recent_display['ELO After'] = recent_display['ELO After'].apply(lambda x: f"{x:.0f}")
                st.dataframe(recent_display, width='stretch', hide_index=True)
    else:
        st.info("No history data available for selected teams")

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

st.dataframe(league_stats, width='stretch', hide_index=True)

# Footer
st.divider()
st.caption("Data: football-data.co.uk")
