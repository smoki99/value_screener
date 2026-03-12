# NASDAQ-100 Screener

A Python-based stock screener with web interface that analyzes all NASDAQ-100 stocks using Novy-Marx and multi-factor scoring methodologies. Generates beautiful interactive HTML reports with comprehensive financial metrics, gauge charts, and candlestick visualizations.

## Overview

This project fetches real-time data from Yahoo Finance for all 100 stocks in the NASDAQ-100 index, calculates various valuation and quality metrics, applies star ratings based on multiple factors, and produces an easy-to-read HTML report that categorizes stocks into "Buy", "Hold", and "Sell" recommendations. It includes a Flask-based API server with REST endpoints for programmatic access to stock data.

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

### Web Interface Features
- Interactive tables with sortable columns and color-coded metrics
- Gauge charts showing GP/A, Gross Margin, and ROE percentages
- Candlestick charts with 50-day and 200-day Simple Moving Averages (SMA)
- Real-time data refresh capability
- Responsive design for desktop and mobile viewing

## Project Structure

```
value_screener/
├── server/                # Flask API server components
│   ├── app.py            # Application initialization, configuration, frontend serving
│   ├── data_processing.py# Data conversion and sanitization functions
│   └── endpoints.py      # API endpoint handlers (routes registered dynamically)
├── frontend.html          # Web interface HTML file
├── requirements.txt       # Python dependencies
├── css/styles.css         # Frontend styles (responsive design)
├── js/app.js             # Frontend JavaScript (Chart.js integration)
├── modules/               # Core functionality
│   ├── __init__.py       # Package exports
│   ├── config.py         # Configuration (DB path, cache settings)
│   ├── cache.py          # SQLite caching layer for stock data
│   ├── fetcher.py        # Yahoo Finance & Wikipedia data fetching
│   ├── metrics.py        # Financial metric calculations
│   ├── scoring.py        # Star rating and multi-factor scoring
│   ├── ranking.py        # Percentile rank calculations
│   ├── report.py         # Analysis and table generation
│   ├── colors.py         # Color coding utilities for Novy-Marx thresholds
│   ├── html_report.py    # HTML report generation functions
│   ├── html_template.py  # HTML template rendering
│   └── logging_config.py # Logging configuration setup
├── tests/                 # Unit tests (67 Python + ~10 JavaScript)
│   ├── test_cache.py     # Cache module tests
│   ├── test_colors.py    # Color utility tests
│   ├── test_config.py    # Configuration tests
│   ├── test_fetcher.py   # Fetcher module tests
│   ├── test_metrics.py   # Metrics calculation tests
│   └── js/               # JavaScript unit tests with Jest
├── Dockerfile             # Container configuration for deployment
├── build-docker.sh        # Script to build Docker image
├── start-docker.sh        # Script to run container with port mapping
├── nasdaq100_cache.db    # SQLite cache database (auto-generated)
└── README.md             # This documentation file
```

## Current State

### ✅ Completed
- Full NASDAQ-100 data fetching from Yahoo Finance with caching
- Comprehensive metric calculations (valuation, quality, growth)
- Multi-factor star rating system (Novy-Marx methodology)
- Beautiful interactive HTML report generation
- Flask-based API server with REST endpoints
- SQLite-based caching to avoid repeated API calls
- 67 passing unit tests covering core modules
- Rate limiting for sustainable API usage
- Gauge charts using Chart.js + datalabels plugin
- Candlestick charts with moving averages (50-day, 200-day SMA)

### 📊 Key Statistics
- **Test Coverage**: 67 tests across multiple test files (100% pass rate)
- **Cache Duration**: 24 hours default (configurable via CACHE_MAX_AGE_HOURS)
- **Database**: SQLite with stock_cache and ticker_cache tables
- **API Endpoints**: 10+ REST endpoints for programmatic access

## Installation

### Prerequisites
- Python 3.12+
- pip package manager

### Setup

```bash
# Clone or navigate to the project directory
cd value_screener

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

## Quick Start

### Using Startup Scripts (Recommended)

**Linux/Mac:**
```bash
chmod +x start.sh && ./start.sh
```

**Windows:**
- Double-click `start.bat` or run in Command Prompt:
```cmd
start.bat
```

The startup scripts automatically:
1. Create virtual environment if missing
2. Activate the environment
3. Install dependencies from requirements.txt
4. Start the server on http://localhost:5000

### Manual Startup

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server/app.py
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python server\app.py
```

