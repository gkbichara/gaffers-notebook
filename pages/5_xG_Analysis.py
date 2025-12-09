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
    leagues = ["All Leagues"] + sorted(xg_df['league_display'].dropna().unique().tolist())
    selected_league = st.selectbox(
        "League",
        options=leagues,
        index=0,  # "All Leagues" is default
        key="xg_league"
    )

# Apply season gap filling
if selected_seasons_display:
    selected_seasons_display = fill_season_gaps(selected_seasons_display, available_seasons_display)

# Convert display names back to codes
selected_seasons = [SEASON_CODES.get(s, s) for s in selected_seasons_display]

# Filter data by seasons (and optionally league)
if selected_league == "All Leagues":
    filtered_df = xg_df[xg_df['season'].isin(selected_seasons)]
    # Create team options with league in parentheses
    team_league_map = filtered_df.groupby('team')['league_display'].first().to_dict()
    available_teams_raw = sorted(filtered_df['team'].unique().tolist())
    available_teams = [f"{team} ({team_league_map[team]})" for team in available_teams_raw]
    team_name_map = {f"{team} ({team_league_map[team]})": team for team in available_teams_raw}
else:
    filtered_df = xg_df[
        (xg_df['league_display'] == selected_league) &
        (xg_df['season'].isin(selected_seasons))
    ]
    available_teams = sorted(filtered_df['team'].unique().tolist())
    team_name_map = {team: team for team in available_teams}

# Find Roma as default (or first team if Roma not available)
default_team = None
for team_option in available_teams:
    if 'Roma' in team_option:
        default_team = team_option
        break
if default_team is None and available_teams:
    default_team = available_teams[0]

with col3:
    selected_teams_display = st.multiselect(
        "Team(s) - max 2",
        options=available_teams,
        default=[default_team] if default_team else [],
        max_selections=2,
        key="xg_teams"
    )

if not selected_teams_display:
    st.info("Select at least one team to view xG analysis.")
    st.stop()

# Convert display names back to actual team names
selected_teams = [team_name_map.get(t, t) for t in selected_teams_display]

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
        attack_status = "Clinical"
        attack_color = "green"
    elif goals_diff < -1:
        attack_status = "Wasteful"
        attack_color = "red"
    else:
        attack_status = "Expected"
        attack_color = "gray"
    
    if ga_diff < -1:
        defense_status = "Solid"
        defense_color = "green"
    elif ga_diff > 1:
        defense_status = "Vulnerable"
        defense_color = "red"
    else:
        defense_status = "Expected"
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


