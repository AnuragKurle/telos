# Publishing Quick Start

## First Time Setup

### 1. Get PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `telos-publishing`
4. Scope: `Entire account` (or specific to `telos-tracker` after first upload)
5. Copy the token (starts with `pypi-`)

### 2. Configure Credentials

Create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-YOUR-ACTUAL-TOKEN-HERE
```

**Windows users:** File location is `C:\Users\YourName\.pypirc`

### 3. Install Tools

```bash
pip install build twine
```

## Publishing a New Version

### Option 1: Automated Script (Recommended)

**Windows:**
```powershell
cd client
.\publish.ps1 0.1.1 "Bug fixes and performance improvements"
```

**Linux/macOS:**
```bash
cd client
chmod +x publish.sh
./publish.sh 0.1.1 "Bug fixes and performance improvements"
```

The script does everything automatically!

### Option 2: Manual Steps

```bash
cd client

# 1. Update version
# Edit pyproject.toml: version = "0.1.1"
# Edit telos_tracker/__init__.py: __version__ = "0.1.1"

# 2. Build
rm -rf dist/ build/
python -m build

# 3. Upload
twine upload dist/*

# 4. Git tag
git add pyproject.toml telos_tracker/__init__.py
git commit -m "Bump version to 0.1.1"
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin main-monorepo v0.1.1
```

## Testing Before Publishing

### Test Locally

```bash
cd client
python -m build
pip install dist/telos_tracker-0.1.1-py3-none-any.whl
telos help
```

### Test on TestPyPI (Safer)

```powershell
# Windows
.\publish.ps1 0.1.1 "Test" -TestPyPI

# Linux/macOS
./publish.sh 0.1.1 "Test" skip-tests testpypi
```

Install from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ telos-tracker
```

## After Publishing

1. **Push to GitHub:**
   ```bash
   git push origin main-monorepo
   git push origin v0.1.1
   ```

2. **Verify Installation:**
   ```bash
   pip install telos-tracker==0.1.1
   telos --version
   ```

3. **Check PyPI Page:**
   https://pypi.org/project/telos-tracker/

## Common Commands

| Task | Command |
|------|---------|
| Publish new version | `.\publish.ps1 0.1.1 "Changes"` |
| Test locally | `python -m build && pip install dist/*.whl` |
| Publish to TestPyPI | `.\publish.ps1 0.1.1 "Test" -TestPyPI` |
| Skip local tests | `.\publish.ps1 0.1.1 "Quick" -SkipTests` |
| Check package | `twine check dist/*` |
| View on PyPI | `https://pypi.org/project/telos-tracker/` |

## Version Numbers

- **Patch** (0.1.X): Bug fixes, no new features
- **Minor** (0.X.0): New features, backward compatible
- **Major** (X.0.0): Breaking changes

## Troubleshooting

**"Version already exists"**
- Cannot overwrite published versions
- Increment version number and republish

**"Invalid credentials"**
- Check `~/.pypirc` file exists and has correct token
- Verify token at https://pypi.org/manage/account/token/

**"Package name already taken"**
- Change name in `pyproject.toml`
- Try `telos-activity-tracker` or similar

**Upload hangs**
- Check internet connection
- Try TestPyPI first: `publish.ps1 -TestPyPI`

## Help

- Full guide: `PUBLISHING.md`
- Release workflow: `../docs/releases.md`
- PyPI help: https://packaging.python.org/

