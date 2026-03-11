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
import pandas as pd

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
    
    # Filter: quality rating is "★★★" OR ("★★" with forward_peg < 1.0) - both are buys
    buy_stocks = [
        stock for stock in cached_data 
        if stock.get('quality_rating') == '★★★' or 
           (stock.get('quality_rating') == '★★' and stock.get('forward_peg') is not None and stock.get('forward_peg') < 1.0)
    ]
    
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
    
    # Filter: "★★" with peg >= 1.0 AND peg < 1.5 (hold till peg > 1.5)
    # Excludes those already in buy (forward_peg < 1.0)
    hold_stocks = [
        stock for stock in cached_data 
        if stock.get('quality_rating') == '★★' and 
           stock.get('peg_ratio') is not None and 
           stock.get('peg_ratio') >= 1.0 and 
           stock.get('peg_ratio') < 1.5
    ]
    
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
    
    # Filter: everything else (sell)
    # Includes: "★★" with peg >= 1.5, and all other ratings
    sell_stocks = [
        stock for stock in cached_data 
        if not (
            stock.get('quality_rating') == '★★★' or 
            (stock.get('quality_rating') == '★★' and stock.get('forward_peg') is not None and stock.get('forward_peg') < 1.0) or
            (stock.get('quality_rating') == '★★' and stock.get('peg_ratio') is not None and stock.get('peg_ratio') >= 1.0 and stock.get('peg_ratio') < 1.5)
        )
    ]
    
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


@app.route('/api/stock/<symbol>/history')
def get_stock_history(symbol):
    """
    Get historical price data for a stock with moving averages.
    GET /api/stock/{symbol}/history
    
    Fetches 1 year of OHLCV data from Yahoo Finance and calculates:
    - 50-day Simple Moving Average (SMA)
    - 200-day Simple Moving Average (SMA)
    
    Returns JSON with dates, open/high/low/close/volume + moving averages
    """
    try:
        import yfinance as yf
        from datetime import timedelta
        
        # Parse period query parameter (e.g., ?period=3y for 3 years)
        from flask import request
        period_param = request.args.get('period', '2y')  # Default to 2 years
        
        # Calculate days based on period value
        try:
            if period_param.endswith('y'):  # Years (e.g., "1y", "3y")
                years = int(period_param[:-1])
                days = years * 365
            elif period_param.endswith('w'):  # Weeks (e.g., "52w")
                weeks = int(period_param[:-1])
                days = weeks * 7
            else:
                days = 730  # Default to 2 years if invalid format
        except ValueError:
            days = 730  # Default to 2 years if parsing fails
        
        # Calculate date range based on period parameter
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch historical data from Yahoo Finance
        ticker = yf.Ticker(symbol.upper())
        hist_data = ticker.history(start=start_date, end=end_date)
        
        if hist_data.empty:
            return jsonify({
                'error': 'No historical data found',
                'message': f'Could not fetch 1 year of price history for {symbol}'
            }), 404
        
        # Calculate Simple Moving Averages (SMA)
        hist_data['sma_50'] = hist_data['Close'].rolling(window=50).mean()
        hist_data['sma_200'] = hist_data['Close'].rolling(window=200).mean()
        
        # Calculate 52-week high and low (from the last 52 weeks of data)
        recent_weeks = hist_data.tail(365)  # Last 365 days (~52 weeks)
        fifty_two_week_high = recent_weeks['High'].max()
        fifty_two_week_low = recent_weeks['Low'].min()
        
        # Convert to list of dictionaries for JSON serialization
        history_list = []
        for date, row in hist_data.iterrows():
            entry = {
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']) if not pd.isna(row['Open']) else None,
                'high': float(row['High']) if not pd.isna(row['High']) else None,
                'low': float(row['Low']) if not pd.isna(row['Low']) else None,
                'close': float(row['Close']) if not pd.isna(row['Close']) else None,
                'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                'sma_50': float(row['sma_50']) if not pd.isna(row['sma_50']) else None,
                'sma_200': float(row['sma_200']) if not pd.isna(row['sma_200']) else None
            }
            history_list.append(entry)
        
        return jsonify({
            'symbol': symbol.upper(),
            'data': history_list,
            'count': len(history_list),
            'period': '2 years',
            'fifty_two_week_high': float(fifty_two_week_high) if not pd.isna(fifty_two_week_high) else None,
            'fifty_two_week_low': float(fifty_two_week_low) if not pd.isna(fifty_two_week_low) else None
        })
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to fetch historical data',
            'message': str(e)
        }), 500


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
    buy_count = sum(
        1 for s in cached_data 
        if s.get('quality_rating') == '★★★' or 
           (s.get('quality_rating') == '★★' and s.get('forward_peg') is not None and s.get('forward_peg') < 1.0)
    )
    hold_count = sum(
        1 for s in cached_data 
        if s.get('quality_rating') == '★★' and 
           s.get('peg_ratio') is not None and 
           s.get('peg_ratio') >= 1.0 and 
           s.get('peg_ratio') < 1.5
    )
    sell_count = total - buy_count - hold_count
    
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


@app.route('/css/<path:filename>')
def serve_css(filename):
    """
    Serve CSS files from the css/ directory.
    GET /css/{filename}
    
    This allows users to access stylesheets at http://localhost:5000/css/styles.css
    """
    try:
        return send_file(f'css/{filename}', mimetype='text/css')
    except Exception as e:
        print(f"Error serving CSS {filename}: {e}")
        return jsonify({
            'error': 'CSS file not available',
            'message': str(e)
        }), 404


@app.route('/js/<path:filename>')
def serve_js(filename):
    """
    Serve JavaScript files from the js/ directory.
    GET /js/{filename}
    
    This allows users to access scripts at http://localhost:5000/js/app.js
    """
    try:
        return send_file(f'js/{filename}', mimetype='application/javascript')
    except Exception as e:
        print(f"Error serving JS {filename}: {e}")
        return jsonify({
            'error': 'JavaScript file not available',
            'message': str(e)
        }), 404


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
