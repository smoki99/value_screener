"""
Financial metric calculations.

Computes PEG ratios, growth rates, and other key financial indicators.
Based on original.py reference implementation.

Key Decisions:
- Two PEGs: GAAP (backward-looking) vs Forward (forward-looking)
- Analyst overoptimism handled by capping at 60% and dampening formula
- PEG < 0 = no profit situation, PEG > 50 = calculation issue
- GP/A is core Novy-Marx factor for predicting future returns
"""

import pandas as pd
from typing import Any


def calculate_gaap_peg(info: dict, financials: pd.DataFrame | None) -> float | None:
    """Calculate GAAP PEG ratio using historical Net Income CAGR.
    
    This is the BACKWARD-LOOKING PEG - uses actual historical performance
    to see how the company has grown in reality (not analyst estimates).
    
    Why CAGR? Smooths multi-year volatility for realistic growth rate.
    Single year changes can be noisy; geometric mean over multiple years
    gives a more stable picture of sustainable growth.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame with 'Net Income' row
        
    Returns:
        GAAP PEG ratio or None if not calculable
    """
    try:
        # Use trailing PE (historical) for backward-looking perspective
        trailing_pe = info.get('trailingPE')
        if trailing_pe is None or trailing_pe <= 0:
            return None
        if financials is None or financials.empty:
            return None
        net_income = financials.loc['Net Income']
        if len(net_income) < 2:
            return None
        net_income = net_income.dropna()
        if len(net_income) < 2:
            return None
        latest = net_income.iloc[0]
        oldest = net_income.iloc[-1]
        years = len(net_income) - 1
        if oldest <= 0 or latest <= 0:
            return None
        # CAGR smooths multi-year volatility for realistic growth rate
        cagr = (latest / oldest) ** (1 / years) - 1
        growth_pct = cagr * 100
        if growth_pct <= 0:
            return None
        return trailing_pe / growth_pct
    except (KeyError, IndexError, ZeroDivisionError):
        return None


def calculate_forward_peg(info: dict, growth_estimates: dict | None) -> tuple[float | None, float | None, str]:
    """Calculate Forward PEG ratio with capping and dampening.
    
    This is the FORWARD-LOOKING PEG - uses analyst estimates to see
    expected future performance. Handles overoptimistic analysts by:
    1. Capping growth at 60% (analysts tend to be overly optimistic)
    2. Dampening formula for info-based sources: only count first 30%
       fully, then add just 20% of excess (max 50%) - penalizes less
       reliable data sources that aren't analyst estimates.
    
    Data Source Cascade:
    - GE-2Y: growth_estimates 2-year blend (most reliable)
    - EE-2Y: earnings_estimate 2-year blend (second choice)
    - info-based with dampening: single year, less reliable
    
    Why 2-year blend? More reliable than single year, reduces noise.
    Single year changes can be volatile; geometric mean over 2 years
    gives a more stable picture of expected sustainable growth.
    
    Args:
        info: Stock info dictionary from yfinance
        growth_estimates: Dictionary with 'growth_2y', 'growth_1y', 'source' keys
        
    Returns:
        Tuple of (peg_value, growth_used_as_decimal, source_string)
    """
    # Use forward PE for forward-looking perspective
    forward_pe = info.get('forwardPE')
    if forward_pe is None or forward_pe <= 0:
        return None, None, "N/A"

    if growth_estimates is None:
        return None, None, "N/A"

    # Try 2-year blend first (from GE-2Y or EE-2Y)
    g2 = growth_estimates.get('growth_2y')
    if g2 is not None and g2 > 0:
        capped = min(g2, 0.60)  # Cap at 60% - analysts tend to be overly optimistic
        growth_pct = capped * 100
        peg = forward_pe / growth_pct
        return peg, capped, growth_estimates.get('source', 'GE-2Y')

    # Try 1-year from GE or EE sources
    g1_ge = growth_estimates.get('growth_1y')
    src = growth_estimates.get('source', 'N/A')
    if g1_ge is not None and g1_ge > 0 and (src.startswith('GE') or src.startswith('EE')):
        capped = min(g1_ge, 0.60)  # Cap at 60% - analysts tend to be overly optimistic
        growth_pct = capped * 100
        peg = forward_pe / growth_pct
        return peg, capped, src

    # Fallback: info-based growth with dampening (30% base + 20% of excess, max 50%)
    if g1_ge is not None and g1_ge > 0:
        base = min(g1_ge, 0.30)  # Count first 30% fully
        excess = max(0, g1_ge - 0.30) * 0.2  # Only add 20% of anything above 30%
        dampened = base + excess
        dampened = min(dampened, 0.50)  # Cap at 50% - penalizes less reliable info sources
        growth_pct = dampened * 100
        peg = forward_pe / growth_pct
        return peg, dampened, f"1Y→{src}"

    return None, None, "N/A"


