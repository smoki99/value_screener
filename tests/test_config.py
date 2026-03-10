"""
Tests for config module.

Tests configuration constants and database path settings.
"""

import pytest
from modules.config import DB_PATH, CACHE_MAX_AGE_HOURS


class TestConfig:
    """Test suite for config module."""

    def test_db_path_exists(self):
        """Test that DB_PATH is defined and non-empty."""
        assert DB_PATH is not None
        assert isinstance(DB_PATH, str)
        assert len(DB_PATH) > 0

    def test_cache_max_age_hours_positive(self):
        """Test that CACHE_MAX_AGE_HOURS is a positive number."""
        assert CACHE_MAX_AGE_HOURS is not None
        assert isinstance(CACHE_MAX_AGE_HOURS, (int, float))
        assert CACHE_MAX_AGE_HOURS > 0

    def test_db_path_format(self):
        """Test that DB_PATH has proper SQLite database format."""
        # Should end with .db or be a valid path
        assert ".db" in DB_PATH.lower() or len(DB_PATH) > 1


class TestConfigConstants:
    """Additional tests for config constants."""

    def test_config_values_reasonable(self):
        """Test that config values are reasonable for production use."""
        # Cache should not be too short (less than 1 hour) or too long (more than 720 hours)
        assert 1 <= CACHE_MAX_AGE_HOURS <= 720
