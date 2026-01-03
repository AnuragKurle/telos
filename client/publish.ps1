# Publish Telos to PyPI
# Usage: .\publish.ps1 <version> "<release notes>"
# Example: .\publish.ps1 0.1.1 "Bug fixes and improvements"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$true)]
    [string]$ReleaseNotes,
    
    [switch]$SkipTests,
    [switch]$TestPyPI
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Info "=== Publishing Telos v$Version ==="

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+') {
    Write-Error "Error: Version must be in format X.Y.Z (e.g., 0.1.1)"
    exit 1
}

# Check if we're in the client directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "Error: Must run from client/ directory"
    exit 1
}

# Check for required tools
$tools = @("python", "git")
foreach ($tool in $tools) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "Error: $tool not found. Please install it first."
        exit 1
    }
}

# Install build tools if needed
Write-Info "`n[1/9] Checking build tools..."
python -m pip install --quiet --upgrade build twine

# Update version in pyproject.toml
Write-Info "`n[2/9] Updating version in pyproject.toml..."
$content = Get-Content "pyproject.toml" -Raw
$content = $content -replace 'version = "[^"]*"', "version = `"$Version`""
Set-Content "pyproject.toml" -Value $content -NoNewline
Write-Success "Updated to version $Version"

# Update version in __init__.py
Write-Info "`n[3/9] Updating version in __init__.py..."
$content = Get-Content "telos_tracker\__init__.py" -Raw
$content = $content -replace '__version__ = "[^"]*"', "__version__ = `"$Version`""
Set-Content "telos_tracker\__init__.py" -Value $content -NoNewline
Write-Success "Updated to version $Version"

# Update CHANGELOG
Write-Info "`n[4/9] Updating CHANGELOG.md..."
$date = Get-Date -Format "yyyy-MM-dd"
$changelogEntry = @"
## [$Version] - $date

$ReleaseNotes

"@

if (Test-Path "CHANGELOG.md") {
    $changelog = Get-Content "CHANGELOG.md" -Raw
    $changelog = $changelog -replace '(# Changelog\s+)', "`$1`n$changelogEntry"
    Set-Content "CHANGELOG.md" -Value $changelog -NoNewline
} else {
    $newChangelog = @"
# Changelog

All notable changes to this project will be documented in this file.

$changelogEntry
"@
    Set-Content "CHANGELOG.md" -Value $newChangelog -NoNewline
}
Write-Success "Updated CHANGELOG.md"

# Git commit
Write-Info "`n[5/9] Committing version bump..."
git add pyproject.toml telos_tracker\__init__.py CHANGELOG.md
git commit -m "Bump version to $Version"
Write-Success "Committed version bump"

# Clean old builds
Write-Info "`n[6/9] Cleaning old builds..."
Remove-Item -Path dist, build, *.egg-info -Recurse -Force -ErrorAction SilentlyContinue
Write-Success "Cleaned build directories"

# Build package
Write-Info "`n[7/9] Building package..."
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed!"
    exit 1
}
Write-Success "Built distribution packages"

# Test installation locally (unless skipped)
if (-not $SkipTests) {
    Write-Info "`n[8/9] Testing local installation..."
    
    # Create temp venv
    python -m venv test_env_temp
    .\test_env_temp\Scripts\pip install --quiet dist\telos_tracker-$Version-py3-none-any.whl
    
    # Test command
    $output = .\test_env_temp\Scripts\telos help
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Local installation test passed"
    } else {
        Write-Error "Local installation test failed!"
        Remove-Item test_env_temp -Recurse -Force
        exit 1
    }
    
    # Cleanup
    Remove-Item test_env_temp -Recurse -Force
} else {
    Write-Warning "`n[8/9] Skipping local tests..."
}

# Upload to PyPI
Write-Info "`n[9/9] Uploading to PyPI..."

if ($TestPyPI) {
    Write-Warning "Uploading to TestPyPI (test server)..."
    twine upload --repository testpypi dist\*
} else {
    twine upload dist\*
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Upload failed!"
    exit 1
}

Write-Success "`n✓ Successfully published telos-tracker v$Version to PyPI!"

# Create git tag
Write-Info "`nCreating git tag v$Version..."
git tag -a "v$Version" -m "Release v$Version - $ReleaseNotes"
Write-Success "Created tag v$Version"

# Instructions
Write-Info "`n=== Next Steps ==="
Write-Host "1. Push commits and tags:"
Write-Host "   git push origin main-monorepo"
Write-Host "   git push origin v$Version"
Write-Host ""
Write-Host "2. View on PyPI:"
if ($TestPyPI) {
    Write-Host "   https://test.pypi.org/project/telos-tracker/$Version/"
} else {
    Write-Host "   https://pypi.org/project/telos-tracker/$Version/"
}
Write-Host ""
Write-Host "3. Test installation:"
if ($TestPyPI) {
    Write-Host "   pip install --index-url https://test.pypi.org/simple/ telos-tracker==$Version"
} else {
    Write-Host "   pip install telos-tracker==$Version"
}
Write-Host ""
Write-Success "Done!"

