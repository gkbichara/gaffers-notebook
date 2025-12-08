import math
import pandas as pd

class EloTracker:
    def __init__(self, k_factor_stable=20, k_factor_volatile=40, volatile_match_count=30, home_advantage=40, base_rating=1500):
        """
        Initialize the ELO tracking system with dynamic K-factors.
        
        Args:
            k_factor_stable (int): Standard K for established teams (default 20).
            k_factor_volatile (int): High K for new/provisionally rated teams (default 40).
            volatile_match_count (int): Number of matches a team plays before switching to stable K (default 30).
            home_advantage (int): Points added to home team rating for prediction.
            base_rating (int): Starting rating for new teams.
        """
        self.ratings = {}      # {team_name: rating}
        self.match_counts = {} # {team_name: count}
        self.team_leagues = {} # {team_name: league} - last league played in
        self.history = []      # List of match dicts
        
        self.k_stable = k_factor_stable
        self.k_volatile = k_factor_volatile
        self.volatile_limit = volatile_match_count
        self.home_adv = home_advantage
        self.base = base_rating

    def get_rating(self, team):
        """Get current rating for a team, initializing if new."""
        return self.ratings.get(team, self.base)
    
    def get_k_factor(self, team):
        """Determine K-factor based on how many games the team has played."""
        count = self.match_counts.get(team, 0)
        if count < self.volatile_limit:
            return self.k_volatile
        return self.k_stable

    def _expected_score(self, rating_a, rating_b):
        """
        Calculate expected score (win probability) for team A vs team B.
        Standard logistic curve formula.
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def _get_margin_multiplier(self, goal_diff):
        """
        Calculate multiplier based on goal difference.
        Winning by more goals should yield more points.
        Formula roughly based on World Football ELO.
        """
        if goal_diff <= 0:
            return 1  # Should not happen for winner (logic handled in process_match)
        elif goal_diff == 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        else:
            # Diminishing returns for huge blowouts: (11 + diff) / 8
            return (11 + goal_diff) / 8

    def process_match(self, home_team, away_team, fthg, ftag, date, season, league):
        """
        Update ratings based on a single match result.
        """
        # Get current state
        r_home = self.get_rating(home_team)
        r_away = self.get_rating(away_team)
        
        k_home = self.get_k_factor(home_team)
        k_away = self.get_k_factor(away_team)

        # Determine match outcome (1 = Home Win, 0.5 = Draw, 0 = Away Win)
        if fthg > ftag:
            actual_home = 1.0
            goal_diff = fthg - ftag
        elif fthg == ftag:
            actual_home = 0.5
            goal_diff = 0
        else:
            actual_home = 0.0
            goal_diff = ftag - fthg

        # Calculate Expected Score (Home team gets advantage boost for calculation only)
        expected_home = self._expected_score(r_home + self.home_adv, r_away)
        
        # Margin of Victory Multiplier (applies to both)
        g_mult = self._get_margin_multiplier(goal_diff)

        # Calculate Rating Deltas
        # Note: We calculate separate deltas because K-factors might differ!
        # Delta = K * G * (Actual - Expected)
        
        delta_home = k_home * g_mult * (actual_home - expected_home)
        
        # For away team, Expected_Away = 1 - Expected_Home
        # Actual_Away = 1 - Actual_Home
        # So (Actual_Away - Expected_Away) is just -(Actual_Home - Expected_Home)
        delta_away = k_away * g_mult * ((1 - actual_home) - (1 - expected_home))
        
        # Update Ratings
        new_home = r_home + delta_home
        new_away = r_away + delta_away

        self.ratings[home_team] = new_home
        self.ratings[away_team] = new_away
        
        # Update Match Counts
        self.match_counts[home_team] = self.match_counts.get(home_team, 0) + 1
        self.match_counts[away_team] = self.match_counts.get(away_team, 0) + 1
        
        # Track league (uses last league played)
        self.team_leagues[home_team] = league
        self.team_leagues[away_team] = league

        # Log history
        self.history.append({
            'Date': date,
            'Season': season,
            'League': league,
            'HomeTeam': home_team,
            'AwayTeam': away_team,
            'FTHG': fthg,
            'FTAG': ftag,
            'HomeRating_Before': round(r_home, 2),
            'AwayRating_Before': round(r_away, 2),
            'HomeRating_After': round(new_home, 2),
            'AwayRating_After': round(new_away, 2),
            'Expected_Home_Win': round(expected_home, 3),
            'Rating_Change_Home': round(delta_home, 2),
            'Rating_Change_Away': round(delta_away, 2)
        })

    def process_league_season(self, df, season, league_key):
        """
        Process an entire season DataFrame chronologically.
        Expects DF to have columns: Date, HomeTeam, AwayTeam, FTHG, FTAG.
        """
        # Ensure chronological order
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
             df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
             
        df = df.sort_values('Date')
        
        for _, row in df.iterrows():
            self.process_match(
                home_team=row['HomeTeam'],
                away_team=row['AwayTeam'],
                fthg=row['FTHG'],
                ftag=row['FTAG'],
                date=row['Date'],
                season=season,
                league=league_key
            )

    def get_history_df(self):
        """Return the entire match history with ratings as a DataFrame."""
        return pd.DataFrame(self.history)

    def get_current_ratings_df(self):
        """Return current ratings for all teams."""
        data = [{
            'Team': k, 
            'Elo': round(v, 2), 
            'Matches': self.match_counts.get(k, 0),
            'league': self.team_leagues.get(k)
        } for k, v in self.ratings.items()]
        df = pd.DataFrame(data).sort_values('Elo', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        return df[['Rank', 'Team', 'Elo', 'Matches', 'league']]

    
    def load_from_db(self, ratings_df):
        """Load existing ratings and match counts from database."""
        for _, row in ratings_df.iterrows():
            self.ratings[row['team']] = row['elo_rating']
            self.match_counts[row['team']] = row['matches_played']
            if row.get('league'):
                self.team_leagues[row['team']] = row['league']
        print(f"   Loaded {len(self.ratings)} team ratings from DB")

    @classmethod
    def from_db(cls):
        """Create an EloTracker initialized from database state."""
        from src.database import get_elo_ratings
        
        tracker = cls()
        ratings_df = get_elo_ratings()
        if len(ratings_df) > 0:
            tracker.load_from_db(ratings_df)
        return tracker

    def process_new_matches(self, matches_df):
        """Process matches (already filtered to new ones from DB query)."""
        if len(matches_df) == 0:
            print("   No new matches to process")
            return 0
        
        if 'date' in matches_df.columns:
            matches_df = matches_df.rename(columns={'date': 'Date'})
        
        if not pd.api.types.is_datetime64_any_dtype(matches_df['Date']):
            matches_df['Date'] = pd.to_datetime(matches_df['Date'])
        
        matches_df = matches_df.sort_values('Date')
        
        for _, row in matches_df.iterrows():
            # Use explicit None checks (0 is valid for goals)
            fthg = row.get('fthg') if row.get('fthg') is not None else row.get('FTHG')
            ftag = row.get('ftag') if row.get('ftag') is not None else row.get('FTAG')
            
            self.process_match(
                home_team=row.get('home_team') or row.get('HomeTeam'),
                away_team=row.get('away_team') or row.get('AwayTeam'),
                fthg=fthg,
                ftag=ftag,
                date=row['Date'],
                season=row.get('season') or row.get('Season'),
                league=row.get('league') or row.get('League')
            )
        
        print(f"   Processed {len(matches_df)} new matches")
        return len(matches_df)


def run_incremental_elo():
    """Run incremental ELO update using database."""
    from src.database import (
        get_raw_matches, 
        get_last_processed_match_date,
        upload_elo_ratings,
        upload_elo_match_history
    )
    
    print("\n--- Incremental ELO Update ---")
    
    # Load tracker with existing state from DB
    tracker = EloTracker.from_db()
    
    # Get only new matches (filtered at DB level)
    last_date = get_last_processed_match_date()
    print(f"   Last processed: {last_date or 'None (fresh start)'}")
    
    new_matches = get_raw_matches(after_date=last_date)
    tracker.process_new_matches(new_matches)
    
    # Upload results if there were new matches
    if len(tracker.history) > 0:
        history_df = tracker.get_history_df()
        upload_elo_match_history(history_df)
        
        ratings_df = tracker.get_current_ratings_df()
        upload_elo_ratings(ratings_df)
        
        print(f"   ✓ Uploaded {len(tracker.history)} new ELO records")
    else:
        print("   ✓ ELO ratings are up to date")