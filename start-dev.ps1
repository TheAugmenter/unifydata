# UnifyData.AI Development Server Startup Script
# This script starts all services needed for development

Write-Host "================================" -ForegroundColor Cyan
Write-Host "UnifyData.AI Development Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command($command) {
    try {
        if (Get-Command $command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$allGood = $true

if (Test-Command docker) {
    Write-Host "[OK] Docker is installed" -ForegroundColor Green
} else {
    Write-Host "[!] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "    Install from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    $allGood = $false
}

if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "[OK] Python is installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[!] Python is not installed or not in PATH" -ForegroundColor Red
    $allGood = $false
}

if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "[OK] Node.js is installed: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "[!] Node.js is not installed or not in PATH" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

if (-not $allGood) {
    Write-Host "Please install missing prerequisites first." -ForegroundColor Red
    Write-Host "See README.md for installation instructions." -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env file created. Please update with your credentials." -ForegroundColor Green
    Write-Host ""
}

# Ask user which services to start
Write-Host "Which services do you want to start?" -ForegroundColor Cyan
Write-Host "1. All services with Docker Compose (recommended)" -ForegroundColor White
Write-Host "2. Only Docker services (Postgres, Redis, Neo4j)" -ForegroundColor White
Write-Host "3. Only Backend API (local)" -ForegroundColor White
Write-Host "4. Only Frontend (local)" -ForegroundColor White
Write-Host "5. Backend + Frontend (local, requires Docker services running)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting all services with Docker Compose..." -ForegroundColor Yellow
        docker compose up -d

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] All services started successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Services available at:" -ForegroundColor Cyan
            Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
            Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
            Write-Host "  - Health Check: http://localhost:8000/health" -ForegroundColor White
            Write-Host "  - Neo4j Browser: http://localhost:7474" -ForegroundColor White
            Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
            Write-Host ""
            Write-Host "To view logs: docker compose logs -f" -ForegroundColor Yellow
            Write-Host "To stop: docker compose down" -ForegroundColor Yellow
        } else {
            Write-Host "[!] Failed to start services" -ForegroundColor Red
        }
    }

    "2" {
        Write-Host ""
        Write-Host "Starting Docker services only..." -ForegroundColor Yellow
        docker compose up -d postgres redis neo4j

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] Docker services started!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Services running:" -ForegroundColor Cyan
            Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
            Write-Host "  - Redis: localhost:6379" -ForegroundColor White
            Write-Host "  - Neo4j: localhost:7474 (browser), localhost:7687 (bolt)" -ForegroundColor White
            Write-Host ""
            Write-Host "Now you can start backend/frontend manually." -ForegroundColor Yellow
        }
    }

    "3" {
        Write-Host ""
        Write-Host "Starting Backend API locally..." -ForegroundColor Yellow
        Write-Host ""

        # Check if virtual environment exists
        if (-not (Test-Path "backend\venv")) {
            Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
            python -m venv backend\venv
        }

        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & backend\venv\Scripts\Activate.ps1

        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r backend\requirements.txt -q

        Write-Host ""
        Write-Host "[OK] Starting backend server..." -ForegroundColor Green
        Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""

        Set-Location backend
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    }

    "4" {
        Write-Host ""
        Write-Host "Starting Frontend locally..." -ForegroundColor Yellow

        Set-Location web

        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
            npm install
        }

        Write-Host ""
        Write-Host "[OK] Starting frontend server..." -ForegroundColor Green
        Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""

        npm run dev
    }

    "5" {
        Write-Host ""
        Write-Host "Starting Backend + Frontend locally..." -ForegroundColor Yellow
        Write-Host "This will open two terminal windows." -ForegroundColor Yellow
        Write-Host ""

        # Start backend in new window
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-dev.ps1 backend"

        # Wait a bit for backend to start
        Start-Sleep -Seconds 2

        # Start frontend in new window
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-dev.ps1 frontend"

        Write-Host "[OK] Services starting in separate windows..." -ForegroundColor Green
        Write-Host ""
        Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    }

    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
