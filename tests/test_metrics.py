"""
Unit tests for financial metric calculations.

Tests PEG ratio calculations and other key financial indicators.
Based on original.py reference implementation.
"""

import pytest
import pandas as pd
from modules.metrics import (
    calculate_gaap_peg,
    calculate_forward_peg,
    get_peg_values,
    get_star_rating,
)


class TestCalculateGaapPeg:
    """Tests for GAAP PEG calculation using Net Income CAGR."""
    
    def test_valid_calculation(self):
        """Test with valid trailingPE and financials with Net Income."""
        info = {
            'trailingPE': 20.0,
        }
        # Create financials DataFrame with Net Income row
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
            '2022': [600],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        # CAGR from 600 to 1000 over 2 years: (1000/600)^(1/2) - 1 = 0.291
        # Growth% = 29.1%
        # PEG = 20 / 29.1 = ~0.687
        assert result is not None
        assert abs(result - 0.687) < 0.01
    
    def test_negative_oldest_income(self):
        """Test with negative oldest Net Income should return None."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [-500],  # Negative
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_missing_trailingpe(self):
        """Test with missing trailingPE should return None."""
        info = {}
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_missing_financials(self):
        """Test with missing financials should return None."""
        info = {
            'trailingPE': 20.0,
        }
        result = calculate_gaap_peg(info, None)
        assert result is None
    
    def test_empty_financials(self):
        """Test with empty financials should return None."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame()
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_single_year_financials(self):
        """Test with only one year of data should return None."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_zero_latest_income(self):
        """Test with zero latest Net Income should return None."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [0],
            '2023': [800],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_negative_growth(self):
        """Test with declining Net Income (negative growth) should return None."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [500],
            '2023': [1000],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None


class TestCalculateForwardPeg:
    """Tests for Forward PEG calculation with capping and dampening."""
    
    def test_valid_calculation_ge2y(self):
        """Test with valid forwardPE and GE-2Y growth estimate."""
        info = {
            'forwardPE': 15.0,
        }
        growth_estimates = {
            'growth_2y': 0.12,  # 12% growth
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # PEG = 15 / 12 = 1.25
        assert abs(peg_value - 1.25) < 0.01
        assert growth_used == 0.12
        assert source == 'GE-2Y'
    
    def test_growth_capped_at_60_percent(self):
        """Test that high growth rates are capped at 60%."""
        info = {
            'forwardPE': 30.0,
        }
        growth_estimates = {
            'growth_2y': 1.5,  # 150% - should be capped
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # Growth capped at 60%, PEG = 30 / 60 = 0.5
        assert abs(peg_value - 0.5) < 0.01
        assert growth_used == 0.60
    
    def test_fallback_to_ge1y(self):
        """Test fallback to GE-1Y when no 2-year estimate."""
        info = {
            'forwardPE': 20.0,
        }
        growth_estimates = {
            'growth_1y': 0.10,  # 10% growth
            'source': 'GE-1Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # PEG = 20 / 10 = 2.0
        assert abs(peg_value - 2.0) < 0.01
        assert growth_used == 0.10
        assert source == 'GE-1Y'
    
    def test_dampening_for_info_source(self):
        """Test dampening formula for info-based growth."""
        info = {
            'forwardPE': 25.0,
        }
        # High growth from info source should be dampened
        growth_estimates = {
            'growth_1y': 0.40,  # 40% - will be dampened
            'source': 'info-eGr',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # Dampening: base=30%, excess=(40-30)*0.2=2%, total=32%
        # PEG = 25 / 32 = ~0.781
        assert abs(growth_used - 0.32) < 0.01
        assert '1Y' in source
    
    def test_dampening_capped_at_50_percent(self):
        """Test that dampened growth is capped at 50%."""
        info = {
            'forwardPE': 25.0,
        }
        # Very high growth should be capped after dampening
        growth_estimates = {
            'growth_1y': 1.0,  # 100% - will be dampened and capped
            'source': 'info-eGr',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # Dampening: base=30%, excess=(100-30)*0.2=14%, total=44% (under 50% cap)
        assert abs(growth_used - 0.44) < 0.01
    
    def test_missing_forwardpe(self):
        """Test with missing forwardPE should return None."""
        info = {}
        growth_estimates = {
            'growth_2y': 0.10,
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        assert peg_value is None
        assert growth_used is None
        assert source == "N/A"
    
    def test_missing_growth_estimates(self):
        """Test with missing growth estimates should return None."""
        info = {
            'forwardPE': 15.0,
        }
        peg_value, growth_used, source = calculate_forward_peg(info, None)
        assert peg_value is None
        assert growth_used is None
        assert source == "N/A"
    
    def test_zero_growth(self):
        """Test with zero growth should return None."""
        info = {
            'forwardPE': 15.0,
        }
        growth_estimates = {
            'growth_2y': 0.0,
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        assert peg_value is None
    
    def test_negative_growth(self):
        """Test with negative growth should return None."""
        info = {
            'forwardPE': 15.0,
        }
        growth_estimates = {
            'growth_2y': -0.05,
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        assert peg_value is None


class TestGetPegValues:
    """Tests for getting both PEG values with source tracking."""
    
    def test_both_values_present(self):
        """Test when both GAAP and Forward PEG are calculable."""
        info = {
            'trailingPE': 20.0,
            'forwardPE': 15.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
            '2022': [600],
        }, index=['Net Income'])
        growth_estimates = {
            'growth_2y': 0.15,
            'source': 'GE-2Y',
        }
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        # Forward PEG: 15 / 15 = 1.0
        assert abs(fwd_peg - 1.0) < 0.01
        # GAAP PEG: ~0.687 (from CAGR)
        assert gaap_peg is not None
        assert growth_used == 0.15
        assert peg_source == 'GE-2Y'
    
    def test_only_gaap_present(self):
        """Test when only GAAP PEG is calculable."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
        }, index=['Net Income'])
        growth_estimates = None
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        assert fwd_peg is None
        assert gaap_peg is not None
    
    def test_only_forward_present(self):
        """Test when only Forward PEG is calculable."""
        info = {
            'forwardPE': 15.0,
        }
        financials = None
        growth_estimates = {
            'growth_2y': 0.10,
            'source': 'GE-2Y',
        }
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        assert fwd_peg == 1.5
        assert gaap_peg is None
    
    def test_neither_present(self):
        """Test when neither PEG is calculable."""
        info = {}
        financials = None
        growth_estimates = None
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        assert fwd_peg is None
        assert gaap_peg is None
    
    def test_extreme_forward_peg_filtered(self):
        """Test that extreme Forward PEG values (>50) are filtered out."""
        info = {
            'forwardPE': 100.0,
        }
        financials = None
        growth_estimates = {
            'growth_2y': 0.01,  # Very low growth -> high PEG
            'source': 'GE-2Y',
        }
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        # PEG would be 100/1 = 100, which is >50, so should be filtered
        assert fwd_peg is None


