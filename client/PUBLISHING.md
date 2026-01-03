# Publishing Telos to PyPI

This guide covers publishing `telos-tracker` to PyPI and managing versioned releases.

## Initial Setup (One-time)

### 1. Install Publishing Tools

```bash
pip install build twine
```

### 2. Configure PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with scope: "Entire account"
3. Copy the token (starts with `pypi-`)

4. Create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
```

**Security:** This file contains your API token. Keep it secure!

```bash
# Linux/macOS
chmod 600 ~/.pypirc

# Windows (PowerShell)
icacls $env:USERPROFILE\.pypirc /inheritance:r /grant:r "$env:USERNAME:(R)"
```

## Publishing a New Release

### Step 1: Update Version

Edit `client/pyproject.toml`:

```toml
[project]
name = "telos-tracker"
version = "0.1.1"  # Increment this
```

Also update `client/telos_tracker/__init__.py`:

```python
__version__ = "0.1.1"
```

### Step 2: Update Changelog

Update `client/CHANGELOG.md` with new features/fixes.

### Step 3: Build Distribution

```bash
cd client

# Clean old builds
rm -rf dist/ build/ *.egg-info/

# Build wheel and source distribution
python -m build
```

This creates:
- `dist/telos_tracker-X.Y.Z-py3-none-any.whl` (wheel)
- `dist/telos_tracker-X.Y.Z.tar.gz` (source)

### Step 4: Test Locally (Optional)

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# OR
.\test_env\Scripts\activate    # Windows

# Install your package
pip install dist/telos_tracker-0.1.1-py3-none-any.whl

# Test it
telos help
telos setup

# Clean up
deactivate
rm -rf test_env
```

### Step 5: Upload to TestPyPI (Optional First Upload)

For your first release, test on TestPyPI:

1. Create account at https://test.pypi.org/account/register/
2. Get API token from https://test.pypi.org/manage/account/token/
3. Upload:

```bash
twine upload --repository testpypi dist/*
```

4. Test install:

```bash
pip install --index-url https://test.pypi.org/simple/ telos-tracker
```

### Step 6: Upload to Production PyPI

```bash
cd client
twine upload dist/*
```

You'll see output like:

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading telos_tracker-0.1.1-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.0/50.0 kB • 00:00 • ?
Uploading telos_tracker-0.1.1.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.0/45.0 kB • 00:00 • ?

View at:
https://pypi.org/project/telos-tracker/0.1.1/
```

### Step 7: Verify Installation

```bash
pip install telos-tracker
telos --version
```

## Git Version Control for Releases

### Tagging Strategy

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Workflow

```bash
# 1. Make sure you're on the right branch
git checkout main-monorepo
git pull

# 2. Update version in files (see Step 1 above)

# 3. Commit version bump
git add client/pyproject.toml client/telos_tracker/__init__.py client/CHANGELOG.md
git commit -m "Bump version to 0.1.1"

# 4. Create git tag
git tag -a v0.1.1 -m "Release v0.1.1 - Description of changes"

# 5. Push commits and tags
git push origin main-monorepo
git push origin v0.1.1

# 6. Build and publish (see steps above)
cd client
rm -rf dist/ build/
python -m build
twine upload dist/*

# 7. Create GitHub Release (optional)
# Go to https://github.com/YOUR_USERNAME/telos/releases/new
# Select tag v0.1.1
# Add release notes
# Attach dist files if desired
```

### Cherry-pick to Production Branch

```bash
# After testing on main-monorepo, cherry-pick to prod
git checkout prod-monorepo
git cherry-pick v0.1.1
git push origin prod-monorepo
```

## Quick Reference: Publishing Script

Use the provided `publish.sh` (Linux/macOS) or `publish.ps1` (Windows) script:

```bash
./publish.sh 0.1.1 "Bug fixes and improvements"
```

## Versioning Guidelines

### When to Increment

**Patch (0.1.X)**:
- Bug fixes
- Documentation updates
- Performance improvements
- No new features

**Minor (0.X.0)**:
- New features
- Backward compatible changes
- New optional parameters

**Major (X.0.0)**:
- Breaking API changes
- Removed features
- Major architecture changes

### Pre-release Versions

For beta/alpha releases:

```toml
version = "0.2.0b1"  # Beta 1
version = "0.2.0rc1" # Release candidate 1
```

## Troubleshooting

### Package Name Already Taken

If `telos-tracker` is unavailable:

```toml
name = "telos-activity-tracker"  # Alternative name
```

### Upload Fails

```bash
# Check credentials
cat ~/.pypirc

# Verify package builds
python -m build
twine check dist/*

# Test upload to TestPyPI first
twine upload --repository testpypi dist/*
```

### Version Already Exists

You cannot replace a published version. Increment and republish:

```bash
# Fix version in pyproject.toml
# Rebuild and re-upload
python -m build
twine upload dist/*
```

## Automation with GitHub Actions

See `.github/workflows/publish-pypi.yml` for automated publishing on tag push.

## Best Practices

1. **Always test locally before publishing**
2. **Update CHANGELOG.md** with every release
3. **Use TestPyPI** for first-time uploads
4. **Tag releases in git** for version control
5. **Keep version numbers consistent** across files
6. **Review dist/ contents** before uploading
7. **Never delete published versions** (violates PyPI policy)

## Links

- Your package: https://pypi.org/project/telos-tracker/
- Publishing guide: https://packaging.python.org/tutorials/packaging-projects/
- Versioning: https://semver.org/

