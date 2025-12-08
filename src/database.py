import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Missing Supabase credentials in .env file")

supabase: Client = create_client(url, key)

def get_db():
    
    return supabase


def update_player_stats(league_key, season, player_data_list):
    """
    Upserts player stats into Supabase.
    
    Args:
        league_key: e.g. 'serie_a'
        season: e.g. '2526'
        player_data_list: List of dicts from understat_scraper
    """
    client = get_db()
    
    # Prepare data for Supabase (match columns to SQL table)
    records = []
    # Use a set to track unique keys for deduplication within the batch
    seen_keys = set()
    
    for p in player_data_list:
        # Create a unique key tuple based on the DB constraint
        unique_key = (p['player'], p['team'], league_key, season)
        
        if unique_key in seen_keys:
            # Skip duplicates in the same payload
            continue
            
        seen_keys.add(unique_key)
        
        record = {
            "league": league_key,
            "season": season,
            "player_name": p['player'],
            "team": p['team'],
            "goals": p['goals'],
            "assists": p['assists'],
            "contributions": p['contributions'],
            "contribution_pct": p['contribution_pct'],
            "goals_pct": p['goals_pct'],
            "assists_pct": p['assists_pct'],
            "games_played": p['games'],
            # updated_at defaults to NOW() in SQL, but we can force it here too if we want
        }
        records.append(record)
        
    # Perform Upsert
    # on_conflict matches the UNIQUE constraint we created in SQL
    try:
        # Supabase might still choke on a large batch if there are hidden duplicates,
        # but the python-side dedup should solve 99% of cases.
        response = client.table("player_stats").upsert(records, on_conflict="player_name, team, league, season").execute()
        print(f"   ✓ Uploaded {len(records)} records to Supabase")
        return True
    except Exception as e:
        print(f"   ✗ Database Upload Failed: {e}")
        return False

    

def update_team_stats(league_key, season, results_df):
    """
    Upserts team stats into Supabase.
    
    Args:
        league_key: e.g. 'serie_a'
        season: e.g. '2526'
        results_df: DataFrame from analyze_league()
    """
    client = get_db()
    
    # Convert DataFrame to list of dicts
    # Replace NaN with None for SQL compatibility
    records = []
    
    for _, row in results_df.iterrows():
        # Handle NaN values safely
        def clean(val):
            return None if pd.isna(val) else val

        record = {
            "league": league_key,
            "season": season,
            "team_name": row['Team'],
            "match_number": int(row['Match_Number']),
            "date": str(row['Date'].date()) if pd.notna(row['Date']) else None,
            "opponent": row['Opponent'],
            "venue": row['Venue'],
            "result": row['Result'],
            "goals_for": int(row['FTHG']) if row['Venue'] == 'H' else int(row['FTAG']),
            "goals_against": int(row['FTAG']) if row['Venue'] == 'H' else int(row['FTHG']),
            "points_current": int(row['Points_cur']),
            "points_previous": int(row['Points_prev']) if pd.notna(row['Points_prev']) else None,
            "differential": int(row['Differential']) if pd.notna(row['Differential']) else None,
            "cumulative_differential": int(row['Cumulative']) if pd.notna(row['Cumulative']) else None,
        }
        records.append(record)
        
    # Perform Upsert (batch in chunks if necessary, but 1000 rows is fine for Supabase)
    try:
        # Supabase has a request size limit, so let's chunk it if it's huge
        chunk_size = 1000
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            client.table("team_stats").upsert(chunk, on_conflict="team_name, match_number, league, season").execute()
            
        print(f"   ✓ Uploaded {len(records)} team match records to Supabase")
        return True
    except Exception as e:
        print(f"   ✗ Team Stats Upload Failed: {e}")
        return False


def upload_raw_matches(df):
    """Upload raw match data to Supabase."""
    client = get_db()
    
    # Core columns to extract (everything else goes to betting_odds)
    core_cols = [
        'Div', 'Date', 'Time', 'HomeTeam', 'AwayTeam',
        'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR',
        'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC',
        'HY', 'AY', 'HR', 'AR', 'league', 'season'
    ]
    
    records = []
    for _, row in df.iterrows():
        # Build core record with lowercase keys for DB
        record = {
            'league': row.get('league'),
            'season': row.get('season'),
            'div': row.get('Div'),
            'date': pd.to_datetime(row.get('Date'), dayfirst=True).strftime('%Y-%m-%d') if pd.notna(row.get('Date')) else None,
            'time': row.get('Time'),
            'home_team': row.get('HomeTeam'),
            'away_team': row.get('AwayTeam'),
            'fthg': row.get('FTHG'),
            'ftag': row.get('FTAG'),
            'ftr': row.get('FTR'),
            'hthg': row.get('HTHG'),
            'htag': row.get('HTAG'),
            'htr': row.get('HTR'),
            'hs': row.get('HS'),
            'as_col': row.get('AS'),
            'hst': row.get('HST'),
            'ast': row.get('AST'),
            'hf': row.get('HF'),
            'af': row.get('AF'),
            'hc': row.get('HC'),
            'ac': row.get('AC'),
            'hy': row.get('HY'),
            'ay': row.get('AY'),
            'hr': row.get('HR'),
            'ar': row.get('AR'),
        }
        
        # Bundle betting odds into JSONB
        betting = {k: v for k, v in row.items() if k not in core_cols and pd.notna(v)}
        record['betting_odds'] = betting if betting else None
        
        # Clean NaN values
        record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
        records.append(record)
    
    try:
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            client.table("raw_matches").upsert(
                chunk,
                on_conflict="league, season, date, home_team, away_team"
            ).execute()
        
        print(f"   ✓ Uploaded {len(records)} raw matches to Supabase")
        return True
    except Exception as e:
        print(f"   ✗ Raw Matches Upload Failed: {e}")
        return False


