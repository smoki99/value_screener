"""
NASDAQ-100 Screener Web Server

Simple Flask-based API server.
No multi-threading - SQLite is not made for this.
On startup: auto-refresh data if older than 24 hours.
"""

import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import math

# Add modules to path
sys.path.insert(0, '.')

from modules import (
    DB_PATH,
    init_db,
    deduplicate_tickers,
    get_nasdaq100_tickers,
    analyze_nasdaq100,
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
db_conn = None
cached_data = None
cache_timestamp = None


def convert_percentages_to_whole_numbers(stock_data):
    """
    Convert decimal percentages (0.50) to whole numbers (50).
    Applied in-place for efficiency.
    
    Args:
        stock_data: List of stock dictionaries
        
    Returns:
        Modified list with percentage values as whole numbers
    """
    for stock in stock_data:
        # GP/A - Gross Profit / Assets (percentage)
        if 'gp_a' in stock and stock['gp_a'] is not None:
            stock['gp_a'] = round(stock['gp_a'] * 100, 2)
        
        # GM - Gross Margin (percentage)
        if 'gross_margin' in stock and stock['gross_margin'] is not None:
            stock['gross_margin'] = round(stock['gross_margin'] * 100, 2)
        
        # Profit Margin (percentage)
        if 'profit_margin' in stock and stock['profit_margin'] is not None:
            stock['profit_margin'] = round(stock['profit_margin'] * 100, 2)
        
        # ROE - Return on Equity (percentage)
        if 'roe' in stock and stock['roe'] is not None:
            stock['roe'] = round(stock['roe'] * 100, 2)
        
        # Growth Rate (percentage)
        if 'growth_rate' in stock and stock['growth_rate'] is not None:
            stock['growth_rate'] = round(stock['growth_rate'] * 100, 2)
        
        # Asset Growth (percentage)
        if 'asset_growth' in stock and stock['asset_growth'] is not None:
            stock['asset_growth'] = round(stock['asset_growth'] * 100, 2)
        
        # Performance 6M (percentage)
        if 'perf_6m' in stock and stock['perf_6m'] is not None:
            stock['perf_6m'] = round(stock['perf_6m'] * 100, 2)
        
        # Performance 12M (percentage)
        if 'perf_12m' in stock and stock['perf_12m'] is not None:
            stock['perf_12m'] = round(stock['perf_12m'] * 100, 2)
    
    return stock_data


def sanitize_for_json(obj):
    """
    Recursively convert NaN/Inf values to None for JSON serialization.
    Handles dicts, lists, and primitive types.
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
    Run full NASDAQ-100 analysis and update cache.
    Called on startup if data is older than 24 hours.
    
    Args:
        conn: Optional database connection. If None, uses global db_conn.
              Used by POST /api/analyze to create fresh connection per request.
    """
    global cached_data, cache_timestamp
    
    # Use provided connection or fall back to global
    db = conn if conn is not None else db_conn
    
    print("\n" + "=" * 60)
    print("Running NASDAQ-100 Analysis")
    print("=" * 60 + "\n")
    
    try:
        # Get ticker list from Wikipedia (cached)
        tickers = get_nasdaq100_tickers(db)
        if not tickers:
            print("ERROR: Could not fetch NASDAQ-100 ticker list.")
            return
        
        # Deduplicate
        tickers = deduplicate_tickers(tickers)
        print(f"\nAnalyzing {len(tickers)} stocks...\n")
        
        # Analyze all stocks (this fetches fresh data from Yahoo Finance)
        df = analyze_nasdaq100(tickers, db, output_html=False)
        
        # Convert to list of dictionaries
        cached_data = df.to_dict('records')
        cache_timestamp = datetime.now().isoformat()
        
        print(f"\n✓ Analysis complete! {len(cached_data)} stocks analyzed.")
        print(f"  Cache updated at: {cache_timestamp}\n")
        
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()


def init_server():
    """
    Initialize server with database connection.
    Auto-refresh data if older than 24 hours.
    """
    global db_conn, cached_data, cache_timestamp
    
    # Initialize database
    db_conn = init_db(DB_PATH)
    print(f"Database initialized: {DB_PATH}")
    
    # Check if we have cached data and when it was fetched
    try:
        cursor = db_conn.execute(
            "SELECT tickers_json, fetched_at FROM ticker_cache ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        
        if row:
            import json
            # Parse JSON - ensure it's a list of dicts
            parsed_data = json.loads(row[0])
            cache_timestamp = row[1]
            print(f"Found cached data from: {cache_timestamp}")
            
            # Validate data structure - must be list of dictionaries
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                if isinstance(parsed_data[0], dict):
                    cached_data = parsed_data
                    print(f"Cache contains {len(cached_data)} stocks")
                    
                    # Check if older than 24 hours - auto refresh
                    last_fetch = datetime.fromisoformat(cache_timestamp)
                    age_hours = (datetime.now() - last_fetch).total_seconds() / 3600
                    print(f"Cache age: {age_hours:.1f} hours")
                    
                    if age_hours > 24:
                        print("\nData is older than 24 hours. Auto-refreshing...\n")
                        run_analysis()
                    else:
                        print(f"\nUsing cached data ({len(cached_data)} stocks).\n")
                else:
                    # Invalid structure - fetch fresh
                    print("Invalid cache format (not list of dicts). Fetching fresh data...\n")
                    run_analysis()
            else:
                # Empty or invalid - fetch fresh
                print("Empty or invalid cache. Fetching fresh data...\n")
                run_analysis()
        else:
            # No cached data - fetch fresh
            print("No cached data found. Fetching fresh data...\n")
            run_analysis()
    except Exception as e:
        print(f"Error loading cache: {e}")
        import traceback
        traceback.print_exc()
        print("Fetching fresh data...\n")
        run_analysis()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    Returns server status and cache information.
    """
    global cached_data, cache_timestamp
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_available': cached_data is not None,
        'last_update': cache_timestamp,
        'stocks_cached': len(cached_data) if cached_data else 0
    })


@app.route('/api/stocks')
def get_all_stocks():
    """
    Return all stock data as JSON.
    GET /api/stocks
    """
    global cached_data, cache_timestamp
    
    if not cached_data:
        return jsonify({
            'error': 'No data available',
            'message': 'Analysis has not been run yet or failed'
        }), 404
    
    # Convert percentages to whole numbers (0.50 -> 50)
    converted_data = convert_percentages_to_whole_numbers(cached_data.copy())
    
    # Sanitize NaN/Inf values for JSON serialization
    sanitized_data = sanitize_for_json(converted_data)
    
    return jsonify({
        'data': sanitized_data,
        'count': len(sanitized_data),
        'last_update': cache_timestamp
    })


@app.route('/api/buy-recommendations')
def get_buy_recommendations():
    """
    Return only 4-5 star stocks (buy recommendations).
    GET /api/buy-recommendations
    """
    global cached_data, cache_timestamp
    
    # Handle empty data gracefully - return empty list instead of 404
    if not cached_data:
        return jsonify({
            'data': [],
            'count': 0,
            'last_update': None
        })
    
    # Filter stocks with 4-5 stars
    buy_stocks = [stock for stock in cached_data if stock.get('stars', 0) >= 4]
    
    # Convert percentages to whole numbers (0.50 -> 50)
    converted_buy_stocks = convert_percentages_to_whole_numbers(buy_stocks.copy())
    
    # Sanitize NaN/Inf values for JSON serialization
    sanitized_buy_stocks = sanitize_for_json(converted_buy_stocks)
    
    return jsonify({
        'data': sanitized_buy_stocks,
        'count': len(sanitized_buy_stocks),
        'last_update': cache_timestamp
    })


@app.route('/api/hold-recommendations')
def get_hold_recommendations():
    """
    Return only 3 star stocks (hold recommendations).
    GET /api/hold-recommendations
    """
    global cached_data, cache_timestamp
    
    # Handle empty data gracefully - return empty list instead of 404
    if not cached_data:
        return jsonify({
            'data': [],
            'count': 0,
            'last_update': None
        })
    
    # Filter stocks with exactly 3 stars
    hold_stocks = [stock for stock in cached_data if stock.get('stars', 0) == 3]
    
    # Convert percentages to whole numbers (0.50 -> 50)
    converted_hold_stocks = convert_percentages_to_whole_numbers(hold_stocks.copy())
    
    # Sanitize NaN/Inf values for JSON serialization
    sanitized_hold_stocks = sanitize_for_json(converted_hold_stocks)
    
    return jsonify({
        'data': sanitized_hold_stocks,
        'count': len(sanitized_hold_stocks),
        'last_update': cache_timestamp
    })


@app.route('/api/sell-avoidance')
def get_sell_avoidance():
    """
    Return only 0-2 star stocks (sell/avoid recommendations).
    GET /api/sell-avoidance
    """
    global cached_data, cache_timestamp
    
    # Handle empty data gracefully - return empty list instead of 404
    if not cached_data:
        return jsonify({
            'data': [],
            'count': 0,
            'last_update': None
        })
    
    # Filter stocks with 0-2 stars
    sell_stocks = [stock for stock in cached_data if stock.get('stars', 0) <= 2]
    
    # Convert percentages to whole numbers (0.50 -> 50)
    converted_sell_stocks = convert_percentages_to_whole_numbers(sell_stocks.copy())
    
    # Sanitize NaN/Inf values for JSON serialization
    sanitized_sell_stocks = sanitize_for_json(converted_sell_stocks)
    
    return jsonify({
        'data': sanitized_sell_stocks,
        'count': len(sanitized_sell_stocks),
        'last_update': cache_timestamp
    })


@app.route('/api/stock/<symbol>')
def get_stock_by_symbol(symbol):
    """
    Get individual stock details by ticker symbol.
    GET /api/stock/{symbol}
    
    Example: /api/stock/AAPL
    """
    global cached_data, cache_timestamp
    
    if not cached_data:
        return jsonify({
            'error': 'No data available',
            'message': 'Analysis has not been run yet or failed'
        }), 404
    
    # Find stock by symbol (case-insensitive)
    symbol_upper = symbol.upper()
    stock = next((s for s in cached_data if s.get('symbol', '').upper() == symbol_upper), None)
    
    if not stock:
        return jsonify({
            'error': 'Stock not found',
            'message': f'No data available for {symbol}'
        }), 404
    
    # Convert percentages to whole numbers (0.50 -> 50)
    converted_stock = convert_percentages_to_whole_numbers([stock.copy()])[0]
    
    return jsonify({
        'data': converted_stock,
        'last_update': cache_timestamp
    })


@app.route('/api/stats')
def get_stats():
    """
    Return summary statistics.
    GET /api/stats
    
    Returns: total stocks, buy count, hold count, sell count
    """
    global cached_data, cache_timestamp
    
    # Calculate statistics (handle empty data gracefully)
    if not cached_data:
        return jsonify({
            'total': 0,
            'buy_recommendations': 0,
            'hold_recommendations': 0,
            'sell_avoidance': 0,
            'last_update': None
        })
    
    # Calculate statistics
    total = len(cached_data)
    buy_count = sum(1 for s in cached_data if s.get('stars', 0) >= 4)
    hold_count = sum(1 for s in cached_data if s.get('stars', 0) == 3)
    sell_count = sum(1 for s in cached_data if s.get('stars', 0) <= 2)
    
    return jsonify({
        'total': total,
        'buy_recommendations': buy_count,
        'hold_recommendations': hold_count,
        'sell_avoidance': sell_count,
        'last_update': cache_timestamp
    })


@app.route('/api/analyze', methods=['POST'])
def trigger_analysis():
    """
    Trigger manual fresh analysis.
    POST /api/analyze
    
    This will fetch new data from Yahoo Finance and update the cache.
    Creates fresh db connection for this request to avoid SQLite threading issues.
    """
    global cached_data, cache_timestamp
    
    try:
        # Create fresh connection for this request (Flask runs handlers in separate thread)
        # This avoids "SQLite objects created in a thread can only be used in that same thread"
        fresh_conn = init_db(DB_PATH)
        
        # Run analysis with the fresh connection
        run_analysis(fresh_conn)
        
        # Close the fresh connection
        fresh_conn.close()
        
        return jsonify({
            'status': 'analysis_complete',
            'message': 'Fresh analysis completed successfully'
        })
    except Exception as e:
        print(f"Error during manual analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/')
def serve_frontend():
    """
    Serve the frontend HTML file.
    GET /
    
    This allows users to access the web interface at http://localhost:5000/
    """
    try:
        return send_file('frontend.html', mimetype='text/html')
    except Exception as e:
        print(f"Error serving frontend: {e}")
        return jsonify({
            'error': 'Frontend not available',
            'message': str(e)
        }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Initialize server (database + auto-refresh if needed)
    init_server()
    
    print("\n" + "=" * 60)
    print("NASDAQ-100 Screener Server")
    print("=" * 60)
    print("\nServer running on http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  GET /health                    - Health check")
    print("  GET /api/stocks                - All stock data")
    print("  GET /api/buy-recommendations   - 4-5 star stocks")
    print("  GET /api/hold-recommendations  - 3 star stocks")
    print("  GET /api/sell-avoidance        - 0-2 star stocks")
    print("  GET /api/stock/{symbol}        - Individual stock by symbol")
    print("  GET /api/stats                 - Summary statistics")
    print("  POST /api/analyze              - Trigger fresh analysis")
    print("\nPress Ctrl+C to stop server\n")
    
    # Run Flask app with threading disabled
    # This prevents "SQLite objects created in a thread can only be used in that same thread" errors
    # because all requests will run in the main thread where db_conn was created
    from werkzeug.serving import WSGIRequestHandler
    
    class SingleThreadedWSGIRequestHandler(WSGIRequestHandler):
        def process_request(self, *args, **kwargs):
            # Disable threading - each request runs synchronously in the main thread
            self.server = type('obj', (object,), {'threading': False})()
            super().process_request(*args, **kwargs)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=False
    )
