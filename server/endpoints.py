"""
NASDAQ-100 Screener - API Endpoints

All API endpoint handlers for stock data, recommendations, and analysis.
Provides route registration functions that are called from server.app module.
"""

import sys
from datetime import datetime, timedelta
from flask import jsonify, request
import yfinance as yf
import pandas as pd

# Import data processing functions - use absolute imports since paths are added in app.py
try:
    from data_processing import (
        convert_percentages_to_whole_numbers,
        sanitize_for_json,
        run_analysis,
    )
except ImportError:
    # Fallback if imported directly without path setup
    pass

# Global variables that will be set by the calling module
app = None
cached_data = None
cache_timestamp = None
db_conn = None


def init_endpoints(flask_app, data=None, timestamp=None, conn=None):
    """
    Initialize endpoints - called from server.app main block.
    This function registers all routes with the Flask app and sets globals.
    
    Args:
        flask_app: The Flask application instance
        data: Cached stock data (optional)
        timestamp: Cache timestamp (optional)
        conn: Database connection (optional)
    """
    global app, cached_data, cache_timestamp, db_conn
    
    # Set globals from calling module
    app = flask_app
    cached_data = data
    cache_timestamp = timestamp
    db_conn = conn
    
    # Register all routes with the Flask app
    register_all_routes()


def register_all_routes():
    """
    Register all API routes with the Flask app.
    This is called after globals are set by init_endpoints().
    """
    global app
    
    # ============================================================================
    # STOCK DATA ENDPOINTS
    # ============================================================================
    
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
        
        # Filter: rounded star rating >= 4 AND <= 5 AND forward_peg <= 1.5 - buy recommendations
        buy_stocks = [
            stock for stock in cached_data 
            if stock.get('star_rating') is not None and 
               round(stock.get('star_rating')) >= 4 and 
               round(stock.get('star_rating')) <= 5 and
               (stock.get('forward_peg') is None or stock.get('forward_peg') <= 1.5)
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
        
        # Filter: rounded star rating == 3 AND forward_peg <= 1.5 - hold recommendations
        hold_stocks = [
            stock for stock in cached_data 
            if stock.get('star_rating') is not None and 
               round(stock.get('star_rating')) == 3 and
               (stock.get('forward_peg') is None or stock.get('forward_peg') <= 1.5)
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
        
        # Filter: rounded star rating <= 2 OR quality_rating is '★' or '—' OR forward_peg > 1.5 - sell/avoid recommendations
        sell_stocks = [
            stock for stock in cached_data 
            if (stock.get('star_rating') is None or round(stock.get('star_rating')) <= 2) or
               stock.get('quality_rating') == '★' or
               stock.get('quality_rating') == '—' or
               (stock.get('forward_peg') is not None and stock.get('forward_peg') > 1.5)
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
            # Parse period query parameter (e.g., ?period=3y for 3 years)
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
    
    # ============================================================================
    # STATS AND ANALYSIS ENDPOINTS
    # ============================================================================
    
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
        
        # Calculate statistics by counting actual filter results
        total = len(cached_data)
        
        # Count buy: rounded star rating >= 4 AND <= 5 AND forward_peg <= 1.5
        # Ensure each item is a dict before calling .get()
        buy_count = sum(
            1 for s in cached_data 
            if isinstance(s, dict) and
               s.get('star_rating') is not None and 
               round(s.get('star_rating')) >= 4 and 
               round(s.get('star_rating')) <= 5 and
               (s.get('forward_peg') is None or s.get('forward_peg') <= 1.5)
        )
        
        # Count hold: rounded star rating == 3 AND forward_peg <= 1.5
        # Ensure each item is a dict before calling .get()
        hold_count = sum(
            1 for s in cached_data 
            if isinstance(s, dict) and
               s.get('star_rating') is not None and 
               round(s.get('star_rating')) == 3 and
               (s.get('forward_peg') is None or s.get('forward_peg') <= 1.5)
        )
        
        # Count sell: rounded star rating <= 2 OR quality_rating is '★' or '—' OR forward_peg > 1.5
        # Ensure each item is a dict before calling .get()
        sell_count = sum(
            1 for s in cached_data 
            if isinstance(s, dict) and
               ((s.get('star_rating') is None or round(s.get('star_rating')) <= 2) or
                s.get('quality_rating') == '★' or
                s.get('quality_rating') == '—' or
                (s.get('forward_peg') is not None and s.get('forward_peg') > 1.5))
        )
        
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
            # Import init_db from modules
            from modules import init_db, DB_PATH
            
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
