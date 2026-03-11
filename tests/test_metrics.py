"""
Unit tests for financial metric calculations.

Tests PEG ratio calculations and other key financial indicators.
Based on original.py reference implementation.

Test Coverage:
- GAAP PEG: CAGR calculation, edge cases (negative income, missing data)
- Forward PEG: Growth capping at 60%, dampening formula for info sources
- Star ratings: All metric types with proper thresholds
- compute_metrics: Complete metrics computation pipeline
"""

import pytest
import pandas as pd
from modules.metrics import (
    calculate_gaap_peg,
    calculate_forward_peg,
    get_peg_values,
    get_star_rating,
    compute_metrics,
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
    
    def test_nan_values_in_financials(self):
        """Test with NaN values should be handled correctly."""
        info = {
            'trailingPE': 20.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [float('nan')],
            '2022': [600],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        # After dropna, only 2 values remain (1000 and 600), so should work
        assert result is not None
    
    def test_zero_trailingpe(self):
        """Test with zero trailingPE should return None."""
        info = {
            'trailingPE': 0.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_negative_trailingpe(self):
        """Test with negative trailingPE should return None."""
        info = {
            'trailingPE': -5.0,
        }
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        assert result is None
    
    def test_longer_history(self):
        """Test with longer history (5 years) for CAGR calculation."""
        info = {
            'trailingPE': 25.0,
        }
        # 5 years of data: from 400 to 1000
        financials = pd.DataFrame({
            '2024': [1000],
            '2023': [800],
            '2022': [640],
            '2021': [512],
            '2020': [400],
        }, index=['Net Income'])
        
        result = calculate_gaap_peg(info, financials)
        # CAGR: (1000/400)^(1/4) - 1 = 0.257
        # Growth% = 25.7%
        # PEG = 25 / 25.7 = ~0.973
        assert result is not None
        assert abs(result - 0.973) < 0.01


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
    
    def test_fallback_to_ee2y(self):
        """Test fallback to EE-2Y (earnings_estimate 2-year blend)."""
        info = {
            'forwardPE': 18.0,
        }
        growth_estimates = {
            'growth_2y': 0.15,  # 15% growth
            'source': 'EE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # PEG = 18 / 15 = 1.2
        assert abs(peg_value - 1.2) < 0.01
        assert growth_used == 0.15
        assert source == 'EE-2Y'
    
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
    
    def test_dampening_exact_50_cap(self):
        """Test dampening when result would exceed 50%."""
        info = {
            'forwardPE': 25.0,
        }
        # Growth that after dampening exceeds 50% should be capped
        growth_estimates = {
            'growth_1y': 1.5,  # 150% - will exceed 50% cap after dampening
            'source': 'info-eGr',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # Dampening: base=30%, excess=(150-30)*0.2=24%, total=54% -> capped at 50%
        assert abs(growth_used - 0.50) < 0.01
    
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
    
    def test_zero_forwardpe(self):
        """Test with zero forwardPE should return None."""
        info = {
            'forwardPE': 0.0,
        }
        growth_estimates = {
            'growth_2y': 0.10,
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        assert peg_value is None
    
    def test_negative_forwardpe(self):
        """Test with negative forwardPE should return None."""
        info = {
            'forwardPE': -5.0,
        }
        growth_estimates = {
            'growth_2y': 0.10,
            'source': 'GE-2Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        assert peg_value is None
    
    def test_ge_source_fallback(self):
        """Test GE source fallback when no 2-year estimate."""
        info = {
            'forwardPE': 16.0,
        }
        growth_estimates = {
            'growth_1y': 0.08,  # 8% growth
            'source': 'GE-1Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # PEG = 16 / 8 = 2.0 (no dampening for GE sources)
        assert abs(peg_value - 2.0) < 0.01
        assert growth_used == 0.08
    
    def test_ee_source_fallback(self):
        """Test EE source fallback when no 2-year estimate."""
        info = {
            'forwardPE': 16.0,
        }
        growth_estimates = {
            'growth_1y': 0.08,  # 8% growth
            'source': 'EE-1Y',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # PEG = 16 / 8 = 2.0 (no dampening for EE sources)
        assert abs(peg_value - 2.0) < 0.01
        assert growth_used == 0.08
    
    def test_info_source_with_low_growth(self):
        """Test info source with low growth (under 30%, no dampening needed)."""
        info = {
            'forwardPE': 20.0,
        }
        growth_estimates = {
            'growth_1y': 0.25,  # 25% - under 30%, no dampening
            'source': 'info-eGr',
        }
        peg_value, growth_used, source = calculate_forward_peg(info, growth_estimates)
        # No dampening needed: base=25%, excess=0, total=25%
        assert abs(growth_used - 0.25) < 0.01
        assert abs(peg_value - 0.8) < 0.01


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
    
    def test_negative_forward_peg_filtered(self):
        """Test that negative Forward PEG values are filtered out."""
        info = {
            'forwardPE': -10.0,
        }
        financials = None
        growth_estimates = {
            'growth_2y': 0.10,
            'source': 'GE-2Y',
        }
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        # Negative PEG indicates no profit situation (invalid ratio)
        assert fwd_peg is None
    
    def test_boundary_forward_peg(self):
        """Test Forward PEG at boundary value of 50."""
        info = {
            'forwardPE': 50.0,
        }
        financials = None
        growth_estimates = {
            'growth_2y': 1.0,  # 100% growth -> PEG = 50/100 = 0.5 (capped at 60%)
            'source': 'GE-2Y',
        }
        
        fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
            info, financials, growth_estimates
        )
        # Growth capped at 60%, PEG = 50/60 = ~0.833 (under 50 threshold)
        assert fwd_peg is not None
        assert abs(fwd_peg - 0.833) < 0.01


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
    
    def test_nan_value_zero_stars(self):
        """Test NaN value gets 0 stars."""
        result = get_star_rating(float('nan'), [0.1, 0.2, 0.3, 0.4])
        assert result == 0
    
    def test_exact_threshold_value(self):
        """Test value exactly at threshold gets appropriate stars."""
        # Value = 0.2 should get 3 stars (>=0.1 and >=0.2)
        result = get_star_rating(0.2, [0.1, 0.2, 0.3, 0.4])
        assert result == 3
    
    def test_gp_a_thresholds(self):
        """Test GP/A star rating with actual thresholds."""
        # GP/A >= 0.4 gets 5 stars
        result = get_star_rating(0.45, [0.1, 0.2, 0.3, 0.4])
        assert result == 5
        
        # GP/A between 0.3 and 0.4 gets 4 stars
        result = get_star_rating(0.35, [0.1, 0.2, 0.3, 0.4])
        assert result == 4
    
    def test_roe_thresholds(self):
        """Test ROE star rating with actual thresholds."""
        # ROE >= 0.30 gets 5 stars
        result = get_star_rating(0.35, [0.05, 0.10, 0.20, 0.30], penalize_negative=True)
        assert result == 5
    
    def test_pb_thresholds(self):
        """Test P/B star rating with reverse thresholds."""
        # P/B <= 5 gets 5 stars (lower is better)
        result = get_star_rating(3.0, [40.0, 20.0, 10.0, 5.0], reverse=True, penalize_negative=True)
        assert result == 5
    
    def test_fwd_peg_thresholds(self):
        """Test Forward PEG star rating with reverse thresholds."""
        # Fwd PEG <= 1.0 gets 5 stars (lower is better)
        result = get_star_rating(0.8, [2.5, 2.0, 1.5, 1.0], reverse=True)
        assert result == 5
    
    def test_momentum_thresholds(self):
        """Test Momentum star rating with actual thresholds."""
        # Perf >= 0.50 gets 5 stars
        result = get_star_rating(0.60, [0.0, 0.10, 0.25, 0.50])
        assert result == 5
    
    def test_negative_pb_not_penalized(self):
        """Test negative P/B gets penalized."""
        result = get_star_rating(-2.0, [40.0, 20.0, 10.0, 5.0], reverse=True, penalize_negative=True)
        assert result == 1
    
    def test_zero_value(self):
        """Test zero value gets appropriate stars."""
        # Zero is >= all negative thresholds but < positive ones
        result = get_star_rating(0.0, [0.1, 0.2, 0.3, 0.4])
        assert result == 1
    
    def test_very_high_value(self):
        """Test very high value still capped at 5 stars."""
        result = get_star_rating(100.0, [0.1, 0.2, 0.3, 0.4])
        assert result == 5
    
    def test_very_low_reverse_value(self):
        """Test very low value with reverse=True still capped at 5 stars."""
        result = get_star_rating(0.1, [40.0, 20.0, 10.0, 5.0], reverse=True)
        assert result == 5


class TestComputeMetrics:
    """Tests for complete metrics computation pipeline."""
    
    def test_all_metrics_computed(self):
        """Test that all expected metrics are computed and returned."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
            'trailingPE': 20.0,
            'forwardPE': 15.0,
            'returnOnEquity': 0.25,
            'priceToBook': 8.0,
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500, 1000, 200],
        }, index=['Gross Profit', 'Total Revenue', 'Net Income'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {
            'growth_2y': 0.15,
            'source': 'GE-2Y',
        }
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Check all expected keys are present
        assert 'symbol' in result
        assert 'name' in result
        assert 'gp_a' in result
        assert 'gross_margin' in result
        assert 'roe' in result
        assert 'pb' in result
        assert 'fwd_peg' in result
        assert 'gaap_peg' in result
        assert 'growth_used' in result
        assert 'peg_source' in result
        assert 'asset_growth' in result
        assert 's_gpa' in result
        assert 's_roe' in result
        assert 's_pb' in result
        assert 's_fwd_peg' in result
        assert 's_mom' in result
    
    def test_gp_a_calculation(self):
        """Test GP/A calculation."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # GP/A = 500 / 2000 = 0.25
        assert abs(result['gp_a'] - 0.25) < 0.01
    
    def test_gross_margin_calculation(self):
        """Test Gross Margin calculation."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500, 1000],
        }, index=['Gross Profit', 'Total Revenue'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Gross Margin = 500 / 1000 = 0.50
        assert abs(result['gross_margin'] - 0.50) < 0.01
    
    def test_negative_pb_handled(self):
        """Test that negative P/B is set to None."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
            'priceToBook': -5.0,
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Negative P/B should be set to None
        assert result['pb'] is None
    
    def test_roe_adjusted_for_extreme_pb(self):
        """Test that ROE is adjusted when pb > 50 and roe > 1.0."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
            'returnOnEquity': 2.0,  # Very high
            'priceToBook': 60.0,  # Very high
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # ROE should still be present but s_roe should reflect adjustment
        assert result['roe'] == 2.0
        # Star rating for adjusted ROE (None) should be 0
        assert result['s_roe'] == 0
    
    def test_missing_financials(self):
        """Test with missing financials."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, None, balance_sheet, None, None, growth_estimates
        )
        
        # GP/A and gross_margin should be None
        assert result['gp_a'] is None
        assert result['gross_margin'] is None
    
    def test_missing_balance_sheet(self):
        """Test with missing balance sheet."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, None, None, None, growth_estimates
        )
        
        # GP/A should be None (no assets)
        assert result['gp_a'] is None
    
    def test_star_ratings_computed(self):
        """Test that star ratings are computed correctly."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
            'returnOnEquity': 0.35,  # High ROE
            'priceToBook': 4.0,  # Low P/B (good)
            'forwardPE': 12.0,
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [800, 1000],
        }, index=['Gross Profit', 'Total Revenue'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {
            'growth_2y': 0.15,
            'source': 'GE-2Y',
        }
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # GP/A = 800/2000 = 0.4 -> should get 5 stars (>=0.4)
        assert result['s_gpa'] == 5
        
        # ROE = 0.35 -> should get 5 stars (>=0.30)
        assert result['s_roe'] == 5
        
        # P/B = 4.0 -> should get 5 stars (<=5.0, reverse=True)
        assert result['s_pb'] == 5
    
    def test_company_name_from_longname(self):
        """Test company name fallback to longName."""
        info = {
            'symbol': 'TEST',
            'longName': 'Long Name Company Inc.',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Should use longName when shortName is missing
        assert result['name'] == 'Long Name Company Inc.'
    
    def test_empty_company_name(self):
        """Test empty company name when both names are missing."""
        info = {
            'symbol': 'TEST',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Should be empty string when both names are missing
        assert result['name'] == ''
    
    def test_zero_revenue(self):
        """Test gross margin with zero revenue."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500, 0],  # Zero revenue
        }, index=['Gross Profit', 'Total Revenue'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # Gross margin should be None (division by zero)
        assert result['gross_margin'] is None
    
    def test_zero_assets(self):
        """Test GP/A with zero assets."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [0],  # Zero assets
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, None, None, growth_estimates
        )
        
        # GP/A should be None (division by zero)
        assert result['gp_a'] is None
    
    def test_performance_values_preserved(self):
        """Test that performance values are preserved in output."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        result = compute_metrics(
            info, financials, balance_sheet, 0.15, 0.30, growth_estimates
        )
        
        # Performance values should be preserved
        assert abs(result['perf_6m'] - 0.15) < 0.01
        assert abs(result['perf_12m'] - 0.30) < 0.01
    
    def test_momentum_star_rating(self):
        """Test momentum star rating calculation."""
        info = {
            'symbol': 'TEST',
            'shortName': 'Test Company',
        }
        # Financials with years as columns, metric names as index
        financials = pd.DataFrame({
            '2024': [500],
        }, index=['Gross Profit'])
        balance_sheet = pd.DataFrame({
            '2024': [2000],
        }, index=['Total Assets'])
        growth_estimates = {}
        
        # High momentum (>=50%) should get 5 stars
        result = compute_metrics(
            info, financials, balance_sheet, None, 0.60, growth_estimates
        )
        assert result['s_mom'] == 5
        
        # Low momentum (<0%) should get 1 star
        result = compute_metrics(
            info, financials, balance_sheet, None, -0.10, growth_estimates
        )
        assert result['s_mom'] == 1
