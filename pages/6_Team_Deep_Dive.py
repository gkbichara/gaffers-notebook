"""
Team Deep Dive - Single team focus with detailed analysis.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.database import get_elo_ratings, get_team_elo_history, get_player_stats, get_xg_matches, get_raw_matches
from src.config import LEAGUE_DISPLAY_NAMES, PLOTLY_COLOR_SEQUENCE, CHART_COLORS, SEASON_DISPLAY_NAMES

st.set_page_config(
    page_title="Team Deep Dive | Gaffer's Notebook",
    layout="wide"
)

st.title("Team Deep Dive")
st.markdown("In-depth analysis for a single team.")
st.divider()


@st.cache_data(ttl=3600)
def load_elo_ratings():
    return get_elo_ratings()


@st.cache_data(ttl=3600)
def load_team_history(team):
    return get_team_elo_history(team=team)


@st.cache_data(ttl=3600)
def load_player_stats():
    return get_player_stats()


@st.cache_data(ttl=3600)
def load_xg_data():
    return get_xg_matches()


@st.cache_data(ttl=3600)
def load_raw_matches():
    return get_raw_matches()


# Load data
elo_df = load_elo_ratings()

if len(elo_df) == 0:
    st.warning("No team data available")
    st.stop()

# Add display names
elo_df['league_display'] = elo_df['league'].map(LEAGUE_DISPLAY_NAMES)

# --- Team Selector ---
team_league_map = elo_df.set_index('team')['league_display'].to_dict()
available_teams_raw = sorted(elo_df['team'].unique().tolist())
available_teams = [f"{team} ({team_league_map[team]})" for team in available_teams_raw]
team_name_map = {f"{team} ({team_league_map[team]})": team for team in available_teams_raw}

# Find Roma as default
default_team_display = None
for team_option in available_teams:
    if 'Roma' in team_option:
        default_team_display = team_option
        break
if default_team_display is None and available_teams:
    default_team_display = available_teams[0]

default_idx = available_teams.index(default_team_display) if default_team_display else 0

selected_team_display = st.selectbox(
    "Select Team",
    options=available_teams,
    index=default_idx,
    key="deep_dive_team"
)

selected_team = team_name_map.get(selected_team_display, selected_team_display)
team_info = elo_df[elo_df['team'] == selected_team].iloc[0]

# Team header
col1, col2, col3 = st.columns(3)
col1.metric("League", team_info['league_display'])
col2.metric("Current ELO", f"{team_info['elo_rating']:.0f}")
col3.metric("Matches Played", team_info['matches_played'])

st.divider()

# ============================================================
# ELO Over Time
# ============================================================
st.subheader("ELO Over Time")

team_history = load_team_history(selected_team)

if len(team_history) > 0:
    team_history['date'] = pd.to_datetime(team_history['date'])
    
    # Date range filter
    min_date = team_history['date'].min().date()
    max_date = team_history['date'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
    
    # Filter
    filtered = team_history[
        (team_history['date'].dt.date >= start_date) &
        (team_history['date'].dt.date <= end_date)
    ]
    
    if len(filtered) > 0:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=filtered['date'],
            y=filtered['elo_rating'],
            mode='lines+markers',
            name='ELO Rating',
            line=dict(color=PLOTLY_COLOR_SEQUENCE[0], width=2),
            marker=dict(size=4)
        ))
        
        fig.add_hline(y=1500, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            height=400,
            template="plotly_dark",
            xaxis_title="Date",
            yaxis_title="ELO Rating",
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Summary
        start_elo = filtered.iloc[0]['elo_rating']
        end_elo = filtered.iloc[-1]['elo_rating']
        change = end_elo - start_elo
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Start ELO", f"{start_elo:.0f}")
        c2.metric("End ELO", f"{end_elo:.0f}")
        c3.metric("Change", f"{change:+.0f}")
        c4.metric("Matches", len(filtered))
    else:
        st.info("No matches in selected date range")
else:
    st.info("No ELO history available")

st.divider()

# ============================================================
# Player Reliance
# ============================================================
st.subheader("Player Reliance")

player_df = load_player_stats()
team_players = player_df[player_df['team'] == selected_team].copy()

if len(team_players) > 0:
    # Season filter
    available_seasons = sorted(team_players['season'].unique().tolist(), reverse=True)
    season_options = [SEASON_DISPLAY_NAMES.get(s, s) for s in available_seasons]
    
    selected_season_display = st.selectbox(
        "Season",
        options=season_options,
        index=0,
        key="player_season"
    )
    
    # Convert back to code
    season_code = next((k for k, v in SEASON_DISPLAY_NAMES.items() if v == selected_season_display), selected_season_display)
    season_players = team_players[team_players['season'] == season_code].copy()
    
    if len(season_players) > 0:
        # Sort by contributions
        season_players = season_players.sort_values('contributions', ascending=False)
        top_8 = season_players.head(8)
        
        # Calculate % of team goals (goals + assists both count toward team output)
        total_team_goals = season_players['goals'].sum()
        
        top_8 = top_8.copy()
        top_8['goals_pct'] = (top_8['goals'] / total_team_goals * 100) if total_team_goals > 0 else 0
        top_8['assists_pct'] = (top_8['assists'] / total_team_goals * 100) if total_team_goals > 0 else 0
        
        # Horizontal stacked bar chart showing % contribution
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=top_8['player_name'],
            x=top_8['goals_pct'],
            name='Goals %',
            orientation='h',
            marker_color='#2ca02c',  # Green
            text=top_8['goals_pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='inside',
            textfont=dict(color='white'),
            hovertemplate='%{y}: %{x:.1f}% of team goals<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            y=top_8['player_name'],
            x=top_8['assists_pct'],
            name='Assists %',
            orientation='h',
            marker_color=CHART_COLORS['primary'],  # Blue
            text=top_8['assists_pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='inside',
            textfont=dict(color='white'),
            hovertemplate='%{y}: %{x:.1f}% of team goals (assists)<extra></extra>'
        ))
        
        fig.update_layout(
            barmode='stack',
            height=350,
            template="plotly_dark",
            xaxis_title="% of Team Goals",
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Top contributors table
        display_df = top_8[['player_name', 'games_played', 'goals', 'assists', 'contributions', 'contribution_pct']].copy()
        display_df.columns = ['Player', 'Games', 'Goals', 'Assists', 'G+A', 'Team %']
        
        st.dataframe(
            display_df,
            hide_index=True,
            width='stretch',
            column_config={
                'Team %': st.column_config.NumberColumn(format="%.1f%%"),
            }
        )
    else:
        st.info("No player data for selected season")
else:
    st.info("No player stats available for this team")

st.divider()

# ============================================================
# Form Trends (uses all history, not filtered)
# ============================================================
st.subheader("Form Trends")

if len(team_history) > 0:
    # Sort by date and calculate rolling stats
    form_df = team_history.sort_values('date').copy()
    form_df['points'] = form_df['team_result'].map({'W': 3, 'D': 1, 'L': 0})
    
    # Rolling averages
    form_df['rolling_5'] = form_df['points'].rolling(5, min_periods=5).mean()
    form_df['rolling_10'] = form_df['points'].rolling(10, min_periods=10).mean()
    
    # Current form (last 5 and 10)
    last_5 = form_df.tail(5)
    last_10 = form_df.tail(10)
    
    last_5_form = ''.join(last_5['team_result'].tolist())
    last_5_ppg = last_5['points'].mean()
    last_10_ppg = last_10['points'].mean() if len(last_10) >= 10 else last_10['points'].mean()
    
    # Form string with colors
    form_html = ''
    for r in last_5_form:
        if r == 'W':
            form_html += '<span style="color: #2ca02c; font-weight: bold;">W</span> '
        elif r == 'L':
            form_html += '<span style="color: #d62728; font-weight: bold;">L</span> '
        else:
            form_html += '<span style="color: #7f7f7f; font-weight: bold;">D</span> '
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Last 5:** {form_html}", unsafe_allow_html=True)
    with col2:
        st.metric("Last 5 PPG", f"{last_5_ppg:.2f}")
    with col3:
        st.metric("Last 10 PPG", f"{last_10_ppg:.2f}")
    
    # Rolling PPG line chart
    plot_df = form_df.dropna(subset=['rolling_5'])
    
    if len(plot_df) > 0:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=plot_df['date'],
            y=plot_df['rolling_5'],
            mode='lines',
            name='5-Match Rolling',
            line=dict(color=PLOTLY_COLOR_SEQUENCE[0], width=2)
        ))
        
        if 'rolling_10' in plot_df.columns:
            plot_df_10 = form_df.dropna(subset=['rolling_10'])
            if len(plot_df_10) > 0:
                fig.add_trace(go.Scatter(
                    x=plot_df_10['date'],
                    y=plot_df_10['rolling_10'],
                    mode='lines',
                    name='10-Match Rolling',
                    line=dict(color=PLOTLY_COLOR_SEQUENCE[1], width=2)
                ))
        
        # Reference lines
        fig.add_hline(y=2.0, line_dash="dash", line_color="green", opacity=0.3)
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", opacity=0.3)
        
        fig.update_layout(
            height=350,
            template="plotly_dark",
            yaxis_title="Points Per Game",
            xaxis_title="Date",
            yaxis=dict(range=[0, 3]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        st.caption("Green line = 2.0 PPG (title form), Red line = 1.0 PPG (relegation form)")
else:
    st.info("No match history available")

st.divider()

# ============================================================
# Shared Season Filter (for sections below)
# ============================================================
st.subheader("Season Filter")
st.caption("Applies to all sections below")

# Load xG data to get available seasons
xg_df = load_xg_data()
team_xg = xg_df[xg_df['team'] == selected_team].copy()

# Get all available seasons from both data sources
all_seasons_xg = set(team_xg['season'].unique()) if len(team_xg) > 0 else set()
all_seasons_history = set(team_history['season'].unique()) if len(team_history) > 0 else set()
all_seasons = sorted(all_seasons_xg | all_seasons_history, reverse=True)

season_options_display = ["All Seasons"] + [SEASON_DISPLAY_NAMES.get(s, s) for s in all_seasons]
all_seasons_list = [SEASON_DISPLAY_NAMES.get(s, s) for s in all_seasons]

# Handle mutual exclusivity: All Seasons vs individual seasons
if "shared_season_filter" in st.session_state:
    current = st.session_state["shared_season_filter"]
    # If All Seasons was just added alongside others, keep only All Seasons
    if "All Seasons" in current and len(current) > 1:
        # Check if All Seasons was there before
        prev = st.session_state.get("_prev_season_filter", ["All Seasons"])
        if "All Seasons" in prev:
            # User added a specific season, remove All Seasons
            st.session_state["shared_season_filter"] = [s for s in current if s != "All Seasons"]
        else:
            # User added All Seasons, keep only that
            st.session_state["shared_season_filter"] = ["All Seasons"]
    
    # Sort selected seasons chronologically (excluding All Seasons) - oldest first
    current = st.session_state["shared_season_filter"]
    if "All Seasons" not in current and len(current) > 1:
        sorted_current = sorted(current, key=lambda x: all_seasons_list.index(x) if x in all_seasons_list else 0, reverse=True)
        if current != sorted_current:
            st.session_state["shared_season_filter"] = sorted_current

selected_seasons_display = st.multiselect(
    "Select Season(s)",
    options=season_options_display,
    default=["All Seasons"],
    key="shared_season_filter"
)

# Store for next comparison
st.session_state["_prev_season_filter"] = selected_seasons_display.copy()

# Convert to season codes
if "All Seasons" in selected_seasons_display or len(selected_seasons_display) == 0:
    selected_season_codes = all_seasons  # All seasons
else:
    selected_season_codes = [
        next((k for k, v in SEASON_DISPLAY_NAMES.items() if v == s), s)
        for s in selected_seasons_display
    ]

# Filter data based on selection
filtered_team_xg = team_xg[team_xg['season'].isin(selected_season_codes)].copy() if len(team_xg) > 0 else pd.DataFrame()
filtered_team_history = team_history[team_history['season'].isin(selected_season_codes)].copy() if len(team_history) > 0 else pd.DataFrame()

st.divider()

# ============================================================
# Attack/Defense Profile
# ============================================================
st.subheader("Attack & Defense Profile")

if len(filtered_team_xg) > 0:
    season_xg = filtered_team_xg
    
    # Aggregate stats
    total_goals = season_xg['goals_for'].sum()
    total_xg = season_xg['xg_for'].sum()
    total_ga = season_xg['goals_against'].sum()
    total_xga = season_xg['xg_against'].sum()
    matches = len(season_xg)
    
    goals_diff = total_goals - total_xg
    ga_diff = total_ga - total_xga
    
    # Determine profiles
    if goals_diff > 3:
        attack_profile = "Clinical"
        attack_desc = "Scoring more than expected"
    elif goals_diff < -3:
        attack_profile = "Wasteful"
        attack_desc = "Underperforming xG"
    else:
        attack_profile = "On Track"
        attack_desc = "Scoring as expected"
    
    if ga_diff < -3:
        defense_profile = "Solid"
        defense_desc = "Overperforming xGA"
    elif ga_diff > 3:
        defense_profile = "Leaky"
        defense_desc = "Underperforming xGA"
    else:
        defense_profile = "Average"
        defense_desc = "Performing to xGA"
    
    # Calculate per-match diffs
    season_xg['attack_diff'] = season_xg['goals_for'] - season_xg['xg_for']
    season_xg['defense_diff'] = season_xg['goals_against'] - season_xg['xg_against']
    
    # Get top 3 examples based on profile
    if attack_profile == "Clinical":
        attack_examples = season_xg.nlargest(3, 'attack_diff')
    else:  # Wasteful or On Track - show worst
        attack_examples = season_xg.nsmallest(3, 'attack_diff')
    
    if defense_profile == "Solid":
        defense_examples = season_xg.nsmallest(3, 'defense_diff')
    else:  # Leaky or Average - show worst
        defense_examples = season_xg.nlargest(3, 'defense_diff')
    
    # Display metrics
    home_count = len(season_xg[season_xg['venue'].str.upper() == 'H'])
    away_count = len(season_xg[season_xg['venue'].str.upper() == 'A'])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Matches", matches)
    m2.metric("Home", home_count)
    m3.metric("Away", away_count)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Attack: {attack_profile}**")
        st.caption(attack_desc)
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", total_goals)
        m2.metric("xG", f"{total_xg:.1f}")
        m3.metric("Diff", f"{goals_diff:+.1f}")
        
        # Top 3 attack examples
        st.markdown("**Key matches:**")
        for _, row in attack_examples.iterrows():
            diff = row['attack_diff']
            st.caption(f"vs {row['opponent']} ({row['venue']}): {int(row['goals_for'])} goals from {row['xg_for']:.1f} xG ({diff:+.1f})")
    
    with col2:
        st.markdown(f"**Defense: {defense_profile}**")
        st.caption(defense_desc)
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals Against", total_ga)
        m2.metric("xGA", f"{total_xga:.1f}")
        m3.metric("Diff", f"{ga_diff:+.1f}")
        
        # Top 3 defense examples
        st.markdown("**Key matches:**")
        for _, row in defense_examples.iterrows():
            diff = row['defense_diff']
            st.caption(f"vs {row['opponent']} ({row['venue']}): {int(row['goals_against'])} GA from {row['xg_against']:.1f} xGA ({diff:+.1f})")
    
    # Per-game averages chart
    fig = go.Figure()
    
    categories = ['Goals/Game', 'xG/Game', 'GA/Game', 'xGA/Game']
    values = [
        total_goals / matches,
        total_xg / matches,
        total_ga / matches,
        total_xga / matches
    ]
    colors = ['#2ca02c', '#2ca02c', '#d62728', '#d62728']
    patterns = ['', '/', '', '/']
    
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        marker_pattern_shape=patterns,
        text=[f"{v:.2f}" for v in values],
        textposition='outside'
    ))
    
    fig.update_layout(
        height=300,
        template="plotly_dark",
        yaxis_title="Per Game",
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch')
else:
    st.info("No xG data available for selected seasons")

st.divider()

# ============================================================
# Home vs Away Form
# ============================================================
st.subheader("Home vs Away Form")

if len(filtered_team_history) > 0:
    home_matches = filtered_team_history[filtered_team_history['venue'] == 'H']
    away_matches = filtered_team_history[filtered_team_history['venue'] == 'A']
    
    def calc_stats(matches):
        if len(matches) == 0:
            return {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'GF': 0, 'GA': 0, 'PPG': 0, 'Win%': 0}
        w = (matches['team_result'] == 'W').sum()
        d = (matches['team_result'] == 'D').sum()
        l = (matches['team_result'] == 'L').sum()
        gf = matches['goals_for'].sum()
        ga = matches['goals_against'].sum()
        pts = w * 3 + d
        return {
            'P': len(matches), 'W': w, 'D': d, 'L': l,
            'GF': gf, 'GA': ga, 'GD': gf - ga,
            'PPG': pts / len(matches),
            'Win%': w / len(matches) * 100
        }
    
    home = calc_stats(home_matches)
    away = calc_stats(away_matches)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Home**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Played", home['P'])
        m2.metric("W-D-L", f"{home['W']}-{home['D']}-{home['L']}")
        m3.metric("Win %", f"{home['Win%']:.0f}%")
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Goals For", home['GF'])
        m5.metric("Goals Against", home['GA'])
        m6.metric("GD", f"{home['GD']:+d}")
    
    with col2:
        st.markdown("**Away**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Played", away['P'])
        m2.metric("W-D-L", f"{away['W']}-{away['D']}-{away['L']}")
        m3.metric("Win %", f"{away['Win%']:.0f}%")
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Goals For", away['GF'])
        m5.metric("Goals Against", away['GA'])
        m6.metric("GD", f"{away['GD']:+d}")
    
    # Comparison bar chart
    fig = go.Figure()
    
    metrics = ['PPG', 'Goals/Game', 'GA/Game']
    home_vals = [
        home['PPG'],
        home['GF'] / home['P'] if home['P'] > 0 else 0,
        home['GA'] / home['P'] if home['P'] > 0 else 0
    ]
    away_vals = [
        away['PPG'],
        away['GF'] / away['P'] if away['P'] > 0 else 0,
        away['GA'] / away['P'] if away['P'] > 0 else 0
    ]
    
    fig.add_trace(go.Bar(name='Home', x=metrics, y=home_vals, marker_color=CHART_COLORS['primary']))
    fig.add_trace(go.Bar(name='Away', x=metrics, y=away_vals, marker_color=CHART_COLORS['accent']))
    
    fig.update_layout(
        barmode='group',
        height=300,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width='stretch')
else:
    st.info("No match history for selected seasons")

st.divider()

# ============================================================
# First Half vs Second Half
# ============================================================
st.subheader("First Half vs Second Half")

raw_df = load_raw_matches()

# Filter for selected team (home or away)
team_raw = raw_df[(raw_df['home_team'] == selected_team) | (raw_df['away_team'] == selected_team)].copy()

# Filter by selected seasons
team_raw = team_raw[team_raw['season'].isin(selected_season_codes)]

if len(team_raw) > 0:
    # Calculate HT and FT results for the team
    def get_team_result(row):
        is_home = row['home_team'] == selected_team
        if is_home:
            ht_gf, ht_ga = row['hthg'], row['htag']
            ft_gf, ft_ga = row['fthg'], row['ftag']
        else:
            ht_gf, ht_ga = row['htag'], row['hthg']
            ft_gf, ft_ga = row['ftag'], row['fthg']
        
        ht_result = 'W' if ht_gf > ht_ga else ('L' if ht_gf < ht_ga else 'D')
        ft_result = 'W' if ft_gf > ft_ga else ('L' if ft_gf < ft_ga else 'D')
        
        return pd.Series({'ht_result': ht_result, 'ft_result': ft_result})
    
    results = team_raw.apply(get_team_result, axis=1)
    team_raw = pd.concat([team_raw, results], axis=1)
    
    # FT results
    ft_wins = team_raw[team_raw['ft_result'] == 'W']
    ft_draws = team_raw[team_raw['ft_result'] == 'D']
    ft_losses = team_raw[team_raw['ft_result'] == 'L']
    
    matches = len(team_raw)
    
    # Summary metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matches", matches)
    m2.metric("Wins", len(ft_wins))
    m3.metric("Draws", len(ft_draws))
    m4.metric("Losses", len(ft_losses))
    
    # Calculate where each FT result came from (HT position)
    def calc_ht_breakdown(df):
        if len(df) == 0:
            return {'W': 0, 'D': 0, 'L': 0}
        total = len(df)
        return {
            'W': (df['ht_result'] == 'W').sum() / total * 100,
            'D': (df['ht_result'] == 'D').sum() / total * 100,
            'L': (df['ht_result'] == 'L').sum() / total * 100
        }
    
    wins_from = calc_ht_breakdown(ft_wins)
    draws_from = calc_ht_breakdown(ft_draws)
    losses_from = calc_ht_breakdown(ft_losses)
    
    # 100% stacked horizontal bar chart
    fig = go.Figure()
    
    ft_outcomes = ['Losses', 'Draws', 'Wins']
    winning_ht = [losses_from['W'], draws_from['W'], wins_from['W']]
    drawing_ht = [losses_from['D'], draws_from['D'], wins_from['D']]
    losing_ht = [losses_from['L'], draws_from['L'], wins_from['L']]
    
    fig.add_trace(go.Bar(
        name='Winning at HT',
        y=ft_outcomes,
        x=winning_ht,
        orientation='h',
        marker_color='#2ca02c',
        text=[f"{v:.0f}%" for v in winning_ht],
        textposition='inside'
    ))
    
    fig.add_trace(go.Bar(
        name='Drawing at HT',
        y=ft_outcomes,
        x=drawing_ht,
        orientation='h',
        marker_color='#7f7f7f',
        text=[f"{v:.0f}%" for v in drawing_ht],
        textposition='inside'
    ))
    
    fig.add_trace(go.Bar(
        name='Losing at HT',
        y=ft_outcomes,
        x=losing_ht,
        orientation='h',
        marker_color='#d62728',
        text=[f"{v:.0f}%" for v in losing_ht],
        textposition='inside'
    ))
    
    fig.update_layout(
        barmode='stack',
        height=250,
        template="plotly_dark",
        xaxis_title="% of Results",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Text summary
    st.caption(f"**Wins:** {wins_from['W']:.0f}% held lead, {wins_from['D']:.0f}% pushed on from draw, {wins_from['L']:.0f}% comeback")
    st.caption(f"**Draws:** {draws_from['W']:.0f}% dropped points, {draws_from['D']:.0f}% stayed level, {draws_from['L']:.0f}% salvaged point")
    st.caption(f"**Losses:** {losses_from['W']:.0f}% collapsed, {losses_from['D']:.0f}% faded, {losses_from['L']:.0f}% stayed behind")
else:
    st.info("No match data for selected seasons")

st.divider()

# ============================================================
# Head-to-Head Records
# ============================================================
st.subheader("Head-to-Head Records")

if len(filtered_team_history) > 0:
    # Calculate H2H stats against all opponents
    h2h_stats = filtered_team_history.groupby('opponent').agg({
        'team_result': list,
        'goals_for': ['sum', 'count'],
        'goals_against': 'sum'
    }).reset_index()
    
    h2h_stats.columns = ['Opponent', 'results', 'GF', 'Matches', 'GA']
    
    # Calculate W/D/L
    h2h_stats['W'] = h2h_stats['results'].apply(lambda x: x.count('W'))
    h2h_stats['D'] = h2h_stats['results'].apply(lambda x: x.count('D'))
    h2h_stats['L'] = h2h_stats['results'].apply(lambda x: x.count('L'))
    h2h_stats['Points'] = h2h_stats['W'] * 3 + h2h_stats['D']
    h2h_stats['PPG'] = h2h_stats['Points'] / h2h_stats['Matches']
    h2h_stats['GD'] = h2h_stats['GF'] - h2h_stats['GA']
    h2h_stats['Win%'] = h2h_stats['W'] / h2h_stats['Matches'] * 100
    
    # Min matches filter
    max_matches = int(h2h_stats['Matches'].max())
    min_matches = st.slider("Minimum matches", min_value=1, max_value=max_matches, value=2, key="h2h_min_matches")
    
    frequent = h2h_stats[h2h_stats['Matches'] >= min_matches].copy()
    
    if len(frequent) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Best Record Against (min {min_matches} matches)**")
            best = frequent.nlargest(5, 'PPG')
            for _, row in best.iterrows():
                st.caption(f"{row['Opponent']}: {row['W']}-{row['D']}-{row['L']} ({row['PPG']:.2f} PPG, GD {row['GD']:+d})")
        
        with col2:
            st.markdown(f"**Worst Record Against (min {min_matches} matches)**")
            worst = frequent.nsmallest(5, 'PPG')
            for _, row in worst.iterrows():
                st.caption(f"{row['Opponent']}: {row['W']}-{row['D']}-{row['L']} ({row['PPG']:.2f} PPG, GD {row['GD']:+d})")
    
    # Full table
    st.markdown("**All Opponents**")
    
    sort_option = st.selectbox(
        "Sort by",
        options=['Most Matches', 'Best PPG', 'Worst PPG', 'Best GD', 'Worst GD'],
        key="h2h_sort"
    )
    
    if sort_option == 'Most Matches':
        frequent = frequent.sort_values('Matches', ascending=False)
    elif sort_option == 'Best PPG':
        frequent = frequent.sort_values('PPG', ascending=False)
    elif sort_option == 'Worst PPG':
        frequent = frequent.sort_values('PPG', ascending=True)
    elif sort_option == 'Best GD':
        frequent = frequent.sort_values('GD', ascending=False)
    else:
        frequent = frequent.sort_values('GD', ascending=True)
    
    display_h2h = frequent[['Opponent', 'Matches', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'PPG']].head(15)
    
    st.dataframe(
        display_h2h,
        hide_index=True,
        width='stretch',
        column_config={
            'PPG': st.column_config.NumberColumn(format="%.2f"),
            'GD': st.column_config.NumberColumn(format="%+d"),
        }
    )
else:
    st.info("No match history for selected seasons")

st.divider()

# ============================================================
# Day of Week Performance
# ============================================================
st.subheader("Day of Week Performance")

# Reuse team_raw from First Half vs Second Half section
if len(team_raw) > 0 and 'ft_result' in team_raw.columns:
    # Extract day of week
    team_raw['date'] = pd.to_datetime(team_raw['date'])
    team_raw['day_of_week'] = team_raw['date'].dt.day_name()
    
    # Calculate stats by day
    def calc_day_stats(df):
        if len(df) == 0:
            return {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'PPG': 0, 'Win%': 0}
        w = (df['ft_result'] == 'W').sum()
        d = (df['ft_result'] == 'D').sum()
        l = (df['ft_result'] == 'L').sum()
        pts = w * 3 + d
        return {
            'P': len(df), 'W': w, 'D': d, 'L': l,
            'PPG': pts / len(df),
            'Win%': w / len(df) * 100
        }
    
    # Group by day of week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_stats = []
    
    for day in days_order:
        day_matches = team_raw[team_raw['day_of_week'] == day]
        if len(day_matches) > 0:
            stats = calc_day_stats(day_matches)
            stats['Day'] = day
            day_stats.append(stats)
    
    if day_stats:
        day_df = pd.DataFrame(day_stats)
        
        # Bar chart - PPG by day
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=day_df['Day'],
            y=day_df['PPG'],
            marker_color=[CHART_COLORS['primary'] if d in ['Saturday', 'Sunday'] else CHART_COLORS['accent'] for d in day_df['Day']],
            text=day_df['P'].apply(lambda x: f"{x} games"),
            textposition='outside'
        ))
        
        max_ppg = day_df['PPG'].max()
        fig.update_layout(
            height=300,
            template="plotly_dark",
            yaxis_title="Points Per Game",
            xaxis_title="Day of Week",
            yaxis=dict(range=[0, max_ppg * 1.25])  # Add headroom for labels
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Summary table
        display_day = day_df[['Day', 'P', 'W', 'D', 'L', 'PPG', 'Win%']].copy()
        display_day.columns = ['Day', 'Played', 'W', 'D', 'L', 'PPG', 'Win %']
        
        st.dataframe(
            display_day,
            hide_index=True,
            width='stretch',
            column_config={
                'PPG': st.column_config.NumberColumn(format="%.2f"),
                'Win %': st.column_config.NumberColumn(format="%.0f%%"),
            }
        )
        
        # Weekend vs Midweek summary
        weekend = team_raw[team_raw['day_of_week'].isin(['Saturday', 'Sunday'])]
        midweek = team_raw[~team_raw['day_of_week'].isin(['Saturday', 'Sunday'])]
        
        weekend_stats = calc_day_stats(weekend)
        midweek_stats = calc_day_stats(midweek)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Weekend (Sat/Sun)**")
            st.caption(f"{weekend_stats['P']} matches, {weekend_stats['PPG']:.2f} PPG, {weekend_stats['Win%']:.0f}% win rate")
        with col2:
            st.markdown("**Midweek (Mon-Fri)**")
            st.caption(f"{midweek_stats['P']} matches, {midweek_stats['PPG']:.2f} PPG, {midweek_stats['Win%']:.0f}% win rate")
else:
    st.info("No match data for selected seasons")

st.divider()

# ============================================================
# Opponent Strength
# ============================================================
st.subheader("Performance by Opponent Strength")

if len(filtered_team_history) > 0:
    # Get current ELO ratings for opponents
    opp_elo = elo_df.set_index('team')['elo_rating'].to_dict()
    
    opp_df = filtered_team_history.copy()
    opp_df['opp_elo'] = opp_df['opponent'].map(opp_elo)
    opp_df = opp_df.dropna(subset=['opp_elo'])
    
    if len(opp_df) > 0:
        # Categorize opponents by ELO
        elo_median = opp_df['opp_elo'].median()
        elo_75 = opp_df['opp_elo'].quantile(0.75)
        elo_25 = opp_df['opp_elo'].quantile(0.25)
        
        def categorize_opponent(elo):
            if elo >= elo_75:
                return 'Strong'
            elif elo <= elo_25:
                return 'Weak'
            else:
                return 'Average'
        
        opp_df['opp_category'] = opp_df['opp_elo'].apply(categorize_opponent)
        opp_df['points'] = opp_df['team_result'].map({'W': 3, 'D': 1, 'L': 0})
        
        # Stats by category
        def calc_opp_stats(df):
            if len(df) == 0:
                return {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'PPG': 0, 'Win%': 0, 'GF': 0, 'GA': 0}
            w = (df['team_result'] == 'W').sum()
            d = (df['team_result'] == 'D').sum()
            l = (df['team_result'] == 'L').sum()
            pts = w * 3 + d
            return {
                'P': len(df), 'W': w, 'D': d, 'L': l,
                'PPG': pts / len(df),
                'Win%': w / len(df) * 100,
                'GF': df['goals_for'].sum(),
                'GA': df['goals_against'].sum()
            }
        
        strong = calc_opp_stats(opp_df[opp_df['opp_category'] == 'Strong'])
        average = calc_opp_stats(opp_df[opp_df['opp_category'] == 'Average'])
        weak = calc_opp_stats(opp_df[opp_df['opp_category'] == 'Weak'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**vs Strong** (ELO ≥ {elo_75:.0f})")
            st.caption(f"{strong['P']} matches, {strong['W']}-{strong['D']}-{strong['L']}")
            st.metric("PPG", f"{strong['PPG']:.2f}")
        
        with col2:
            st.markdown(f"**vs Average** (ELO {elo_25:.0f}-{elo_75:.0f})")
            st.caption(f"{average['P']} matches, {average['W']}-{average['D']}-{average['L']}")
            st.metric("PPG", f"{average['PPG']:.2f}")
        
        with col3:
            st.markdown(f"**vs Weak** (ELO ≤ {elo_25:.0f})")
            st.caption(f"{weak['P']} matches, {weak['W']}-{weak['D']}-{weak['L']}")
            st.metric("PPG", f"{weak['PPG']:.2f}")
        
        # Bar chart
        fig = go.Figure()
        
        categories = ['vs Strong', 'vs Average', 'vs Weak']
        ppg_vals = [strong['PPG'], average['PPG'], weak['PPG']]
        colors = ['#d62728', '#7f7f7f', '#2ca02c']
        
        fig.add_trace(go.Bar(
            x=categories,
            y=ppg_vals,
            marker_color=colors,
            text=[f"{v:.2f}" for v in ppg_vals],
            textposition='outside'
        ))
        
        fig.update_layout(
            height=280,
            template="plotly_dark",
            yaxis_title="Points Per Game",
            yaxis=dict(range=[0, max(ppg_vals) * 1.25 if ppg_vals else 3])
        )
        
        st.plotly_chart(fig, width='stretch')
else:
    st.info("No match history for selected seasons")

st.divider()

# ============================================================
# Rest Days Analysis
# ============================================================
st.subheader("Rest Days Analysis")

if len(team_raw) > 0 and 'ft_result' in team_raw.columns:
    rest_df = team_raw.sort_values('date').copy()
    rest_df['date'] = pd.to_datetime(rest_df['date'])
    rest_df['days_rest'] = rest_df['date'].diff().dt.days
    rest_df = rest_df.dropna(subset=['days_rest'])
    
    if len(rest_df) > 0:
        # Categorize rest days
        def categorize_rest(days):
            if days <= 3:
                return 'Short (≤3 days)'
            elif days <= 7:
                return 'Normal (4-7 days)'
            else:
                return 'Long (8+ days)'
        
        rest_df['rest_category'] = rest_df['days_rest'].apply(categorize_rest)
        
        # Stats by category
        def calc_rest_stats(df):
            if len(df) == 0:
                return {'P': 0, 'PPG': 0, 'Win%': 0}
            w = (df['ft_result'] == 'W').sum()
            d = (df['ft_result'] == 'D').sum()
            pts = w * 3 + d
            return {
                'P': len(df),
                'PPG': pts / len(df),
                'Win%': w / len(df) * 100
            }
        
        short = calc_rest_stats(rest_df[rest_df['rest_category'] == 'Short (≤3 days)'])
        normal = calc_rest_stats(rest_df[rest_df['rest_category'] == 'Normal (4-7 days)'])
        long_rest = calc_rest_stats(rest_df[rest_df['rest_category'] == 'Long (8+ days)'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Short Rest (≤3 days)**")
            st.caption(f"{short['P']} matches")
            st.metric("PPG", f"{short['PPG']:.2f}")
        
        with col2:
            st.markdown("**Normal Rest (4-7 days)**")
            st.caption(f"{normal['P']} matches")
            st.metric("PPG", f"{normal['PPG']:.2f}")
        
        with col3:
            st.markdown("**Long Rest (8+ days)**")
            st.caption(f"{long_rest['P']} matches")
            st.metric("PPG", f"{long_rest['PPG']:.2f}")
        
        # Bar chart
        fig = go.Figure()
        
        categories = ['Short (≤3)', 'Normal (4-7)', 'Long (8+)']
        ppg_vals = [short['PPG'], normal['PPG'], long_rest['PPG']]
        match_counts = [short['P'], normal['P'], long_rest['P']]
        
        fig.add_trace(go.Bar(
            x=categories,
            y=ppg_vals,
            marker_color=[CHART_COLORS['negative'], CHART_COLORS['primary'], CHART_COLORS['positive']],
            text=[f"{p} games" for p in match_counts],
            textposition='outside'
        ))
        
        max_ppg = max(ppg_vals) if ppg_vals and max(ppg_vals) > 0 else 3
        fig.update_layout(
            height=280,
            template="plotly_dark",
            yaxis_title="Points Per Game",
            xaxis_title="Days Since Last Match",
            yaxis=dict(range=[0, max_ppg * 1.3])
        )
        
        st.plotly_chart(fig, width='stretch')
else:
    st.info("No match data for selected seasons")

st.divider()

# ============================================================
# Shots Analysis
# ============================================================
st.subheader("Shots Analysis")

if len(team_raw) > 0:
    shots_df = team_raw.copy()
    
    # Calculate shots for/against based on home/away
    def get_shots(row):
        is_home = row['home_team'] == selected_team
        if is_home:
            return pd.Series({
                'shots_for': row.get('hs', 0) or 0,
                'shots_against': row.get('as_col', 0) or 0,
                'sot_for': row.get('hst', 0) or 0,
                'sot_against': row.get('ast', 0) or 0,
                'goals_for': row.get('fthg', 0) or 0,
                'goals_against': row.get('ftag', 0) or 0
            })
        else:
            return pd.Series({
                'shots_for': row.get('as_col', 0) or 0,
                'shots_against': row.get('hs', 0) or 0,
                'sot_for': row.get('ast', 0) or 0,
                'sot_against': row.get('hst', 0) or 0,
                'goals_for': row.get('ftag', 0) or 0,
                'goals_against': row.get('fthg', 0) or 0
            })
    
    shot_stats = shots_df.apply(get_shots, axis=1)
    shots_df = pd.concat([shots_df, shot_stats], axis=1)
    
    # Filter out rows with missing shot data
    shots_df = shots_df[shots_df['shots_for'] > 0]
    
    if len(shots_df) > 0:
        # Aggregate stats
        total_shots = shots_df['shots_for'].sum()
        total_sot = shots_df['sot_for'].sum()
        total_goals = shots_df['goals_for'].sum()
        total_shots_against = shots_df['shots_against'].sum()
        total_sot_against = shots_df['sot_against'].sum()
        matches = len(shots_df)
        
        # Per game averages
        shots_pg = total_shots / matches
        sot_pg = total_sot / matches
        goals_pg = total_goals / matches
        shots_against_pg = total_shots_against / matches
        
        # Conversion rates
        sot_pct = (total_sot / total_shots * 100) if total_shots > 0 else 0
        conversion = (total_goals / total_shots * 100) if total_shots > 0 else 0
        sot_conversion = (total_goals / total_sot * 100) if total_sot > 0 else 0
        
        # Get xG data for the same period
        total_xg = filtered_team_xg['xg_for'].sum() if len(filtered_team_xg) > 0 else 0
        total_xga = filtered_team_xg['xg_against'].sum() if len(filtered_team_xg) > 0 else 0
        
        # xG per shot metrics
        xg_per_shot = (total_xg / total_shots) if total_shots > 0 else 0
        xg_per_sot = (total_xg / total_sot) if total_sot > 0 else 0
        xga_per_shot = (total_xga / total_shots_against) if total_shots_against > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Attacking**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Shots/Game", f"{shots_pg:.1f}")
            m2.metric("On Target/Game", f"{sot_pg:.1f}")
            m3.metric("Goals/Game", f"{goals_pg:.2f}")
            
            m4, m5, m6 = st.columns(3)
            m4.metric("Accuracy", f"{sot_pct:.0f}%")
            m5.metric("Conversion", f"{conversion:.1f}%")
            m6.metric("SOT Conversion", f"{sot_conversion:.0f}%")
            
            if total_xg > 0:
                m7, m8, m9 = st.columns(3)
                m7.metric("xG/Shot", f"{xg_per_shot:.2f}")
                m8.metric("xG/SOT", f"{xg_per_sot:.2f}")
                m9.metric("Total xG", f"{total_xg:.1f}")
        
        with col2:
            st.markdown("**Defensive**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Shots Against/Game", f"{shots_against_pg:.1f}")
            m2.metric("SOT Against/Game", f"{total_sot_against/matches:.1f}")
            m3.metric("GA/Game", f"{shots_df['goals_against'].sum()/matches:.2f}")
            
            if total_xga > 0:
                m4, m5, m6 = st.columns(3)
                m4.metric("xGA/Shot Against", f"{xga_per_shot:.2f}")
                m5.metric("Total xGA", f"{total_xga:.1f}")
                m6.metric("", "")
        
        # Comparison bar chart
        fig = go.Figure()
        
        metrics = ['Shots/Game', 'On Target/Game', 'Goals/Game']
        for_vals = [shots_pg, sot_pg, goals_pg]
        against_vals = [shots_against_pg, total_sot_against/matches, shots_df['goals_against'].sum()/matches]
        
        fig.add_trace(go.Bar(name='For', x=metrics, y=for_vals, marker_color=CHART_COLORS['positive']))
        fig.add_trace(go.Bar(name='Against', x=metrics, y=against_vals, marker_color=CHART_COLORS['negative']))
        
        fig.update_layout(
            barmode='group',
            height=280,
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width='stretch')
        st.caption(f"Based on {matches} matches with shot data")
    else:
        st.info("No shot data available")
else:
    st.info("No match data for selected seasons")

st.divider()

# ============================================================
# Day vs Night Performance
# ============================================================
st.subheader("Day vs Night Performance")

if len(team_raw) > 0:
    time_df = team_raw.copy()
    time_df = time_df.dropna(subset=['time'])
    time_df = time_df[time_df['time'] != '']
    
    if len(time_df) > 0:
        # Parse time and categorize
        def categorize_time(time_str):
            try:
                hour = int(str(time_str).split(':')[0])
                if hour < 18:
                    return 'Day (before 18:00)'
                else:
                    return 'Night (18:00+)'
            except:
                return None
        
        time_df['time_category'] = time_df['time'].apply(categorize_time)
        time_df = time_df.dropna(subset=['time_category'])
        
        if len(time_df) > 0 and 'ft_result' in time_df.columns:
            # Stats by time
            def calc_time_stats(df):
                if len(df) == 0:
                    return {'P': 0, 'W': 0, 'D': 0, 'L': 0, 'PPG': 0, 'Win%': 0}
                w = (df['ft_result'] == 'W').sum()
                d = (df['ft_result'] == 'D').sum()
                l = (df['ft_result'] == 'L').sum()
                pts = w * 3 + d
                return {
                    'P': len(df), 'W': w, 'D': d, 'L': l,
                    'PPG': pts / len(df),
                    'Win%': w / len(df) * 100
                }
            
            day = calc_time_stats(time_df[time_df['time_category'] == 'Day (before 18:00)'])
            night = calc_time_stats(time_df[time_df['time_category'] == 'Night (18:00+)'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Day (before 18:00)**")
                st.caption(f"{day['P']} matches, {day['W']}-{day['D']}-{day['L']}")
                st.metric("PPG", f"{day['PPG']:.2f}")
                st.metric("Win %", f"{day['Win%']:.0f}%")
            
            with col2:
                st.markdown("**Night (18:00+)**")
                st.caption(f"{night['P']} matches, {night['W']}-{night['D']}-{night['L']}")
                st.metric("PPG", f"{night['PPG']:.2f}")
                st.metric("Win %", f"{night['Win%']:.0f}%")
            
            # Bar chart
            fig = go.Figure()
            
            categories = ['Day', 'Night']
            ppg_vals = [day['PPG'], night['PPG']]
            match_counts = [day['P'], night['P']]
            
            fig.add_trace(go.Bar(
                x=categories,
                y=ppg_vals,
                marker_color=[CHART_COLORS['accent'], CHART_COLORS['primary']],
                text=[f"{p} games" for p in match_counts],
                textposition='outside'
            ))
            
            max_ppg = max(ppg_vals) if ppg_vals and max(ppg_vals) > 0 else 3
            fig.update_layout(
                height=280,
                template="plotly_dark",
                yaxis_title="Points Per Game",
                yaxis=dict(range=[0, max_ppg * 1.3])
            )
            
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No time data with results available")
    else:
        st.info("No kickoff time data available")
else:
    st.info("No match data for selected seasons")

st.divider()
st.caption("Data: football-data.co.uk, Understat")
