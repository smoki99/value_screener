#!/bin/bash
# NASDAQ-100 Screener - Test Runner Script

echo "========================================"
echo "NASDAQ-100 Screener Tests"
echo "========================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Install pytest if not already installed
pip install pytest > /dev/null 2>&1

# Run all tests
echo "Running all Python tests..."
python -m pytest tests/ -v

# Deactivate virtual environment
deactivate

echo "========================================"
echo "Tests completed!"
echo "========================================"