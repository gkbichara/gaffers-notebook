"""
ELO Snapshot - Historical ELO rankings at specific points in time.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import get_team_elo_history
from src.config import LEAGUE_DISPLAY_NAMES, CHART_COLORS, PLOTLY_COLOR_SEQUENCE, SEASONS, SEASON_DISPLAY_NAMES, SEASON_CODES

st.set_page_config(
    page_title="ELO Snapshot | Gaffer's Notebook",
    layout="wide"
)

st.title("ELO Snapshot")
st.markdown("View historical ELO rankings at specific points in time.")
st.caption("ELO ratings calculated from season 2020/21 onwards.")

st.divider()


@st.cache_data(ttl=3600)
def load_all_elo_history():
    """Load all ELO history data."""
    return get_team_elo_history()


# Load data
history_df = load_all_elo_history()

if len(history_df) == 0:
    st.warning("No ELO history data available")
    st.stop()

# Add league display names
history_df['league_display'] = history_df['league'].map(LEAGUE_DISPLAY_NAMES)

# Get available seasons (ordered) - use display names
available_season_codes = sorted(history_df['season'].unique().tolist())
available_seasons_display = [SEASON_DISPLAY_NAMES.get(s, s) for s in available_season_codes]


def fill_season_gaps(seasons_display: list, all_seasons_display: list) -> list:
    """Fill gaps between non-adjacent seasons (works with display names)."""
    if len(seasons_display) <= 1:
        return seasons_display
    
    sorted_selected = sorted(seasons_display)
    first_idx = all_seasons_display.index(sorted_selected[0])
    last_idx = all_seasons_display.index(sorted_selected[-1])
    
    # Return all seasons from first to last (inclusive)
    return all_seasons_display[first_idx:last_idx + 1]


# Handle reset
if "reset_snapshot" in st.session_state and st.session_state["reset_snapshot"]:
    st.session_state["reset_snapshot"] = False
    st.session_state["snapshot_seasons"] = [available_seasons_display[-1]] if available_seasons_display else []
    st.session_state["snapshot_league"] = None
    st.session_state["snapshot_teams"] = []
    st.session_state["snapshot_teams_saved"] = []
    st.session_state["snapshot_last_filter_key"] = None
    st.session_state["snapshot_mode"] = "Match Range"
    st.session_state["snapshot_match_from"] = 1
    st.session_state["snapshot_match_to"] = 10

# --- Filters ---
col1, col2, col3 = st.columns([1.5, 1, 0.5])

with col1:
    # Sort selected seasons before rendering (keeps them in chronological order)
    if "snapshot_seasons" in st.session_state:
        current = st.session_state["snapshot_seasons"]
        sorted_current = sorted(current, key=lambda x: available_seasons_display.index(x) if x in available_seasons_display else 0)
        if current != sorted_current:
            st.session_state["snapshot_seasons"] = sorted_current
    
    # Multi-season selection (using display names)
    selected_seasons_display_raw = st.multiselect(
        "Season(s)",
        options=available_seasons_display,
        default=[available_seasons_display[-1]] if available_seasons_display else [],
        key="snapshot_seasons"
    )

with col2:
    # League filter with "All Leagues" as default
    leagues = ["All Leagues"] + sorted(history_df['league_display'].dropna().unique().tolist())
    selected_league = st.selectbox(
        "League",
        options=leagues,
        index=0,  # "All Leagues" is default
        key="snapshot_league"
    )

with col3:
    st.write("")
    st.write("")
    if st.button("Reset", key="reset_snapshot_btn"):
        st.session_state["reset_snapshot"] = True
        load_all_elo_history.clear()
        st.rerun()

if not selected_seasons_display_raw:
    st.info("Select at least one season")
    st.stop()

# Auto-fill gaps between non-adjacent seasons (using display names)
selected_seasons_display = fill_season_gaps(selected_seasons_display_raw, available_seasons_display)

# Show info if seasons were auto-filled
if len(selected_seasons_display) > len(selected_seasons_display_raw):
    filled_seasons = [s for s in selected_seasons_display if s not in selected_seasons_display_raw]
    st.info(f"Auto-filled gap seasons: {', '.join(filled_seasons)}")

# Convert display names to codes for filtering
selected_seasons = [SEASON_CODES.get(s, s) for s in selected_seasons_display]

# Filter by seasons (using filled list)
season_df = history_df[history_df['season'].isin(selected_seasons)].copy()

# Sort seasons for proper ordering
selected_seasons_sorted = sorted(selected_seasons)
selected_seasons_display_sorted = sorted(selected_seasons_display)

# Get max match number for selected seasons (per-season)
max_match = int(season_df['season_match_number'].max()) if len(season_df) > 0 else 38

# --- Match Selection ---
st.markdown("### Match Selection")

col_mode, col_from, col_to = st.columns([1, 1, 1])

with col_mode:
    mode = st.radio(
        "View type",
        options=["Specific Match", "Match Range"],
        index=1,
        horizontal=True,
        key="snapshot_mode"
    )

with col_from:
    if mode == "Specific Match":
        match_num = st.number_input(
            "Match Number",
            min_value=1,
            max_value=max_match,
            value=min(10, max_match),
            key="snapshot_match_from"
        )
        match_from = match_num
        match_to = match_num
    else:
        match_from = st.number_input(
            "From Match",
            min_value=1,
            max_value=max_match,
            value=1,
            key="snapshot_match_from"
        )

with col_to:
    if mode == "Match Range":
        match_to = st.number_input(
            "To Match",
            min_value=1,
            max_value=max_match,
            value=min(10, max_match),
            key="snapshot_match_to"
        )

# Info about multi-season behavior
if len(selected_seasons) > 1:
    st.info(f"Multi-season range: Match {match_from} of {selected_seasons_display_sorted[0]} → Match {match_to} of {selected_seasons_display_sorted[-1]}")

# --- Team Selection ---
# Filter available teams by league
if selected_league and selected_league != "All Leagues":
    available_teams_raw = sorted(season_df[season_df['league_display'] == selected_league]['team'].unique().tolist())
    available_teams = available_teams_raw
    team_name_map = {team: team for team in available_teams_raw}
else:
    # Show teams with league in parentheses
    team_league_map = season_df.groupby('team')['league_display'].first().to_dict()
    available_teams_raw = sorted(season_df['team'].unique().tolist())
    available_teams = [f"{team} ({team_league_map[team]})" for team in available_teams_raw]
    team_name_map = {f"{team} ({team_league_map[team]})": team for team in available_teams_raw}

# Track filter changes to know when to restore saved teams
current_filter_key = f"{selected_seasons_display}_{selected_league}"
if "snapshot_last_filter_key" not in st.session_state:
    st.session_state["snapshot_last_filter_key"] = current_filter_key

# Only restore saved teams when filters change (not on every rerun)
if st.session_state["snapshot_last_filter_key"] != current_filter_key:
    # Filters changed - restore valid saved teams
    if "snapshot_teams_saved" in st.session_state:
        valid_saved = [t for t in st.session_state["snapshot_teams_saved"] if t in available_teams]
        st.session_state["snapshot_teams"] = valid_saved
    st.session_state["snapshot_last_filter_key"] = current_filter_key

selected_teams_display = st.multiselect(
    "Compare Teams (optional - leave empty for all)",
    options=available_teams,
    max_selections=10,
    placeholder="Select teams or leave empty for all...",
    key="snapshot_teams"
)

# Convert display names to actual team names
selected_teams = [team_name_map.get(t, t) for t in selected_teams_display]

# Always save current selection
st.session_state["snapshot_teams_saved"] = selected_teams_display

st.divider()

# --- Filter Data ---
# For multi-season, we need to build the range properly
if len(selected_seasons) == 1:
    # Single season: filter by season_match_number
    filtered_df = season_df[
        (season_df['season_match_number'] >= match_from) & 
        (season_df['season_match_number'] <= match_to)
    ].copy()
else:
    # Multi-season: from match X of first season to match Y of last season
    first_season = selected_seasons_sorted[0]
    last_season = selected_seasons_sorted[-1]
    middle_seasons = selected_seasons_sorted[1:-1] if len(selected_seasons_sorted) > 2 else []
    
    # First season: from match_from onwards
    first_df = season_df[
        (season_df['season'] == first_season) & 
        (season_df['season_match_number'] >= match_from)
    ]
    
    # Middle seasons: all matches
    middle_df = season_df[season_df['season'].isin(middle_seasons)] if middle_seasons else pd.DataFrame()
    
    # Last season: up to match_to
    last_df = season_df[
        (season_df['season'] == last_season) & 
        (season_df['season_match_number'] <= match_to)
    ]
    
    filtered_df = pd.concat([first_df, middle_df, last_df], ignore_index=True)

# Filter by league
if selected_league and selected_league != "All Leagues":
    filtered_df = filtered_df[filtered_df['league_display'] == selected_league]

# Filter by teams if selected
if selected_teams:
    filtered_df = filtered_df[filtered_df['team'].isin(selected_teams)]

if len(filtered_df) == 0:
    st.warning("No data found for selected filters")
    st.stop()

# --- Calculate Rankings ---
if mode == "Specific Match" and len(selected_seasons) == 1:
    # Single season, specific match
    snapshot_df = filtered_df[filtered_df['season_match_number'] == match_num].copy()
    snapshot_df = snapshot_df.sort_values('elo_rating', ascending=False).reset_index(drop=True)
    snapshot_df['rank'] = range(1, len(snapshot_df) + 1)
    
    st.subheader(f"Rankings after Match {match_num} ({selected_seasons_display[0]})")
    
    # Display table
    display_df = snapshot_df[['rank', 'team', 'league_display', 'elo_rating']].copy()
    display_df.columns = ['Rank', 'Team', 'League', 'ELO']
    display_df['ELO'] = display_df['ELO'].apply(lambda x: f"{x:.0f}")
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    # Bar chart for multiple teams
    if len(snapshot_df) > 1:
        st.subheader("ELO Comparison")
        
        if selected_teams:
            color_map = {team: PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)] 
                         for i, team in enumerate(selected_teams)}
        else:
            teams_sorted = snapshot_df.sort_values('elo_rating', ascending=False)['team'].tolist()
            color_map = {team: PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)] 
                         for i, team in enumerate(teams_sorted)}
        
        fig = px.bar(
            snapshot_df.sort_values('elo_rating', ascending=True),
            x='elo_rating',
            y='team',
            orientation='h',
            color='team',
            color_discrete_map=color_map,
            labels={'elo_rating': 'ELO Rating', 'team': 'Team'}
        )
        
        fig.add_vline(x=1500, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Starting ELO")
        
        fig.update_layout(
            height=max(300, len(snapshot_df) * 35),
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')

else:
    # Match range (single or multi-season)
    # Get start and end ELO for each team
    if len(selected_seasons) == 1:
        start_data = filtered_df[filtered_df['season_match_number'] == match_from]
        end_data = filtered_df[filtered_df['season_match_number'] == match_to]
    else:
        # Multi-season: start is match_from of first season, end is match_to of last season
        start_data = filtered_df[
            (filtered_df['season'] == selected_seasons_sorted[0]) & 
            (filtered_df['season_match_number'] == match_from)
        ]
        end_data = filtered_df[
            (filtered_df['season'] == selected_seasons_sorted[-1]) & 
            (filtered_df['season_match_number'] == match_to)
        ]
    
    start_elo = start_data.set_index('team')['elo_rating']
    end_elo = end_data.set_index('team')['elo_rating']
    
    # Get teams that have data for both start and end
    common_teams = start_elo.index.intersection(end_elo.index)
    
    if len(common_teams) == 0:
        st.warning("No teams found with data for both start and end of range")
        st.stop()
    
    range_df = pd.DataFrame({
        'team': common_teams,
        'elo_start': [start_elo[t] for t in common_teams],
        'elo_end': [end_elo[t] for t in common_teams],
    })
    range_df['change'] = range_df['elo_end'] - range_df['elo_start']
    
    # Add league info
    team_leagues = filtered_df.drop_duplicates('team').set_index('team')['league_display']
    range_df['league'] = range_df['team'].map(team_leagues)
    
    # Sort by end ELO and add rank
    range_df = range_df.sort_values('elo_end', ascending=False).reset_index(drop=True)
    range_df['rank'] = range(1, len(range_df) + 1)
    
    if len(selected_seasons) == 1:
        st.subheader(f"Rankings: Match {match_from} to {match_to} ({selected_seasons_display[0]})")
    else:
        st.subheader(f"Rankings: {selected_seasons_display_sorted[0]} Match {match_from} → {selected_seasons_display_sorted[-1]} Match {match_to}")
    
    # Display table
    display_df = range_df[['rank', 'team', 'league', 'elo_start', 'elo_end', 'change']].copy()
    display_df.columns = ['Rank', 'Team', 'League', 'ELO (Start)', 'ELO (End)', 'Change']
    
    def style_change(val):
        if val > 0:
            return f'+{val:.0f}'
        return f'{val:.0f}'
    
    display_df['ELO (Start)'] = display_df['ELO (Start)'].apply(lambda x: f"{x:.0f}")
    display_df['ELO (End)'] = display_df['ELO (End)'].apply(lambda x: f"{x:.0f}")
    display_df['Change'] = display_df['Change'].apply(style_change)
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    # Line chart for progression
    if len(range_df) > 0:
        st.subheader("ELO Progression")
        
        teams_to_show = range_df['team'].tolist()
        if selected_teams:
            teams_to_show = [t for t in selected_teams if t in teams_to_show]
        
        # Limit to max 10 teams for readability
        teams_to_show = teams_to_show[:10]
        
        chart_df = filtered_df[filtered_df['team'].isin(teams_to_show)].copy()
        
        # Create normalized match index (1, 2, 3...) per team within the selected range
        chart_df = chart_df.sort_values(['team', 'date'])
        chart_df['range_match'] = chart_df.groupby('team').cumcount() + 1
        
        # Create stable color map
        color_map = {team: PLOTLY_COLOR_SEQUENCE[i % len(PLOTLY_COLOR_SEQUENCE)] 
                     for i, team in enumerate(teams_to_show)}
        
        fig = px.line(
            chart_df,
            x='range_match',
            y='elo_rating',
            color='team',
            markers=True,
            color_discrete_map=color_map,
            labels={
                'range_match': 'Match in Range',
                'elo_rating': 'ELO Rating',
                'team': 'Team'
            }
        )
        
        fig.add_hline(y=1500, line_dash="dash", line_color="gray", opacity=0.5,
                      annotation_text="Starting ELO (1500)")
        
        fig.update_layout(
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width='stretch')

# Footer
st.divider()
st.caption("Data: football-data.co.uk | ELO calculated from 2020/21 season")
