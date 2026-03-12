#!/bin/bash
# NASDAQ-100 Screener - Local Docker Test Runner

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$HOME/.nasdaq-screener-cache"

# Ensure local cache exists
mkdir -p "$CACHE_DIR"

echo "Building local test image..."
docker build -t nasdaq-screener-test "$SCRIPT_DIR"

echo "========================================"
echo "Running NASDAQ-100 Screener Tests"
echo "========================================"

# Run the tests inside the container
# Note: No 'source venv' needed as deps are installed to global python site-packages
docker run --rm \
    -v "$CACHE_DIR:/app/cache" \
    -e CACHE_DB_PATH="/app/cache/screener.db" \
    -e FLASK_ENV=testing \
    nasdaq-screener-test \
    bash -c "pytest tests/ -v && npm test"

echo "========================================"
echo "Tests completed!"
echo "========================================"
