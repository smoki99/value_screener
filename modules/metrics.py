"""
Financial metric calculations.

Computes PEG ratios, growth rates, and other key financial indicators.
"""

import pandas as pd
from typing import Any


def calculate_gaap_peg(info: dict) -> float | None:
    """Calculate GAAP PEG ratio (P/E / Growth).
    
    Args:
        info: Stock info dictionary from yfinance
        
    Returns:
        GAAP PEG ratio or None if not calculable
    """
    try:
        pe = info.get('trailingPE')
        growth = info.get('earningsGrowth')
        # earningsGrowth is a decimal (e.g., 0.12 for 12%)
        # PEG = PE / Growth% where Growth% is the whole number
        if pe and growth and growth > 0:
            return float(pe) / (float(growth) * 100)
    except (KeyError, TypeError):
        pass
    return None


def calculate_forward_peg(info: dict, growth_rate: float | None = None) -> float | None:
    """Calculate Forward PEG ratio.
    
    Args:
        info: Stock info dictionary from yfinance
        growth_rate: Optional forward-looking growth rate as decimal (e.g., 0.12 for 12%)
        
    Returns:
        Forward PEG ratio or None if not calculable
    """
    try:
        forward_pe = info.get('forwardPE')
        # Use provided growth_rate first, fallback to earningsGrowth
        growth = growth_rate if growth_rate is not None else info.get('earningsGrowth')
        if forward_pe and growth and growth > 0:
            # Convert decimal growth rate (e.g., 0.12) to percentage (e.g., 12)
            # PEG = PE / Growth% where Growth% is the whole number
            return float(forward_pe) / (float(growth) * 100)
    except (KeyError, TypeError):
        pass
    return None


def get_peg_values(info: dict, financials: pd.DataFrame | None) -> tuple[float | None, float | None]:
    """Get both GAAP and Forward PEG values.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame (unused but kept for compatibility)
        
    Returns:
        Tuple of (gaap_peg, forward_peg)
    """
    gaap = calculate_gaap_peg(info)
    forward = calculate_forward_peg(info)
    return gaap, forward


def compute_metrics(
    info: dict,
    financials: pd.DataFrame | None,
    balance_sheet: pd.DataFrame | None,
    perf_6m: float | None,
    perf_12m: float | None,
    growth_estimates: dict
) -> dict:
    """Compute all key metrics for a stock.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame
        balance_sheet: Balance sheet DataFrame
        perf_6m: 6-month performance
        perf_12m: 12-month performance
        growth_estimates: Growth estimates dictionary
        
    Returns:
        Dictionary with all computed metrics
    """
    from .fetcher import calculate_asset_growth
    
    # Get PEG values
    gaap_peg, forward_peg = get_peg_values(info, financials)
    
    # Calculate growth rate (prefer 2-year blend, fallback to 1-year)
    growth_rate = None
    if growth_estimates.get('growth_2y'):
        growth_rate = float(growth_estimates['growth_2y'])
    elif growth_estimates.get('growth_1y'):
        growth_rate = float(growth_estimates['growth_1y'])
    
    # Calculate asset growth
    asset_growth = calculate_asset_growth(balance_sheet)
    
    return {
        'gaap_peg': gaap_peg,
        'forward_peg': forward_peg,
        'growth_rate': growth_rate,
        'asset_growth': asset_growth,
        'perf_6m': perf_6m,
        'perf_12m': perf_12m,
    }
