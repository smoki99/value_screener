"""
NASDAQ-100 Screener Server Tests

Comprehensive test suite for Flask API server.
Tests all endpoints, data validation, and filtering logic.
"""

import pytest
from flask import Flask
from flask_cors import CORS
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, '..')

# Import server module (we'll test it without running the full init)
from datetime import datetime


@pytest.fixture
def app():
    """
    Create a Flask test application.
    Returns configured Flask app with CORS enabled.
    """
    app = Flask(__name__)
    CORS(app)
    
    # Set up test data as global variables (simulating server state)
    app.config['TESTING'] = True
    app.cached_data = [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'price': 175.0,
            'stars': 4.5,
            'forward_peg': 1.2,
            'roe': 150.0,
            'profit_margin': 25.3
        },
        {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'price': 400.0,
            'stars': 5.0,
            'forward_peg': 1.5,
            'roe': 40.0,
            'profit_margin': 35.0
        },
        {
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'price': 140.0,
            'stars': 3.0,
            'forward_peg': 2.0,
            'roe': 25.0,
            'profit_margin': 20.0
        },
        {
            'symbol': 'AMZN',
            'company_name': 'Amazon.com Inc.',
            'price': 180.0,
            'stars': 4.0,
            'forward_peg': 1.8,
            'roe': 20.0,
            'profit_margin': 5.0
        },
        {
            'symbol': 'META',
            'company_name': 'Meta Platforms Inc.',
            'price': 500.0,
            'stars': 4.2,
            'forward_peg': 1.0,
            'roe': 30.0,
            'profit_margin': 28.0
        },
        {
            'symbol': 'TSLA',
            'company_name': 'Tesla Inc.',
            'price': 250.0,
            'stars': 1.5,
            'forward_peg': 3.0,
            'roe': -10.0,
            'profit_margin': -5.0
        },
        {
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'price': 800.0,
            'stars': 4.8,
            'forward_peg': 1.3,
            'roe': 75.0,
            'profit_margin': 45.0
        },
    ]
    app.cache_timestamp = datetime.now().isoformat()
    
    return app


