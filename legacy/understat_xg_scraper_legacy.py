"""
LEGACY: Understat xG scraper using HTML parsing.

THIS APPROACH NO LONGER WORKS as of Dec 2024.

Understat changed their architecture to serve data via XHR API calls
instead of embedding it in the HTML. The HTML page now only contains
a ~18KB shell that loads data dynamically.

See compare_scrapers.py for the comparison test that proved this.

The new working approach is in src/scrapers/understat.py using:
- get_league_data_api() - calls JSON API endpoint
- get_team_match_xg() - extracts match data with npxG

Kept for historical reference only.
"""
import requests
import json
import re
import html

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def get_matches_data_legacy(league_key, season_code):
    """
    LEGACY: Get match-level data from Understat's datesData.
    
    THIS NO LONGER WORKS - datesData is not in the HTML anymore.
    
    Args:
        league_key: e.g., 'serie_a'
        season_code: e.g., '2526'
    
    Returns:
        list: Empty list (this approach is broken)
    """
    # Map our league keys to Understat keys
    league_map = {
        'serie_a': 'Serie_A',
        'premier_league': 'EPL',
        'la_liga': 'La_Liga',
        'bundesliga': 'Bundesliga',
        'ligue_1': 'Ligue_1',
    }
    
    # Map season codes to years
    season_map = {
        '2021': '2020',
        '2122': '2021',
        '2223': '2022',
        '2324': '2023',
        '2425': '2024',
        '2526': '2025',
    }
    
    understat_key = league_map.get(league_key, league_key)
    year = season_map.get(season_code, season_code)
    
    url = f"https://understat.com/league/{understat_key}/{year}"
    response = requests.get(url, headers=HEADERS)
    
    # Try to find datesData in HTML
    match = re.search(r"var datesData\s*=\s*JSON\.parse\('(.+?)'\)", response.text)
    if not match:
        print(f"WARNING: datesData not found in HTML (this approach is deprecated)")
        print(f"Response size: {len(response.content)} bytes")
        return []
    
    encoded = match.group(1)
    decoded = encoded.encode('utf-8').decode('unicode_escape')
    matches = json.loads(decoded)
    
    # Decode HTML entities in team names
    for m in matches:
        m['h']['title'] = html.unescape(m['h']['title'])
        m['a']['title'] = html.unescape(m['a']['title'])
    
    # Filter to only completed matches
    completed = [m for m in matches if m['isResult']]
    print(f"Found {len(completed)} completed matches")
    return completed


def get_team_match_xg_legacy(league_key, season_code):
    """
    LEGACY: Extract per-match xG data using datesData HTML parsing.
    
    THIS NO LONGER WORKS - use get_team_match_xg() from src/scrapers/understat.py instead.
    
    Note: Even when this worked, it did NOT have npxG data.
    The new API approach provides npxG.
    """
    matches_data = get_matches_data_legacy(league_key, season_code)
    
    if not matches_data:
        return []
    
    # Track match count per team to assign match_number
    team_match_counts = {}
    
    records = []
    for match in matches_data:
        home_team = match['h']['title']
        away_team = match['a']['title']
        match_date = match['datetime']
        
        home_goals = int(match['goals']['h'])
        away_goals = int(match['goals']['a'])
        home_xg = float(match['xG']['h'])
        away_xg = float(match['xG']['a'])
        
        # Determine results
        if home_goals > away_goals:
            home_result, away_result = 'W', 'L'
            home_pts, away_pts = 3, 0
        elif home_goals < away_goals:
            home_result, away_result = 'L', 'W'
            home_pts, away_pts = 0, 3
        else:
            home_result, away_result = 'D', 'D'
            home_pts, away_pts = 1, 1
        
        # Update match counts
        team_match_counts[home_team] = team_match_counts.get(home_team, 0) + 1
        team_match_counts[away_team] = team_match_counts.get(away_team, 0) + 1
        
        # Home team record
        records.append({
            'league': league_key,
            'season': season_code,
            'team': home_team,
            'opponent': away_team,
            'venue': 'h',
            'match_date': match_date,
            'match_number': team_match_counts[home_team],
            'goals_for': home_goals,
            'goals_against': away_goals,
            'xg_for': home_xg,
            'xg_against': away_xg,
            'npxg_for': None,  # NOT AVAILABLE in datesData
            'npxg_against': None,  # NOT AVAILABLE in datesData
            'result': home_result,
            'points': home_pts,
        })
        
        # Away team record
        records.append({
            'league': league_key,
            'season': season_code,
            'team': away_team,
            'opponent': home_team,
            'venue': 'a',
            'match_date': match_date,
            'match_number': team_match_counts[away_team],
            'goals_for': away_goals,
            'goals_against': home_goals,
            'xg_for': away_xg,
            'xg_against': home_xg,
            'npxg_for': None,
            'npxg_against': None,
            'result': away_result,
            'points': away_pts,
        })
    
    print(f"Extracted {len(records)} team-match records for {league_key} {season_code}")
    return records


if __name__ == "__main__":
    print("Testing legacy scraper (expected to fail)...")
    print()
    
    matches = get_team_match_xg_legacy('serie_a', '2526')
    
    if matches:
        print(f"Got {len(matches)} matches")
    else:
        print("No matches returned (as expected - this approach is broken)")
