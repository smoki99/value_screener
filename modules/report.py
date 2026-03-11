"""
Report generation and analysis functions.

Builds unified rows with comprehensive stock data for flexible frontend use.
"""

import pandas as pd
from typing import Any, List, Dict


def build_unified_row(
    symbol: str,
    info: dict,
    financials: pd.DataFrame | None,
    balance_sheet: pd.DataFrame | None,
    perf_6m: float | None,
    perf_12m: float | None,
    growth_estimates: dict
) -> Dict[str, Any]:
    """Build a comprehensive unified row of data for a stock.
    
    Includes all available metrics and fields for flexible frontend display.
    
    Args:
        symbol: Stock ticker symbol
        info: Stock info dictionary from yfinance
        financials: Financial statements DataFrame
        balance_sheet: Balance sheet DataFrame
        perf_6m: 6-month performance
        perf_12m: 12-month performance
        growth_estimates: Growth estimates dictionary
        
    Returns:
        Dictionary with all stock data in unified format
    """
    from .metrics import compute_metrics, get_peg_values, calculate_forward_peg
    from .scoring import (
        score_novy_marx,
        score_multi_factor,
        score_novy_marx_weighted,
        score_multi_factor_weighted,
        get_star_rating,
        get_quality_rating
    )
    from .fetcher import calculate_asset_growth
    
    # Compute metrics - this includes gp_a calculation and all other metrics
    metrics = compute_metrics(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates)
    
    # Get PEG values with source tracking
    fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(info, financials, growth_estimates)
    forward_peg = fwd_peg
    
    # Calculate individual star ratings for weighted scoring
    s_gpa = get_star_rating(metrics['gp_a'], [0.1, 0.2, 0.3, 0.4], reverse=False) if metrics['gp_a'] else 0
    s_roe = get_star_rating(info.get('returnOnEquity'), [0.05, 0.10, 0.20, 0.30], penalize_negative=True) if info.get('returnOnEquity') else 0
    s_pb = get_star_rating(info.get('priceToBook'), [40.0, 20.0, 10.0, 5.0], reverse=True, penalize_negative=True) if info.get('priceToBook') else 0
    s_fpeg = get_star_rating(forward_peg, [2.5, 2.0, 1.5, 1.0], reverse=True) if forward_peg else 0
    
    # Calculate momentum star rating (12-month performance)
    s_momentum = get_star_rating(perf_12m, [0.0, 0.10, 0.25, 0.50]) if perf_12m is not None else 0
    
    # Calculate weighted scores (0-4.0 scale)
    nm_score = score_novy_marx_weighted(s_gpa, s_pb, s_momentum)
    mf_score = score_multi_factor_weighted(s_gpa, s_roe, s_pb, s_fpeg, s_momentum)
    
    # Calculate quality rating based on weighted scores (best of NM and MF)
    quality_rating = get_quality_rating(nm_score, mf_score)
    
    # Star rating is the maximum of nm_score and mf_score
    star_rating = max(nm_score, mf_score)
    
    # Extract all available info fields for comprehensive data
    return {
        # Basic identification
        'symbol': symbol,
        'name': info.get('shortName', ''),
        'company_name': info.get('shortName', ''),
        'long_name': info.get('longName', ''),
        
        # Price and market data
        'price': info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose'),
        'open': info.get('open'),
        'day_low': info.get('dayLow'),
        'day_high': info.get('dayHigh'),
        'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
        'market_cap': info.get('marketCap'),
        'enterprise_value': info.get('enterpriseValue'),
        
        # Volume data
        'volume': info.get('regularMarketVolume'),
        'average_volume': info.get('averageVolume'),
        'average_volume_10day': info.get('averageVolume10days'),
        
        # Valuation ratios
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': gaap_peg,
        'forward_peg': forward_peg,
        'pb_ratio': info.get('priceToBook'),
        'ps_ratio': info.get('priceToSalesTrailing12Months'),
        'pcf_ratio': info.get('priceToFreeCashflow'),
        
        # Profitability metrics (from compute_metrics)
        'gp_a': metrics['gp_a'],  # Gross Profit / Total Assets
        'gross_margin': metrics['gross_margin'],
        'profit_margin': info.get('profitMargins'),
        'roe': info.get('returnOnEquity'),
        'roa': info.get('returnOnAssets'),
        
        # Growth metrics
        'asset_growth': metrics['asset_growth'],
        'revenue_growth_ttm': info.get('revenueGrowth'),
        'earnings_growth_quarterly': info.get('earningsQuarterlyGrowth'),
        
        # Performance data
        'perf_6m': perf_6m,
        'perf_12m': perf_12m,
        
        # Dividend data
        'dividend_rate': info.get('dividendRate'),
        'dividend_yield': info.get('dividendYield') / 100 if info.get('dividendYield') else None,
        'payout_ratio': info.get('payoutRatio'),

        'ex_dividend_date': info.get('exDividendDate'),
        
        # Balance sheet data
        'total_assets': info.get('totalAssets'),
        'total_debt': info.get('totalDebt'),
        'debt_to_equity': info.get('debtToEquity'),
        'current_ratio': info.get('currentRatio'),
        
        # Cash flow data
        'operating_cash_flow': info.get('operatingCashflow'),
        'free_cash_flow': info.get('freeCashflow'),
        
        # Scores and ratings
        'nm_score': nm_score,
        'mf_score': mf_score,
        'star_rating': star_rating,
        'quality_rating': quality_rating,
        
        # PEG source tracking
        'growth_used': growth_used,
        'peg_source': peg_source,
        
        # Additional useful fields
        'beta': info.get('beta'),
        'shares_outstanding': info.get('sharesOutstanding'),
        'float_shares': info.get('floatShares'),
        'held_percent_insiders': info.get('heldPercentInsiders'),
        'held_percent_institutions': info.get('heldPercentInstitutions'),
        
        # Sector and industry
        'sector': info.get('sector', ''),
        'industry': info.get('industry', ''),
        'full_time_employees': info.get('fullTimeEmployees'),
    }


