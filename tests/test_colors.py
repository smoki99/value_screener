"""
Tests for colors module.

Tests ANSI color codes and colorization helpers.
"""

import pytest
from modules.colors import (
    Color,
    colorize_peg,
    colorize_gm,
    colorize_gpa,
    colorize_roe,
    colorize_pb,
    colorize_decile,
    colorize_nm_rank,
    colorize_asset_growth,
    peg_zone
)


class TestColorClass:
    """Test suite for Color class."""

    def test_color_codes_defined(self):
        """Test that all color codes are defined."""
        assert hasattr(Color, 'RED')
        assert hasattr(Color, 'GREEN')
        assert hasattr(Color, 'YELLOW')
        assert hasattr(Color, 'RESET')
        assert hasattr(Color, 'BOLD')

    def test_color_codes_are_strings(self):
        """Test that color codes are strings."""
        assert isinstance(Color.RED, str)
        assert isinstance(Color.GREEN, str)
        assert isinstance(Color.YELLOW, str)
        assert isinstance(Color.RESET, str)
        assert isinstance(Color.BOLD, str)

    def test_color_codes_contain_ansi_escape(self):
        """Test that color codes contain ANSI escape sequences."""
        assert '\033[' in Color.RED
        assert '\033[' in Color.GREEN
        assert '\033[' in Color.YELLOW
        assert '\033[0m' == Color.RESET


class TestColorizePeg:
    """Test suite for colorize_peg function."""

    def test_colorize_peg_none_value(self):
        """Test that None value returns original string."""
        result = colorize_peg(None, "N/A")
        assert result == "N/A"

    def test_colorize_peg_good_value(self):
        """Test that good PEG (<=1.0) is green."""
        result = colorize_peg(0.8, "0.80")
        assert Color.GREEN in result
        assert Color.RESET in result

    def test_colorize_peg_fair_value(self):
        """Test that fair PEG (1.0-1.5) is yellow."""
        result = colorize_peg(1.2, "1.20")
        assert Color.YELLOW in result
        assert Color.RESET in result

    def test_colorize_peg_bad_value(self):
        """Test that bad PEG (>1.5) is red."""
        result = colorize_peg(2.0, "2.00")
        assert Color.RED in result
        assert Color.RESET in result

    def test_colorize_peg_boundary_values(self):
        """Test boundary values for PEG zones."""
        # Exactly 1.0 should be green
        result = colorize_peg(1.0, "1.00")
        assert Color.GREEN in result
        
        # Exactly 1.5 should be yellow
        result = colorize_peg(1.5, "1.50")
        assert Color.YELLOW in result


class TestColorizeGm:
    """Test suite for colorize_gm function."""

    def test_colorize_gm_none_value(self):
        """Test that None value returns original string."""
        result = colorize_gm(None, "N/A")
        assert result == "N/A"

    def test_colorize_gm_good_value(self):
        """Test that good gross margin (>=0.50) is green."""
        result = colorize_gm(0.60, "60%")
        assert Color.GREEN in result

    def test_colorize_gm_fair_value(self):
        """Test that fair gross margin (0.30-0.50) is yellow."""
        result = colorize_gm(0.40, "40%")
        assert Color.YELLOW in result

    def test_colorize_gm_bad_value(self):
        """Test that bad gross margin (<0.30) is red."""
        result = colorize_gm(0.20, "20%")
        assert Color.RED in result


class TestColorizeGpa:
    """Test suite for colorize_gpa function."""

    def test_colorize_gpa_none_value(self):
        """Test that None value returns original string."""
        result = colorize_gpa(None, "N/A")
        assert result == "N/A"

    def test_colorize_gpa_good_value(self):
        """Test that good GP/A (>=0.30) is green."""
        result = colorize_gpa(0.40, "0.40")
        assert Color.GREEN in result

    def test_colorize_gpa_fair_value(self):
        """Test that fair GP/A (0.15-0.30) is yellow."""
        result = colorize_gpa(0.20, "0.20")
        assert Color.YELLOW in result

    def test_colorize_gpa_bad_value(self):
        """Test that bad GP/A (<0.15) is red."""
        result = colorize_gpa(0.10, "0.10")
        assert Color.RED in result


class TestColorizeRoe:
    """Test suite for colorize_roe function."""

    def test_colorize_roe_none_value(self):
        """Test that None value returns original string."""
        result = colorize_roe(None, "N/A")
        assert result == "N/A"

    def test_colorize_roe_good_value(self):
        """Test that good ROE (>=0.20) is green."""
        result = colorize_roe(0.30, "30%")
        assert Color.GREEN in result

    def test_colorize_roe_fair_value(self):
        """Test that fair ROE (0.10-0.20) is yellow."""
        result = colorize_roe(0.15, "15%")
        assert Color.YELLOW in result

    def test_colorize_roe_bad_value(self):
        """Test that bad ROE (<0.10) is red."""
        result = colorize_roe(0.05, "5%")
        assert Color.RED in result


