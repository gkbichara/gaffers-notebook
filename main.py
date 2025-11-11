from scraper import main as run_scraper
from analysis import main as run_analysis
from understat_scraper import calculate_contributions, print_table, save_player_results
from config import LEAGUE_KEYS

def main():
    print("="*60)
    print("FOOTBALL DATA PIPELINE - Starting")
    print("="*60)
    
    # Step 1: Scrape football-data.co.uk (team data)
    print("\n[1/3] Scraping team data...")
    try:
        run_scraper()
    except Exception as e:
        print(f"Scraper failed: {e}")
        print("→ Using existing data for analysis")
    
    # Step 2: Run YoY analysis
    print("\n[2/3] Running YoY analysis...")
    try:
        run_analysis()
    except Exception as e:
        print(f"Analysis failed: {e}")
    
    # Step 3: Scrape Understat (player data - independent)
    print("\n[3/3] Fetching player contribution data...")
    try:
        for league_key in LEAGUE_KEYS:
            contributions = calculate_contributions(league_key)
            save_player_results(contributions, league_key)
        
        
    except Exception as e:
        print(f"Understat scraper failed: {e}")
    
    print("\n" + "="*60)
    print("Pipeline complete!")
    print("="*60)


if __name__ == "__main__":
    main()