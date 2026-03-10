"""
Unit tests for scoring and rating functions.

Tests Novy-Marx, multi-factor, star ratings, and quality ratings.
"""

import pytest
from modules.scoring import (
    get_star_rating,
    score_novy_marx_weighted,
    score_multi_factor_weighted,
    get_quality_rating,
    stars_str
)


class TestGetStarRating:
    """Tests for generic star rating function."""
    
    def test_gp_a_thresholds(self):
        """Test GP/A thresholds [0.1, 0.2, 0.3, 0.4]."""
        # Value of 0.35 should get 4 stars (>= 0.1, >= 0.2, >= 0.3)
        result = get_star_rating(0.35, [0.1, 0.2, 0.3, 0.4])
        assert result == 4
        
        # Value of 0.45 should get 5 stars (>= all thresholds)
        result = get_star_rating(0.45, [0.1, 0.2, 0.3, 0.4])
        assert result == 5
        
        # Value of 0.05 should get 1 star (< all thresholds)
        result = get_star_rating(0.05, [0.1, 0.2, 0.3, 0.4])
        assert result == 1
    
    def test_pb_thresholds_reverse(self):
        """Test P/B thresholds (reverse) [40.0, 20.0, 10.0, 5.0]."""
        # Value of 8.0 should get 4 stars (<= 40, <= 20, <= 10)
        result = get_star_rating(8.0, [40.0, 20.0, 10.0, 5.0], reverse=True)
        assert result == 4
        
        # Value of 3.0 should get 5 stars (<= all thresholds)
        result = get_star_rating(3.0, [40.0, 20.0, 10.0, 5.0], reverse=True)
        assert result == 5
    
    def test_peg_thresholds_reverse(self):
        """Test PEG thresholds (reverse) [0.75, 1.0, 1.25, 1.5]."""
        # Value of 0.6 should get 5 stars
        result = get_star_rating(0.6, [0.75, 1.0, 1.25, 1.5], reverse=True)
        assert result == 5
        
        # Value of 1.3 should get 2 stars (<= 1.25 only)
        result = get_star_rating(1.3, [0.75, 1.0, 1.25, 1.5], reverse=True)
        assert result == 2
    
    def test_none_value(self):
        """Test with None value should return 0."""
        result = get_star_rating(None, [0.1, 0.2, 0.3, 0.4])
        assert result == 0
    
    def test_penalize_negative(self):
        """Test penalize_negative flag for momentum."""
        # Negative value should get minimum rating of 1
        result = get_star_rating(-0.1, [0.1, 0.2, 0.3, 0.4], penalize_negative=True)
        assert result == 1
    

class TestScoreNovyMarxWeighted:
    """Tests for weighted Novy-Marx scoring."""
    
    def test_all_stars_max(self):
        """Test all stars at max (4 each)."""
        result = score_novy_marx_weighted(4, 4, 4)
        assert result == 4.0
    
    def test_mixed_scores(self):
        """Test mixed scores."""
        # Expected: round((3 * 0.40 + 2 * 0.35 + 4 * 0.25), 1) = 2.9
        result = score_novy_marx_weighted(3, 2, 4)
        assert result == 2.9
    
    def test_pb_penalty(self):
        """Test P/B penalty when s_pb == 1."""
        # Should be capped at 3.0 due to penalty
        result = score_novy_marx_weighted(4, 1, 4)
        assert result <= 3.0
    
    def test_missing_factor(self):
        """Test with one missing factor (s_pb == 0)."""
        # Should apply -0.15 penalty for missing factor
        result = score_novy_marx_weighted(4, 0, 4)
        assert result < 4.0
    
    def test_too_few_active(self):
        """Test with too few active factors."""
        # Only one active factor should return 0
        result = score_novy_marx_weighted(4, 0, 0)
        assert result == 0
    

class TestScoreMultiFactorWeighted:
    """Tests for weighted multi-factor scoring."""
    
    def test_all_stars_max(self):
        """Test all stars at max (4 each)."""
        result = score_multi_factor_weighted(4, 4, 4, 4, 4)
        assert result == 4.0
    
    def test_mixed_scores(self):
        """Test mixed scores."""
        # Expected: round((3 * 0.25 + 4 * 0.20 + 2 * 0.20 + 3 * 0.15 + 4 * 0.20), 1) = 3.2
        result = score_multi_factor_weighted(3, 4, 2, 3, 4)
        assert result == 3.2
    
    def test_pb_penalty(self):
        """Test P/B penalty when s_pb == 1."""
        # Should be capped at 3.0 due to penalty
        result = score_multi_factor_weighted(4, 4, 1, 4, 4)
        assert result <= 3.0
    
    def test_fpeg_gpa_penalty(self):
        """Test FPEG/GPA penalty when s_fpeg == 1 and s_gpa <= 3."""
        # Should be capped at 3.0 due to penalty
        result = score_multi_factor_weighted(3, 4, 4, 1, 4)
        assert result <= 3.0
    
    def test_missing_factors(self):
        """Test with missing factors."""
        # Should apply -0.15 penalty per missing factor
        result = score_multi_factor_weighted(4, 4, 0, 0, 4)
        assert result < 4.0
    

class TestGetQualityRating:
    """Tests for quality rating function."""
    
    def test_triple_star(self):
        """Test triple star rating (best >= 4.5)."""
        assert get_quality_rating(4.5, 3.0) == "★★★"
        assert get_quality_rating(3.0, 4.5) == "★★★"
    
    def test_double_star(self):
        """Test double star rating (best >= 3.5)."""
        assert get_quality_rating(3.5, 2.0) == "★★"
        assert get_quality_rating(2.0, 3.5) == "★★"
    
    def test_single_star(self):
        """Test single star rating (best >= 2.5)."""
        assert get_quality_rating(2.5, 1.0) == "★"
        assert get_quality_rating(1.0, 2.5) == "★"
    
    def test_no_star(self):
        """Test no star rating (best < 2.5)."""
        assert get_quality_rating(2.0, 1.5) == "—"
        assert get_quality_rating(1.5, 2.0) == "—"
    

class TestStarsStr:
    """Tests for stars string conversion."""
    
    def test_five_stars(self):
        """Test five star rating."""
        result = stars_str(5)
        assert result == '★★★★★'
    
    def test_three_stars(self):
        """Test three star rating."""
        result = stars_str(3)
        assert result == '★★★'
    
    def test_zero_stars(self):
        """Test zero star rating should return empty string."""
        result = stars_str(0)
        assert result == ''
    
    def test_negative_stars(self):
        """Test negative star rating should return empty string."""
        result = stars_str(-1)
        assert result == ''
