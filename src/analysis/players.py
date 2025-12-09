import os
import pandas as pd
from src.config import DATA_DIR, LEAGUES

def calculate_contribution_stats(player, team_total_goals, team_total_xg=0):
    """
    Calculate contribution percentages and xG stats for a single player.
    
    Args:
        player: Dict containing raw player stats (goals, assists, xG, xA, etc.)
        team_total_goals: Integer of total goals scored by the team
        team_total_xg: Float of total xG for the team
        
    Returns:
        Dict with calculated contribution metrics and xG stats
    """
    goals = int(player['goals'])
    assists = int(player['assists'])
    total_contribs = goals + assists
    
    # xG stats from Understat
    xg = float(player.get('xG', 0))
    xa = float(player.get('xA', 0))
    npxg = float(player.get('npxG', 0))
    shots = int(player.get('shots', 0))
    minutes = int(player.get('time', 0))
    
    # Calculated metrics
    goals_minus_xg = round(goals - xg, 2)
    
    # Avoid division by zero
    if team_total_goals > 0:
        contribution_pct = (total_contribs / team_total_goals * 100)
        goals_pct = (goals / team_total_goals * 100)
        assists_pct = (assists / team_total_goals * 100)
    else:
        contribution_pct = 0
        goals_pct = 0
        assists_pct = 0
    
    # xG percentage of team total
    xg_pct = (xg / team_total_xg * 100) if team_total_xg > 0 else 0
        
    return {
        'player': player['player_name'],
        'team': player['team_title'],
        'goals': goals,
        'assists': assists,
        'contributions': total_contribs,
        'contribution_pct': round(contribution_pct, 1),
        'goals_pct': round(goals_pct, 1),
        'assists_pct': round(assists_pct, 1),
        'games': int(player['games']),
        # xG fields
        'xg': round(xg, 2),
        'xa': round(xa, 2),
        'npxg': round(npxg, 2),
        'xg_pct': round(xg_pct, 1),
        'shots': shots,
        'minutes': minutes,
        'goals_minus_xg': goals_minus_xg,
    }


def process_league_players(all_players_raw, team_totals_dict, season_code):
    """
    Process raw player list into analyzed contribution stats.
    
    Args:
        all_players_raw: List of dicts from Understat scraper
        team_totals_dict: Dict mapping team names to {'goals': X, 'xG': Y}
        season_code: String season identifier (e.g., '2324')
        
    Returns:
        List of dicts sorted by contribution percentage
    """
    processed_stats = []
    
    for player in all_players_raw:
        player_team = player['team_title']
        
        # Skip multi-team players (business rule)
        if ',' in player_team:
            continue
        
        # Get team totals (goals and xG)
        team_data = team_totals_dict.get(player_team, {'goals': 0, 'xG': 0})
        team_total_goals = team_data['goals']
        team_total_xg = team_data['xG']
        
        stats = calculate_contribution_stats(player, team_total_goals, team_total_xg)
        stats['season'] = season_code
        
        processed_stats.append(stats)
        
    # Sort by contribution percentage descending
    processed_stats.sort(key=lambda x: x['contribution_pct'], reverse=True)
    
    return processed_stats


def save_player_results(contributions, league_key, season_code):
    """
    Save player contributions to CSV.
    
    Args:
        contributions: List of player contribution dicts
        league_key: League key from config (e.g., 'serie_a')
        season_code: Season identifier
    """
    # Create file path using league folder
    folder = LEAGUES[league_key]['folder']
    league_folder = os.path.join(DATA_DIR, folder)
    file_path = os.path.join(league_folder, f'player_results_{season_code}.csv')
    
    # Ensure directory exists
    os.makedirs(league_folder, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(contributions)
    
    # Save to CSV
    df.to_csv(file_path, index=False)
    
    print(f"   ✓ Saved player results to {file_path}")