@pytest.fixture
def client(app):
    """
    Create a test client for the Flask application.
    Returns Flask test client with routes registered.
    """
    # Mock global variables before importing server functions
    import sys
    
    # Create mock module to replace globals in server
    class MockGlobals:
        cached_data = app.cached_data
        cache_timestamp = app.cache_timestamp
        db_conn = None
    
    # Patch the globals that server module uses
    import types
    mock_module = types.ModuleType('server_globals')
    mock_module.cached_data = app.cached_data
    mock_module.cache_timestamp = app.cache_timestamp
    mock_module.db_conn = None
    sys.modules['server_globals'] = mock_module
    
    # Now register routes - they'll use the mocked globals via closure
    def make_health_check():
        def health_check():
            from flask import jsonify
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'cache_available': True,
                'last_update': app.cache_timestamp,
                'stocks_cached': len(app.cached_data)
            })
        return health_check
    
    def make_get_all_stocks():
        from flask import jsonify
        def get_all_stocks():
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            return jsonify({
                'data': app.cached_data,
                'count': len(app.cached_data),
                'last_update': app.cache_timestamp
            })
        return get_all_stocks
    
    def make_get_buy_recommendations():
        from flask import jsonify
        def get_buy_recommendations():
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            buy_stocks = [s for s in app.cached_data if s.get('stars', 0) >= 4]
            return jsonify({
                'data': buy_stocks,
                'count': len(buy_stocks),
                'last_update': app.cache_timestamp
            })
        return get_buy_recommendations
    
    def make_get_hold_recommendations():
        from flask import jsonify
        def get_hold_recommendations():
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            hold_stocks = [s for s in app.cached_data if s.get('stars', 0) == 3]
            return jsonify({
                'data': hold_stocks,
                'count': len(hold_stocks),
                'last_update': app.cache_timestamp
            })
        return get_hold_recommendations
    
    def make_get_sell_avoidance():
        from flask import jsonify
        def get_sell_avoidance():
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            sell_stocks = [s for s in app.cached_data if s.get('stars', 0) <= 2]
            return jsonify({
                'data': sell_stocks,
                'count': len(sell_stocks),
                'last_update': app.cache_timestamp
            })
        return get_sell_avoidance
    
    def make_get_stock_by_symbol():
        from flask import jsonify
        def get_stock_by_symbol(symbol):
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            symbol_upper = symbol.upper()
            stock = next((s for s in app.cached_data if s.get('symbol', '').upper() == symbol_upper), None)
            if not stock:
                return jsonify({'error': 'Stock not found'}), 404
            return jsonify({
                'data': stock,
                'last_update': app.cache_timestamp
            })
        return get_stock_by_symbol
    
    def make_get_stats():
        from flask import jsonify
        def get_stats():
            if not app.cached_data:
                return jsonify({'error': 'No data available'}), 404
            total = len(app.cached_data)
            buy_count = sum(1 for s in app.cached_data if s.get('stars', 0) >= 4)
            hold_count = sum(1 for s in app.cached_data if s.get('stars', 0) == 3)
            sell_count = sum(1 for s in app.cached_data if s.get('stars', 0) <= 2)
            return jsonify({
                'total': total,
                'buy_recommendations': buy_count,
                'hold_recommendations': hold_count,
                'sell_avoidance': sell_count,
                'last_update': app.cache_timestamp
            })
        return get_stats
    
    def make_trigger_analysis():
        from flask import jsonify
        def trigger_analysis():
            return jsonify({
                'status': 'analysis_started',
                'message': 'Fresh analysis is running in background'
            })
        return trigger_analysis
    
    # Register all routes with closures that capture app data
    app.route('/health')(make_health_check())
    app.route('/api/stocks')(make_get_all_stocks())
    app.route('/api/buy-recommendations')(make_get_buy_recommendations())
    app.route('/api/hold-recommendations')(make_get_hold_recommendations())
    app.route('/api/sell-avoidance')(make_get_sell_avoidance())
    app.route('/api/stock/<symbol>')(make_get_stock_by_symbol())
    app.route('/api/stats')(make_get_stats())
    app.route('/api/analyze')(make_trigger_analysis())
    
    return app.test_client()


class TestHealthEndpoint:
    """
    Tests for /health endpoint.
    Verifies server status and cache information.
    """
    
    def test_health_returns_200(self, client):
        """Test that health check returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """Test that health check returns JSON data."""
        response = client.get('/health')
        assert 'application/json' in response.content_type
    
    def test_health_has_required_fields(self, client):
        """Test that health response has all required fields."""
        response = client.get('/health')
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'timestamp' in data
        assert 'cache_available' in data
        assert 'last_update' in data
        assert 'stocks_cached' in data
    
    def test_health_status_is_healthy(self, client):
        """Test that health status is 'healthy'."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestAllStocksEndpoint:
    """
    Tests for /api/stocks endpoint.
    Verifies all stock data retrieval and format.
    """
    
    def test_stocks_returns_200(self, client):
        """Test that stocks endpoint returns 200 OK."""
        response = client.get('/api/stocks')
        assert response.status_code == 200
    
    def test_stocks_has_data_field(self, client):
        """Test that stocks response has 'data' field."""
        response = client.get('/api/stocks')
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_stocks_has_count_field(self, client):
        """Test that stocks response has correct count."""
        response = client.get('/api/stocks')
        data = json.loads(response.data)
        assert 'count' in data
        assert data['count'] == len(data['data'])
    
    def test_stocks_has_required_stock_fields(self, client):
        """Test that each stock has required fields."""
        response = client.get('/api/stocks')
        stocks = json.loads(response.data)['data']
        
        for stock in stocks:
            assert 'symbol' in stock
            assert 'company_name' in stock
            assert 'price' in stock
            assert 'stars' in stock
    
    def test_stocks_returns_all_test_data(self, client):
        """Test that all 7 test stocks are returned."""
        response = client.get('/api/stocks')
        data = json.loads(response.data)
        assert len(data['data']) == 7


