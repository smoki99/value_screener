"""
Scoring and rating functions.

Implements Novy-Marx, multi-factor, and star rating systems.
"""

import pandas as pd
from typing import Any


def get_star_rating(value: float | None, thresholds: list[float], reverse: bool = False,
                    penalize_negative: bool = False) -> int:
    """Get star rating based on value and thresholds.
    
    Args:
        value: The metric value to rate
        thresholds: List of threshold values for each star level (4 thresholds for 5 stars)
        reverse: If True, lower values are better (e.g., P/B ratio)
        penalize_negative: If True, negative values get minimum rating
        
    Returns:
        Star rating 1-5, or 0 if not calculable
    """
    if value is None or pd.isna(value):
        return 0
    if penalize_negative and value < 0:
        return 1
    stars = 1
    for t in thresholds:
        if not reverse:
            if value >= t:
                stars += 1
        else:
            if value <= t:
                stars += 1
    return min(stars, 5)


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
        # Gross margin - relaxed threshold to 20%
        gm = info.get('grossMargins')
        if not gm or gm <= 0.20:
            return 0
        
        # GP/A (Gross Profit / Assets) - relaxed threshold to 5%
        gpa = info.get('profitMargins')
        if not gpa or gpa <= 0.05:
            return 0
        
        # ROE - relaxed threshold to 10% (was 20%)
        roe = info.get('returnOnEquity')
        if not roe or roe < 0.10:
            return 0
        
        # P/B (lower is better) - increased limit to 30
        pb = info.get('priceToBook')
        if pb and pb > 30.0:
            return 0
        
        # Asset growth control factor - relaxed threshold to 50%
        asset_growth = calculate_asset_growth(balance_sheet)
        if asset_growth and asset_growth > 0.50:
            return 0
        
        # All criteria met - assign score based on PEG (relaxed to 2.0)
        from .metrics import get_peg_values
        gaap_peg, _ = get_peg_values(info, financials)
        if gaap_peg and gaap_peg <= 2.0:
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


def score_novy_marx_weighted(s_gpa: int, s_pb: int, s_momentum: int) -> float:
    """Calculate Novy-Marx score using star ratings.
    
    Args:
        s_gpa: GP/A star rating (1-5)
        s_pb: P/B star rating (1-5)
        s_momentum: Momentum star rating (1-5)
        
    Returns:
        Weighted score 0-4.0
    """
    weights = {
        'gpa': (s_gpa, 0.40),
        'pb': (s_pb, 0.35),
        'momentum': (s_momentum, 0.25)
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    
    # Penalties
    if s_pb == 1:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 3 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)


def score_multi_factor_weighted(s_gpa: int, s_roe: int, s_pb: int, s_fpeg: int, s_momentum: int) -> float:
    """Calculate multi-factor score using star ratings.
    
    Args:
        s_gpa: GP/A star rating (1-5)
        s_roe: ROE star rating (1-5)
        s_pb: P/B star rating (1-5)
        s_fpeg: Forward PEG star rating (1-5)
        s_momentum: Momentum star rating (1-5)
        
    Returns:
        Weighted score 0-4.0
    """
    weights = {
        'gpa': (s_gpa, 0.25),
        'roe': (s_roe, 0.20),
        'pb': (s_pb, 0.20),
        'peg': (s_fpeg, 0.15),
        'momentum': (s_momentum, 0.20)
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    
    # Penalties
    if s_pb == 1:
        weighted_sum = min(weighted_sum, 3.0)
    if s_fpeg == 1 and s_gpa <= 3:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 5 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)


def get_quality_rating(nm_score: float, mf_score: float) -> str:
    """Get quality rating based on best(NM, MF) score.
    
    Args:
        nm_score: Novy-Marx weighted score
        mf_score: Multi-factor weighted score
        
    Returns:
        Quality rating string (★★★, ★★, ★, or —)
    """
    best = max(nm_score, mf_score)
    if best >= 4.5:
        return "★★★"
    elif best >= 3.5:
        return "★★"
    elif best >= 2.5:
        return "★"
    else:
        return "—"


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