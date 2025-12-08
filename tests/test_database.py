"""Tests for database functions."""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock


class TestGetRawMatches:
    """Tests for get_raw_matches function."""
    
    def test_returns_dataframe(self):
        """Should return a pandas DataFrame."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            
            mock_response = Mock()
            mock_response.data = [
                {'id': 1, 'home_team': 'Arsenal', 'away_team': 'Chelsea', 'date': '2025-08-15'}
            ]
            
            mock_client.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = mock_response
            
            from src.database import get_raw_matches
            result = get_raw_matches()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
    
    def test_filters_by_league(self):
        """Should filter by league when provided."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            
            mock_query = Mock()
            mock_client.table.return_value.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value.range.return_value.execute.return_value = Mock(data=[])
            
            from src.database import get_raw_matches
            get_raw_matches(league='premier_league')
            
            mock_query.eq.assert_called_with('league', 'premier_league')
    
    def test_filters_by_after_date(self):
        """Should filter by after_date when provided."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            
            mock_query = Mock()
            mock_client.table.return_value.select.return_value = mock_query
            mock_query.gt.return_value = mock_query
            mock_query.order.return_value.range.return_value.execute.return_value = Mock(data=[])
            
            from src.database import get_raw_matches
            get_raw_matches(after_date='2025-12-01')
            
            mock_query.gt.assert_called_with('date', '2025-12-01')


class TestGetMatchesForAnalysis:
    """Tests for get_matches_for_analysis function."""
    
    def test_renames_columns_correctly(self):
        """Should rename DB columns to analysis format."""
        with patch('src.database.get_raw_matches') as mock_get:
            mock_get.return_value = pd.DataFrame([{
                'date': '2025-08-15',
                'home_team': 'Arsenal',
                'away_team': 'Chelsea',
                'fthg': 2,
                'ftag': 1,
                'ftr': 'H'
            }])
            
            from src.database import get_matches_for_analysis
            result = get_matches_for_analysis('premier_league', '2526')
            
            assert 'HomeTeam' in result.columns
            assert 'AwayTeam' in result.columns
            assert 'FTHG' in result.columns
            assert 'FTAG' in result.columns
            assert result.iloc[0]['HomeTeam'] == 'Arsenal'
    
    def test_returns_empty_dataframe_when_no_data(self):
        """Should return empty DataFrame when no matches found."""
        with patch('src.database.get_raw_matches') as mock_get:
            mock_get.return_value = pd.DataFrame()
            
            from src.database import get_matches_for_analysis
            result = get_matches_for_analysis('premier_league', '9999')
            
            assert len(result) == 0


class TestUploadRawMatches:
    """Tests for upload_raw_matches function."""
    
    def test_converts_date_format(self):
        """Should convert DD/MM/YYYY to YYYY-MM-DD."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            mock_client.table.return_value.upsert.return_value.execute.return_value = Mock()
            
            df = pd.DataFrame([{
                'Date': '15/08/2025',
                'HomeTeam': 'Arsenal',
                'AwayTeam': 'Chelsea',
                'FTHG': 2,
                'FTAG': 1,
                'league': 'premier_league',
                'season': '2526'
            }])
            
            from src.database import upload_raw_matches
            upload_raw_matches(df)
            
            # Check the date was converted
            call_args = mock_client.table.return_value.upsert.call_args
            records = call_args[0][0]
            assert records[0]['date'] == '2025-08-15'


class TestGetLastProcessedMatchDate:
    """Tests for get_last_processed_match_date function."""
    
    def test_returns_date_when_exists(self):
        """Should return the most recent date."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
                data=[{'date': '2025-12-04'}]
            )
            
            from src.database import get_last_processed_match_date
            result = get_last_processed_match_date()
            
            assert result == '2025-12-04'
    
    def test_returns_none_when_empty(self):
        """Should return None when no matches processed."""
        with patch('src.database.get_db') as mock_db:
            mock_client = Mock()
            mock_db.return_value = mock_client
            mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
                data=[]
            )
            
            from src.database import get_last_processed_match_date
            result = get_last_processed_match_date()
            
            assert result is None
