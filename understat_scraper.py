import requests
import json
import re
import unicodedata
import html

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

def get_player_contribution(league_name, player_name, team_name=None):
    """Calculate player's contribution to team goals
    
    Args:
        league_name: League key from LEAGUES dict
        player_name: Player name (accent-insensitive, e.g., 'Soule' matches 'Soulé')
        team_name: Optional team name for filtering
    """
    # Get all players
    all_players = get_league_players(league_name)
    
    # Normalize search name
    search_name = normalize_name(player_name)
    
    # Find our player (flexible matching)
    player = None
    for p in all_players:
        name_match = normalize_name(p['player_name']) == search_name
        team_match = team_name is None or p['team_title'] == team_name
        
        if name_match and team_match:
            player = p
            break
    
    if not player:
        print(f"Player not found: {player_name}")
        if team_name:
            print(f"  (searching in team: {team_name})")
        return None
    
    # Calculate team total goals (use player's actual team)
    player_team = player['team_title']
    team_goals = sum(int(p['goals']) for p in all_players if p['team_title'] == player_team)
    
    # Player stats
    goals = int(player['goals'])
    assists = int(player['assists'])
    contributions = goals + assists
    contribution_pct = (contributions / team_goals * 100) if team_goals > 0 else 0
    
    return {
        'player': player['player_name'],  # Use actual name from data
        'team': player_team,
        'goals': goals,
        'assists': assists,
        'contributions': contributions,
        'team_total': team_goals,
        'contribution_pct': round(contribution_pct, 2)
    }

def get_all_player_contributions(league_name, team_name=None):
    """Get contribution stats for all players in a league or team
    
    Args:
        league_name: League key from LEAGUES dict
        team_name: Optional team name to filter by
    
    Returns:
        List of player contribution dictionaries, sorted by contribution %
    """
    all_players = get_league_players(league_name)
    
    # Calculate team totals once
    team_totals = {}
    for p in all_players:
        team = p['team_title']
        if team not in team_totals:
            team_totals[team] = 0
        team_totals[team] += int(p['goals'])
    
    # Build contribution list
    contributions = []
    for p in all_players:
        team = p['team_title']
        
        # Filter by team if specified
        if team_name and team != team_name:
            continue
        
        goals = int(p['goals'])
        assists = int(p['assists'])
        total_contrib = goals + assists
        team_total = team_totals[team]
        contrib_pct = (total_contrib / team_total * 100) if team_total > 0 else 0
        
        contributions.append({
            'player': p['player_name'],
            'team': team,
            'goals': goals,
            'assists': assists,
            'contributions': total_contrib,
            'team_total': team_total,
            'contribution_pct': round(contrib_pct, 2),
            'games': int(p['games'])
        })
    
    # Sort by contribution percentage (highest first)
    contributions.sort(key=lambda x: x['contribution_pct'], reverse=True)
    
    return contributions

# Test
if __name__ == "__main__":
    # Get ALL Serie A players sorted by contribution
    print("\nGetting ALL Serie A players...")
    all_players = get_all_player_contributions('serieA')
    
    print("\n" + "="*70)
    print("TOP 20 CONTRIBUTORS IN SERIE A (2024-25)")
    print("="*70)
    print(f"{'Rank':<6} {'Player':<25} {'Team':<15} {'G':<4} {'A':<4} {'Total':<7} {'%':<7}")
    print("-"*70)
    
    for i, p in enumerate(all_players[:20], 1):
        print(f"{i:<6} {p['player']:<25} {p['team']:<15} {p['goals']:<4} {p['assists']:<4} {p['contributions']:<7} {p['contribution_pct']:.1f}%")