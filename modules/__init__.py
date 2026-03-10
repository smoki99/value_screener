"""
NASDAQ-100 Screener Modules

Unified package for all screener functionality.
"""

from .config import DB_PATH, CACHE_MAX_AGE_HOURS
from .cache import init_db, get_cached_tickers, save_tickers_to_cache
from .fetcher import (
    fetch_stock_data,
    calculate_asset_growth,
    deduplicate_tickers,
    get_nasdaq100_tickers,
)
from .metrics import calculate_gaap_peg, calculate_forward_peg, get_peg_values, compute_metrics
from .scoring import get_star_rating, score_novy_marx, score_multi_factor, stars_str, rebalancing_note
from .ranking import add_percentile_ranks
from .report import build_unified_row, print_table_out, generate_html_report, analyze_nasdaq100
from .html_report import (
    format_html_data,
    get_quality_stars,
    calculate_decile,
    categorize_stocks,
    generate_beautiful_html,
)
