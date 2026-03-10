"""
Ranking and percentile calculation functions.

Adds percentile ranks to stock data for comparison across the universe.
"""

import pandas as pd
from typing import Any, List, Dict


def add_percentile_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Add percentile rank columns to DataFrame.
    
    Args:
        df: DataFrame with stock metrics
        
    Returns:
        DataFrame with added percentile rank columns
    """
    # Create a copy to avoid modifying the original
    result = df.copy()
    
    # Calculate percentile ranks for key metrics
    if 'gaap_peg' in result.columns and result['gaap_peg'].notna().any():
        result['peg_rank'] = (1 - result['gaap_peg'].rank(pct=True)).round(2) * 100
    
    if 'growth_rate' in result.columns and result['growth_rate'].notna().any():
        result['growth_rank'] = result['growth_rate'].rank(pct=True).round(2) * 100
    
    return result