def add_dynamic_fill(fig, x_vals, y_actual, y_expected, green_when_above=True):
    """
    Add dynamic fill that changes color based on whether actual > expected.
    
    Args:
        fig: Plotly figure
        x_vals: X axis values (match numbers)
        y_actual: Actual values (goals or goals against)
        y_expected: Expected values (xG or xGA)
        green_when_above: If True, green when actual > expected (for goals)
                         If False, green when actual < expected (for goals against)
    """
    x_list = list(x_vals)
    actual_list = list(y_actual)
    expected_list = list(y_expected)
    
    # Find segments where the relationship changes
    segments = []
    current_segment = {'x': [], 'actual': [], 'expected': [], 'is_green': None}
    
    for i in range(len(x_list)):
        diff = actual_list[i] - expected_list[i]
        is_green = (diff > 0) if green_when_above else (diff < 0)
        
        if current_segment['is_green'] is None:
            current_segment['is_green'] = is_green
        
        if is_green == current_segment['is_green']:
            current_segment['x'].append(x_list[i])
            current_segment['actual'].append(actual_list[i])
            current_segment['expected'].append(expected_list[i])
        else:
            # Interpolate crossover point
            if len(current_segment['x']) > 0:
                # Find approximate crossover x
                prev_diff = current_segment['actual'][-1] - current_segment['expected'][-1]
                curr_diff = diff
                # Linear interpolation for crossover
                t = abs(prev_diff) / (abs(prev_diff) + abs(curr_diff)) if (abs(prev_diff) + abs(curr_diff)) > 0 else 0.5
                cross_x = current_segment['x'][-1] + t * (x_list[i] - current_segment['x'][-1])
                cross_y = current_segment['actual'][-1] + t * (actual_list[i] - current_segment['actual'][-1])
                
                current_segment['x'].append(cross_x)
                current_segment['actual'].append(cross_y)
                current_segment['expected'].append(cross_y)
                segments.append(current_segment)
                
                # Start new segment from crossover
                current_segment = {
                    'x': [cross_x, x_list[i]],
                    'actual': [cross_y, actual_list[i]],
                    'expected': [cross_y, expected_list[i]],
                    'is_green': is_green
                }
            else:
                current_segment = {
                    'x': [x_list[i]],
                    'actual': [actual_list[i]],
                    'expected': [expected_list[i]],
                    'is_green': is_green
                }
    
    # Add final segment
    if len(current_segment['x']) > 0:
        segments.append(current_segment)
    
    # Create fill traces for each segment
    added_green = False
    added_red = False
    
    for seg in segments:
        if len(seg['x']) < 2:
            continue
            
        color = 'rgba(0, 200, 83, 0.3)' if seg['is_green'] else 'rgba(255, 82, 82, 0.3)'
        
        # Show legend only once per color
        if seg['is_green'] and not added_green:
            name = 'Overperforming' if green_when_above else 'Solid Defense'
            show_legend = True
            added_green = True
        elif not seg['is_green'] and not added_red:
            name = 'Underperforming' if green_when_above else 'Vulnerable Defense'
            show_legend = True
            added_red = True
        else:
            name = ''
            show_legend = False
        
        fig.add_trace(go.Scatter(
            x=seg['x'] + seg['x'][::-1],
            y=seg['actual'] + seg['expected'][::-1],
            fill='toself',
            fillcolor=color,
            line=dict(color='rgba(255,255,255,0)'),
            name=name,
            showlegend=show_legend,
            hoverinfo='skip'
        ))


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
    
    # Add dynamic fill (green when goals > xG)
    add_dynamic_fill(
        fig,
        team_data['range_match'],
        team_data['cum_goals'],
        team_data['cum_xg'],
        green_when_above=True
    )
    
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
    
    fig.update_layout(
        title=f"{team}: Cumulative Goals vs xG",
        xaxis_title="Match",
        yaxis_title="Cumulative Goals",
        height=400,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width='stretch')

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
    
    # Add dynamic fill (green when GA < xGA, i.e., conceding less than expected)
    add_dynamic_fill(
        fig,
        team_data['range_match'],
        team_data['cum_ga'],
        team_data['cum_xga'],
        green_when_above=False  # Green when actual < expected (good defense)
    )
    
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
    
    fig.update_layout(
        title=f"{team}: Cumulative Goals Against vs xGA",
        xaxis_title="Match",
        yaxis_title="Cumulative Goals Against",
        height=400,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width='stretch')

st.divider()

