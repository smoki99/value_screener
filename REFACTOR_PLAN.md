# NASDAQ-100 Screener Refactoring Plan

## Overview

This document outlines the modularization and web server implementation for the NASDAQ-100 Cheapest Quality Screener.

**Goals:**
1. Modularize monolithic `screener.py` into testable components
2. Create FastAPI web server (`server.py`) serving HTML reports
3. Achieve 60%+ code coverage with unit tests
4. Maintain existing cache behavior (24h)

---

## Module Architecture

### Directory Structure
```
value_screener/
├── screener.py              # Original monolithic file (keep for reference)
├── server.py                # FastAPI web server entry point
├── requirements.txt         # Dependencies
├── html_template.py         # HTML rendering module (existing)
├── nasdaq100_cache.db       # SQLite cache (runtime generated)
│
├── modules/
│   ├── __init__.py          # Package init
│   ├── config.py            # Configuration constants
│   ├── colors.py            # ANSI color codes & helpers
│   ├── cache.py             # SQLite caching layer
│   ├── fetcher.py           # Yahoo Finance data fetching
│   ├── metrics.py           # Metric calculations (GP/A, ROE, PEG, etc.)
│   ├── scoring.py           # Novy-Marx & Multi-Factor scoring
│   ├── ranking.py           # Percentile/decile rankings
│   └── report.py            # Report generation (terminal + HTML)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_config.py
│   ├── test_colors.py
│   ├── test_cache.py
│   ├── test_fetcher.py
│   ├── test_metrics.py
│   ├── test_scoring.py
│   ├── test_ranking.py
│   └── test_report.py
│
├── nasdaq100_screener.html  # Generated HTML report (runtime)
└── nasdaq100_cheapest_quality.csv  # CSV export (runtime)
```

---

## Module Breakdown

### 1. `modules/config.py`
**Purpose:** Centralized configuration constants.

```python
# Constants to extract:
DB_PATH = "nasdaq100_cache.db"
CACHE_MAX_AGE_HOURS = 24
```

**Test coverage target:** 100% (trivial - just verify values)

---

### 2. `modules/colors.py`
**Purpose:** ANSI color codes and colorization functions.

```python
# Class: Color (RED, GREEN, YELLOW, RESET, BOLD)
# Functions:
colorize_peg(value, formatted_str)
colorize_gm(value, formatted_str)
colorize_gpa(value, formatted_str)
colorize_roe(value, formatted_str)
colorize_pb(value, formatted_str)
colorize_decile(value, formatted_str)
colorize_nm_rank(value, formatted_str)
colorize_asset_growth(value, formatted_str)
peg_zone(value)
```

**Test coverage target:** 100% (pure functions with clear thresholds)

---

### 3. `modules/cache.py`
**Purpose:** SQLite caching layer for stock data.

```python
# Functions:
init_db(db_path=DB_PATH) -> sqlite3.Connection
is_cache_valid(fetched_at_str, max_age_hours=CACHE_MAX_AGE_HOURS) -> bool
get_cached_tickers(conn) -> list | None
save_tickers_to_cache(conn, tickers)
get_cached_stock(conn, symbol) -> dict | None
save_stock_to_cache(conn, symbol, info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates)
clear_cache(db_path=DB_PATH)
_df_to_json(df) -> str
_df_from_json(json_str) -> pd.DataFrame
```

**Test coverage target:** 80% (mock SQLite connections, test logic paths)

---

### 4. `modules/fetcher.py`
**Purpose:** Data fetching from Yahoo Finance and Wikipedia.

```python
# Functions:
fetch_growth_estimates(stock) -> dict
calculate_performance(stock) -> tuple | None
calculate_asset_growth(balance_sheet) -> float | None
deduplicate_tickers(tickers) -> list
get_nasdaq100_tickers(conn) -> list
fetch_stock_data(conn, symbol) -> dict | None
```

**Test coverage target:** 60% (mock yf.Ticker objects, test error handling)

---

### 5. `modules/metrics.py`
**Purpose:** Financial metric calculations.

```python
# Functions:
calculate_gaap_peg(info, financials) -> float | None
calculate_forward_peg(info, growth_estimates) -> tuple
get_peg_values(info, financials, growth_estimates) -> tuple
compute_metrics(data) -> dict
```

**Test coverage target:** 80% (pure functions with mock data)

---

### 6. `modules/scoring.py`
**Purpose:** Scoring models and star ratings.

