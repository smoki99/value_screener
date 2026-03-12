"""
NASDAQ-100 Screener Web Server - Flask App

Flask application initialization, configuration, and frontend serving.
No multi-threading - SQLite is not made for this.
On startup: auto-refresh data if older than 24 hours.
"""

import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os

# Add parent directory to path so we can import modules and server submodules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, script_dir)

from modules import DB_PATH, init_db
from modules.logging_config import setup_logging, get_logger

# Setup logging at module level - this must be done early
logger = setup_logging()

# Configuration for large-cap filtering
USE_LARGECAP = os.environ.get('USE_LARGECAP', 'true').lower() == 'true'
MIN_MARKET_CAP = float(os.environ.get('MIN_MARKET_CAP', '10e9'))  # Default $10B

# Initialize Flask app - must be done BEFORE importing endpoints
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
db_conn = None
cached_data = None
cache_timestamp = None

# Import init_endpoints function (routes are registered when called, not at import time)
from endpoints import init_endpoints


def get_latest_cache():
    """
    Fetch latest cache from database and return (data, timestamp).
    Called after run_analysis updates the cache.
    """
    global db_conn
    try:
        cursor = db_conn.execute(
            "SELECT tickers_json, fetched_at FROM ticker_cache ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            import json
            parsed_data = json.loads(row[0])
            timestamp = row[1]
            return parsed_data, timestamp
    except Exception as e:
        logger.error("Error fetching latest cache: %s", e)
        return None, None
    return None, None


def init_server():
    """
    Initialize server with database connection.
    Auto-refresh data if older than 24 hours.
    Returns: tuple of (cached_data, cache_timestamp) for passing to init_endpoints
    """
    global db_conn, cached_data, cache_timestamp
    
    # Import run_analysis - use absolute import since we added paths above
    from data_processing import run_analysis
    
    # Initialize database
    db_conn = init_db(DB_PATH)
    logger.info("Database initialized: %s", DB_PATH)
    
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
            logger.info("Found cached data from: %s", cache_timestamp)
            
            # Validate data structure - must be list of dictionaries
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                if isinstance(parsed_data[0], dict):
                    cached_data = parsed_data
                    logger.info("Cache contains %d stocks", len(cached_data))
                    
                    # Check if older than 24 hours - auto refresh
                    last_fetch = datetime.fromisoformat(cache_timestamp)
                    age_hours = (datetime.now() - last_fetch).total_seconds() / 3600
                    logger.info("Cache age: %.1f hours", age_hours)
                    
                    if age_hours > 24:
                        logger.warning("Data is older than 24 hours. Auto-refreshing...")
                        run_analysis(db_conn)  # Pass the connection!
                        cached_data, cache_timestamp = get_latest_cache()  # Update globals after refresh
                    else:
                        logger.info("Using cached data (%d stocks)", len(cached_data))
                else:
                    # Invalid structure - fetch fresh
                    logger.warning("Invalid cache format (not list of dicts). Fetching fresh data...")
                    run_analysis(db_conn)  # Pass the connection!
                    cached_data, cache_timestamp = get_latest_cache()  # Update globals after refresh
            else:
                # Empty or invalid - fetch fresh
                logger.warning("Empty or invalid cache. Fetching fresh data...")
                run_analysis(db_conn)  # Pass the connection!
                cached_data, cache_timestamp = get_latest_cache()  # Update globals after refresh
        else:
            # No cached data - fetch fresh
            logger.info("No cached data found. Fetching fresh data...")
            run_analysis(db_conn)  # Pass the connection!
            cached_data, cache_timestamp = get_latest_cache()  # Update globals after refresh
    except Exception as e:
        logger.error("Error loading cache: %s", e)
        import traceback
        traceback.print_exc()
        logger.warning("Fetching fresh data...")
        run_analysis(db_conn)  # Pass the connection!
        cached_data, cache_timestamp = get_latest_cache()  # Update globals after refresh
    
    # Return globals for passing to init_endpoints
    return cached_data, cache_timestamp


# ============================================================================
# HEALTH CHECK ENDPOINT
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


# ============================================================================
# FRONTEND SERVING ENDPOINTS
# ============================================================================

@app.route('/')
def serve_frontend():
    """
    Serve the frontend HTML file.
    GET /
    
    This allows users to access the web interface at http://localhost:5000/
    Frontend files are in parent directory (not server/ subdirectory).
    """
    try:
        # Frontend.html is in parent directory, not in server/ subdirectory
        return send_file(os.path.join(parent_dir, 'frontend.html'), mimetype='text/html')
    except Exception as e:
        logger.error("Error serving frontend: %s", e)
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
    CSS files are in parent directory (not server/ subdirectory).
    """
    try:
        # CSS files are in parent directory, not in server/ subdirectory
        return send_file(os.path.join(parent_dir, 'css', filename), mimetype='text/css')
    except Exception as e:
        logger.error("Error serving CSS %s: %s", filename, e)
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
    JS files are in parent directory (not server/ subdirectory).
    """
    try:
        # JS files are in parent directory, not in server/ subdirectory
        return send_file(os.path.join(parent_dir, 'js', filename), mimetype='application/javascript')
    except Exception as e:
        logger.error("Error serving JS %s: %s", filename, e)
        return jsonify({
            'error': 'JavaScript file not available',
            'message': str(e)
        }), 404


# ============================================================================
# INITIALIZATION - Runs at import time (not just in main block)
# This ensures routes are registered when flask loads the app via "flask run"
# ============================================================================

logger.info("Initializing NASDAQ-100 Screener Server...")
init_server()
init_endpoints(app, cached_data, cache_timestamp, db_conn)

logger.info("")
logger.info("=" * 60)
logger.info("NASDAQ-100 Screener Server")
logger.info("=" * 60)
logger.info("")
logger.info("Server ready on http://localhost:5000")
logger.info("")
logger.info("API Endpoints:")
logger.info("  GET /health                    - Health check")
logger.info("  GET /api/stocks                - All stock data")
logger.info("  GET /api/buy-recommendations   - 4-5 star stocks")
logger.info("  GET /api/hold-recommendations  - 3 star stocks")
logger.info("  GET /api/sell-avoidance        - 0-2 star stocks")
logger.info("  GET /api/stock/{symbol}        - Individual stock by symbol")
logger.info("  GET /api/stats                 - Summary statistics")
logger.info("  POST /api/analyze              - Trigger fresh analysis")


# ============================================================================
# MAIN - Only runs when executed directly (python server/app.py)
# ============================================================================

if __name__ == '__main__':
    logger.info("")
    logger.info("Press Ctrl+C to stop server")
    
    # Run Flask app with threading disabled
    from werkzeug.serving import WSGIRequestHandler
    
    class SingleThreadedWSGIRequestHandler(WSGIRequestHandler):
        def process_request(self, *args, **kwargs):
            self.server = type('obj', (object,), {'threading': False})()
            super().process_request(*args, **kwargs)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=False
    )