def upload_elo_ratings(ratings_df):
    """Upload current ELO ratings to Supabase."""
    client = get_db()
    
    records = []
    for _, row in ratings_df.iterrows():
        record = {
            'team': row['Team'],
            'league': row.get('league'),
            'elo_rating': row['Elo'],
            'matches_played': row['Matches'],
            'last_match_date': row.get('last_match_date'),
        }
        record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
        records.append(record)
    
    try:
        client.table("elo_ratings").upsert(
            records, 
            on_conflict="team"
        ).execute()
        print(f"   ✓ Uploaded {len(records)} ELO ratings to Supabase")
        return True
    except Exception as e:
        print(f"   ✗ ELO Ratings Upload Failed: {e}")
        return False


def upload_elo_match_history(history_df):
    """Upload ELO match history to Supabase."""
    client = get_db()
    
    records = []
    for _, row in history_df.iterrows():
        date_val = row.get('Date')
        if pd.notna(date_val):
            date_val = pd.to_datetime(date_val).strftime('%Y-%m-%d')
        
        record = {
            'date': date_val,
            'season': row['Season'],
            'league': row['League'],
            'home_team': row['HomeTeam'],
            'away_team': row['AwayTeam'],
            'fthg': row.get('FTHG'),
            'ftag': row.get('FTAG'),
            'result': 'H' if row.get('FTHG', 0) > row.get('FTAG', 0) else ('A' if row.get('FTAG', 0) > row.get('FTHG', 0) else 'D'),
            'home_elo_before': row['HomeRating_Before'],
            'away_elo_before': row['AwayRating_Before'],
            'home_elo_after': row['HomeRating_After'],
            'away_elo_after': row['AwayRating_After'],
            'elo_change_home': row.get('Rating_Change_Home'),
            'elo_change_away': row.get('Rating_Change_Away'),
            'expected_home_win': row.get('Expected_Home_Win'),
        }
        record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
        records.append(record)
    
    try:
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            client.table("elo_match_history").upsert(
                chunk,
                on_conflict="league, season, date, home_team, away_team"
            ).execute()
        
        print(f"   ✓ Uploaded {len(records)} ELO match history records to Supabase")
        return True
    except Exception as e:
        print(f"   ✗ ELO Match History Upload Failed: {e}")
        return False


def get_raw_matches(league=None, season=None, after_date=None):
    """Query raw matches from Supabase."""
    client = get_db()
    
    all_data = []
    page_size = 1000
    offset = 0
    
    while True:
        query = client.table("raw_matches").select("*")
        
        if league:
            query = query.eq("league", league)
        if season:
            query = query.eq("season", season)
        if after_date:
            query = query.gt("date", after_date)
        
        query = query.order("date").range(offset, offset + page_size - 1)
        response = query.execute()
        
        if not response.data:
            break
            
        all_data.extend(response.data)
        
        if len(response.data) < page_size:
            break
            
        offset += page_size
    
    return pd.DataFrame(all_data)

    
def get_elo_ratings():
    """Query current ELO ratings from Supabase."""
    client = get_db()
    
    response = client.table("elo_ratings").select("*").order("elo_rating", desc=True).execute()
    return pd.DataFrame(response.data)

    
def get_elo_match_history(league=None):
    """Query ELO match history for incremental processing."""
    client = get_db()
    
    query = client.table("elo_match_history").select("*")
    
    if league:
        query = query.eq("league", league)
    
    query = query.order("date")
    
    response = query.execute()
    return pd.DataFrame(response.data)


def get_last_processed_match_date():
    """Get the most recent match date in ELO history (for incremental processing)."""
    client = get_db()
    
    response = client.table("elo_match_history").select("date").order("date", desc=True).limit(1).execute()
    
    if response.data:
        return response.data[0]['date']
    return None


def get_matches_for_analysis(league, season):
    """
    Get match data formatted for analysis functions.
    
    Returns DataFrame with columns matching the analysis expectations:
    Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR
    """
    df = get_raw_matches(league=league, season=season)
    
    if len(df) == 0:
        return df
    
    # Rename columns to match analysis expectations
    column_map = {
        'date': 'Date',
        'home_team': 'HomeTeam',
        'away_team': 'AwayTeam',
        'fthg': 'FTHG',
        'ftag': 'FTAG',
        'ftr': 'FTR',
    }
    
    df = df.rename(columns=column_map)
    return df


def get_team_stats(league=None, season=None):
    """Query team stats (YoY differentials) from Supabase with pagination."""
    client = get_db()
    
    all_data = []
    page_size = 1000
    offset = 0
    
    while True:
        query = client.table("team_stats").select("*")
        
        if league:
            query = query.eq('league', league)
        if season:
            query = query.eq('season', season)
        
        query = query.range(offset, offset + page_size - 1)
        response = query.execute()
        
        if not response.data:
            break
            
        all_data.extend(response.data)
        
        if len(response.data) < page_size:
            break
            
        offset += page_size
    
    return pd.DataFrame(all_data)


def get_player_stats(league=None, season=None):
    """Query player stats from Supabase with pagination."""
    client = get_db()
    
    all_data = []
    page_size = 1000
    offset = 0
    
    while True:
        query = client.table("player_stats").select("*")
        
        if league:
            query = query.eq('league', league)
        if season:
            query = query.eq('season', season)
        
        query = query.range(offset, offset + page_size - 1)
        response = query.execute()
        
        if not response.data:
            break
            
        all_data.extend(response.data)
        
        if len(response.data) < page_size:
            break
            
        offset += page_size
    
    return pd.DataFrame(all_data)