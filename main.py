import sys
from scraper import main as run_scraper
from analysis import main as run_analysis
from understat_scraper import calculate_contributions, print_table, save_player_results

def main():
    print("="*60)
    print("FOOTBALL DATA PIPELINE - Starting")
    print("="*60)
    
    # Step 1: Scrape football-data.co.uk (team data)
    print("\n[1/3] Scraping team data...")
    try:
        run_scraper()
        scraper_success = True
    except Exception as e:
        print(f"⚠️  Scraper failed: {e}")
        print("→ Using existing data for analysis")
        scraper_success = False
    
    # Step 2: Run YoY analysis (only if scraper succeeded OR we have old data)
    print("\n[2/3] Running YoY analysis...")
    try:
        run_analysis()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Step 3: Scrape Understat (player data - independent)
    print("\n[3/3] Fetching player contribution data...")
    try:
        for league in ['serieA', 'PremierLeague', 'LaLiga', 'Bundesliga', 'ligue1']:
            contributions = calculate_contributions(league)
            save_player_results(contributions, league)
        
        # Print Serie A table as example
        print_table(contributions, top_n=20)  # This will show last league (ligue1)
        # Or fetch Serie A again to display it
    except Exception as e:
        print(f"❌ Understat scraper failed: {e}")

if __name__ == "__main__":
    main()