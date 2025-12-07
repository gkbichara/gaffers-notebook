import requests
import os
from src.config import LEAGUES, LEAGUE_KEYS, SEASONS, FBDATA_BASE_URL, DATA_DIR, CURRENT_SEASON
import pandas as pd
from src.database import upload_raw_matches
from io import StringIO


def download_league_data(league_key, season):
    """
    Download CSV data for a specific league and season.
    
    Args:
        league_key: League key from config (e.g., 'serie_a')
        season: Season code (e.g., '2526')
    """
    league_info = LEAGUES[league_key]
    display_name = league_info['display_name']
    fbdata_code = league_info['fbdata_code']
    folder_name = league_info['folder']
    
    # Construct URL
    url = f"{FBDATA_BASE_URL}/{season}/{fbdata_code}.csv"
    
    # Create directory structure: data/league_folder/
    league_dir = os.path.join(DATA_DIR, folder_name)
    os.makedirs(league_dir, exist_ok=True)
    
    # File path: data/league_folder/season.csv
    file_path = os.path.join(league_dir, f"{season}.csv")
    
    try:
        print(f"Downloading {display_name} {season}... ", end="")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes
        df = pd.read_csv(StringIO(response.text))
        df['league'] = league_key
        df['season'] = season
        
        # Save to local cache
        df.to_csv(file_path, index=False)
        
        print(f"✓ Saved to {file_path}")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed: {e}")
        return None


def main(seasons_to_scrape=None):
    """
    Download league data.
    
    Args:
        seasons_to_scrape (list): Optional list of seasons to download. 
                                  Defaults to CURRENT_SEASON only.
    """
    if seasons_to_scrape is None:
        seasons_to_scrape = [CURRENT_SEASON]

    print("=" * 50)
    print("Football Data Scraper")
    print("=" * 50)
    
    total_downloads = len(LEAGUE_KEYS) * len(seasons_to_scrape)
    successful = 0
    
    for league_key in LEAGUE_KEYS:
        display_name = LEAGUES[league_key]['display_name']
        print(f"\n{display_name}:")
        for season in seasons_to_scrape:
            df = download_league_data(league_key, season)
            if df is not None:
                upload_raw_matches(df)
                successful += 1
    
    print("\n" + "=" * 50)
    print(f"Download complete! {successful}/{total_downloads} files downloaded")
    print("=" * 50)
    
    return successful == total_downloads

def scrape_all_history():
    """Helper to scrape ALL historical seasons (for setup)."""
    return main(seasons_to_scrape=SEASONS)

if __name__ == "__main__":
    main()
