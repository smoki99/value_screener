#!/bin/bash
# NASDAQ-100 Screener - Docker Test Runner with Local Cache DB

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$HOME/.nasdaq-screener-cache"
DB_FILE="$CACHE_DIR/screener.db"

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"
touch "$DB_FILE"
echo "Using local cache database: $DB_FILE"

# Build Docker image (if not already built)
docker build -t nasdaq-screener "$SCRIPT_DIR" > /dev/null 2>&1 || true

echo "========================================"
echo "Running NASDAQ-100 Screener Tests"
echo "========================================"
echo "Cache DB: $DB_FILE"

# Run Docker container with cache volume mount and test mode
docker run --rm \
    -v "$CACHE_DIR:/app/cache" \
    -e CACHE_DB_PATH="/app/cache/screener.db" \
    nasdaq-screener \
    bash -c "source venv/bin/activate && python -m pytest tests/ -v && npm test"

echo "========================================"
echo "Tests completed!"
echo "========================================"