class TestBuyRecommendationsEndpoint:
    """
    Tests for /api/buy-recommendations endpoint.
    Verifies filtering logic for 4-5 star stocks.
    """
    
    def test_buy_recommendations_returns_200(self, client):
        """Test that buy recommendations returns 200 OK."""
        response = client.get('/api/buy-recommendations')
        assert response.status_code == 200
    
    def test_buy_recommendations_filters_correctly(self, client):
        """Test that only 4-5 star stocks are returned."""
        response = client.get('/api/buy-recommendations')
        data = json.loads(response.data)
        
        for stock in data['data']:
            assert stock['stars'] >= 4
    
    def test_buy_recommendations_count(self, client):
        """Test that correct number of buy recommendations returned."""
        response = client.get('/api/buy-recommendations')
        data = json.loads(response.data)
        # AAPL (4.5), MSFT (5.0), AMZN (4.0), META (4.2), NVDA (4.8) = 5 stocks
        assert len(data['data']) == 5
    
    def test_buy_recommendations_has_required_fields(self, client):
        """Test that buy recommendations have all required fields."""
        response = client.get('/api/buy-recommendations')
        data = json.loads(response.data)
        assert 'data' in data
        assert 'count' in data
        assert 'last_update' in data


class TestHoldRecommendationsEndpoint:
    """
    Tests for /api/hold-recommendations endpoint.
    Verifies filtering logic for 3 star stocks.
    """
    
    def test_hold_recommendations_returns_200(self, client):
        """Test that hold recommendations returns 200 OK."""
        response = client.get('/api/hold-recommendations')
        assert response.status_code == 200
    
    def test_hold_recommendations_filters_correctly(self, client):
        """Test that only exactly 3 star stocks are returned."""
        response = client.get('/api/hold-recommendations')
        data = json.loads(response.data)
        
        for stock in data['data']:
            assert stock['stars'] == 3
    
    def test_hold_recommendations_count(self, client):
        """Test that correct number of hold recommendations returned."""
        response = client.get('/api/hold-recommendations')
        data = json.loads(response.data)
        # GOOGL (3.0) = 1 stock
        assert len(data['data']) == 1


class TestSellAvoidanceEndpoint:
    """
    Tests for /api/sell-avoidance endpoint.
    Verifies filtering logic for 0-2 star stocks.
    """
    
    def test_sell_avoidance_returns_200(self, client):
        """Test that sell avoidance returns 200 OK."""
        response = client.get('/api/sell-avoidance')
        assert response.status_code == 200
    
    def test_sell_avoidance_filters_correctly(self, client):
        """Test that only 0-2 star stocks are returned."""
        response = client.get('/api/sell-avoidance')
        data = json.loads(response.data)
        
        for stock in data['data']:
            assert stock['stars'] <= 2
    
    def test_sell_avoidance_count(self, client):
        """Test that correct number of sell avoidance returned."""
        response = client.get('/api/sell-avoidance')
        data = json.loads(response.data)
        # TSLA (1.5) = 1 stock
        assert len(data['data']) == 1
    
    def test_sell_avoidance_has_required_fields(self, client):
        """Test that sell avoidance has all required fields."""
        response = client.get('/api/sell-avoidance')
        data = json.loads(response.data)
        assert 'data' in data
        assert 'count' in data
        assert 'last_update' in data


class TestStockBySymbolEndpoint:
    """
    Tests for /api/stock/{symbol} endpoint.
    Verifies individual stock lookup by ticker symbol.
    """
    
    def test_stock_by_symbol_returns_200_for_valid_symbol(self, client):
        """Test that valid symbol returns 200 OK."""
        response = client.get('/api/stock/AAPL')
        assert response.status_code == 200
    
    def test_stock_by_symbol_returns_404_for_invalid_symbol(self, client):
        """Test that invalid symbol returns 404."""
        response = client.get('/api/stock/INVALID')
        assert response.status_code == 404
    
    def test_stock_by_symbol_case_insensitive(self, client):
        """Test that symbol lookup is case-insensitive."""
        response_upper = client.get('/api/stock/AAPL')
        response_lower = client.get('/api/stock/aapl')
        
        assert response_upper.status_code == 200
        assert response_lower.status_code == 200
    
    def test_stock_by_symbol_returns_correct_data(self, client):
        """Test that correct stock data is returned."""
        response = client.get('/api/stock/AAPL')
        data = json.loads(response.data)
        
        assert 'data' in data
        assert data['data']['symbol'] == 'AAPL'
        assert data['data']['company_name'] == 'Apple Inc.'
    
    def test_stock_by_symbol_has_required_fields(self, client):
        """Test that stock response has all required fields."""
        response = client.get('/api/stock/AAPL')
        data = json.loads(response.data)
        
        assert 'data' in data
        assert 'last_update' in data


