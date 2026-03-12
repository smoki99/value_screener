@echo off
REM NASDAQ-100 Screener Server - Windows Startup Script

echo ========================================
echo NASDAQ-100 Screener Server
echo ========================================

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the server
echo Starting server on http://localhost:5000
python server\app.py

pause