## Usage

### Run the Web Server

```bash
python server.py
```

This will:
1. Initialize SQLite cache database (nasdaq100_cache.db)
2. Auto-refresh data if older than 24 hours
3. Start Flask API server on http://localhost:5000
4. Serve web interface at http://localhost:5000/

### Access the Web Interface

Open your browser and navigate to:
- **Web Interface**: http://localhost:5000/
- **API Endpoints**: See below for available endpoints

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with cache status |
| `/api/stocks` | GET | All stock data as JSON |
| `/api/buy-recommendations` | GET | 4-5 star stocks (buy recommendations) |
| `/api/hold-recommendations` | GET | 3 star stocks (hold recommendations) |
| `/api/sell-avoidance` | GET | 0-2 star stocks (sell/avoid recommendations) |
| `/api/stats` | GET | Summary statistics (total, buy, hold, sell counts) |
| `/api/stock/{symbol}` | GET | Individual stock details by ticker symbol |
| `/api/stock/{symbol}/history` | GET | Historical OHLCV data with moving averages |
| `/api/analyze` | POST | Trigger fresh analysis from Yahoo Finance |

### Example API Usage

```bash
# Get all stocks
curl http://localhost:5000/api/stocks

# Get buy recommendations only
curl http://localhost:5000/api/buy-recommendations

# Get summary statistics
curl http://localhost:5000/api/stats

# Get individual stock details by symbol
curl http://localhost:5000/api/stock/AAPL

# Get historical price data with moving averages (2 years default)
curl "http://localhost:5000/api/stock/AAPL/history"

# Get 3 years of historical data
curl "http://localhost:5000/api/stock/AAPL/history?period=3y"

# Trigger fresh analysis
curl -X POST http://localhost:5000/api/analyze
```

### Run Tests

**Using test.sh (Recommended):**
```bash
chmod +x test.sh && ./test.sh
```

The test script automatically:
1. Creates virtual environment if missing
2. Installs Python dependencies and pytest
3. Runs all Python tests with verbose output
4. Installs Node.js dependencies (Jest) if needed
5. Runs JavaScript unit tests

**Manual Test Run:**
```bash
# Install pytest if not already installed
pip install pytest

# Run all Python tests
python -m pytest tests/
```

**JavaScript Tests with Jest:**
```bash
# Install Node.js dependencies
npm install

# Run JavaScript unit tests
npm test
```

The project includes:
- **67 Python tests** covering core modules (cache, metrics, scoring, etc.)
- **~10 JavaScript tests** for utility functions and table operations

## Configuration

### Python Configuration

Edit `modules/config.py` to customize:

- **DB_PATH**: Location of SQLite cache database (default: `nasdaq100_cache.db`)
- **CACHE_MAX_AGE_HOURS**: Cache expiration time in hours (default: 24)

Example configuration:
```python
# modules/config.py
DB_PATH = "nasdaq100_cache.db"
CACHE_MAX_AGE_HOURS = 24
```

### Environment Variables

