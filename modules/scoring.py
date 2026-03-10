"""
Scoring and rating functions.

Implements Novy-Marx, multi-factor, and star rating systems.
"""

import pandas as pd
from typing import Any


def get_star_rating(peg: float | None) -> int:
    """Get star rating based on PEG ratio.
    
    Args:
        peg: PEG ratio value (lower is better)
        
    Returns:
        Star rating 1-5, or 0 if not calculable
    """
    if peg is None:
        return 0
    if peg <= 0.75:
        return 5
    elif peg <= 1.0:
        return 4
    elif peg <= 1.25:
        return 3
    elif peg <= 1.5:
        return 2
    else:
        return 1


def score_novy_marx(
    info: dict,
    financials: pd.DataFrame | None,
    balance_sheet: pd.DataFrame | None,
    perf_6m: float | None,
    perf_12m: float | None,
    growth_estimates: dict
) -> int:
    """Calculate Novy-Marx score.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame
        balance_sheet: Balance sheet DataFrame
        perf_6m: 6-month performance
        perf_12m: 12-month performance
        growth_estimates: Growth estimates dictionary
        
    Returns:
        NM score (higher is better)
    """
    from .fetcher import calculate_asset_growth
    
    try:
        # Gross margin
        gm = info.get('grossMargins')
        if not gm or gm <= 0.30:
            return 0
        
        # GP/A (Gross Profit / Assets)
        gpa = info.get('profitMargins')
        if not gpa or gpa <= 0.15:
            return 0
        
        # ROE
        roe = info.get('returnOnEquity')
        if not roe or roe < 0.20:
            return 0
        
        # P/B (lower is better)
        pb = info.get('priceToBook')
        if pb and pb > 15.0:
            return 0
        
        # Asset growth control factor
        asset_growth = calculate_asset_growth(balance_sheet)
        if asset_growth and asset_growth > 0.25:
            return 0
        
        # All criteria met - assign score based on PEG
        from .metrics import get_peg_values
        gaap_peg, _ = get_peg_values(info, financials)
        if gaap_peg and gaap_peg <= 1.5:
            return 20
        
    except (KeyError, TypeError):
        pass
    
    return 0


def score_multi_factor(
    info: dict,
    financials: pd.DataFrame | None,
    balance_sheet: pd.DataFrame | None,
    perf_6m: float | None,
    perf_12m: float | None,
    growth_estimates: dict
) -> int:
    """Calculate multi-factor score.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame
        balance_sheet: Balance sheet DataFrame
        perf_6m: 6-month performance
        perf_12m: 12-month performance
        growth_estimates: Growth estimates dictionary
        
    Returns:
        Multi-factor score (higher is better)
    """
    from .metrics import get_peg_values
    
    try:
        # PEG-based scoring
        gaap_peg, forward_peg = get_peg_values(info, financials)
        peg_score = 0
        if gaap_peg and gaap_peg <= 1.5:
            peg_score = 20 - int(gaap_peg * 10)
        
        # Growth score
        growth_rate = None
        if growth_estimates.get('growth_2y'):
            growth_rate = float(growth_estimates['growth_2y'])
        elif growth_estimates.get('growth_1y'):
            growth_rate = float(growth_estimates['growth_1y'])
        
        growth_score = 0
        if growth_rate and growth_rate > 0.30:
            growth_score = min(20, int(growth_rate * 50))
        
        # Performance score (6-month)
        perf_score = 0
        if perf_6m is not None:
            perf_score = max(0, min(10, int(perf_6m * 20)))
        
        return peg_score + growth_score + perf_score
    except (KeyError, TypeError):
        pass
    
    return 0


def stars_str(rating: int) -> str:
    """Convert star rating to string.
    
    Args:
        rating: Star rating 1-5 or 0
        
    Returns:
        String with star characters (e.g., '★★★★★')
    """
    if rating <= 0:
        return ''
    return '★' * min(5, max(1, rating))


def rebalancing_note() -> str:
    """Get quarterly rebalancing note.
    
    Returns:
        Note string about quarterly rebalancing
    """
    return "\nHinweis: Quartalsweise Rebalancierung empfohlen."