def print_table_out(df: pd.DataFrame) -> None:
    """Print DataFrame to console as formatted table.
    
    Args:
        df: DataFrame with stock data
    """
    # Configure display options
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', lambda x: f'{x:.2f}')
    
    print("\n" + "=" * 80)
    print(df.to_string(index=False))
    print("=" * 80 + "\n")


def generate_html_report(
    df: pd.DataFrame,
    output_path: str = "nasdaq100_analysis.html"
) -> None:
    """Generate HTML report from DataFrame.
    
    Args:
        df: DataFrame with stock data
        output_path: Path to save the HTML file
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>NASDAQ-100 Analyse</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>NASDAQ-100 Analyse</h1>
    {df.to_html(index=False)}
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def analyze_nasdaq100(
    tickers: List[str],
    conn: Any,
    output_html: bool = True
) -> pd.DataFrame:
    """Analyze all NASDAQ-100 stocks.
    
    Args:
        tickers: List of ticker symbols to analyze
        conn: Database connection for caching
        output_html: Whether to generate HTML report
        
    Returns:
        DataFrame with analysis results
    """
    from .fetcher import fetch_stock_data
    from .report import build_unified_row, print_table_out, generate_html_report
    
    rows = []
    for symbol in tickers:
        data = fetch_stock_data(conn, symbol)
        if data:
            row = build_unified_row(
                symbol,
                data['info'],
                data['financials'],
                data['balance_sheet'],
                data['perf_6m'],
                data['perf_12m'],
                data['growth_estimates']
            )
            rows.append(row)
    
    df = pd.DataFrame(rows)
    print_table_out(df)
    
    if output_html:
        generate_html_report(df)
    
    return df
