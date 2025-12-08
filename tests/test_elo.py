"""Tests for ELO calculation and tracking."""
import pytest
import pandas as pd
from unittest.mock import patch, Mock

from src.analysis.elo import EloTracker


class TestEloTracker:
    """Tests for EloTracker class."""
    
    def test_new_team_gets_base_rating(self):
        """New teams should start at base rating (1500)."""
        tracker = EloTracker()
        assert tracker.get_rating('NewTeam') == 1500
    
    def test_new_team_uses_volatile_k_factor(self):
        """New teams should use higher K-factor."""
        tracker = EloTracker(k_factor_volatile=40, k_factor_stable=20)
        assert tracker.get_k_factor('NewTeam') == 40
    
    def test_established_team_uses_stable_k_factor(self):
        """Teams with 30+ matches should use stable K-factor."""
        tracker = EloTracker(k_factor_volatile=40, k_factor_stable=20, volatile_match_count=30)
        tracker.match_counts['OldTeam'] = 30
        assert tracker.get_k_factor('OldTeam') == 20
    
    def test_home_win_increases_home_rating(self):
        """Home win should increase home team's rating."""
        tracker = EloTracker()
        initial_home = tracker.get_rating('HomeTeam')
        
        tracker.process_match(
            home_team='HomeTeam',
            away_team='AwayTeam', 
            fthg=2, ftag=0,
            date='2025-08-15',
            season='2526',
            league='test'
        )
        
        assert tracker.get_rating('HomeTeam') > initial_home
    
    def test_away_win_increases_away_rating(self):
        """Away win should increase away team's rating."""
        tracker = EloTracker()
        initial_away = tracker.get_rating('AwayTeam')
        
        tracker.process_match(
            home_team='HomeTeam',
            away_team='AwayTeam',
            fthg=0, ftag=2,
            date='2025-08-15',
            season='2526',
            league='test'
        )
        
        assert tracker.get_rating('AwayTeam') > initial_away
    
    def test_draw_with_equal_ratings_minimal_change(self):
        """Draw between equal teams should result in minimal change."""
        tracker = EloTracker()
        
        tracker.process_match(
            home_team='TeamA',
            away_team='TeamB',
            fthg=1, ftag=1,
            date='2025-08-15',
            season='2526',
            league='test'
        )
        
        # Both started at 1500, draw should result in small changes
        # Home team has advantage so expected to win, draw hurts them slightly
        assert abs(tracker.get_rating('TeamA') - 1500) < 20
        assert abs(tracker.get_rating('TeamB') - 1500) < 20
    
    def test_match_counts_increment(self):
        """Match counts should increment for both teams."""
        tracker = EloTracker()
        
        tracker.process_match(
            home_team='TeamA',
            away_team='TeamB',
            fthg=1, ftag=0,
            date='2025-08-15',
            season='2526',
            league='test'
        )
        
        assert tracker.match_counts['TeamA'] == 1
        assert tracker.match_counts['TeamB'] == 1
    
    def test_history_records_match(self):
        """History should record the match with before/after ratings."""
        tracker = EloTracker()
        
        tracker.process_match(
            home_team='TeamA',
            away_team='TeamB',
            fthg=2, ftag=1,
            date='2025-08-15',
            season='2526',
            league='test'
        )
        
        assert len(tracker.history) == 1
        record = tracker.history[0]
        assert record['HomeTeam'] == 'TeamA'
        assert record['AwayTeam'] == 'TeamB'
        assert record['HomeRating_Before'] == 1500
        assert record['AwayRating_Before'] == 1500
        assert record['HomeRating_After'] > 1500
    
    def test_margin_multiplier_single_goal(self):
        """Single goal margin should have multiplier of 1."""
        tracker = EloTracker()
        assert tracker._get_margin_multiplier(1) == 1.0
    
    def test_margin_multiplier_two_goals(self):
        """Two goal margin should have multiplier of 1.5."""
        tracker = EloTracker()
        assert tracker._get_margin_multiplier(2) == 1.5
    
    def test_margin_multiplier_large_margin(self):
        """Large margins should have diminishing returns."""
        tracker = EloTracker()
        # Formula: (11 + diff) / 8
        assert tracker._get_margin_multiplier(5) == (11 + 5) / 8


class TestEloTrackerFromDb:
    """Tests for loading EloTracker from database."""
    
    def test_from_db_creates_tracker_with_ratings(self):
        """from_db should create tracker with loaded ratings."""
        with patch('src.database.get_elo_ratings') as mock_get:
            mock_get.return_value = pd.DataFrame([
                {'team': 'Arsenal', 'elo_rating': 1650.5, 'matches_played': 50},
                {'team': 'Chelsea', 'elo_rating': 1580.0, 'matches_played': 45},
            ])
            
            tracker = EloTracker.from_db()
            
            assert tracker.ratings['Arsenal'] == 1650.5
            assert tracker.ratings['Chelsea'] == 1580.0
            assert tracker.match_counts['Arsenal'] == 50
    
    def test_from_db_handles_empty_database(self):
        """from_db should handle empty database gracefully."""
        with patch('src.database.get_elo_ratings') as mock_get:
            mock_get.return_value = pd.DataFrame()
            
            tracker = EloTracker.from_db()
            
            assert len(tracker.ratings) == 0


class TestProcessNewMatches:
    """Tests for processing new matches."""
    
    def test_process_new_matches_updates_ratings(self):
        """Should process matches and update ratings."""
        tracker = EloTracker()
        tracker.ratings['TeamA'] = 1500
        tracker.ratings['TeamB'] = 1500
        
        df = pd.DataFrame([{
            'Date': '2025-08-15',
            'HomeTeam': 'TeamA',
            'AwayTeam': 'TeamB',
            'FTHG': 2,
            'FTAG': 0,
            'Season': '2526',
            'League': 'test'
        }])
        
        count = tracker.process_new_matches(df)
        
        assert count == 1
        assert tracker.get_rating('TeamA') > 1500
    
    def test_process_new_matches_handles_empty_df(self):
        """Should handle empty DataFrame gracefully."""
        tracker = EloTracker()
        
        df = pd.DataFrame()
        count = tracker.process_new_matches(df)
        
        assert count == 0
    
    def test_process_new_matches_handles_column_variations(self):
        """Should handle both lowercase and uppercase column names."""
        tracker = EloTracker()
        
        # Uppercase columns (from CSV)
        df = pd.DataFrame([{
            'Date': '2025-08-15',
            'HomeTeam': 'TeamA',
            'AwayTeam': 'TeamB',
            'FTHG': 1,
            'FTAG': 1,
            'Season': '2526',
            'League': 'test'
        }])
        
        count = tracker.process_new_matches(df)
        assert count == 1


class TestRunIncrementalElo:
    """Tests for run_incremental_elo function."""
    
    def test_run_incremental_elo_no_new_matches(self):
        """Should handle case with no new matches."""
        with patch('src.database.get_elo_ratings') as mock_ratings, \
             patch('src.database.get_raw_matches') as mock_matches, \
             patch('src.database.get_last_processed_match_date') as mock_date:
            
            mock_ratings.return_value = pd.DataFrame([
                {'team': 'Arsenal', 'elo_rating': 1600, 'matches_played': 10}
            ])
            mock_date.return_value = '2025-12-04'
            mock_matches.return_value = pd.DataFrame()  # No new matches
            
            from src.analysis.elo import run_incremental_elo
            run_incremental_elo()
            
            # Should complete without error
