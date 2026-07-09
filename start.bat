@echo off
REM Buzz Bee Naturals - Quick Start Script for Windows

echo.
echo ===================================
echo   BUZZ BEE NATURALS - Quick Start
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Install dependencies
echo.
echo [*] Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed

REM Create database
echo.
echo [*] Initializing database...
python -c "from app import init_db, add_default_products; init_db(); add_default_products()"

if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)

echo [OK] Database initialized

REM Start Flask server
echo.
echo ===================================
echo   Starting Flask Server...
echo ===================================
echo.
echo [*] Server running at http://localhost:5000
echo [*] Admin dashboard: http://localhost:5000/admin.html
echo [*] Press Ctrl+C to stop the server
echo.

python app.py