The server supports the following environment variables for runtime configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LARGECAP` | `true` | Enable large-cap filtering (true/false) |
| `MIN_MARKET_CAP` | `10e9` | Minimum market cap in dollars ($10B default) |

Example usage:
```bash
# Linux/Mac - filter stocks with minimum $20B market cap
export USE_LARGECAP=true
export MIN_MARKET_CAP=20e9
python server/app.py
```

```cmd
:: Windows - disable large-cap filtering
set USE_LARGECAP=false
python server\app.py
```

## Dependencies

Core dependencies from requirements.txt:
- **yfinance** - Yahoo Finance data API
- **pandas** - Data manipulation and analysis
- **requests** - HTTP library for Wikipedia fetching
- **lxml** - HTML parsing
- **Flask** - Web framework for API server
- **flask-cors** - CORS support for frontend access

Development dependencies:
- **pytest** - Testing framework

## Output Example

The web interface includes:
- **Summary Statistics**: Total stocks analyzed, buy/hold/sell counts with color-coded cards
- **Buy Recommendations Table**: 4-5 star stocks with detailed metrics and sortable columns
- **Hold Recommendations Table**: 3-star stocks requiring further analysis
- **Sell Avoidance Table**: 0-2 star stocks to avoid
- **Interactive Features**:
  - Click any stock row to view detailed information in a modal
  - Gauge charts showing GP/A, Gross Margin, and ROE percentages
  - Candlestick charts with moving averages (50-day, 200-day SMA)
  - Color-coded values based on Novy-Marx thresholds

## Novy-Marx Methodology

This screener implements the Novy-Marx factor model which emphasizes:
1. **Quality over Momentum**: Focus on fundamental quality metrics
2. **Asset Growth Control Factor**: Adjusts for asset growth to avoid value traps
3. **Multi-Factor Scoring**: Combines valuation, profitability, and quality into unified star ratings

### Color Coding Thresholds

| Metric | Green (Good) | Yellow (Moderate) | Red (Poor) |
|--------|--------------|-------------------|------------|
| GP/A | ≥30% | 15-30% | <15% |
| Gross Margin | ≥50% | 30-50% | <30% |
| ROE | ≥20% | 10-20% | <10% |
| P/B Ratio | ≤5 | 5-15 | >15 |
| PEG Ratio | ≤1.0 | 1.0-1.5 | >1.5 |

## License

This project is provided as-is for educational purposes.

## Notes

- The screener uses rate limiting (0.5 second delay between API calls) to avoid being blocked by Yahoo Finance
- First run may take several minutes; subsequent runs are faster due to caching
- Web interface includes timestamp of analysis and can be opened in any modern web browser
- SQLite database is not thread-safe, so the server runs with threading disabled for stability

## Docker Deployment

The project supports containerized deployment using Docker.

### Build Docker Image

```bash
# Make build script executable (if needed)
chmod +x build-docker.sh

# Build the Docker image
./build-docker.sh
```

This creates a Docker image named `value_screener` based on the provided Dockerfile.

### Run Container

```bash
# Make start script executable (if needed)
chmod +x start-docker.sh

# Run container with port mapping to localhost:5000
./start-docker.sh
```

The container will:
1. Start the Flask API server on port 5000
2. Map the port to your host machine (http://localhost:5000)
3. Auto-refresh data if older than 24 hours on startup
4. Serve both web interface and REST API endpoints

### Manual Docker Commands

```bash
# Build image manually
docker build -t value_screener .

# Run container with port mapping
docker run -p 5000:5000 --name value_screener_container value_screener
```

### Stop and Remove Container

```bash
# Stop running container
docker stop value_screener_container

# Remove container (optional)
docker rm value_screener_container
```

## Technical Specifications

For detailed calculation formulas and threshold specifications, see [`financial_ratio.md`](financial_ratio.md):
- Forward PEG growth source priority rules (GE-2Y → EE-2Y → GE-1Y → info-eGr)
- Star rating thresholds for all metrics (GP/A, ROE, P/B, fPEG, Momentum 12M)
- Quality star ratings methodology
- Decile ranking calculations

### Forward PEG Growth Source Priority

The screener uses a priority-based approach to determine growth estimates:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | GE-2Y | Blended 2-year from stock.growth_estimates (0y + 1y) |
| 2 | EE-2Y | Blended 2-year from stock.earnings_estimate (0y + 1y) |
| 3 | GE-1Y / EE-1Y | Single year '+1y' value directly |
| 4 | info-eGr | Fallback to stock.info['earningsGrowth'] with dampening |

### Growth Capping Rules

| Source Type | Cap | Dampening Formula |
|-------------|-----|-------------------|
| GE-2Y / EE-2Y | 60% | None |
| GE-1Y / EE-1Y | 60% | None |
| info-eGr | 50% (dampened) | base = min(g, 30%) + max(0, g - 30%) × 20% |

### Scoring Model Weight Comparison

**Novy-Marx Score:**
- GP/A: 40%
- P/B: 35%
- Momentum 12M: 25%

**Multi-Factor Score:**
- GP/A: 25%
- ROE: 20%
- P/B: 20%
- fPEG: 15%
- Momentum 12M: 20%

### Quality Star Ratings

Based on best(NM, MF) combined score:

| Quality | Score Range |
|---------|-------------|
| ★★★ | ≥ 4.5 |
| ★★ | ≥ 3.5 |
| ★ | ≥ 2.5 |
| — | < 2.5 |
