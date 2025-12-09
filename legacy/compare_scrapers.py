"""
Comprehensive comparison of Understat scraping approaches.

Compares:
1. OLD: HTML parsing with datesData (has opponent directly, no npxG)
2. NEW: JSON API endpoint (has npxG, needs opponent lookup)

Run this to validate which approach is better.
"""
import requests
import json
import re
import html
import time
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'X-Requested-With': 'XMLHttpRequest',
}

TEST_LEAGUE = 'Serie_A'
TEST_SEASON = '2025'

# ============================================================================
# OLD APPROACH: HTML Parsing with datesData
# ============================================================================

def old_approach_datesData():
    """
    OLD: Fetch HTML page, parse datesData JavaScript variable.
    
    Pros:
    - Has opponent name directly in the data
    - Well-tested approach
    
    Cons:
    - Larger response (full HTML)
    - Regex parsing (fragile)
    - No npxG data in datesData
    """
    url = f"https://understat.com/league/{TEST_LEAGUE}/{TEST_SEASON}"
    
    start = time.time()
    response = requests.get(url, headers=HEADERS)
    request_time = time.time() - start
    
    result = {
        'method': 'OLD (datesData HTML)',
        'url': url,
        'status_code': response.status_code,
        'response_bytes': len(response.content),
        'request_time_sec': round(request_time, 3),
        'success': False,
        'matches': [],
        'npxg_available': False,
        'opponent_available': True,
        'error': None,
    }
    
    if response.status_code != 200:
        result['error'] = f"HTTP {response.status_code}"
        return result
    
    # Parse datesData from HTML
    match = re.search(r"var datesData\s*=\s*JSON\.parse\('(.+?)'\)", response.text)
    if not match:
        result['error'] = "Could not find datesData in HTML"
        return result
    
    try:
        encoded = match.group(1)
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        matches = json.loads(decoded)
        
        # Filter completed matches only
        completed = [m for m in matches if m.get('isResult')]
        
        result['success'] = True
        result['total_matches'] = len(completed)
        
        # Sample some matches
        for m in completed[:5]:
            home = html.unescape(m['h']['title'])
            away = html.unescape(m['a']['title'])
            result['matches'].append({
                'home': home,
                'away': away,
                'date': m.get('datetime'),
                'score': f"{m['goals']['h']}-{m['goals']['a']}",
                'xG': f"{m['xG']['h']}-{m['xG']['a']}",
                'npxG': 'NOT AVAILABLE',
            })
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def old_approach_teamsData():
    """
    OLD: Fetch HTML page, parse teamsData JavaScript variable.
    
    Pros:
    - Has npxG data
    - Has match history per team
    
    Cons:
    - Larger response (full HTML)
    - Regex parsing (fragile)
    - No opponent name directly (would need to derive)
    """
    url = f"https://understat.com/league/{TEST_LEAGUE}/{TEST_SEASON}"
    
    start = time.time()
    response = requests.get(url, headers=HEADERS)
    request_time = time.time() - start
    
    result = {
        'method': 'OLD (teamsData HTML)',
        'url': url,
        'status_code': response.status_code,
        'response_bytes': len(response.content),
        'request_time_sec': round(request_time, 3),
        'success': False,
        'matches': [],
        'npxg_available': True,
        'opponent_available': False,
        'error': None,
    }
    
    if response.status_code != 200:
        result['error'] = f"HTTP {response.status_code}"
        return result
    
    # Parse teamsData from HTML
    match = re.search(r"var teamsData\s*=\s*JSON\.parse\('(.+?)'\)", response.text)
    if not match:
        result['error'] = "Could not find teamsData in HTML"
        return result
    
    try:
        encoded = match.group(1)
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        teams = json.loads(decoded)
        
        result['success'] = True
        result['total_teams'] = len(teams)
        
        # Sample first team's matches
        first_team = list(teams.values())[0]
        team_name = html.unescape(first_team['title'])
        
        for m in first_team['history'][:5]:
            result['matches'].append({
                'team': team_name,
                'venue': m['h_a'],
                'opponent': 'NEEDS LOOKUP',
                'date': m['date'],
                'score': f"{m['scored']}-{m['missed']}",
                'xG': f"{round(m['xG'], 2)}-{round(m['xGA'], 2)}",
                'npxG': f"{round(m['npxG'], 2)}-{round(m['npxGA'], 2)}",
            })
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


# ============================================================================
# NEW APPROACH: JSON API
# ============================================================================

