"""
NASDAQ-100 Screener - Data Processing Functions

Data conversion, sanitization, and analysis functions.
Handles JSON serialization and NASDAQ data processing.
"""

import sys
from datetime import datetime
import math
import json
import pandas as pd

# Import modules from parent directory (added to path in app.py)
try:
    from modules import (
        deduplicate_tickers,
        get_nasdaq100_tickers,
        get_nasdaq_largecap_tickers,
        analyze_nasdaq100,
    )
except ImportError:
    # Fallback if imported directly without path setup
    pass

# Import configuration from environment variables (not from app module)
import os
USE_LARGECAP = os.environ.get('USE_LARGECAP', 'true').lower() == 'true'
MIN_MARKET_CAP = float(os.environ.get('MIN_MARKET_CAP', '10e9'))  # Default $10B


def save_analysis_to_cache(conn, result_data):
    """
    Save analysis results to the database cache.
    
    Args:
        conn: Database connection
        result_data: List of stock dictionaries from analyze_nasdaq100()
    """
    try:
        # Convert list of dicts to JSON string
        json_data = json.dumps(result_data)
        timestamp = datetime.now().isoformat()
        
        # Insert or replace in ticker_cache table
        conn.execute(
            "INSERT OR REPLACE INTO ticker_cache (id, tickers_json, fetched_at) VALUES (1, ?, ?)",
            (json_data, timestamp)
        )
        conn.commit()
        print(f"  Saved {len(result_data)} stocks to cache at: {timestamp}")
    except Exception as e:
        print(f"ERROR saving to cache: {e}")
        import traceback
        traceback.print_exc()


def convert_percentages_to_whole_numbers(stock_data):
    """
    No conversion needed - source data is already in decimal format.
    Star ratings and color coding expect decimals (e.g., 0.14679).
    Frontend handles display formatting by multiplying by 100.
    
    Args:
        stock_data: List of stock dictionaries
        
    Returns:
        Unmodified list - keeps decimal format from source
    """
    # No conversion needed - keep decimals from source data
    return stock_data


def sanitize_for_json(obj):
    """
    Recursively convert NaN/Inf values to None for JSON serialization.
    Handles dicts, lists, and primitive types.
    
    Args:
        obj: Any Python object (dict, list, or primitive)
        
    Returns:
        Sanitized object with NaN/Inf converted to None
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        # Check for NaN or Inf
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


def run_analysis(conn=None):
    """
    Run full NASDAQ-100 or Large-Cap analysis and update cache.
    Called on startup if data is older than 24 hours.
    
    Args:
        conn: Database connection (required). Must be passed by caller.
              Used by init_server() to pass the fresh connection it creates.
    """
    # Validate that a connection was provided
    if conn is None:
        print("ERROR: run_analysis requires a database connection. Pass conn parameter.")
        return
    
    print("\n" + "=" * 60)
    analysis_type = "NASDAQ Large-Cap (> $10B)"
    print(f"Running {analysis_type} Analysis")
    print("=" * 60 + "\n")
    
    try:
        # Get ticker list based on configuration
        if USE_LARGECAP:
            tickers = get_nasdaq_largecap_tickers(conn, min_market_cap=MIN_MARKET_CAP)
            analysis_type = f"NASDAQ Large-Cap (> ${int(MIN_MARKET_CAP/1e9)}B)"
        else:
            tickers = get_nasdaq100_tickers(conn)
            analysis_type = "NASDAQ-100"
        
        if not tickers:
            print(f"ERROR: Could not fetch {analysis_type} ticker list.")
            return
        
        # Deduplicate (only needed for NASDAQ-100, but safe to always call)
        tickers = deduplicate_tickers(tickers)
        print(f"\nAnalyzing {len(tickers)} stocks...\n")
        
        # Analyze all stocks (this fetches fresh data from Yahoo Finance)
        df = analyze_nasdaq100(tickers, conn, output_html=False)
        
        # Convert to list of dictionaries
        result_data = df.to_dict('records')
        cache_timestamp = datetime.now().isoformat()
        
        # Save results to database cache - THIS WAS MISSING!
        save_analysis_to_cache(conn, result_data)
        
        print(f"\n✓ Analysis complete! {len(result_data)} stocks analyzed.")
        print(f"  Cache updated at: {cache_timestamp}\n")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
