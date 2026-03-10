"""
Data fetching from Yahoo Finance and Wikipedia.

Handles all external API calls for stock data retrieval.
"""

import yfinance as yf
import pandas as pd
import requests
import io
from typing import Any

from .cache import get_cached_stock, save_stock_to_cache


def fetch_growth_estimates(stock: yf.Ticker) -> dict:
    """Fetch growth estimates from Yahoo Finance.
    
    Tries multiple sources in order of preference:
    1. stock.growth_estimates (2-year blend)
    2. stock.earnings_estimate (2-year blend)
    3. info['earningsGrowth']
    
    Args:
        stock: yfinance Ticker object
        
    Returns:
        Dictionary with growth_5y, growth_2y, growth_1y, and source keys
    """
    result = {
        'growth_5y': None,
        'growth_2y': None,
        'growth_1y': None,
        'source': 'N/A',
    }

    try:
        # Try growth_estimates first
        try:
            ge = stock.growth_estimates
            if ge is not None and not ge.empty and 'stockTrend' in ge.columns:
                g_0y = None
                g_1y = None

                if '+1y' in ge.index:
                    val = ge.loc['+1y', 'stockTrend']
                    if pd.notna(val):
                        if isinstance(val, str):
                            val = float(val.replace('%', '').replace(',', '.')) / 100
                        g_1y = float(val)

                if '0y' in ge.index:
                    val = ge.loc['0y', 'stockTrend']
                    if pd.notna(val):
                        if isinstance(val, str):
                            val = float(val.replace('%', '').replace(',', '.')) / 100
                        g_0y = float(val)

                if g_0y is not None and g_1y is not None and g_0y > -1 and g_1y > -1:
                    blend = ((1 + g_0y) * (1 + g_1y)) ** 0.5 - 1
                    if blend > 0:
                        result['growth_2y'] = blend
                        result['source'] = 'GE-2Y'

                if result['growth_2y'] is None and g_1y is not None and g_1y > 0:
                    result['growth_1y'] = g_1y
                    result['source'] = 'GE-1Y'
        except Exception:
            pass

        # Try earnings_estimate if growth_estimates failed
        if result['growth_2y'] is None and result['growth_1y'] is None:
            try:
                ee = stock.earnings_estimate
                if ee is not None and not ee.empty and 'growth' in ee.columns:
                    g_0y = None
                    g_1y = None

                    if '+1y' in ee.index:
                        val = ee.loc['+1y', 'growth']
                        if pd.notna(val):
                            g_1y = float(val)

                    if '0y' in ee.index:
                        val = ee.loc['0y', 'growth']
                        if pd.notna(val):
                            g_0y = float(val)

                    if g_0y is not None and g_1y is not None and g_0y > -1 and g_1y > -1:
                        blend = ((1 + g_0y) * (1 + g_1y)) ** 0.5 - 1
                        if blend > 0:
                            result['growth_2y'] = blend
                            result['source'] = 'EE-2Y'

                    if result['growth_2y'] is None and g_1y is not None and g_1y > 0:
                        result['growth_1y'] = g_1y
                        result['source'] = 'EE-1Y'
            except Exception:
                pass

        # Fallback to info earningsGrowth
        if result['growth_2y'] is None and result['growth_1y'] is None:
            try:
                info = stock.info
                eg = info.get('earningsGrowth')
                if eg is not None and eg > 0:
                    result['growth_1y'] = float(eg)
                    result['source'] = 'info-eGr'
            except Exception:
                pass

    except Exception:
        pass

    return result


def calculate_performance(stock: yf.Ticker) -> tuple[float | None, float | None]:
    """Calculate 6-month and 12-month performance.
    
    Args:
        stock: yfinance Ticker object
        
    Returns:
        Tuple of (perf_6m, perf_12m) or (None, None) on error
    """
    try:
        hist = stock.history(period="1y")
        if hist is None or hist.empty or len(hist) < 2:
            return None, None

        end_price = hist['Close'].iloc[-1]

        start_12m = hist['Close'].iloc[0]
        perf_12m = (end_price - start_12m) / start_12m if start_12m > 0 else None

        half = len(hist) // 2
        start_6m = hist['Close'].iloc[half]
        perf_6m = (end_price - start_6m) / start_6m if start_6m > 0 else None

        return perf_6m, perf_12m
    except Exception:
        return None, None


def calculate_asset_growth(balance_sheet: pd.DataFrame) -> float | None:
    """Calculate asset growth rate (Novy-Marx control factor).
    
    Args:
        balance_sheet: Balance sheet DataFrame from yfinance
        
    Returns:
        Asset growth rate as decimal, or None if not calculable
    """
    try:
        if balance_sheet is None or balance_sheet.empty:
            return None
        assets = balance_sheet.loc['Total Assets']
        if len(assets) >= 2:
            latest = assets.iloc[0]
            previous = assets.iloc[1]
            if previous > 0:
                return (latest - previous) / previous
    except (KeyError, IndexError):
        pass
    return None


def deduplicate_tickers(tickers: list[str]) -> list[str]:
    """Remove duplicate ticker pairs.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Deduplicated list (removes GOOGL, FOXA)
    """
    skip = {'GOOGL', 'FOXA'}
    return [t for t in tickers if t not in skip]


def get_nasdaq100_tickers(conn: Any) -> list[str]:
    """Get NASDAQ-100 ticker list from Wikipedia.
    
    Args:
        conn: Database connection for caching
        
    Returns:
        List of ticker symbols, empty list on error
    """
    from .cache import get_cached_tickers, save_tickers_to_cache
    
    cached = get_cached_tickers(conn)
    if cached:
        return cached

    print("  Lade Ticker-Liste von Wikipedia...")
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Konnte Wikipedia nicht erreichen: {e}")
        return []

    tables = pd.read_html(io.StringIO(response.text))
    for table in tables:
        if 'Ticker' in table.columns:
            tickers = table['Ticker'].tolist()
            save_tickers_to_cache(conn, tickers)
            print(f"  {len(tickers)} Ticker geladen und gecacht.")
            return tickers
    return []


def fetch_stock_data(conn: Any, symbol: str) -> dict | None:
    """Fetch complete stock data with caching.
    
    Args:
        conn: Database connection for caching
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with info, financials, balance_sheet, perf_6m, perf_12m,
        growth_estimates; or None on error
    """
    from .cache import get_cached_stock, save_stock_to_cache
    
    cached = get_cached_stock(conn, symbol)
    if cached:
        return cached

    time.sleep(0.5)  # Rate limiting
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        if not info or info.get('regularMarketPrice') is None:
            return None

        financials = stock.financials
        balance_sheet = stock.balance_sheet
        perf_6m, perf_12m = calculate_performance(stock)
        growth_estimates = fetch_growth_estimates(stock)

        save_stock_to_cache(conn, symbol, info, financials, balance_sheet,
                            perf_6m, perf_12m, growth_estimates)

        return {
            'info': info,
            'financials': financials,
            'balance_sheet': balance_sheet,
            'perf_6m': perf_6m,
            'perf_12m': perf_12m,
            'growth_estimates': growth_estimates,
        }
    except Exception as e:
        print(f"  Fehler beim Laden von {symbol}: {e}")
        return None