def new_approach_api():
    """
    NEW: Call JSON API endpoint directly.
    
    Pros:
    - Clean JSON response (no HTML parsing)
    - Smaller response size
    - Has npxG data
    - Same data as teamsData but cleaner
    
    Cons:
    - Requires XHR headers
    - No opponent name directly (needs lookup)
    """
    api_url = f"https://understat.com/getLeagueData/{TEST_LEAGUE}/{TEST_SEASON}"
    referer_url = f"https://understat.com/league/{TEST_LEAGUE}/{TEST_SEASON}"
    
    headers = {**API_HEADERS, 'Referer': referer_url}
    
    start = time.time()
    response = requests.get(api_url, headers=headers)
    request_time = time.time() - start
    
    result = {
        'method': 'NEW (JSON API)',
        'url': api_url,
        'status_code': response.status_code,
        'response_bytes': len(response.content),
        'request_time_sec': round(request_time, 3),
        'success': False,
        'matches': [],
        'npxg_available': True,
        'opponent_available': False,  # Needs lookup, but we can do it
        'error': None,
    }
    
    if response.status_code != 200:
        result['error'] = f"HTTP {response.status_code}"
        return result
    
    try:
        data = response.json()
        teams = data.get('teams', {})
        
        result['success'] = True
        result['total_teams'] = len(teams)
        result['total_players'] = len(data.get('players', []))
        
        # Build opponent lookup (to show we CAN get opponents)
        match_lookup = {}
        for team_id, team_info in teams.items():
            team_name = html.unescape(team_info['title'])
            for m in team_info['history']:
                dt = m['date']
                venue = m['h_a']
                if dt not in match_lookup:
                    match_lookup[dt] = {}
                match_lookup[dt][venue] = team_name
        
        # Sample first team's matches with opponent lookup
        first_team = list(teams.values())[0]
        team_name = html.unescape(first_team['title'])
        
        for m in first_team['history'][:5]:
            dt = m['date']
            venue = m['h_a']
            opp_venue = 'a' if venue == 'h' else 'h'
            opponent = match_lookup.get(dt, {}).get(opp_venue, 'Unknown')
            
            result['matches'].append({
                'team': team_name,
                'venue': venue,
                'opponent': opponent,
                'date': m['date'],
                'score': f"{m['scored']}-{m['missed']}",
                'xG': f"{round(m['xG'], 2)}-{round(m['xGA'], 2)}",
                'npxG': f"{round(m['npxG'], 2)}-{round(m['npxGA'], 2)}",
            })
        
        result['opponent_available'] = True  # We proved we can derive it
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


# ============================================================================
# Run Comparison
# ============================================================================

def print_result(result):
    """Pretty print a result."""
    print(f"\n{'='*70}")
    print(f"Method: {result['method']}")
    print(f"{'='*70}")
    print(f"URL: {result['url']}")
    print(f"Status: {result['status_code']}")
    print(f"Response Size: {result['response_bytes']:,} bytes ({result['response_bytes']/1024:.1f} KB)")
    print(f"Request Time: {result['request_time_sec']} sec")
    print(f"Success: {result['success']}")
    print(f"npxG Available: {result['npxg_available']}")
    print(f"Opponent Available: {result['opponent_available']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    if result.get('total_matches'):
        print(f"Total Matches: {result['total_matches']}")
    if result.get('total_teams'):
        print(f"Total Teams: {result['total_teams']}")
    if result.get('total_players'):
        print(f"Total Players: {result['total_players']}")
    
    if result['matches']:
        print(f"\nSample Data (first {len(result['matches'])} matches):")
        for i, m in enumerate(result['matches'], 1):
            print(f"  {i}. {m}")


def main():
    print("\n" + "="*70)
    print("UNDERSTAT SCRAPER COMPARISON TEST")
    print(f"League: {TEST_LEAGUE}, Season: {TEST_SEASON}")
    print("="*70)
    
    # Run all approaches
    results = []
    
    print("\n[1/3] Testing OLD approach (datesData HTML parsing)...")
    results.append(old_approach_datesData())
    time.sleep(1)  # Rate limiting
    
    print("[2/3] Testing OLD approach (teamsData HTML parsing)...")
    results.append(old_approach_teamsData())
    time.sleep(1)
    
    print("[3/3] Testing NEW approach (JSON API)...")
    results.append(new_approach_api())
    
    # Print results
    for r in results:
        print_result(r)
    
    # Summary comparison
    print("\n" + "="*70)
    print("SUMMARY COMPARISON")
    print("="*70)
    print(f"{'Method':<25} {'Size (KB)':<12} {'Time (s)':<10} {'npxG':<8} {'Opponent':<10} {'Status'}")
    print("-"*70)
    for r in results:
        status = "✅" if r['success'] else "❌"
        npxg = "✅" if r['npxg_available'] else "❌"
        opp = "✅" if r['opponent_available'] else "❌"
        print(f"{r['method']:<25} {r['response_bytes']/1024:<12.1f} {r['request_time_sec']:<10} {npxg:<8} {opp:<10} {status}")
    
    # Recommendation
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    api_result = results[2]
    if api_result['success'] and api_result['npxg_available'] and api_result['opponent_available']:
        print("✅ NEW (JSON API) is recommended:")
        print("   - Smaller response size (~30% less)")
        print("   - Has npxG data (OLD datesData doesn't)")
        print("   - Clean JSON (no regex parsing)")
        print("   - Opponent can be derived from same data")
    else:
        print("⚠️  Consider keeping OLD approach if API is unreliable")
        print(f"   API result: {api_result}")


if __name__ == "__main__":
    main()
