"""
Unit tests for financial metric calculations.

Tests PEG ratio calculations and other key financial indicators.
"""

import pytest
from modules.metrics import calculate_gaap_peg, calculate_forward_peg, get_peg_values


class TestCalculateGaapPeg:
    """Tests for GAAP PEG calculation."""
    
    def test_valid_calculation(self):
        """Test with valid trailingPE and earningsGrowth."""
        info = {
            'trailingPE': 20.0,
            'earningsGrowth': 0.10,  # 10% growth
        }
        result = calculate_gaap_peg(info)
        # PEG = PE / Growth% = 20 / 10 = 2.0
        assert result == 2.0
    
    def test_high_growth(self):
        """Test with high growth rate."""
        info = {
            'trailingPE': 30.0,
            'earningsGrowth': 0.15,  # 15% growth
        }
        result = calculate_gaap_peg(info)
        # PEG = 30 / 15 = 2.0
        assert result == 2.0
    
    def test_zero_growth(self):
        """Test with zero earningsGrowth should return None."""
        info = {
            'trailingPE': 20.0,
            'earningsGrowth': 0.0,
        }
        result = calculate_gaap_peg(info)
        assert result is None
    
    def test_negative_growth(self):
        """Test with negative earningsGrowth should return None."""
        info = {
            'trailingPE': 20.0,
            'earningsGrowth': -0.05,  # Negative growth
        }
        result = calculate_gaap_peg(info)
        assert result is None
    
    def test_missing_trailingpe(self):
        """Test with missing trailingPE should return None."""
        info = {
            'earningsGrowth': 0.10,
        }
        result = calculate_gaap_peg(info)
        assert result is None
    
    def test_missing_growth(self):
        """Test with missing earningsGrowth should return None."""
        info = {
            'trailingPE': 20.0,
        }
        result = calculate_gaap_peg(info)
        assert result is None
    
    def test_empty_info(self):
        """Test with empty dict should return None."""
        info = {}
        result = calculate_gaap_peg(info)
        assert result is None


class TestCalculateForwardPeg:
    """Tests for Forward PEG calculation."""
    
    def test_valid_calculation_with_growth_rate(self):
        """Test with valid forwardPE and growth_rate parameter."""
        info = {
            'forwardPE': 15.0,
        }
        result = calculate_forward_peg(info, growth_rate=0.12)  # 12% growth
        # PEG = 15 / 12 = 1.25
        assert result == 1.25
    
    def test_fallback_to_earningsgrowth(self):
        """Test fallback to earningsGrowth when no growth_rate provided."""
        info = {
            'forwardPE': 20.0,
            'earningsGrowth': 0.10,  # 10% growth
        }
        result = calculate_forward_peg(info)
        # PEG = 20 / 10 = 2.0
        assert result == 2.0
    
    def test_growth_rate_takes_precedence(self):
        """Test that provided growth_rate takes precedence over earningsGrowth."""
        info = {
            'forwardPE': 20.0,
            'earningsGrowth': 0.10,  # Would give PEG of 2.0
        }
        result = calculate_forward_peg(info, growth_rate=0.20)  # Should use this instead
        # PEG = 20 / 20 = 1.0 (using provided growth_rate)
        assert result == 1.0
    
    def test_zero_growth(self):
        """Test with zero growth should return None."""
        info = {
            'forwardPE': 15.0,
        }
        result = calculate_forward_peg(info, growth_rate=0.0)
        assert result is None
    
    def test_missing_forwardpe(self):
        """Test with missing forwardPE should return None."""
        info = {}
        result = calculate_forward_peg(info, growth_rate=0.10)
        assert result is None


class TestGetPegValues:
    """Tests for getting both PEG values."""
    
    def test_both_values_present(self):
        """Test when both GAAP and Forward PEG are calculable."""
        info = {
            'trailingPE': 20.0,
            'forwardPE': 15.0,
            'earningsGrowth': 0.10,  # 10% growth
        }
        gaap_peg, forward_peg = get_peg_values(info, None)
        assert gaap_peg == 2.0  # 20 / 10
        assert forward_peg == 1.5  # 15 / 10
    
    def test_only_gaap_present(self):
        """Test when only GAAP PEG is calculable."""
        info = {
            'trailingPE': 20.0,
            'earningsGrowth': 0.10,  # 10% growth
        }
        gaap_peg, forward_peg = get_peg_values(info, None)
        assert gaap_peg == 2.0
        assert forward_peg is None
    
    def test_only_forward_present(self):
        """Test when only Forward PEG is calculable."""
        info = {
            'forwardPE': 15.0,
            'earningsGrowth': 0.10,  # 10% growth
        }
        gaap_peg, forward_peg = get_peg_values(info, None)
        assert gaap_peg is None
        assert forward_peg == 1.5
    
    def test_neither_present(self):
        """Test when neither PEG is calculable."""
        info = {}
        gaap_peg, forward_peg = get_peg_values(info, None)
        assert gaap_peg is None
        assert forward_peg is None
