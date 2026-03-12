#!/bin/bash
# NASDAQ-100 Screener - Docker Image Builder

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="nasdaq-screener"

echo "========================================"
echo "Building Docker Image: $IMAGE_NAME"
echo "========================================"
echo "Project directory: $SCRIPT_DIR"

# Build Docker image with progress output
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo "========================================"
echo "Build complete!"
echo "Image name: $IMAGE_NAME"
echo "Run with: ./start-docker.sh"
echo "========================================"