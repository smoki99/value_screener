"""
SQLite caching layer for stock data.

Caches ticker lists and individual stock data to avoid repeated API calls.
Cache entries expire after CACHE_MAX_AGE_HOURS (default 24 hours).
"""

import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
import io

from .config import DB_PATH, CACHE_MAX_AGE_HOURS


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initialize the SQLite database with required tables.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Database connection object
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_cache (
            symbol TEXT PRIMARY KEY,
            info_json TEXT,
            financials_json TEXT,
            balance_sheet_json TEXT,
            history_6m_json TEXT,
            history_12m_json TEXT,
            growth_estimates_json TEXT,
            fetched_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ticker_cache (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            tickers_json TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()

    # Add missing columns if table was created before they existed
    for col in ['history_6m_json', 'history_12m_json', 'growth_estimates_json']:
        try:
            conn.execute(f"SELECT {col} FROM stock_cache LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE stock_cache ADD COLUMN {col} TEXT")
            conn.commit()

    return conn


def is_cache_valid(fetched_at_str: str | None, max_age_hours: int = CACHE_MAX_AGE_HOURS) -> bool:
    """Check if a cached entry is still valid.
    
    Args:
        fetched_at_str: ISO format datetime string when data was fetched
        max_age_hours: Maximum age in hours before cache expires
        
    Returns:
        True if cache is valid, False otherwise
    """
    if not fetched_at_str:
        return False
    fetched_at = datetime.fromisoformat(fetched_at_str)
    return datetime.now() - fetched_at < timedelta(hours=max_age_hours)


def get_cached_tickers(conn: sqlite3.Connection) -> list | None:
    """Get cached ticker list if valid.
    
    Args:
        conn: Database connection
        
    Returns:
        List of tickers if cache is valid, None otherwise
    """
    row = conn.execute("SELECT tickers_json, fetched_at FROM ticker_cache WHERE id = 1").fetchone()
    if row and is_cache_valid(row[1]):
        tickers = json.loads(row[0])
        print(f"  Ticker-Liste aus Cache geladen ({len(tickers)} Ticker, Stand: {row[1]})")
        return tickers
    return None


def save_tickers_to_cache(conn: sqlite3.Connection, tickers: list) -> None:
    """Save ticker list to cache.
    
    Args:
        conn: Database connection
        tickers: List of ticker symbols
    """
    conn.execute(
        "INSERT OR REPLACE INTO ticker_cache (id, tickers_json, fetched_at) VALUES (1, ?, ?)",
        (json.dumps(tickers), datetime.now().isoformat())
    )
    conn.commit()


def get_cached_stock(conn: sqlite3.Connection, symbol: str) -> dict | None:
    """Get cached stock data if valid.
    
    Args:
        conn: Database connection
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with stock data if cache is valid, None otherwise
    """
    row = conn.execute(
        "SELECT info_json, financials_json, balance_sheet_json, "
        "history_6m_json, history_12m_json, growth_estimates_json, fetched_at "
        "FROM stock_cache WHERE symbol = ?",
        (symbol,)
    ).fetchone()
    if row and is_cache_valid(row[6]):
        return {
            'info': json.loads(row[0]),
            'financials': _df_from_json(row[1]),
            'balance_sheet': _df_from_json(row[2]),
            'perf_6m': json.loads(row[3]) if row[3] else None,
            'perf_12m': json.loads(row[4]) if row[4] else None,
            'growth_estimates': json.loads(row[5]) if row[5] else None,
        }
    return None


def save_stock_to_cache(
    conn: sqlite3.Connection,
    symbol: str,
    info: dict,
    financials: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    perf_6m: float | None,
    perf_12m: float | None,
    growth_estimates: dict
) -> None:
    """Save stock data to cache.
    
    Args:
        conn: Database connection
        symbol: Stock ticker symbol
        info: Stock info dictionary
        financials: Financial statements DataFrame
        balance_sheet: Balance sheet DataFrame
        perf_6m: 6-month performance
        perf_12m: 12-month performance
        growth_estimates: Growth estimates dictionary
    """
    conn.execute(
        "INSERT OR REPLACE INTO stock_cache "
        "(symbol, info_json, financials_json, balance_sheet_json, "
        "history_6m_json, history_12m_json, growth_estimates_json, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            symbol,
            json.dumps(info, default=str),
            _df_to_json(financials),
            _df_to_json(balance_sheet),
            json.dumps(perf_6m),
            json.dumps(perf_12m),
            json.dumps(growth_estimates),
            datetime.now().isoformat()
        )
    )
    conn.commit()


def _df_to_json(df: pd.DataFrame | None) -> str:
    """Convert DataFrame to JSON string.
    
    Args:
        df: Pandas DataFrame or None
        
    Returns:
        JSON string representation of the DataFrame
    """
    if df is None or df.empty:
        return json.dumps(None)
    return df.to_json(date_format='iso')


def _df_from_json(json_str: str) -> pd.DataFrame:
    """Convert JSON string to DataFrame.
    
    Args:
        json_str: JSON string representation of a DataFrame
        
    Returns:
        Pandas DataFrame or empty DataFrame if None
    """
    data = json.loads(json_str)
    if data is None:
        return pd.DataFrame()
    return pd.read_json(io.StringIO(json_str))


def clear_cache(db_path: str = DB_PATH) -> None:
    """Delete the cache database file.
    
    Args:
        db_path: Path to the SQLite database file
    """
    import os
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Cache '{db_path}' gelöscht.")
