import yfinance as yf
import pandas as pd
from tabulate import tabulate
import requests
import io
import time
import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from html_template import render_html


# --- Konfiguration ---
DB_PATH = "nasdaq100_cache.db"
CACHE_MAX_AGE_HOURS = 24


# =====================================================================
# Farbcodes (ANSI Terminal Colors)
# =====================================================================

class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colorize_peg(value, formatted_str):
    if value is None:
        return formatted_str
    if value <= 1.0:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 1.5:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_gm(value, formatted_str):
    if value is None:
        return formatted_str
    if value >= 0.50:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.30:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_gpa(value, formatted_str):
    if value is None:
        return formatted_str
    if value >= 0.30:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.15:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_roe(value, formatted_str):
    if value is None:
        return formatted_str
    if value >= 0.20:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.10:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_pb(value, formatted_str):
    if value is None:
        return formatted_str
    if value <= 5.0:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 15.0:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_decile(value, formatted_str):
    if value is None:
        return formatted_str
    if value >= 8:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 4:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_nm_rank(value, formatted_str):
    if value is None:
        return formatted_str
    if value >= 16:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 10:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_asset_growth(value, formatted_str):
    if value is None:
        return formatted_str
    if value <= 0.10:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 0.25:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def peg_zone(value):
    if value is None:
        return ""
    if value <= 1.0:
        return "🟢GÜNSTIG"
    elif value <= 1.5:
        return "🟡FAIR"
    else:
        return "🔴TEUER"


# =====================================================================
# SQLite Cache Layer
# =====================================================================

def init_db(db_path=DB_PATH):
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

    for col in ['history_6m_json', 'history_12m_json', 'growth_estimates_json']:
        try:
            conn.execute(f"SELECT {col} FROM stock_cache LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE stock_cache ADD COLUMN {col} TEXT")
            conn.commit()

    return conn


def is_cache_valid(fetched_at_str, max_age_hours=CACHE_MAX_AGE_HOURS):
    if not fetched_at_str:
        return False
    fetched_at = datetime.fromisoformat(fetched_at_str)
    return datetime.now() - fetched_at < timedelta(hours=max_age_hours)


def get_cached_tickers(conn):
    row = conn.execute("SELECT tickers_json, fetched_at FROM ticker_cache WHERE id = 1").fetchone()
    if row and is_cache_valid(row[1]):
        tickers = json.loads(row[0])
        print(f"  Ticker-Liste aus Cache geladen ({len(tickers)} Ticker, Stand: {row[1]})")
        return tickers
    return None


def save_tickers_to_cache(conn, tickers):
    conn.execute(
        "INSERT OR REPLACE INTO ticker_cache (id, tickers_json, fetched_at) VALUES (1, ?, ?)",
        (json.dumps(tickers), datetime.now().isoformat())
    )
    conn.commit()


def get_cached_stock(conn, symbol):
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


def save_stock_to_cache(conn, symbol, info, financials, balance_sheet,
                        perf_6m, perf_12m, growth_estimates):
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


def _df_to_json(df):
    if df is None or df.empty:
        return json.dumps(None)
    return df.to_json(date_format='iso')


def _df_from_json(json_str):
    data = json.loads(json_str)
    if data is None:
        return pd.DataFrame()
    return pd.read_json(io.StringIO(json_str))


