"""
xG Analysis - Goals vs Expected Goals trends and over/underperformance.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import get_xg_matches
from src.config import (
    LEAGUE_DISPLAY_NAMES,
    PLOTLY_COLOR_SEQUENCE,
    SEASONS,
    SEASON_DISPLAY_NAMES,
    SEASON_CODES
)

st.set_page_config(
    page_title="xG Analysis | Gaffer's Notebook",
    layout="wide"
)

st.title("xG Analysis")
st.markdown("Compare actual goals to expected goals (xG) and identify over/underperformance.")
st.divider()


@st.cache_data(ttl=3600)
def load_xg_data():
    """Load all xG match data."""
    return get_xg_matches()


# Load data
xg_df = load_xg_data()

if len(xg_df) == 0:
    st.warning("No xG data available")
    st.stop()

# Add league display names
xg_df['league_display'] = xg_df['league'].map(LEAGUE_DISPLAY_NAMES)

# Get available seasons and leagues
available_season_codes = sorted(xg_df['season'].unique().tolist())
available_seasons_display = [SEASON_DISPLAY_NAMES.get(s, s) for s in available_season_codes]


def fill_season_gaps(seasons_display: list, all_seasons_display: list) -> list:
    """Fill gaps between non-adjacent seasons."""
    if len(seasons_display) <= 1:
        return seasons_display
    
    sorted_selected = sorted(seasons_display)
    first_idx = all_seasons_display.index(sorted_selected[0])
    last_idx = all_seasons_display.index(sorted_selected[-1])
    
    return all_seasons_display[first_idx:last_idx + 1]


# --- Filters ---
col1, col2, col3 = st.columns([1.5, 1, 1.5])

with col1:
    # Sort selected seasons before rendering
    if "xg_seasons" in st.session_state:
        current = st.session_state["xg_seasons"]
        sorted_current = sorted(current, key=lambda x: available_seasons_display.index(x) if x in available_seasons_display else 0)
        if current != sorted_current:
            st.session_state["xg_seasons"] = sorted_current
    
    selected_seasons_display = st.multiselect(
        "Season(s)",
        options=available_seasons_display,
        default=[available_seasons_display[-1]] if available_seasons_display else [],
        key="xg_seasons"
    )

with col2:
    leagues = sorted(xg_df['league_display'].dropna().unique().tolist())
    selected_league = st.selectbox(
        "League",
        options=leagues,
        index=0,
        key="xg_league"
    )

# Apply season gap filling
if selected_seasons_display:
    selected_seasons_display = fill_season_gaps(selected_seasons_display, available_seasons_display)

# Convert display names back to codes
selected_seasons = [SEASON_CODES.get(s, s) for s in selected_seasons_display]

# Filter data by league and seasons
filtered_df = xg_df[
    (xg_df['league_display'] == selected_league) &
    (xg_df['season'].isin(selected_seasons))
]

# Get available teams
available_teams = sorted(filtered_df['team'].unique().tolist())

with col3:
    selected_teams = st.multiselect(
        "Team(s) - max 2",
        options=available_teams,
        default=[available_teams[0]] if available_teams else [],
        max_selections=2,
        key="xg_teams"
    )

if not selected_teams:
    st.info("Select at least one team to view xG analysis.")
    st.stop()

# Filter to selected teams
team_df = filtered_df[filtered_df['team'].isin(selected_teams)].copy()

if len(team_df) == 0:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Match Range Filter ---
col1, col2 = st.columns(2)
with col1:
    max_match = int(team_df['match_number'].max())
    match_from = st.number_input("From Match", min_value=1, max_value=max_match, value=1, key="xg_match_from")
with col2:
    match_to = st.number_input("To Match", min_value=1, max_value=max_match, value=max_match, key="xg_match_to")

# Filter by match range
team_df = team_df[
    (team_df['match_number'] >= match_from) & 
    (team_df['match_number'] <= match_to)
]

st.divider()

# --- Summary Cards ---
st.subheader("Summary")

for idx, team in enumerate(selected_teams):
    team_data = team_df[team_df['team'] == team]
    
    total_goals = team_data['goals_for'].sum()
    total_xg = team_data['xg_for'].sum()
    total_goals_against = team_data['goals_against'].sum()
    total_xga = team_data['xg_against'].sum()
    
    goals_diff = total_goals - total_xg
    ga_diff = total_goals_against - total_xga
    
    # Determine performance status
    if goals_diff > 1:
        attack_status = "🔥 Clinical"
        attack_color = "green"
    elif goals_diff < -1:
        attack_status = "😰 Wasteful"
        attack_color = "red"
    else:
        attack_status = "➡️ Expected"
        attack_color = "gray"
    
    if ga_diff < -1:
        defense_status = "🛡️ Solid"
        defense_color = "green"
    elif ga_diff > 1:
        defense_status = "⚠️ Vulnerable"
        defense_color = "red"
    else:
        defense_status = "➡️ Expected"
        defense_color = "gray"
    
    st.markdown(f"**{team}** ({len(team_data)} matches)")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Goals", f"{total_goals}", f"{goals_diff:+.1f} vs xG")
    c2.metric("xG", f"{total_xg:.1f}", attack_status)
    c3.metric("Goals Against", f"{total_goals_against}", f"{ga_diff:+.1f} vs xGA")
    c4.metric("xGA", f"{total_xga:.1f}", defense_status)
    
    if idx < len(selected_teams) - 1:
        st.markdown("---")

st.divider()

# --- Goals vs xG Chart ---
st.subheader("Goals vs xG Over Time")

# Create normalized match numbers for comparison (start at 1 for each team within range)
team_df['range_match'] = team_df.groupby('team').cumcount() + 1

# Calculate cumulative values
team_df['cum_goals'] = team_df.groupby('team')['goals_for'].cumsum()
team_df['cum_xg'] = team_df.groupby('team')['xg_for'].cumsum()
team_df['cum_diff'] = team_df['cum_goals'] - team_df['cum_xg']

# Create chart for each team
for idx, team in enumerate(selected_teams):
    team_data = team_df[team_df['team'] == team].copy()
    
    fig = go.Figure()
    
    # Add xG line
    fig.add_trace(go.Scatter(
        x=team_data['range_match'],
        y=team_data['cum_xg'],
        name='Expected Goals (xG)',
        line=dict(color='#888888', width=2, dash='dash'),
        mode='lines'
    ))
    
    # Add actual goals line
    fig.add_trace(go.Scatter(
        x=team_data['range_match'],
        y=team_data['cum_goals'],
        name='Actual Goals',
        line=dict(color=PLOTLY_COLOR_SEQUENCE[idx], width=3),
        mode='lines'
    ))
    
    # Add filled area for difference
    fig.add_trace(go.Scatter(
        x=list(team_data['range_match']) + list(team_data['range_match'][::-1]),
        y=list(team_data['cum_goals']) + list(team_data['cum_xg'][::-1]),
        fill='toself',
        fillcolor='rgba(0, 200, 83, 0.2)' if team_data['cum_diff'].iloc[-1] > 0 else 'rgba(255, 82, 82, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Over/Under Performance',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"{team}: Cumulative Goals vs xG",
        xaxis_title="Match",
        yaxis_title="Cumulative Goals",
        height=400,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Defensive xG (xGA) Analysis ---
st.subheader("Defensive Performance: Goals Against vs xGA")

# Calculate cumulative defensive values
team_df['cum_ga'] = team_df.groupby('team')['goals_against'].cumsum()
team_df['cum_xga'] = team_df.groupby('team')['xg_against'].cumsum()
team_df['cum_def_diff'] = team_df['cum_ga'] - team_df['cum_xga']

for idx, team in enumerate(selected_teams):
    team_data = team_df[team_df['team'] == team].copy()
    
    fig = go.Figure()
    
    # Add xGA line
    fig.add_trace(go.Scatter(
        x=team_data['range_match'],
        y=team_data['cum_xga'],
        name='Expected Goals Against (xGA)',
        line=dict(color='#888888', width=2, dash='dash'),
        mode='lines'
    ))
    
    # Add actual goals against line
    fig.add_trace(go.Scatter(
        x=team_data['range_match'],
        y=team_data['cum_ga'],
        name='Actual Goals Against',
        line=dict(color=PLOTLY_COLOR_SEQUENCE[idx], width=3),
        mode='lines'
    ))
    
    # Add filled area (green = conceding less than expected, red = conceding more)
    final_diff = team_data['cum_def_diff'].iloc[-1]
    fig.add_trace(go.Scatter(
        x=list(team_data['range_match']) + list(team_data['range_match'][::-1]),
        y=list(team_data['cum_ga']) + list(team_data['cum_xga'][::-1]),
        fill='toself',
        fillcolor='rgba(0, 200, 83, 0.2)' if final_diff < 0 else 'rgba(255, 82, 82, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Under/Over Performing',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"{team}: Cumulative Goals Against vs xGA",
        xaxis_title="Match",
        yaxis_title="Cumulative Goals Against",
        height=400,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Match-by-Match Table ---
st.subheader("Match Details")

for team in selected_teams:
    team_data = team_df[team_df['team'] == team].copy()
    
    st.markdown(f"**{team}**")
    
    # Create display dataframe
    display_df = team_data[[
        'match_number', 'match_date', 'opponent', 'venue',
        'goals_for', 'goals_against', 'xg_for', 'xg_against',
        'npxg_for', 'npxg_against', 'result', 'points'
    ]].copy()
    
    display_df.columns = [
        'Match #', 'Date', 'Opponent', 'Venue',
        'GF', 'GA', 'xG', 'xGA',
        'npxG', 'npxGA', 'Result', 'Pts'
    ]
    
    # Format date
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Add over/under columns
    display_df['G-xG'] = display_df['GF'] - display_df['xG']
    display_df['GA-xGA'] = display_df['GA'] - display_df['xGA']
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            'G-xG': st.column_config.NumberColumn(format="%.2f"),
            'GA-xGA': st.column_config.NumberColumn(format="%.2f"),
            'xG': st.column_config.NumberColumn(format="%.2f"),
            'xGA': st.column_config.NumberColumn(format="%.2f"),
            'npxG': st.column_config.NumberColumn(format="%.2f"),
            'npxGA': st.column_config.NumberColumn(format="%.2f"),
        }
    )