class TestColorizePb:
    """Test suite for colorize_pb function."""

    def test_colorize_pb_none_value(self):
        """Test that None value returns original string."""
        result = colorize_pb(None, "N/A")
        assert result == "N/A"

    def test_colorize_pb_good_value(self):
        """Test that good P/B (<=5.0) is green."""
        result = colorize_pb(3.0, "3.0")
        assert Color.GREEN in result

    def test_colorize_pb_fair_value(self):
        """Test that fair P/B (5.0-15.0) is yellow."""
        result = colorize_pb(10.0, "10.0")
        assert Color.YELLOW in result

    def test_colorize_pb_bad_value(self):
        """Test that bad P/B (>15.0) is red."""
        result = colorize_pb(20.0, "20.0")
        assert Color.RED in result


class TestColorizeDecile:
    """Test suite for colorize_decile function."""

    def test_colorize_decile_none_value(self):
        """Test that None value returns original string."""
        result = colorize_decile(None, "N/A")
        assert result == "N/A"

    def test_colorize_decile_good_value(self):
        """Test that good decile (>=8) is green."""
        result = colorize_decile(9, "9")
        assert Color.GREEN in result

    def test_colorize_decile_fair_value(self):
        """Test that fair decile (4-8) is yellow."""
        result = colorize_decile(6, "6")
        assert Color.YELLOW in result

    def test_colorize_decile_bad_value(self):
        """Test that bad decile (<4) is red."""
        result = colorize_decile(2, "2")
        assert Color.RED in result


class TestColorizeNmRank:
    """Test suite for colorize_nm_rank function."""

    def test_colorize_nm_rank_none_value(self):
        """Test that None value returns original string."""
        result = colorize_nm_rank(None, "N/A")
        assert result == "N/A"

    def test_colorize_nm_rank_good_value(self):
        """Test that good NM rank (>=16) is green."""
        result = colorize_nm_rank(20, "20")
        assert Color.GREEN in result

    def test_colorize_nm_rank_fair_value(self):
        """Test that fair NM rank (10-16) is yellow."""
        result = colorize_nm_rank(13, "13")
        assert Color.YELLOW in result

    def test_colorize_nm_rank_bad_value(self):
        """Test that bad NM rank (<10) is red."""
        result = colorize_nm_rank(5, "5")
        assert Color.RED in result


class TestColorizeAssetGrowth:
    """Test suite for colorize_asset_growth function."""

    def test_colorize_asset_growth_none_value(self):
        """Test that None value returns original string."""
        result = colorize_asset_growth(None, "N/A")
        assert result == "N/A"

    def test_colorize_asset_growth_good_value(self):
        """Test that good asset growth (<=0.10) is green."""
        result = colorize_asset_growth(0.05, "5%")
        assert Color.GREEN in result

    def test_colorize_asset_growth_fair_value(self):
        """Test that fair asset growth (0.10-0.25) is yellow."""
        result = colorize_asset_growth(0.18, "18%")
        assert Color.YELLOW in result

    def test_colorize_asset_growth_bad_value(self):
        """Test that bad asset growth (>0.25) is red."""
        result = colorize_asset_growth(0.30, "30%")
        assert Color.RED in result


class TestPegZone:
    """Test suite for peg_zone function."""

    def test_peg_zone_none_value(self):
        """Test that None value returns empty string."""
        result = peg_zone(None)
        assert result == ""

    def test_peg_zone_gunstig(self):
        """Test that good PEG (<=1.0) returns GÜNSTIG with green emoji."""
        result = peg_zone(0.8)
        assert "🟢GÜNSTIG" in result

    def test_peg_zone_fair(self):
        """Test that fair PEG (1.0-1.5) returns FAIR with yellow emoji."""
        result = peg_zone(1.2)
        assert "🟡FAIR" in result

    def test_peg_zone_teuer(self):
        """Test that bad PEG (>1.5) returns TEUER with red emoji."""
        result = peg_zone(2.0)
        assert "🔴TEUER" in result

    def test_peg_zone_boundary_values(self):
        """Test boundary values for PEG zones."""
        # Exactly 1.0 should be GÜNSTIG
        result = peg_zone(1.0)
        assert "🟢GÜNSTIG" in result
        
        # Exactly 1.5 should be FAIR
        result = peg_zone(1.5)
        assert "🟡FAIR" in result