"""
Tests for cache module.

Tests ticker list caching with SQLite storage and timestamp validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json
from datetime import datetime, timedelta

# Import the actual functions from the module
from modules.cache import (
    init_db,
    is_cache_valid,
    get_cached_tickers,
    save_tickers_to_cache,
    CACHE_MAX_AGE_HOURS
)


class TestIsCacheValid:
    """Test suite for is_cache_valid function."""

    def test_none_timestamp(self):
        """Test that None timestamp returns False."""
        result = is_cache_valid(None)
        assert result is False

    def test_empty_string(self):
        """Test that empty string returns False."""
        result = is_cache_valid("")
        assert result is False

    def test_recent_timestamp(self):
        """Test that recent timestamp returns True."""
        recent_time = (datetime.now() - timedelta(hours=1)).isoformat()
        result = is_cache_valid(recent_time)
        assert result is True

    def test_expired_timestamp(self):
        """Test that expired timestamp returns False."""
        old_time = (datetime.now() - timedelta(hours=CACHE_MAX_AGE_HOURS + 1)).isoformat()
        result = is_cache_valid(old_time)
        assert result is False

    def test_custom_max_age(self):
        """Test that custom max age hours works."""
        recent_time = (datetime.now() - timedelta(hours=5)).isoformat()
        # With default 24h, this should be valid
        result = is_cache_valid(recent_time)
        assert result is True
        # With 1h max age, this should be invalid
        result = is_cache_valid(recent_time, max_age_hours=1)
        assert result is False


class TestInitDb:
    """Test suite for init_db function."""

    @patch('modules.cache.sqlite3.connect')
    def test_creates_tables(self, mock_connect):
        """Test that database initialization creates required tables."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = init_db("test.db")
        
        assert result == mock_conn
        # Verify CREATE TABLE was called at least twice (stock_cache and ticker_cache)
        assert mock_conn.execute.call_count >= 2

    def test_returns_connection(self):
        """Test that init_db returns a connection object."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            conn = init_db(db_path)
            assert conn is not None
            # Verify tables exist
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [r[0] for r in result]
            assert 'stock_cache' in table_names
            assert 'ticker_cache' in table_names
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


class TestGetCachedTickers:
    """Test suite for get_cached_tickers function."""

    @patch('modules.cache.sqlite3.connect')
    def test_no_cache_returns_none(self, mock_connect):
        """Test that empty cache returns None."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        mock_connect.return_value = mock_conn
        
        result = get_cached_tickers(mock_conn)
        assert result is None

    @patch('modules.cache.sqlite3.connect')
    def test_valid_cache_returns_tickers(self, mock_connect):
        """Test that valid cache returns tickers."""
        mock_conn = MagicMock()
        recent_time = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_conn.execute.return_value.fetchone.return_value = (
            json.dumps(['AAPL', 'MSFT', 'GOOG']),
            recent_time
        )
        mock_connect.return_value = mock_conn
        
        result = get_cached_tickers(mock_conn)
        assert result is not None
        assert len(result) == 3
        assert 'AAPL' in result

    @patch('modules.cache.sqlite3.connect')
    def test_expired_cache_returns_none(self, mock_connect):
        """Test that expired cache returns None."""
        mock_conn = MagicMock()
        old_time = (datetime.now() - timedelta(hours=CACHE_MAX_AGE_HOURS + 1)).isoformat()
        mock_conn.execute.return_value.fetchone.return_value = (
            json.dumps(['AAPL', 'MSFT']),
            old_time
        )
        mock_connect.return_value = mock_conn
        
        result = get_cached_tickers(mock_conn)
        assert result is None


class TestSaveTickersToCache:
    """Test suite for save_tickers_to_cache function."""

    @patch('modules.cache.sqlite3.connect')
    def test_save_success(self, mock_connect):
        """Test that saving tickers works correctly."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        tickers = ['AAPL', 'MSFT', 'GOOG']
        save_tickers_to_cache(mock_conn, tickers)
        
        # Verify execute was called with correct data
        assert mock_conn.execute.called
        call_args = mock_conn.execute.call_args[0]
        assert len(call_args) == 2  # SQL + parameters tuple
        params = call_args[1]  # (tickers_json, fetched_at)
        saved_tickers = json.loads(params[0])
        assert saved_tickers == tickers

    @patch('modules.cache.sqlite3.connect')
    def test_save_with_timestamp(self, mock_connect):
        """Test that timestamp is saved with tickers."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        save_tickers_to_cache(mock_conn, ['AAPL'])
        
        call_args = mock_conn.execute.call_args[0]
        params = call_args[1]
        timestamp_str = params[1]
        # Verify it's a valid ISO format datetime string
        assert isinstance(timestamp_str, str)
        datetime.fromisoformat(timestamp_str)  # Should not raise


class TestCacheConfig:
    """Test suite for cache configuration."""

    def test_cache_max_age_hours_positive(self):
        """Test that CACHE_MAX_AGE_HOURS is a positive number."""
        assert CACHE_MAX_AGE_HOURS is not None
        assert isinstance(CACHE_MAX_AGE_HOURS, (int, float))
        assert CACHE_MAX_AGE_HOURS > 0
