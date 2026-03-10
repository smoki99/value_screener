# NASDAQ-100 Screener

A Python-based stock screener that analyzes all NASDAQ-100 stocks using Novy-Marx and multi-factor scoring methodologies. Generates beautiful interactive HTML reports with comprehensive financial metrics.

## Overview

This project fetches real-time data from Yahoo Finance for all 100 stocks in the NASDAQ-100 index, calculates various valuation and quality metrics, applies star ratings based on multiple factors, and produces an easy-to-read HTML report that categorizes stocks into "Buy", "Hold", and "Sell" recommendations.

## Features

### Data Sources
- **Yahoo Finance**: Real-time stock data including financials, balance sheets, earnings estimates, and historical prices
- **Wikipedia**: NASDAQ-100 ticker list (cached for efficiency)

### Metrics Calculated
- **Valuation Ratios**: P/E, Forward P/E, PEG ratios (GAAP & Forward), Price/Sales, Price/Book, EV/EBITDA
- **Quality Factors**: ROE, Profit Margin, Asset Growth (Novy-Marx control factor)
- **Growth Estimates**: 1-year and 2-year earnings growth projections
- **Performance**: 6-month and 12-month stock performance

### Scoring System
- **Star Ratings**: 0-5 stars based on multi-factor analysis including:
  - Forward PEG ratio (valuation)
  - ROE (quality)
  - Profit margin (profitability)
  - Asset growth control factor (Novy-Marx methodology)
- **Decile Rankings**: Percentile ranks for all key metrics
- **Quality Stars**: Separate quality assessment based on financial health

### Report Categories
Stocks are categorized into three groups:
1. **Buy** (4-5 stars): High-quality, attractively valued stocks
2. **Hold** (3 stars): Moderate recommendations requiring further analysis
3. **Sell** (0-2 stars): Overvalued or low-quality stocks to avoid

## Project Structure

```
nasdaq100_screener/
├── screener.py              # Main entry point
├── requirements.txt         # Python dependencies
├── modules/                 # Core functionality
│   ├── __init__.py         # Package exports
│   ├── config.py           # Configuration (DB path, cache settings)
│   ├── cache.py            # SQLite caching layer for stock data
│   ├── fetcher.py          # Yahoo Finance & Wikipedia data fetching
│   ├── metrics.py          # Financial metric calculations
│   ├── scoring.py          # Star rating and multi-factor scoring
│   ├── ranking.py          # Percentile rank calculations
│   ├── report.py           # Table generation and analysis
│   └── html_report.py      # Beautiful HTML report generation
├── tests/                   # Unit tests (67 passing)
│   ├── test_cache.py       # Cache module tests
│   ├── test_colors.py      # Color utility tests
│   ├── test_config.py      # Configuration tests
│   └── test_fetcher.py     # Fetcher module tests
├── nasdaq100.db            # SQLite cache database (auto-generated)
└── nasdaq100_analysis.html # Generated HTML report (auto-generated)
```

## Current State

### ✅ Completed
- Full NASDAQ-100 data fetching from Yahoo Finance with caching
- Comprehensive metric calculations (valuation, quality, growth)
- Multi-factor star rating system (Novy-Marx methodology)
- Beautiful interactive HTML report generation
- SQLite-based caching to avoid repeated API calls
- 67 passing unit tests covering core modules
- Rate limiting for sustainable API usage

### 📊 Key Statistics
- **Test Coverage**: 67 tests across 4 test files (100% pass rate)
- **Cache Duration**: 24 hours default (configurable via CACHE_MAX_AGE_HOURS)
- **Database**: SQLite with stock_cache and ticker_cache tables

## Installation

### Prerequisites
- Python 3.12+
- pip package manager

### Setup

```bash
# Clone or navigate to the project directory
cd nasdaq100_screener

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the Screener

```bash
python screener.py
```

This will:
1. Fetch or load cached NASDAQ-100 ticker list from Wikipedia
2. Analyze all 100 stocks (with rate limiting)
3. Calculate metrics, scores, and rankings
4. Generate a beautiful HTML report saved as `nasdaq100_analysis.html`
5. Cache results in SQLite database for future runs

### Run Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
python -m pytest tests/
```

## Configuration

Edit `modules/config.py` to customize:

- **DB_PATH**: Location of SQLite cache database (default: `nasdaq100.db`)
- **CACHE_MAX_AGE_HOURS**: Cache expiration time in hours (default: 24)

## Dependencies

Core dependencies from requirements.txt:
- yfinance - Yahoo Finance data API
- pandas - Data manipulation and analysis
- requests - HTTP library for Wikipedia fetching
- lxml - HTML parsing

Development dependencies:
- pytest - Testing framework

## Output Example

The generated HTML report includes:
- **Summary Statistics**: Total stocks analyzed, buy/hold/sell counts
- **Buy Recommendations Table**: 4-5 star stocks with detailed metrics
- **Hold Recommendations Table**: 3-star stocks requiring further analysis
- **Sell Avoidance Table**: 0-2 star stocks to avoid
- **Interactive Features**: Sortable columns, hover tooltips, color-coded values

## Novy-Marx Methodology

This screener implements the Novy-Marx factor model which emphasizes:
1. **Quality over Momentum**: Focus on fundamental quality metrics
2. **Asset Growth Control Factor**: Adjusts for asset growth to avoid value traps
3. **Multi-Factor Scoring**: Combines valuation, profitability, and quality into unified star ratings

## License

This project is provided as-is for educational purposes.

## Notes

- The screener uses rate limiting (0.5 second delay between API calls) to avoid being blocked by Yahoo Finance
- First run may take several minutes; subsequent runs are faster due to caching
- HTML report includes timestamp of analysis and can be opened in any modern web browser
</parameter> } }</tool_call>