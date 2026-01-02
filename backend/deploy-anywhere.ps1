# Deploy from ANY terminal - automatically loads gcloud
# This script ensures gcloud is available before deploying

$ErrorActionPreference = "Stop"

# Ensure gcloud is in PATH for this session
$gcloudPath = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin"
if ($env:Path -notlike "*$gcloudPath*") {
    Write-Host "Loading Google Cloud SDK..." -ForegroundColor Cyan
    $env:Path = "$env:Path;$gcloudPath"
}

# Verify gcloud is available
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not accessible" -ForegroundColor Red
    Write-Host "Please ensure Google Cloud SDK is installed at: $gcloudPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Google Cloud SDK loaded successfully!" -ForegroundColor Green
Write-Host ""

# Run the deployment script
& "$PSScriptRoot\deploy.ps1"

