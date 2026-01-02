# Telos Monorepo Migration Script
Write-Host ""
Write-Host "Telos Monorepo Migration Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  - Create client/ directory" -ForegroundColor Yellow
Write-Host "  - Move Python code into client/" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Migration cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Starting migration..." -ForegroundColor Cyan
Write-Host ""

# Create client directory
Write-Host "[1/4] Creating client/ directory..." -ForegroundColor Green
if (!(Test-Path "client")) {
    New-Item -ItemType Directory -Path "client" -Force | Out-Null
    Write-Host "      Created client/" -ForegroundColor Gray
}

# Move Python application directories
Write-Host ""
Write-Host "[2/4] Moving Python directories..." -ForegroundColor Green
$dirsToMove = @("core", "tui", "utils", "prompts")
foreach ($dir in $dirsToMove) {
    if (Test-Path $dir) {
        Write-Host "      Moving $dir/" -ForegroundColor Gray
        Move-Item -Path $dir -Destination "client/" -Force
    }
}

# Move Python files
Write-Host ""
Write-Host "[3/4] Moving Python files..." -ForegroundColor Green
$filesToMove = @("main.py", "service.py", "requirements.txt", "config.yaml.example")
foreach ($file in $filesToMove) {
    if (Test-Path $file) {
        Write-Host "      Moving $file" -ForegroundColor Gray
        Move-Item -Path $file -Destination "client/" -Force
    }
}

# Move temp_screenshots if it exists
if (Test-Path "temp_screenshots") {
    Write-Host "      Moving temp_screenshots/" -ForegroundColor Gray
    Move-Item -Path "temp_screenshots" -Destination "client/" -Force
}

# Create client README
Write-Host ""
Write-Host "[4/4] Creating client/README.md..." -ForegroundColor Green
$clientReadme = @"
# Telos Client (Python)

Python TUI application for tracking screen activity.

## Quick Start

``````bash
pip install -r requirements.txt
python main.py setup
python main.py
``````

See the main repository README for full documentation.
"@
$clientReadme | Out-File -FilePath "client/README.md" -Encoding UTF8
Write-Host "      Created client/README.md" -ForegroundColor Gray

# Summary
Write-Host ""
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "New structure:" -ForegroundColor Cyan
Write-Host "  client/      - Python app is here now" -ForegroundColor White
Write-Host "  backend/     - Node.js backend (ready)" -ForegroundColor White
Write-Host "  shared/      - API contracts" -ForegroundColor White
Write-Host ""
Write-Host "Next: Test the client" -ForegroundColor Yellow
Write-Host "  cd client" -ForegroundColor Gray
Write-Host "  python main.py --help" -ForegroundColor Gray
Write-Host ""