def get_peg_values(info: dict, financials: pd.DataFrame | None, growth_estimates: dict | None) -> tuple[float | None, float | None, float | None, str]:
    """Get both GAAP and Forward PEG values with source tracking.
    
    Args:
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame
        growth_estimates: Growth estimates dictionary
        
    Returns:
        Tuple of (fwd_peg, gaap_peg, growth_used, peg_source)
    """
    fwd_peg, growth_used, peg_source = calculate_forward_peg(info, growth_estimates)

    # Sanity check: discard extreme values for data quality
    # PEG < 0 indicates no profit situation (invalid ratio)
    # PEG > 50 suggests calculation issue or extreme anomaly
    if fwd_peg is not None and (fwd_peg < 0 or fwd_peg > 50):
        fwd_peg = None

    gaap_peg = calculate_gaap_peg(info, financials)

    return fwd_peg, gaap_peg, growth_used, peg_source


def get_star_rating(value: float | None, thresholds: list[float], reverse: bool = False, penalize_negative: bool = False) -> int:
    """Calculate star rating (1-5) based on value and thresholds.
    
    Args:
        value: The metric value to rate
        thresholds: List of 4 threshold values for stars 2-5
        reverse: If True, lower is better (e.g., P/B ratio)
        penalize_negative: If True, negative values get 1 star
        
    Returns:
        Star rating from 0 to 5
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
        Dictionary with all computed metrics including star ratings
    """
    from .fetcher import calculate_asset_growth
    
    # Get PEG values with source tracking
    fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(info, financials, growth_estimates)
    
    # Calculate GP/A (Gross Profit / Total Assets)
    # Novy-Marx paper: Gross Profitability predicts future returns better than other factors
    gp_a = None
    gross_margin = None
    try:
        gp = financials.loc['Gross Profit'].iloc[0]
        assets = balance_sheet.loc['Total Assets'].iloc[0]
        gp_a = gp / assets
    except (KeyError, IndexError, ZeroDivisionError):
        pass

    # Calculate Gross Margin
    try:
        gp = financials.loc['Gross Profit'].iloc[0]
        revenue = financials.loc['Total Revenue'].iloc[0]
        if revenue and revenue > 0:
            gross_margin = gp / revenue
    except (KeyError, IndexError, ZeroDivisionError):
        pass

    # Get ROE and P/B from info
    roe = info.get('returnOnEquity')
    pb = info.get('priceToBook')

    # Handle negative P/B
    if pb is not None and pb < 0:
        pb = None

    # Adjust ROE for scoring when extreme values present
    roe_for_scoring = roe
    if roe is not None and pb is not None:
        if roe > 1.0 and pb > 50:
            roe_for_scoring = None

    # Calculate asset growth (Novy-Marx control factor)
    asset_growth = calculate_asset_growth(balance_sheet)

    # Calculate star ratings
    s_gpa = get_star_rating(gp_a, [0.1, 0.2, 0.3, 0.4])
    s_roe = get_star_rating(roe_for_scoring, [0.05, 0.10, 0.20, 0.30], penalize_negative=True)
    s_pb = get_star_rating(pb, [40.0, 20.0, 10.0, 5.0], reverse=True, penalize_negative=True)
    s_fwd_peg = get_star_rating(fwd_peg, [2.5, 2.0, 1.5, 1.0], reverse=True)
    s_mom = get_star_rating(perf_12m, [0.0, 0.10, 0.25, 0.50])

    # Get company name
    name = info.get('shortName') or info.get('longName') or ''

    return {
        'symbol': info.get('symbol', ''),
        'name': name,
        'gp_a': gp_a,
        'gross_margin': gross_margin,
        'roe': roe,
        'pb': pb,
        'fwd_peg': fwd_peg,
        'gaap_peg': gaap_peg,
        'growth_used': growth_used,
        'peg_source': peg_source,
        'asset_growth': asset_growth,
        'perf_6m': perf_6m,
        'perf_12m': perf_12m,
        's_gpa': s_gpa,
        's_roe': s_roe,
        's_pb': s_pb,
        's_fwd_peg': s_fwd_peg,
        's_mom': s_mom,
    }
