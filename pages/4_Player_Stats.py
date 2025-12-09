"""
Player Stats - Top contributors by goals and assists.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import unicodedata
from streamlit_searchbox import st_searchbox

from src.database import get_player_stats
from src.config import LEAGUE_DISPLAY_NAMES, CURRENT_SEASON, CHART_COLORS, SEASON_DISPLAY_NAMES, SEASON_CODES

st.set_page_config(
    page_title="Player Stats | Gaffer's Notebook",
    layout="wide"
)

st.title("Player Stats")
st.markdown("Top contributors by goals, assists, and overall contribution to team goals.")

st.divider()


def normalize_text(text):
    """Remove accents for search matching."""
    if not text:
        return ""
    # Normalize to NFD form, then remove combining characters (accents)
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn').lower()


@st.cache_data(ttl=3600)
def load_player_stats():
    return get_player_stats()


# Load data
player_stats_df = load_player_stats()

if len(player_stats_df) == 0:
    st.warning("No player stats data available")
    st.stop()

# Add display names and normalized names for search
player_stats_df['league_display'] = player_stats_df['league'].map(LEAGUE_DISPLAY_NAMES)
player_stats_df['player_name_normalized'] = player_stats_df['player_name'].apply(normalize_text)

# Get current season display name
CURRENT_SEASON_DISPLAY = SEASON_DISPLAY_NAMES.get(CURRENT_SEASON, CURRENT_SEASON)

# Handle reset
if "reset_player_filters" in st.session_state and st.session_state["reset_player_filters"]:
    st.session_state["reset_player_filters"] = False
    st.session_state["player_league"] = None
    st.session_state["player_season"] = CURRENT_SEASON_DISPLAY
    st.session_state["player_team"] = None
    st.session_state["selected_players_list"] = []
    st.session_state["player_min_games"] = 1
    st.session_state["player_min_contributions"] = 0
    st.session_state["skip_add_player"] = True  # Skip adding on this rerun
    # Clear searchbox state
    for key in list(st.session_state.keys()):
        if "searchbox" in key:
            del st.session_state[key]

# --- Filters Row 1 ---
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1.5, 1, 1, 0.5])

with col1:
    # League filter with "All Leagues" as default
    leagues = ["All Leagues"] + sorted(player_stats_df['league_display'].unique().tolist())
    selected_league = st.selectbox(
        "League",
        options=leagues,
        index=0,  # "All Leagues" is default
        key="player_league"
    )

with col2:
    # Season filter - default to current season (using display names)
    available_season_codes = sorted(player_stats_df['season'].unique().tolist())
    available_seasons_display = [SEASON_DISPLAY_NAMES.get(s, s) for s in available_season_codes]
    default_season_idx = available_seasons_display.index(CURRENT_SEASON_DISPLAY) if CURRENT_SEASON_DISPLAY in available_seasons_display else 0
    selected_season_display = st.selectbox(
        "Season",
        options=available_seasons_display,
        index=default_season_idx,
        key="player_season"
    )
    # Convert back to code for filtering
    selected_season = SEASON_CODES.get(selected_season_display, selected_season_display)

with col3:
    # Team filter (filtered by league)
    team_filter_df = player_stats_df.copy()
    if selected_league and selected_league != "All Leagues":
        league_key = [k for k, v in LEAGUE_DISPLAY_NAMES.items() if v == selected_league][0]
        team_filter_df = team_filter_df[team_filter_df['league'] == league_key]
    if selected_season:
        team_filter_df = team_filter_df[team_filter_df['season'] == selected_season]
    
    # Show teams with league in parentheses when "All Leagues" selected
    if selected_league == "All Leagues":
        team_league_map = team_filter_df.groupby('team')['league_display'].first().to_dict()
        available_teams_raw = sorted(team_filter_df['team'].unique().tolist())
        available_teams = ["All Teams"] + [f"{team} ({team_league_map[team]})" for team in available_teams_raw]
    else:
        available_teams = ["All Teams"] + sorted(team_filter_df['team'].unique().tolist())
    
    selected_team_display = st.selectbox(
        "Team",
        options=available_teams,
        index=0,  # "All Teams" is default
        key="player_team"
    )
    
    # Extract actual team name
    if selected_team_display == "All Teams":
        selected_team = None
    elif " (" in selected_team_display:
        selected_team = selected_team_display.rsplit(" (", 1)[0]
    else:
        selected_team = selected_team_display

with col4:
    min_games = st.number_input(
        "Min Games",
        min_value=1,
        max_value=50,
        value=st.session_state.get("player_min_games", 1),
        key="player_min_games"
    )

with col5:
    min_contributions = st.number_input(
        "Min G+A",
        min_value=0,
        max_value=50,
        value=st.session_state.get("player_min_contributions", 0),
        key="player_min_contributions"
    )

with col6:
    st.write("")
    st.write("")
    if st.button("Reset", key="reset_player_btn"):
        load_player_stats.clear()
        st.session_state["reset_player_filters"] = True
        st.rerun()

# --- Apply base filters ---
filtered_df = player_stats_df.copy()

if selected_league and selected_league != "All Leagues":
    league_key = [k for k, v in LEAGUE_DISPLAY_NAMES.items() if v == selected_league][0]
    filtered_df = filtered_df[filtered_df['league'] == league_key]

if selected_season:
    filtered_df = filtered_df[filtered_df['season'] == selected_season]

if selected_team:
    filtered_df = filtered_df[filtered_df['team'] == selected_team]

filtered_df = filtered_df[filtered_df['games_played'] >= min_games]
filtered_df = filtered_df[filtered_df['contributions'] >= min_contributions]

if len(filtered_df) == 0:
    st.warning("No data found for selected filters")
    st.stop()

# --- Player Search & Compare ---
st.markdown("### Compare Players")

# Initialize selected players in session state
if "selected_players_list" not in st.session_state:
    st.session_state["selected_players_list"] = []

# Create player lookup for searchbox
all_players = filtered_df['player_name'].unique().tolist()
player_normalized_map = {name: normalize_text(name) for name in all_players}

def search_players(search_term: str) -> list:
    """Search players with accent-insensitive matching."""
    already_selected = st.session_state.get("selected_players_list", [])
    
    if not search_term:
        # Show first 20 available players when no search term
        available = [name for name in all_players if name not in already_selected]
        return sorted(available)[:20]
    
    search_normalized = normalize_text(search_term)
    matches = [
        name for name, normalized in player_normalized_map.items()
        if search_normalized in normalized and name not in already_selected
    ]
    return sorted(matches)[:20]  # Limit to 20 results

col_search, col_selected = st.columns([1, 2])

with col_search:
    selected_player = st_searchbox(
        search_players,
        label="Search Player (accents optional)",
        placeholder="Type to search...",
        key="player_searchbox",
        clear_on_submit=True
    )
    
    # Add player to list when selected (skip if just reset)
    skip_add = st.session_state.pop("skip_add_player", False)
    if not skip_add and selected_player and selected_player not in st.session_state["selected_players_list"]:
        if len(st.session_state["selected_players_list"]) < 10:
            st.session_state["selected_players_list"].append(selected_player)
            st.rerun()
        else:
            st.warning("Maximum 10 players")

with col_selected:
    st.markdown("**Selected Players:**")
    if st.session_state["selected_players_list"]:
        # Display selected players with remove buttons
        for i, player in enumerate(list(st.session_state["selected_players_list"])):
            col_name, col_btn = st.columns([4, 1])
            with col_name:
                st.write(f"{i+1}. {player}")
            with col_btn:
                if st.button("X", key=f"remove_{i}_{player}"):
                    st.session_state["selected_players_list"].remove(player)
                    st.session_state["skip_add_player"] = True
                    # Clear searchbox to prevent re-add
                    for key in list(st.session_state.keys()):
                        if "searchbox" in key:
                            del st.session_state[key]
                    st.rerun()
    else:
        st.caption("No players selected. Search and click to add.")

selected_players = st.session_state["selected_players_list"]

# --- Bar Chart (if players selected) ---
if selected_players:
    st.divider()
    st.subheader("Contribution Breakdown")
    
    # Get data for selected players from FULL dataset (not filtered)
    # Filter only by season to compare players in same timeframe
    chart_base_df = player_stats_df.copy()
    if selected_season:
        chart_base_df = chart_base_df[chart_base_df['season'] == selected_season]
    
    chart_df = chart_base_df[chart_base_df['player_name'].isin(selected_players)].copy()
    
    if len(chart_df) == 0:
        st.warning("No data found for selected players in this season")
    else:
        # Add team to player name for chart label
        chart_df['label'] = chart_df['player_name'] + ' (' + chart_df['team'] + ')'
        
        # Sort by total contribution
        chart_df = chart_df.sort_values('contribution_pct', ascending=True)
        
        # Create stacked horizontal bar chart
        fig = go.Figure()
        
        # Goals portion
        fig.add_trace(go.Bar(
            y=chart_df['label'],
            x=chart_df['goals_pct'],
            name='Goals %',
            orientation='h',
            marker_color=CHART_COLORS['secondary'],
            text=chart_df['goals_pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='inside'
        ))
        
        # Assists portion
        fig.add_trace(go.Bar(
            y=chart_df['label'],
            x=chart_df['assists_pct'],
            name='Assists %',
            orientation='h',
            marker_color=CHART_COLORS['primary'],
            text=chart_df['assists_pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='inside'
        ))
        
        fig.update_layout(
            barmode='stack',
            height=max(300, len(chart_df) * 50),
            xaxis_title="% of Team Goals",
            yaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=200)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Comparison table for selected players
        st.markdown("**Comparison Details**")
        comparison_df = chart_df[[
            'player_name', 'team', 'league_display', 
            'goals', 'assists', 'contributions', 'contribution_pct', 'games_played'
        ]].copy()
        comparison_df.columns = ['Player', 'Team', 'League', 'Goals', 'Assists', 'G+A', 'Contribution %', 'Games']
        comparison_df = comparison_df.sort_values('G+A', ascending=False)
        
        styled_comparison = comparison_df.style.format({
            'Contribution %': '{:.1f}%',
            'Goals': '{:.0f}',
            'Assists': '{:.0f}',
            'G+A': '{:.0f}',
            'Games': '{:.0f}'
        })
        
        st.dataframe(styled_comparison, width='stretch', hide_index=True)

st.divider()

# --- Display Table ---
st.subheader(f"All Players ({len(filtered_df):,} players)")

# Prepare display dataframe
display_df = filtered_df[[
    'player_name', 'team', 'league_display', 'season',
    'goals', 'assists', 'contributions', 'contribution_pct', 'games_played'
]].copy()

# Convert season to display format
display_df['season'] = display_df['season'].map(SEASON_DISPLAY_NAMES)

display_df.columns = ['Player', 'Team', 'League', 'Season', 'Goals', 'Assists', 'G+A', 'Contribution %', 'Games']

# Sort by contributions descending
display_df = display_df.sort_values('G+A', ascending=False)

# Style the dataframe
styled_df = display_df.style.format({
    'Contribution %': '{:.1f}%',
    'Goals': '{:.0f}',
    'Assists': '{:.0f}',
    'G+A': '{:.0f}',
    'Games': '{:.0f}'
})

st.dataframe(
    styled_df,
    width='stretch',
    hide_index=True,
    height=500
)

# --- Summary Stats ---
st.divider()
st.subheader("Quick Stats")

col1, col2, col3, col4 = st.columns(4)

top_scorer = display_df.nlargest(1, 'Goals').iloc[0] if len(display_df) > 0 else None
top_assister = display_df.nlargest(1, 'Assists').iloc[0] if len(display_df) > 0 else None
top_contributor = display_df.nlargest(1, 'G+A').iloc[0] if len(display_df) > 0 else None
highest_pct = display_df.nlargest(1, 'Contribution %').iloc[0] if len(display_df) > 0 else None

with col1:
    if top_scorer is not None:
        st.metric("Top Scorer", f"{top_scorer['Player']}", f"{int(top_scorer['Goals'])} goals")

with col2:
    if top_assister is not None:
        st.metric("Top Assister", f"{top_assister['Player']}", f"{int(top_assister['Assists'])} assists")

with col3:
    if top_contributor is not None:
        st.metric("Top Contributor", f"{top_contributor['Player']}", f"{int(top_contributor['G+A'])} G+A")

with col4:
    if highest_pct is not None:
        st.metric("Highest Impact", f"{highest_pct['Player']}", f"{highest_pct['Contribution %']:.1f}% of team goals")

# Footer
st.divider()
st.caption("Data: football-data.co.uk & Understat.com")