class TestGetStarRating:
    """Tests for star rating calculation."""
    
    def test_high_value_five_stars(self):
        """Test value above all thresholds gets 5 stars."""
        result = get_star_rating(0.5, [0.1, 0.2, 0.3, 0.4])
        assert result == 5
    
    def test_mid_value_three_stars(self):
        """Test value between thresholds gets appropriate stars."""
        result = get_star_rating(0.25, [0.1, 0.2, 0.3, 0.4])
        assert result == 3
    
    def test_low_value_one_star(self):
        """Test value below all thresholds gets 1 star."""
        result = get_star_rating(0.05, [0.1, 0.2, 0.3, 0.4])
        assert result == 1
    
    def test_none_value_zero_stars(self):
        """Test None value gets 0 stars."""
        result = get_star_rating(None, [0.1, 0.2, 0.3, 0.4])
        assert result == 0
    
    def test_reverse_thresholds(self):
        """Test reverse=True for metrics where lower is better."""
        # For P/B ratio: <=5 gets max stars
        result = get_star_rating(3.0, [40.0, 20.0, 10.0, 5.0], reverse=True)
        assert result == 5
    
    def test_penalize_negative(self):
        """Test penalize_negative=True gives 1 star for negative values."""
        result = get_star_rating(-0.1, [0.05, 0.10, 0.20, 0.30], penalize_negative=True)
        assert result == 1
    
    def test_positive_not_penalized(self):
        """Test positive values not affected by penalize_negative."""
        result = get_star_rating(0.5, [0.05, 0.10, 0.20, 0.30], penalize_negative=True)
        assert result == 5
