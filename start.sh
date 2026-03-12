#!/bin/bash
# NASDAQ-100 Screener Server - Linux/Mac Startup Script

echo "========================================"
echo "NASDAQ-100 Screener Server"
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
pip install -r requirements.txt

# Run the server
echo "Starting server on http://localhost:5000"
python server/app.py
