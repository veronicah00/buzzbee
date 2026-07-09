# Buzz Bee Naturals - Quick Start Script (PowerShell)

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  BUZZ BEE NATURALS - Quick Start" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Install dependencies
Write-Host ""
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Create database
Write-Host ""
Write-Host "[*] Initializing database..." -ForegroundColor Yellow
python -c "from app import init_db, add_default_products; init_db(); add_default_products()"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to initialize database" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "[OK] Database initialized" -ForegroundColor Green

# Start Flask server
Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  Starting Flask Server..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Server running at http://localhost:5000" -ForegroundColor Green
Write-Host "[*] Admin dashboard: http://localhost:5000/admin.html" -ForegroundColor Green
Write-Host "[*] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python app.py
