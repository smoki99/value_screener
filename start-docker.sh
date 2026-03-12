#!/bin/bash
# NASDAQ-100 Screener - Docker Server Runner with Local Cache DB

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
echo "Starting NASDAQ-100 Screener Server"
echo "========================================"
echo "Cache DB: $DB_FILE"
echo "Server URL: http://localhost:5000"

# Run Docker container with cache volume mount and server mode
docker run --rm -d \
    --name nasdaq-screener-server \
    -p 5000:5000 \
    -v "$CACHE_DIR:/app/cache" \
    -e CACHE_DB_PATH="/app/cache/screener.db" \
    -e LOG_LEVEL=INFO \
    -e FLASK_ENV=production \
    nasdaq-screener \
    bash -c "source venv/bin/activate && cd server && flask run --host=0.0.0.0 --port=5000"

echo "========================================"
echo "Server started!"
echo "Access at: http://localhost:5000"
echo "Stop with: docker stop nasdaq-screener-server"
echo "View logs with: docker logs -f nasdaq-screener-server"
echo "Change log level by editing LOG_LEVEL in this script (DEBUG, INFO, WARNING, ERROR)"
echo "========================================"