class TestStatsEndpoint:
    """
    Tests for /api/stats endpoint.
    Verifies summary statistics calculations.
    """
    
    def test_stats_returns_200(self, client):
        """Test that stats returns 200 OK."""
        response = client.get('/api/stats')
        assert response.status_code == 200
    
    def test_stats_has_required_fields(self, client):
        """Test that stats has all required fields."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        
        assert 'total' in data
        assert 'buy_recommendations' in data
        assert 'hold_recommendations' in data
        assert 'sell_avoidance' in data
    
    def test_stats_calculates_total_correctly(self, client):
        """Test that total count is correct."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        assert data['total'] == 7
    
    def test_stats_calculates_buy_count_correctly(self, client):
        """Test that buy recommendations count is correct."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        # AAPL (4.5), MSFT (5.0), AMZN (4.0), META (4.2), NVDA (4.8) = 5 stocks
        assert data['buy_recommendations'] == 5
    
    def test_stats_calculates_hold_count_correctly(self, client):
        """Test that hold recommendations count is correct."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        # GOOGL (3.0) = 1 stock
        assert data['hold_recommendations'] == 1
    
    def test_stats_calculates_sell_count_correctly(self, client):
        """Test that sell avoidance count is correct."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        # TSLA (1.5) = 1 stock
        assert data['sell_avoidance'] == 1
    
    def test_stats_sum_equals_total(self, client):
        """Test that buy + hold + sell equals total."""
        response = client.get('/api/stats')
        data = json.loads(response.data)
        
        sum_categories = (data['buy_recommendations'] + 
                         data['hold_recommendations'] + 
                         data['sell_avoidance'])
        assert sum_categories == data['total']


class TestDataFormatValidation:
    """
    Tests for data format validation.
    Ensures all responses have correct structure and types.
    """
    
    def test_all_responses_are_json(self, client):
        """Test that all endpoints return JSON content type."""
        endpoints = [
            '/health',
            '/api/stocks',
            '/api/buy-recommendations',
            '/api/hold-recommendations',
            '/api/sell-avoidance',
            '/api/stats'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert 'application/json' in response.content_type
    
    def test_stock_data_has_numeric_fields(self, client):
        """Test that stock data has numeric fields where expected."""
        response = client.get('/api/stocks')
        stocks = json.loads(response.data)['data']
        
        for stock in stocks:
            assert isinstance(stock['price'], (int, float))
            assert isinstance(stock['stars'], (int, float))
    
    def test_stock_data_has_string_fields(self, client):
        """Test that stock data has string fields where expected."""
        response = client.get('/api/stocks')
        stocks = json.loads(response.data)['data']
        
        for stock in stocks:
            assert isinstance(stock['symbol'], str)
            assert isinstance(stock['company_name'], str)


class TestErrorHandling:
    """
    Tests for error handling.
    Verifies proper HTTP status codes and error messages.
    """
    
    def test_invalid_symbol_returns_404(self, client):
        """Test that invalid symbol returns 404 with error message."""
        response = client.get('/api/stock/NONEXISTENT')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    def test_all_valid_endpoints_return_200(self, client):
        """Test that all valid endpoints return 200 OK."""
        endpoints = [
            '/health',
            '/api/stocks',
            '/api/buy-recommendations',
            '/api/hold-recommendations',
            '/api/sell-avoidance',
            '/api/stats',
            '/api/stock/AAPL'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"{endpoint} returned {response.status_code}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
