import requests
import json
import re
import unicodedata
import html
import os
import pandas as pd

# Base URL for understat.com
BASE_URL = "https://understat.com/league/"

# Leagues to scrape
LEAGUES = {
    'serieA': 'Serie_A',
    'PremierLeague': 'EPL',
    'LaLiga': 'La_Liga',
    'Bundesliga': 'Bundesliga',
    'ligue1': 'Ligue_1'
}

def normalize_name(name):
    """Remove accents and convert to lowercase for matching"""
    # Remove accents: Matías -> Matias, Soulé -> Soule
    nfd = unicodedata.normalize('NFD', name)
    without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return without_accents.lower().strip()

def get_league_players(league_name):
    """Get all players from a league"""
    url = BASE_URL + LEAGUES[league_name]
    
    print(f"Fetching {league_name} data...")
    response = requests.get(url)
    
    # Find the JavaScript variable with player data
    match = re.search(r"var playersData\s*=\s*JSON\.parse\('(.+?)'\)", response.text)
    
    if not match:
        print("Could not find player data!")
        return []
    
    # Decode hex-encoded string and parse JSON
    encoded = match.group(1)
    decoded = encoded.encode('utf-8').decode('unicode_escape')
    players = json.loads(decoded)
    
    # Decode HTML entities in player names (e.g., &#039; -> ')
    for player in players:
        player['player_name'] = html.unescape(player['player_name'])
    
    print(f"Found {len(players)} players")
    return players


def get_team_data(league_name):
    """Get team-level data (total goals, etc.) from Understat"""
    url = BASE_URL + LEAGUES[league_name]
    response = requests.get(url)

        # Find the JavaScript variable with player data
    match = re.search(r"var teamsData\s*=\s*JSON\.parse\('(.+?)'\)", response.text)

    # Decode hex-encoded string and parse JSON
    encoded = match.group(1)
    decoded = encoded.encode('utf-8').decode('unicode_escape')
    teams = json.loads(decoded)
    
    # Decode HTML entities in team names
    for team_id, team_data in teams.items():
        if 'title' in team_data:
            team_data['title'] = html.unescape(team_data['title'])
    
    print(f"Found {len(teams)} teams")
    return teams


def get_team_totals(league_name):
    """Calculate total goals scored by each team from match history
    
    Returns:
        dict: {'Team Name': total_goals_scored, ...}
    """
    teams_data = get_team_data(league_name)
    
    team_totals = {}
    for team_id, team_info in teams_data.items():
        team_name = team_info['title']
        
        # Sum up goals scored across all matches in history
        total_goals = sum(match['scored'] for match in team_info['history'])
        team_totals[team_name] = total_goals
        
    
    return team_totals


def calculate_contributions(league_name):
    """Calculate contributions for all players in a league"""
    contributions = []  # Keep this name for the list
    all_players = get_league_players(league_name)
    team_goals = get_team_totals(league_name)  # This is a dict
    
    for player in all_players:
        player_team = player['team_title']
        
        # Skip multi-team players
        if ',' in player_team:
            continue
        
        # Get this team's total (keep dict intact)
        team_total = team_goals.get(player_team, 0)
        
        # Player stats
        goals = int(player['goals'])
        assists = int(player['assists'])
        total_contribs = goals + assists  # Different name!
        
        # Calculate percentages using team_total
        contribution_pct = (total_contribs / team_total * 100) if team_total > 0 else 0
        goals_pct = (goals / team_total * 100) if team_total > 0 else 0
        assists_pct = (assists / team_total * 100) if team_total > 0 else 0
        
        contributions.append({
            'player': player['player_name'],  # Fix: was p
            'team': player_team,
            'goals': goals,
            'assists': assists,
            'contributions': total_contribs,  # Fix: use the variable
            'contribution_pct': round(contribution_pct, 1),  # 1 decimal
            'goals_pct': round(goals_pct, 1),
            'assists_pct': round(assists_pct, 1),
            'games': int(player['games'])  # Fix: was p
        })
    
    contributions.sort(key=lambda x: x['contribution_pct'], reverse=True)
    return contributions


def print_table(contributions, top_n=20):
    """Print formatted table of top contributors"""
    
    # Slice to top N
    top_players = contributions[:top_n]
    
    # Print header
    print("\n" + "="*100)
    print(f"TOP {top_n} CONTRIBUTORS - SERIE A (2025-26)")
    print("="*100)
    print(f"{'Rank':<6} {'Player':<25} {'Team':<18} {'G':<5} {'A':<5} {'Total':<7} {'G%':<8} {'A%':<8} {'Cont%':<8}")
    print("-"*100)
    
    # Print data rows
    for i, p in enumerate(top_players, 1):
        print(f"{i:<6} {p['player']:<25} {p['team']:<18} {p['goals']:<5} {p['assists']:<5} {p['contributions']:<7} {p['goals_pct']:<8.1f} {p['assists_pct']:<8.1f} {p['contribution_pct']:<8.1f}")
    
    print("="*100)

def save_player_results(contributions, league_name):
    """Save player contributions to CSV
    
    Args:
        contributions: List of player contribution dicts
        league_name: League key (e.g., 'serieA', 'PremierLeague')
    """
    # Create file path using league_name as folder
    league_folder = f'data/{league_name}'
    file_path = f'{league_folder}/player_results.csv'
    
    # Ensure directory exists (shouldn't be needed, but safe)
    os.makedirs(league_folder, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(contributions)
    
    # Save to CSV
    df.to_csv(file_path, index=False)
    
    print(f"   ✓ Saved player results to {file_path}")


# Test
def main():
    for league_name in LEAGUES:
        players_contributions = calculate_contributions(league_name)    
        print_table(players_contributions, top_n=20)
        save_player_results(players_contributions, league_name)

        
if __name__ == "__main__":
    main()