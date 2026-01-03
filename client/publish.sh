#!/bin/bash
# Publish Telos to PyPI
# Usage: ./publish.sh <version> "<release notes>"
# Example: ./publish.sh 0.1.1 "Bug fixes and improvements"

set -e

VERSION=$1
RELEASE_NOTES=$2
SKIP_TESTS=${3:-false}
TEST_PYPI=${4:-false}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

error() { echo -e "${RED}$1${NC}" >&2; exit 1; }
success() { echo -e "${GREEN}$1${NC}"; }
info() { echo -e "${CYAN}$1${NC}"; }
warning() { echo -e "${YELLOW}$1${NC}"; }

# Validate arguments
if [ -z "$VERSION" ] || [ -z "$RELEASE_NOTES" ]; then
    error "Usage: ./publish.sh <version> \"<release notes>\" [skip-tests] [testpypi]"
fi

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    error "Error: Version must be in format X.Y.Z (e.g., 0.1.1)"
fi

# Check if we're in the client directory
if [ ! -f "pyproject.toml" ]; then
    error "Error: Must run from client/ directory"
fi

# Check for required tools
for tool in python git; do
    if ! command -v $tool &> /dev/null; then
        error "Error: $tool not found. Please install it first."
    fi
done

info "=== Publishing Telos v$VERSION ==="

# Install build tools if needed
info "\n[1/9] Checking build tools..."
python -m pip install --quiet --upgrade build twine
success "Build tools ready"

# Update version in pyproject.toml
info "\n[2/9] Updating version in pyproject.toml..."
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm -f pyproject.toml.bak
success "Updated to version $VERSION"

# Update version in __init__.py
info "\n[3/9] Updating version in __init__.py..."
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" telos_tracker/__init__.py
rm -f telos_tracker/__init__.py.bak
success "Updated to version $VERSION"

# Update CHANGELOG
info "\n[4/9] Updating CHANGELOG.md..."
DATE=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [$VERSION] - $DATE\n\n$RELEASE_NOTES\n"

if [ -f "CHANGELOG.md" ]; then
    sed -i.bak "s/# Changelog/# Changelog\n\n$CHANGELOG_ENTRY/" CHANGELOG.md
    rm -f CHANGELOG.md.bak
else
    echo -e "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n$CHANGELOG_ENTRY" > CHANGELOG.md
fi
success "Updated CHANGELOG.md"

# Git commit
info "\n[5/9] Committing version bump..."
git add pyproject.toml telos_tracker/__init__.py CHANGELOG.md
git commit -m "Bump version to $VERSION"
success "Committed version bump"

# Clean old builds
info "\n[6/9] Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/
success "Cleaned build directories"

# Build package
info "\n[7/9] Building package..."
python -m build
success "Built distribution packages"

# Test installation locally (unless skipped)
if [ "$SKIP_TESTS" != "skip-tests" ]; then
    info "\n[8/9] Testing local installation..."
    
    # Create temp venv
    python -m venv test_env_temp
    source test_env_temp/bin/activate
    pip install --quiet dist/telos_tracker-${VERSION}-py3-none-any.whl
    
    # Test command
    if telos help > /dev/null 2>&1; then
        success "Local installation test passed"
    else
        error "Local installation test failed!"
    fi
    
    # Cleanup
    deactivate
    rm -rf test_env_temp
else
    warning "\n[8/9] Skipping local tests..."
fi

# Upload to PyPI
info "\n[9/9] Uploading to PyPI..."

if [ "$TEST_PYPI" = "testpypi" ]; then
    warning "Uploading to TestPyPI (test server)..."
    twine upload --repository testpypi dist/*
else
    twine upload dist/*
fi

success "\n✓ Successfully published telos-tracker v$VERSION to PyPI!"

# Create git tag
info "\nCreating git tag v$VERSION..."
git tag -a "v$VERSION" -m "Release v$VERSION - $RELEASE_NOTES"
success "Created tag v$VERSION"

# Instructions
info "\n=== Next Steps ==="
echo "1. Push commits and tags:"
echo "   git push origin main-monorepo"
echo "   git push origin v$VERSION"
echo ""
echo "2. View on PyPI:"
if [ "$TEST_PYPI" = "testpypi" ]; then
    echo "   https://test.pypi.org/project/telos-tracker/$VERSION/"
else
    echo "   https://pypi.org/project/telos-tracker/$VERSION/"
fi
echo ""
echo "3. Test installation:"
if [ "$TEST_PYPI" = "testpypi" ]; then
    echo "   pip install --index-url https://test.pypi.org/simple/ telos-tracker==$VERSION"
else
    echo "   pip install telos-tracker==$VERSION"
fi
echo ""
success "Done!"

