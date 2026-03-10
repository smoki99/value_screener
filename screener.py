"""
NASDAQ-100 Screener - Main Entry Point

Analyzes NASDAQ-100 stocks using Novy-Marx and multi-factor scoring.
Generates beautiful interactive HTML reports.
"""

import sys
from datetime import datetime
from modules import (
    DB_PATH, CACHE_MAX_AGE_HOURS,
    init_db, get_cached_tickers, save_tickers_to_cache,
    deduplicate_tickers, get_nasdaq100_tickers, fetch_stock_data,
    build_unified_row, print_table_out, generate_html_report,
    analyze_nasdaq100, rebalancing_note
)
from modules.html_report import generate_beautiful_html


def main():
    """Main function to run the NASDAQ-100 screener."""
    # Initialize database
    conn = init_db(DB_PATH)
    
    print("\n" + "=" * 60)
    print("NASDAQ-100 Screener")
    print("=" * 60 + "\n")
    
    # Get ticker list
    tickers = get_nasdaq100_tickers(conn)
    if not tickers:
        print("ERROR: Could not fetch NASDAQ-100 ticker list.")
        sys.exit(1)
    
    # Deduplicate
    tickers = deduplicate_tickers(tickers)
    print(f"\nAnalyzing {len(tickers)} stocks...\n")
    
    # Analyze all stocks
    df = analyze_nasdaq100(tickers, conn, output_html=False)
    
    # Generate beautiful HTML report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = df.to_dict('records')
    generate_beautiful_html(rows, timestamp, "nasdaq100_analysis.html")
    print(f"\n📄 Beautiful HTML report saved to: nasdaq100_analysis.html")
    
    # Print rebalancing note
    print(rebalancing_note())
    
    # Close database connection
    conn.close()


if __name__ == "__main__":
    main()