def clear_cache(db_path=DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Cache '{db_path}' gelöscht.")


# =====================================================================
# Growth Estimates
# =====================================================================

def fetch_growth_estimates(stock):
    result = {
        'growth_5y': None,
        'growth_2y': None,
        'growth_1y': None,
        'source': 'N/A',
    }

    try:
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


# =====================================================================
# Performance-Berechnung
# =====================================================================

def calculate_performance(stock):
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


# =====================================================================
# Asset Growth (Novy-Marx Kontrollfaktor)
# =====================================================================

def calculate_asset_growth(balance_sheet):
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


# =====================================================================
# Bewertungslogik
# =====================================================================

def get_star_rating(value, thresholds, reverse=False, penalize_negative=False):
    if value is None or pd.isna(value):
        return 0
    if penalize_negative and value < 0:
        return 1
    stars = 1
    for t in thresholds:
        if not reverse:
            if value >= t:
                stars += 1
        else:
            if value <= t:
                stars += 1
    return min(stars, 5)


def calculate_gaap_peg(info, financials):
    try:
        trailing_pe = info.get('trailingPE')
        if trailing_pe is None or trailing_pe <= 0:
            return None
        if financials is None or financials.empty:
            return None
        net_income = financials.loc['Net Income']
        if len(net_income) < 2:
            return None
        net_income = net_income.dropna()
        if len(net_income) < 2:
            return None
        latest = net_income.iloc[0]
        oldest = net_income.iloc[-1]
        years = len(net_income) - 1
        if oldest <= 0 or latest <= 0:
            return None
        cagr = (latest / oldest) ** (1 / years) - 1
        growth_pct = cagr * 100
        if growth_pct <= 0:
            return None
        return trailing_pe / growth_pct
    except (KeyError, IndexError, ZeroDivisionError):
        return None


def calculate_forward_peg(info, growth_estimates):
    forward_pe = info.get('forwardPE')
    if forward_pe is None or forward_pe <= 0:
        return None, None, "N/A"

    if growth_estimates is None:
        return None, None, "N/A"

    g2 = growth_estimates.get('growth_2y')
    if g2 is not None and g2 > 0:
        capped = min(g2, 0.60)
        growth_pct = capped * 100
        peg = forward_pe / growth_pct
        return peg, capped, growth_estimates.get('source', 'GE-2Y')

    g1_ge = growth_estimates.get('growth_1y')
    src = growth_estimates.get('source', 'N/A')
    if g1_ge is not None and g1_ge > 0 and (src.startswith('GE') or src.startswith('EE')):
        capped = min(g1_ge, 0.60)
        growth_pct = capped * 100
        peg = forward_pe / growth_pct
        return peg, capped, src

    if g1_ge is not None and g1_ge > 0:
        base = min(g1_ge, 0.30)
        excess = max(0, g1_ge - 0.30) * 0.2
        dampened = base + excess
        dampened = min(dampened, 0.50)
        growth_pct = dampened * 100
        peg = forward_pe / growth_pct
        return peg, dampened, f"1Y→{src}"

    return None, None, "N/A"


def get_peg_values(info, financials, growth_estimates):
    fwd_peg, growth_used, peg_source = calculate_forward_peg(info, growth_estimates)

    if fwd_peg is not None and (fwd_peg < 0 or fwd_peg > 50):
        fwd_peg = None

    gaap_peg = calculate_gaap_peg(info, financials)

    return fwd_peg, gaap_peg, growth_used, peg_source


# --- Scoring-Modelle ---

def score_novy_marx(s_gpa, s_pb, s_momentum):
    weights = {
        'gpa': (s_gpa, 0.40), 'pb': (s_pb, 0.35), 'momentum': (s_momentum, 0.25),
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    if s_pb == 1:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 3 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)


def score_multi_factor(s1, s2, s3, s4, s5):
    weights = {
        'gpa': (s1, 0.25), 'roe': (s2, 0.20), 'pb': (s3, 0.20),
        'peg': (s4, 0.15), 'momentum': (s5, 0.20),
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    if s3 == 1:
        weighted_sum = min(weighted_sum, 3.0)
    if s4 == 1 and s1 <= 3:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 5 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)


# =====================================================================
# Perzentil-Ranking (Novy-Marx Dezile)
# =====================================================================

def add_percentile_ranks(metrics):
    gpa_values = sorted([m['gp_a'] for m in metrics if m['gp_a'] is not None])
    for m in metrics:
        if m['gp_a'] is not None and len(gpa_values) > 0:
            rank = sum(1 for v in gpa_values if v <= m['gp_a'])
            m['gp_a_pctl'] = rank / len(gpa_values)
            m['gp_a_decile'] = min(10, int(m['gp_a_pctl'] * 10) + 1)
        else:
            m['gp_a_pctl'] = None
            m['gp_a_decile'] = None

    pb_values = sorted([m['pb'] for m in metrics if m['pb'] is not None])
    for m in metrics:
        if m['pb'] is not None and len(pb_values) > 0:
            rank = sum(1 for v in pb_values if v >= m['pb'])
            m['pb_pctl'] = rank / len(pb_values)
            m['pb_decile'] = min(10, int(m['pb_pctl'] * 10) + 1)
        else:
            m['pb_pctl'] = None
            m['pb_decile'] = None

    mom_values = sorted([m['perf_12m'] for m in metrics if m['perf_12m'] is not None])
    for m in metrics:
        if m['perf_12m'] is not None and len(mom_values) > 0:
            rank = sum(1 for v in mom_values if v <= m['perf_12m'])
            m['mom_pctl'] = rank / len(mom_values)
            m['mom_decile'] = min(10, int(m['mom_pctl'] * 10) + 1)
        else:
            m['mom_pctl'] = None
            m['mom_decile'] = None

    for m in metrics:
        if m['gp_a_decile'] is not None and m['pb_decile'] is not None:
            m['nm_rank'] = m['gp_a_decile'] + m['pb_decile']
        else:
            m['nm_rank'] = None


# =====================================================================
# Daten laden
# =====================================================================

def deduplicate_tickers(tickers):
    skip = {'GOOGL', 'FOXA'}
    return [t for t in tickers if t not in skip]


def get_nasdaq100_tickers(conn):
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


def fetch_stock_data(conn, symbol):
    cached = get_cached_stock(conn, symbol)
    if cached:
        return cached

    time.sleep(0.5)
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


# =====================================================================
# Analyse
# =====================================================================

def compute_metrics(data):
    info = data['info']
    financials = data['financials']
    balance_sheet = data['balance_sheet']
    perf_6m = data.get('perf_6m')
    perf_12m = data.get('perf_12m')
    growth_estimates = data.get('growth_estimates')

    gp_a = None
    gross_margin = None
    try:
        gp = financials.loc['Gross Profit'].iloc[0]
        assets = balance_sheet.loc['Total Assets'].iloc[0]
        gp_a = gp / assets
    except (KeyError, IndexError, ZeroDivisionError):
        pass

    try:
        gp = financials.loc['Gross Profit'].iloc[0]
        revenue = financials.loc['Total Revenue'].iloc[0]
        if revenue and revenue > 0:
            gross_margin = gp / revenue
    except (KeyError, IndexError, ZeroDivisionError):
        pass

    roe = info.get('returnOnEquity')
    pb = info.get('priceToBook')

    if pb is not None and pb < 0:
        pb = None

    roe_for_scoring = roe
    if roe is not None and pb is not None:
        if roe > 1.0 and pb > 50:
            roe_for_scoring = None

    fwd_peg, gaap_peg, growth_used, peg_source = get_peg_values(
        info, financials, growth_estimates
    )

    asset_growth = calculate_asset_growth(balance_sheet)

    s_gpa = get_star_rating(gp_a, [0.1, 0.2, 0.3, 0.4])
    s_roe = get_star_rating(roe_for_scoring, [0.05, 0.10, 0.20, 0.30], penalize_negative=True)
    s_pb = get_star_rating(pb, [40.0, 20.0, 10.0, 5.0], reverse=True, penalize_negative=True)
    s_fwd_peg = get_star_rating(fwd_peg, [2.5, 2.0, 1.5, 1.0], reverse=True)
    s_mom = get_star_rating(perf_12m, [0.0, 0.10, 0.25, 0.50])

    name = info.get('shortName') or info.get('longName') or ''

    return {
        'symbol': info.get('symbol', ''),
        'name': name,
        'gp_a': gp_a,
        'gross_margin': gross_margin,
        'roe': roe,
        'pb': pb,
        'fwd_peg': fwd_peg,
        'gaap_peg': gaap_peg,
        'growth_used': growth_used,
        'peg_source': peg_source,
        'asset_growth': asset_growth,
        'perf_6m': perf_6m,
        'perf_12m': perf_12m,
        's_gpa': s_gpa,
        's_roe': s_roe,
        's_pb': s_pb,
        's_fwd_peg': s_fwd_peg,
        's_mom': s_mom,
        'gp_a_decile': None,
        'pb_decile': None,
        'mom_decile': None,
        'nm_rank': None,
    }


def stars_str(n):
    if n <= 0:
        return "—"
    return "⭐" * n


def rebalancing_note():
    month = datetime.now().month
    if month in [6, 7]:
        return "🔄 REBALANCING-FENSTER: Juni/Juli — Novy-Marx empfiehlt jährliches Rebalancing jetzt!"
    next_rebal = "Juli" if month < 7 else "Juli nächstes Jahr"
    return f"📅 Nächstes Rebalancing: {next_rebal}"


def build_unified_row(m, use_color=True):
    nm = score_novy_marx(m['s_gpa'], m['s_pb'], m['s_mom'])
    mf = score_multi_factor(m['s_gpa'], m['s_roe'], m['s_pb'], m['s_fwd_peg'], m['s_mom'])

    best = max(nm, mf)
    if best >= 4.5:
        quality = "★★★"
    elif best >= 3.5:
        quality = "★★"
    elif best >= 2.5:
        quality = "★"
    else:
        quality = "—"

    gpa_val = m['gp_a']
    gpa_display = colorize_gpa(gpa_val, f"{gpa_val * 100:.1f}%") if gpa_val is not None and use_color else (f"{gpa_val * 100:.1f}%" if gpa_val is not None else "N/A")

    gm_val = m['gross_margin']
    gm_display = colorize_gm(gm_val, f"{gm_val * 100:.1f}%") if gm_val is not None and use_color else (f"{gm_val * 100:.1f}%" if gm_val is not None else "N/A")

    roe_val = m['roe']
    roe_display = colorize_roe(roe_val, f"{roe_val * 100:.1f}%") if roe_val is not None and use_color else (f"{roe_val * 100:.1f}%" if roe_val is not None else "N/A")

    pb_val = m['pb']
    pb_display = colorize_pb(pb_val, f"{pb_val:.2f}") if pb_val is not None and use_color else (f"{pb_val:.2f}" if pb_val is not None else "N/A")

    fwd_peg_val = m['fwd_peg']
    fwd_peg_display = colorize_peg(fwd_peg_val, f"{fwd_peg_val:.2f}") if fwd_peg_val is not None and use_color else (f"{fwd_peg_val:.2f}" if fwd_peg_val is not None else "N/A")

    gaap_peg_val = m['gaap_peg']
    gaap_peg_display = colorize_peg(gaap_peg_val, f"{gaap_peg_val:.2f}") if gaap_peg_val is not None and use_color else (f"{gaap_peg_val:.2f}" if gaap_peg_val is not None else "N/A")

    growth = m['growth_used']
    growth_str = f"{growth * 100:.0f}%" if growth is not None else "N/A"

    ag_val = m['asset_growth']
    ag_display = colorize_asset_growth(ag_val, f"{ag_val * 100:+.0f}%") if ag_val is not None and use_color else (f"{ag_val * 100:+.0f}%" if ag_val is not None else "N/A")

    gpa_d = m.get('gp_a_decile')
    gpa_d_display = colorize_decile(gpa_d, str(gpa_d)) if gpa_d is not None and use_color else (str(gpa_d) if gpa_d is not None else "—")

    pb_d = m.get('pb_decile')
    pb_d_display = colorize_decile(pb_d, str(pb_d)) if pb_d is not None and use_color else (str(pb_d) if pb_d is not None else "—")

    nm_rank = m.get('nm_rank')
    nm_rank_display = colorize_nm_rank(nm_rank, str(nm_rank)) if nm_rank is not None and use_color else (str(nm_rank) if nm_rank is not None else "—")

    zone = peg_zone(fwd_peg_val)

    return {
        "Symbol": m['symbol'],
        "Name": m['name'],
        "GP/A": gpa_display,
        "GM": gm_display,
        "ROE": roe_display,
        "P/B": pb_display,
        "NM": nm,
        "NM★": stars_str(round(nm)),
        "MF": mf,
        "MF★": stars_str(round(mf)),
        "Qual": quality,
        "fPEG": fwd_peg_display,
        "gPEG": gaap_peg_display,
        "Grw%": growth_str,
        "Src": m['peg_source'],
        "Zone": zone,
        "D.GP": gpa_d_display,
        "D.PB": pb_d_display,
        "NMR": nm_rank_display,
        "AG": ag_display,
        "6M": f"{m['perf_6m'] * 100:+.1f}%" if m['perf_6m'] is not None else "N/A",
        "12M": f"{m['perf_12m'] * 100:+.1f}%" if m['perf_12m'] is not None else "N/A",
        "_fPEG_sort": fwd_peg_val if fwd_peg_val is not None else float('inf'),
        "_NM": nm,
        "_raw": m,
    }


# =====================================================================
# HTML Report Generator (uses html_template.py)
# =====================================================================

def generate_html_report(metrics, timestamp):
    all_rows = []
    for m in metrics:
        nm = score_novy_marx(m['s_gpa'], m['s_pb'], m['s_mom'])
        mf = score_multi_factor(m['s_gpa'], m['s_roe'], m['s_pb'], m['s_fwd_peg'], m['s_mom'])
        best = max(nm, mf)
        if best >= 4.5:
            quality = "★★★"
        elif best >= 3.5:
            quality = "★★"
        elif best >= 2.5:
            quality = "★"
        else:
            quality = "—"

        all_rows.append({
            'symbol': m['symbol'],
            'name': m['name'],
            'gp_a': m['gp_a'],
            'gross_margin': m['gross_margin'],
            'roe': m['roe'],
            'pb': m['pb'],
            'nm': nm,
            'mf': mf,
            'quality': quality,
            'fwd_peg': m['fwd_peg'],
            'gaap_peg': m['gaap_peg'],
            'growth_used': m['growth_used'],
            'peg_source': m['peg_source'],
            'asset_growth': m['asset_growth'],
            'gp_a_decile': m.get('gp_a_decile'),
            'pb_decile': m.get('pb_decile'),
            'mom_decile': m.get('mom_decile'),
            'nm_rank': m.get('nm_rank'),
            'perf_6m': m['perf_6m'],
            'perf_12m': m['perf_12m'],
        })

    all_rows.sort(key=lambda r: r['fwd_peg'] if r['fwd_peg'] is not None else float('inf'))

    sweet = [r for r in all_rows if r['fwd_peg'] is not None and (r['nm'] >= 3.5 or r['mf'] >= 3.5)]
    traps = [r for r in all_rows if r['fwd_peg'] is not None and r['nm'] < 2.5 and r['mf'] < 2.5]
    no_peg = sorted([r for r in all_rows if r['fwd_peg'] is None], key=lambda r: -r['nm'])

    divergent = []
    for r in all_rows:
        if r['fwd_peg'] is not None and r['gaap_peg'] is not None and r['gaap_peg'] > 0:
            ratio = r['fwd_peg'] / r['gaap_peg']
            if ratio < 0.5 or ratio > 2.0:
                divergent.append({**r, 'ratio': ratio,
                                  'signal': '📈 Bullish' if ratio < 1 else '📉 Bearish'})

    nm_top = sorted([r for r in all_rows if r['nm_rank'] is not None],
                    key=lambda r: -r['nm_rank'])

    return render_html({
        'TIMESTAMP': timestamp,
        'REBALANCE_NOTE': rebalancing_note(),
        'ALL_DATA': json.dumps(all_rows, default=str),
        'SWEET_DATA': json.dumps(sweet, default=str),
        'TRAPS_DATA': json.dumps(traps, default=str),
        'NO_PEG_DATA': json.dumps(no_peg, default=str),
        'DIVERGENT_DATA': json.dumps(divergent, default=str),
        'NM_TOP_DATA': json.dumps(nm_top, default=str),
    })


# =====================================================================
# Terminal Output
# =====================================================================

def print_table_out(df, display_cols, title, subtitle=None):
    print(f"\n{'=' * 160}")
    print(f"  {title}")
    print(f"{'=' * 160}")
    if subtitle:
        if isinstance(subtitle, list):
            for line in subtitle:
                print(f"  {line}")
        else:
            print(f"  {subtitle}")
    print()
    print(tabulate(df[display_cols], headers='keys', tablefmt='psql', showindex=False))


def analyze_nasdaq100():
    conn = init_db()

    tickers = get_nasdaq100_tickers(conn)
    if not tickers:
        print("ERROR: Konnte NASDAQ-100 Ticker nicht laden.")
        conn.close()
        return

    tickers = deduplicate_tickers(tickers)
    metrics = []
    cached_count = 0
    fetched_count = 0

    print(f"\nAnalysiere {len(tickers)} Aktien...")
    print(f"Cache: '{DB_PATH}' (max. Alter: {CACHE_MAX_AGE_HOURS}h)\n")

    for i, symbol in enumerate(tickers):
        if (i + 1) % 10 == 0:
            print(f"  Fortschritt: {i + 1}/{len(tickers)}... "
                  f"(Cache: {cached_count}, API: {fetched_count})")

        was_cached = get_cached_stock(conn, symbol) is not None

        data = fetch_stock_data(conn, symbol)
        if data is None:
            print(f"  Überspringe {symbol}: Keine Daten verfügbar.")
            continue

        if was_cached:
            cached_count += 1
        else:
            fetched_count += 1

        try:
            m = compute_metrics(data)
            if m:
                metrics.append(m)
        except Exception as e:
            print(f"  Fehler bei Analyse von {symbol}: {e}")
            continue

    conn.close()

    if not metrics:
        print("ERROR: Keine Ergebnisse.")
        return

    # === Perzentil-Ranking berechnen (NACH dem Sammeln aller Metriken) ===
    add_percentile_ranks(metrics)

    sources = {}
    for m in metrics:
        src = m['peg_source']
        sources[src] = sources.get(src, 0) + 1

    print(f"\n  Datenquelle: {cached_count} aus Cache, {fetched_count} von Yahoo Finance")
    print(f"  Forward PEG Quellen: {dict(sorted(sources.items(), key=lambda x: -x[1]))}")
    print(f"  {rebalancing_note()}")

    # --- Terminal Output ---
    rows = [build_unified_row(m, use_color=True) for m in metrics]
    df = pd.DataFrame(rows)
    df = df.sort_values(by='_fPEG_sort')

    display_cols = ["Symbol", "Name", "GP/A", "GM", "ROE", "P/B",
                    "NM", "NM★", "MF", "MF★", "Qual",
                    "fPEG", "gPEG", "Grw%", "Src", "Zone",
                    "D.GP", "D.PB", "NMR", "AG", "6M", "12M"]

    legend = [
        "NM   = Novy-Marx (GP/A 40% + P/B 35% + Momentum 25%)",
        "MF   = Multi-Factor (GP/A 25% + ROE 20% + P/B 20% + fPEG 15% + Mom 20%)",
        "NMR  = NM Rank (GP/A Dezil + P/B Dezil, 2–20) | AG = Asset Growth (niedrig=gut)",
        "Qual = ★★★ (≥4.5) | ★★ (≥3.5) | ★ (≥2.5)",
        f"GP/A: {Color.GREEN}■ ≥30%{Color.RESET}  "
        f"{Color.YELLOW}■ 15–30%{Color.RESET}  "
        f"{Color.RED}■ <15%{Color.RESET}     "
        f"GM:  {Color.GREEN}■ ≥50%{Color.RESET}  "
        f"{Color.YELLOW}■ 30–50%{Color.RESET}  "
        f"{Color.RED}■ <30%{Color.RESET}",
        f"ROE:  {Color.GREEN}■ ≥20%{Color.RESET}  "
        f"{Color.YELLOW}■ 10–20%{Color.RESET}  "
        f"{Color.RED}■ <10%{Color.RESET}     "
        f"P/B: {Color.GREEN}■ ≤5{Color.RESET}  "
        f"{Color.YELLOW}■ 5–15{Color.RESET}  "
        f"{Color.RED}■ >15{Color.RESET}",
        f"PEG:  {Color.GREEN}■ ≤1.0 GÜNSTIG{Color.RESET}  "
        f"{Color.YELLOW}■ 1.0–1.5 FAIR{Color.RESET}  "
        f"{Color.RED}■ >1.5 TEUER{Color.RESET}",
        f"AG:   {Color.GREEN}■ ≤10%{Color.RESET}  "
        f"{Color.YELLOW}■ 10–25%{Color.RESET}  "
        f"{Color.RED}■ >25%{Color.RESET}     "
        f"Dezil: {Color.GREEN}■ 8–10{Color.RESET}  "
        f"{Color.YELLOW}■ 4–7{Color.RESET}  "
        f"{Color.RED}■ 1–3{Color.RESET}",
    ]

    print_table_out(df, display_cols,
                    "NASDAQ-100: CHEAPEST QUALITY — sortiert nach Forward PEG",
                    legend)

    sweet = df[(df['_fPEG_sort'] < float('inf')) & ((df['_NM'] >= 3.5) | (df['MF'] >= 3.5))].copy()
    if not sweet.empty:
        print_table_out(sweet, display_cols,
                        "💎 SWEET SPOT: Günstiger Forward PEG + Hohe Qualität (NM oder MF ≥ 3.5)")

    # NM Rank Top
    nm_rank_col = [build_unified_row(m, use_color=True) for m in
                   sorted([m for m in metrics if m.get('nm_rank') is not None],
                          key=lambda x: -x['nm_rank'])]
    if nm_rank_col:
        df_nmr = pd.DataFrame(nm_rank_col)
        print_table_out(df_nmr, display_cols,
                        "📊 NOVY-MARX RANK: Sortiert nach kombiniertem GP/A + P/B Dezil-Rang (höher=besser)")

    traps = df[(df['_fPEG_sort'] < float('inf')) & (df['_NM'] < 2.5) & (df['MF'] < 2.5)].copy()
    if not traps.empty:
        print_table_out(traps, display_cols,
                        "⚠️  VALUE TRAPS: Niedriger fPEG aber schlechte Qualität (NM und MF < 2.5)")

    no_peg = df[df['_fPEG_sort'] == float('inf')].copy()
    no_peg = no_peg.sort_values(by='_NM', ascending=False)
    if not no_peg.empty:
        print_table_out(no_peg, display_cols,
                        "📊 KEIN FORWARD PEG VERFÜGBAR — sortiert nach NM Score")

    # --- HTML Report ---
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = generate_html_report(metrics, timestamp)
    html_file = "nasdaq100_screener.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n  🌐 HTML Report → '{html_file}'")

    # --- CSV Export ---
    csv_rows = [build_unified_row(m, use_color=False) for m in metrics]
    df_csv = pd.DataFrame(csv_rows)
    df_csv = df_csv.sort_values(by='_fPEG_sort')
    csv_cols = ["Symbol", "Name", "GP/A", "GM", "ROE", "P/B", "NM", "MF", "Qual",
                "fPEG", "gPEG", "Grw%", "Src", "Zone", "D.GP", "D.PB", "NMR", "AG", "6M", "12M"]
    df_csv[csv_cols].to_csv("nasdaq100_cheapest_quality.csv", index=False)
    print(f"  📊 CSV Export → 'nasdaq100_cheapest_quality.csv'")


