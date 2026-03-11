"""
Report generation and analysis functions.

Builds unified rows, prints tables, generates HTML reports, and analyzes NASDAQ-100 data.
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
    """Build a unified row of data for a stock.
    
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
    from .scoring import score_novy_marx, score_multi_factor, get_star_rating
    from .fetcher import calculate_asset_growth
    
    # Compute metrics
    metrics = compute_metrics(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates)
    
    # Get PEG values with source tracking
    fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(info, financials, growth_estimates)
    forward_peg = fwd_peg
    
    # Calculate scores
    nm_score = score_novy_marx(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates)
    mf_score = score_multi_factor(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates)
    
    # Get star rating - prefer forward_peg if available (more forward-looking)
    # PEG thresholds: <=0.5=5★, <=1.0=4★, <=1.5=3★, <=2.0=2★, >2.0=1★
    peg_for_rating = forward_peg if forward_peg is not None else gaap_peg
    star_rating = get_star_rating(peg_for_rating, [0.5, 1.0, 1.5, 2.0], reverse=True)
    
    return {
        'symbol': symbol,
        'name': info.get('shortName', ''),
        'price': info.get('regularMarketPrice'),
        'market_cap': info.get('marketCap'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': gaap_peg,
        'forward_peg': forward_peg,
        'growth_rate': metrics['growth_used'],
        'gross_margin': info.get('grossMargins'),
        'profit_margin': info.get('profitMargins'),
        'roe': info.get('returnOnEquity'),
        'pb_ratio': info.get('priceToBook'),
        'asset_growth': metrics['asset_growth'],
        'perf_6m': perf_6m,
        'perf_12m': perf_12m,
        'nm_score': nm_score,
        'mf_score': mf_score,
        'star_rating': star_rating,
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
