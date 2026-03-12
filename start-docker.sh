#!/bin/bash
# NASDAQ-100 Screener - Local Docker Server Runner

set -e

# --- CONFIGURATION ---
# "nasdaq-screener" is clean, lowercase, and matches your repo name
IMAGE_NAME="nasdaq-screener:latest"  
CONTAINER_NAME="nasdaq-screener-server"
CACHE_DIR="$HOME/.nasdaq-screener-cache"

# Ensure local cache exists
mkdir -p "$CACHE_DIR"
echo "Using local cache directory: $CACHE_DIR"

# 1. Build the image locally
# Using --pull ensures we always have the latest base python/node images
echo "Building local image: $IMAGE_NAME..."
docker build --pull -t "$IMAGE_NAME" .

# 2. Stop and remove existing container if running
# This prevents 'name already in use' errors
echo "Cleaning up old containers..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "========================================"
echo "Starting NASDAQ-100 Screener Server"
echo "========================================"

# 3. Run the container
# --restart unless-stopped keeps it alive across reboots
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 5000:5000 \
    -v "$CACHE_DIR:/app/cache" \
    -e CACHE_DB_PATH="/app/cache/screener.db" \
    -e LOG_LEVEL=INFO \
    -e FLASK_ENV=production \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo "========================================"
echo "Server started at: http://localhost:5000"
echo "Image Name:  $IMAGE_NAME"
echo "Container:   $CONTAINER_NAME"
echo "----------------------------------------"
echo "Logs: docker logs -f $CONTAINER_NAME"
echo "Stop: docker stop $CONTAINER_NAME"
echo "========================================"