def print_usage():
    print(f"""
NASDAQ-100 Cheapest Quality Screener v10

Verwendung:
    python nasdaq100_quality_value.py [OPTIONEN]

Optionen:
    --clear-cache  Cache löschen und neu laden
    --no-color     Farbausgabe deaktivieren
    --help         Diese Hilfe anzeigen

Novy-Marx Faktoren:
    GP/A     Gross Profit / Total Assets (Kernfaktor)
    P/B      Price / Book (Value-Komplement)
    Momentum 12M-Performance
    D.GP     GP/A Dezil im Universum (1-10, 10=best)
    D.PB     P/B Dezil im Universum (1-10, 10=cheapest)
    NMR      NM Rank = D.GP + D.PB (2-20, höher=besser)
    AG       Asset Growth (niedrig = bessere zukünftige Returns)

Farbschema:
    GP/A: {Color.GREEN}■ ≥30%{Color.RESET}  {Color.YELLOW}■ 15–30%{Color.RESET}  {Color.RED}■ <15%{Color.RESET}
    GM:   {Color.GREEN}■ ≥50%{Color.RESET}  {Color.YELLOW}■ 30–50%{Color.RESET}  {Color.RED}■ <30%{Color.RESET}
    ROE:  {Color.GREEN}■ ≥20%{Color.RESET}  {Color.YELLOW}■ 10–20%{Color.RESET}  {Color.RED}■ <10%{Color.RESET}
    P/B:  {Color.GREEN}■ ≤5{Color.RESET}    {Color.YELLOW}■ 5–15{Color.RESET}    {Color.RED}■ >15{Color.RESET}
    PEG:  {Color.GREEN}■ ≤1.0{Color.RESET}  {Color.YELLOW}■ 1.0–1.5{Color.RESET} {Color.RED}■ >1.5{Color.RESET}
    AG:   {Color.GREEN}■ ≤10%{Color.RESET}  {Color.YELLOW}■ 10–25%{Color.RESET}  {Color.RED}■ >25%{Color.RESET}
    Dezil:{Color.GREEN}■ 8–10{Color.RESET}  {Color.YELLOW}■ 4–7{Color.RESET}     {Color.RED}■ 1–3{Color.RESET}

Ausgabe:
    1. Terminal:  Farbige Tabellen mit allen Kategorien
    2. HTML:      nasdaq100_screener.html (interaktiv, sortierbar, 6 Tabs)
    3. CSV:       nasdaq100_cheapest_quality.csv
""")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)

    if "--clear-cache" in args:
        clear_cache()
        args.remove("--clear-cache")
        if not args:
            sys.exit(0)

    if "--no-color" in args:
        Color.RED = ""
        Color.GREEN = ""
        Color.YELLOW = ""
        Color.RESET = ""
        Color.BOLD = ""
        args.remove("--no-color")

    start = time.time()
    analyze_nasdaq100()
    elapsed = time.time() - start
    print(f"\nLaufzeit: {elapsed:.1f}s")