```python
# Functions:
get_star_rating(value, thresholds, reverse=False, penalize_negative=False) -> int
score_novy_marx(s_gpa, s_pb, s_momentum) -> float
score_multi_factor(s1, s2, s3, s4, s5) -> float
stars_str(n) -> str
rebalancing_note() -> str
```

**Test coverage target:** 90% (pure functions with deterministic outputs)

---

### 7. `modules/ranking.py`
**Purpose:** Percentile and decile rankings.

```python
# Functions:
add_percentile_ranks(metrics) -> None  # modifies in-place
```

**Test coverage target:** 80% (test ranking calculations)

---

### 8. `modules/report.py`
**Purpose:** Report generation for terminal and HTML.

```python
# Functions:
build_unified_row(m, use_color=True) -> dict
print_table_out(df, display_cols, title, subtitle=None)
generate_html_report(metrics, timestamp) -> str
analyze_nasdaq100()  # Main orchestration function
```

**Test coverage target:** 60% (test row building, HTML generation with mock data)

---

## FastAPI Server (`server.py`)

### Architecture
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="NASDAQ-100 Screener API")

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the main screener report."""
    # Call analyze_nasdaq100() or load from cache
    # Return HTML
    pass

@app.get("/api/data")
def get_data():
    """Return raw metrics as JSON."""
    pass

@app.get("/api/cache/status")
def cache_status():
    """Show cache statistics."""
    pass

@app.post("/api/cache/clear")
def clear_cache():
    """Clear the SQLite cache."""
    pass
```

### Running the Server
```bash
python server.py  # Starts on localhost:8000
# or
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

---

## Testing Strategy (60% Coverage Target)

### Test Files & Focus Areas

| File | Lines to Cover | Priority |
|------|----------------|----------|
| `test_config.py` | All constants | High (trivial) |
| `test_colors.py` | All colorize functions + peg_zone | High (pure functions) |
| `test_cache.py` | Cache validity, JSON serialization | Medium (mock DB) |
| `test_fetcher.py` | Growth estimates, performance calc | Low (external deps) |
| `test_metrics.py` | PEG calculations, compute_metrics | High (core logic) |
| `test_scoring.py` | Star ratings, NM/MF scores | High (pure functions) |
| `test_ranking.py` | Decile calculations | Medium |
| `test_report.py` | Row building, HTML generation | Low (integration-like) |

### Coverage Calculation Strategy
- **High priority modules** (~40% of code): Aim for 80-90% coverage
- **Medium priority modules** (~30% of code): Aim for 60-70% coverage
- **Low priority modules** (~30% of code): Aim for 40-50% coverage

This weighted approach achieves ~60% overall while focusing on core business logic.

---

## Implementation Steps

### Phase 1: Module Extraction (No Behavior Change)
1. Create `modules/` directory and `__init__.py`
2. Extract config constants → `config.py`
3. Extract color functions → `colors.py`
4. Extract cache functions → `cache.py`
5. Extract fetcher functions → `fetcher.py`
6. Extract metrics calculations → `metrics.py`
7. Extract scoring logic → `scoring.py`
8. Extract ranking logic → `ranking.py`
9. Extract report generation → `report.py`
10. Update imports in original `screener.py` to use modules

### Phase 2: Unit Tests
1. Create `tests/` directory with `conftest.py`
2. Write tests for each module (start with pure functions)
3. Run coverage report: `pytest --cov=modules --cov-report=term-missing`
4. Iterate until 60%+ achieved

### Phase 3: FastAPI Server
1. Create `server.py` with endpoints
2. Integrate with modularized code
3. Add CORS middleware (optional)
4. Test server functionality

### Phase 4: Documentation & Cleanup
1. Update `requirements.txt` with FastAPI, uvicorn, pytest-cov
2. Add README with usage instructions
3. Verify all paths work correctly

---

## Dependencies to Add

```txt
# Existing:
yfinance>=0.2.0
pandas>=1.5.0
tabulate>=0.9.0
requests>=2.28.0

# New for web server:
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# New for testing:
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## Verification Checklist

- [ ] All modules importable without errors
- [ ] Original `screener.py` still works (CLI mode)
- [ ] `python server.py` starts successfully
- [ ] HTML report renders correctly in browser
- [ ] pytest passes with 60%+ coverage
- [ ] Cache behavior unchanged (24h TTL)
- [ ] All color schemes preserved
```
</parameter> task_progress: 