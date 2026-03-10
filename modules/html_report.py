"""
HTML Report generation using the beautiful template.

Generates interactive HTML reports with tabs, color-coding, and sorting.
"""

import json
from typing import Any, List, Dict


def format_html_data(row: dict) -> dict:
    """Format a row for HTML output.
    
    Args:
        row: Dictionary with stock data
        
    Returns:
        Formatted dictionary ready for JSON serialization
    """
    return {
        'symbol': row.get('symbol', ''),
        'name': row.get('name', ''),
        'gp_a': row.get('profit_margin'),
        'gross_margin': row.get('gross_margin'),
        'roe': row.get('roe'),
        'pb': row.get('pb_ratio'),
        'nm': row.get('nm_score', 0) / 2.0,
        'mf': row.get('mf_score', 0) / 2.0,
        'quality': get_quality_stars(row),
        'fwd_peg': row.get('forward_peg'),
        'gaap_peg': row.get('peg_ratio'),
        'growth_used': row.get('growth_rate'),
        'peg_source': '',
        'gp_a_decile': calculate_decile(row, 'profit_margin'),
        'pb_decile': calculate_decile(row, 'pb_ratio', inverse=True),
        'nm_rank': row.get('nm_score', 0) + (row.get('mf_score', 0)),
        'asset_growth': row.get('asset_growth'),
        'perf_6m': row.get('perf_6m'),
        'perf_12m': row.get('perf_12m'),
    }


def get_quality_stars(row: dict) -> str:
    """Get quality stars based on star rating.
    
    Args:
        row: Dictionary with stock data
        
    Returns:
        Quality string (★★★, ★★, ★, or —)
    """
    rating = row.get('star_rating', 0)
    if rating >= 4:
        return '★★★'
    elif rating == 3:
        return '★★'
    elif rating == 2:
        return '★'
    else:
        return '—'


def calculate_decile(row: dict, key: str, inverse: bool = False) -> int:
    """Calculate decile rank for a metric.
    
    Args:
        row: Dictionary with stock data
        key: Metric key to evaluate
        inverse: If True, lower values are better (e.g., P/B)
        
    Returns:
        Decile rank 1-10
    """
    value = row.get(key)
    if value is None:
        return 5
    
    if inverse:
        if value <= 3:
            return 10
        elif value <= 5:
            return 8
        elif value <= 7:
            return 6
        elif value <= 10:
            return 4
        elif value <= 15:
            return 2
        else:
            return 1
    else:
        if value >= 0.30:
            return 10
        elif value >= 0.20:
            return 8
        elif value >= 0.15:
            return 6
        elif value >= 0.10:
            return 4
        elif value >= 0.05:
            return 2
        else:
            return 1


def categorize_stocks(rows: List[dict]) -> Dict[str, List[dict]]:
    """Categorize stocks into different groups.
    
    Args:
        rows: List of stock data dictionaries
        
    Returns:
        Dictionary with categorized stocks
    """
    result = {
        'all': [],
        'sweet': [],
        'traps': [],
        'nopeg': [],
        'divergent': [],
    }
    
    for row in rows:
        formatted = format_html_data(row)
        result['all'].append(formatted)
        
        fwd_peg = row.get('forward_peg')
        gaap_peg = row.get('peg_ratio')
        star_rating = row.get('star_rating', 0)
        
        if fwd_peg is not None and fwd_peg <= 1.0:
            result['sweet'].append(formatted)
        elif star_rating <= 2 and (fwd_peg is not None and fwd_peg > 1.5):
            result['traps'].append(formatted)
        
        if fwd_peg is None and gaap_peg is None:
            result['nopeg'].append(formatted)
        elif fwd_peg is not None and gaap_peg is not None:
            ratio = abs(fwd_peg - gaap_peg) / max(fwd_peg, gaap_peg)
            if ratio > 0.3:
                formatted['ratio'] = fwd_peg / gaap_peg if gaap_peg != 0 else None
                formatted['signal'] = 'Divergent'
                result['divergent'].append(formatted)
    
    return result


def generate_beautiful_html(
    rows: List[dict],
    timestamp: str,
    output_path: str = "nasdaq100_analysis.html"
) -> None:
    """Generate beautiful HTML report.
    
    Args:
        rows: List of stock data dictionaries
        timestamp: Timestamp string for the report
        output_path: Path to save the HTML file
    """
    from html_template import render_html
    
    categories = categorize_stocks(rows)
    
    html_data = {
        'TIMESTAMP': timestamp,
        'REBALANCE_NOTE': 'Hinweis: Quartalsweise Rebalancierung empfohlen.',
        'ALL_DATA': json.dumps(categories['all']),
        'SWEET_DATA': json.dumps(categories['sweet']),
        'TRAPS_DATA': json.dumps(categories['traps']),
        'NO_PEG_DATA': json.dumps(categories['nopeg']),
        'DIVERGENT_DATA': json.dumps(categories['divergent']),
        'NM_TOP_DATA': json.dumps(categories['all'][:20]),
    }
    
    html_content = render_html(html_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_html_report(
    rows: List[dict],
    timestamp: str,
    output_path: str = "nasdaq100_analysis.html"
) -> None:
    """Generate HTML report (alias for beautiful version).
    
    Args:
        rows: List of stock data dictionaries
        timestamp: Timestamp string for the report
        output_path: Path to save the HTML file
    """
    generate_beautiful_html(rows, timestamp, output_path)