# --- xG YoY Comparison (Expandable) ---
with st.expander("📊 xG Year-over-Year Comparison", expanded=False):
    st.markdown("Compare xG performance against the same fixtures from last season.")
    
    # Get the previous season for comparison
    if len(selected_seasons) > 0:
        current_season = selected_seasons[-1]  # Most recent selected
        season_idx = SEASONS.index(current_season) if current_season in SEASONS else -1
        
        if season_idx > 0:
            prev_season = SEASONS[season_idx - 1]
            prev_season_display = SEASON_DISPLAY_NAMES.get(prev_season, prev_season)
            current_season_display = SEASON_DISPLAY_NAMES.get(current_season, current_season)
            
            for team in selected_teams:
                st.markdown(f"**{team}**: {prev_season_display} → {current_season_display}")
                
                # Get current and previous season data for this team
                current_data = xg_df[(xg_df['team'] == team) & (xg_df['season'] == current_season)].copy()
                prev_data = xg_df[(xg_df['team'] == team) & (xg_df['season'] == prev_season)].copy()
                
                if len(current_data) == 0 or len(prev_data) == 0:
                    st.info(f"Insufficient data for YoY comparison (need both {prev_season_display} and {current_season_display})")
                    continue
                
                # Create lookup for previous season by opponent + venue
                prev_lookup = prev_data.set_index(['opponent', 'venue'])[['xg_for', 'xg_against']].to_dict('index')
                
                # Build comparison dataframe
                comparison_rows = []
                cumulative_xg_diff = 0
                cumulative_xga_diff = 0
                
                for _, row in current_data.iterrows():
                    key = (row['opponent'], row['venue'])
                    if key in prev_lookup:
                        prev_xg = prev_lookup[key]['xg_for']
                        prev_xga = prev_lookup[key]['xg_against']
                        xg_diff = row['xg_for'] - prev_xg
                        xga_diff = row['xg_against'] - prev_xga
                        cumulative_xg_diff += xg_diff
                        cumulative_xga_diff += xga_diff
                        
                        comparison_rows.append({
                            'Match': row['match_number'],
                            'Opponent': row['opponent'],
                            'Venue': row['venue'].upper(),
                            f'xG ({current_season_display[:4]})': row['xg_for'],
                            f'xG ({prev_season_display[:4]})': prev_xg,
                            'xG Diff': xg_diff,
                            'Cum xG Diff': cumulative_xg_diff,
                            f'xGA ({current_season_display[:4]})': row['xg_against'],
                            f'xGA ({prev_season_display[:4]})': prev_xga,
                            'xGA Diff': xga_diff,
                            'Cum xGA Diff': cumulative_xga_diff,
                        })
                
                if comparison_rows:
                    comp_df = pd.DataFrame(comparison_rows)
                    
                    # Style function for differential columns
                    def color_diff(val):
                        if pd.isna(val):
                            return ''
                        if val > 0.1:
                            return 'color: green; font-weight: bold'
                        elif val < -0.1:
                            return 'color: red; font-weight: bold'
                        return ''
                    
                    def color_xga_diff(val):
                        """For xGA, lower is better"""
                        if pd.isna(val):
                            return ''
                        if val < -0.1:
                            return 'color: green; font-weight: bold'
                        elif val > 0.1:
                            return 'color: red; font-weight: bold'
                        return ''
                    
                    styled_df = comp_df.style.map(
                        color_diff, subset=['xG Diff', 'Cum xG Diff']
                    ).map(
                        color_xga_diff, subset=['xGA Diff', 'Cum xGA Diff']
                    ).format({
                        'xG Diff': lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}",
                        'Cum xG Diff': lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}",
                        'xGA Diff': lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}",
                        'Cum xGA Diff': lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}",
                        f'xG ({current_season_display[:4]})': '{:.2f}',
                        f'xG ({prev_season_display[:4]})': '{:.2f}',
                        f'xGA ({current_season_display[:4]})': '{:.2f}',
                        f'xGA ({prev_season_display[:4]})': '{:.2f}',
                    })
                    
                    st.dataframe(styled_df, hide_index=True, width='stretch')
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    final_xg_diff = cumulative_xg_diff
                    final_xga_diff = cumulative_xga_diff
                    
                    col1.metric(
                        "Total xG Change", 
                        f"{final_xg_diff:+.2f}",
                        "Attacking Improvement" if final_xg_diff > 0 else "Attacking Decline"
                    )
                    col2.metric(
                        "Matches Compared",
                        len(comparison_rows)
                    )
                    col3.metric(
                        "Total xGA Change",
                        f"{final_xga_diff:+.2f}",
                        "Defensive Improvement" if final_xga_diff < 0 else "Defensive Decline"
                    )
                    col4.metric(
                        "Net xG Change",
                        f"{(final_xg_diff - final_xga_diff):+.2f}",
                        "Overall Better" if (final_xg_diff - final_xga_diff) > 0 else "Overall Worse"
                    )
                else:
                    st.info("No matching fixtures found between seasons")
                
                st.markdown("---")
        else:
            st.info("Select a season with a previous season available for YoY comparison")
    else:
        st.info("Select at least one season for YoY comparison")

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
        width='stretch',
        column_config={
            'G-xG': st.column_config.NumberColumn(format="%.2f"),
            'GA-xGA': st.column_config.NumberColumn(format="%.2f"),
            'xG': st.column_config.NumberColumn(format="%.2f"),
            'xGA': st.column_config.NumberColumn(format="%.2f"),
            'npxG': st.column_config.NumberColumn(format="%.2f"),
            'npxGA': st.column_config.NumberColumn(format="%.2f"),
        }
    )
