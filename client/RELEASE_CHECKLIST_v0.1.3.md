# Release Checklist for v0.1.3

## Pre-Release Checklist

- [x] Version bumped in `pyproject.toml` (0.1.3)
- [x] Version bumped in `telos_tracker/__init__.py` (0.1.3)
- [x] CHANGELOG.md updated with release notes
- [ ] All changes committed to git
- [ ] Tested locally with `pip install .`

## Release Commands

### 1. Commit Version Bump

```bash
cd client
git add pyproject.toml telos_tracker/__init__.py CHANGELOG.md
git add INSTALLATION_TROUBLESHOOTING.md QUICK_FIX.md USER_MESSAGE_TEMPLATE.md
git add README.md PUBLISHING.md
git add ../docs/INSTALLATION_ISSUES_EXPLAINED.md
git commit -m "Release v0.1.3 - Installation troubleshooting improvements"
```

### 2. Create Git Tag

```bash
git tag -a v0.1.3 -m "Release v0.1.3

Documentation improvements:
- Added comprehensive installation troubleshooting guides
- Enhanced CLI help with PATH workaround hints
- Added pipx installation recommendation
- Platform-specific setup guides (Windows/Mac/Linux)
- Support response templates for common issues

This release helps users resolve 'telos is unrecognized' errors."
```

### 3. Push to Remote

```bash
git push origin main-monorepo
git push origin v0.1.3
```

### 4. Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build wheel and source distribution
python -m build
```

**Expected output:**
```
dist/
├── telos_tracker-0.1.3-py3-none-any.whl
└── telos_tracker-0.1.3.tar.gz
```

### 5. Test Locally (Recommended)

```bash
# Create fresh test environment
python -m venv test_v0.1.3
source test_v0.1.3/bin/activate  # Mac/Linux
# OR
.\test_v0.1.3\Scripts\activate    # Windows

# Install from wheel
pip install dist/telos_tracker-0.1.3-py3-none-any.whl

# Test commands
telos --version        # Should show 0.1.3
telos help             # Check updated help text
python -m telos_tracker.cli --version  # Test module syntax

# Check bundled docs
ls ~/.telos/           # Verify user directory created

# Clean up
deactivate
rm -rf test_v0.1.3
```

### 6. Upload to PyPI

```bash
twine upload dist/*
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading telos_tracker-0.1.3-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
Uploading telos_tracker-0.1.3.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 

View at:
https://pypi.org/project/telos-tracker/0.1.3/
```

### 7. Verify on PyPI

**Check these on the PyPI page:**
- [ ] Version shows 0.1.3
- [ ] Updated description is visible
- [ ] README renders correctly
- [ ] CHANGELOG is visible

**Visit:** https://pypi.org/project/telos-tracker/0.1.3/

### 8. Test Installation from PyPI

```bash
# Create fresh environment
python -m venv test_pypi_install
source test_pypi_install/bin/activate  # Mac/Linux
# OR
.\test_pypi_install\Scripts\activate   # Windows

# Install from PyPI (wait 1-2 minutes for PyPI to update)
pip install --upgrade telos-tracker

# Verify version
pip show telos-tracker | grep Version  # Should show 0.1.3

# Test functionality
python -m telos_tracker.cli help       # Should show updated help
python -m telos_tracker.cli --version  # Should show 0.1.3

# Clean up
deactivate
rm -rf test_pypi_install
```

## Post-Release Tasks

### 9. Create GitHub Release (Optional but Recommended)

1. Go to: https://github.com/AnuragKurle/telos/releases/new
2. Select tag: `v0.1.3`
3. Release title: `v0.1.3 - Installation Troubleshooting Improvements`
4. Description:

```markdown
## What's New

This release focuses on improving the installation experience and helping users resolve common PATH configuration issues.

### Documentation Improvements

- **New comprehensive troubleshooting guide** (`INSTALLATION_TROUBLESHOOTING.md`)
- **Quick fix reference** for common errors (`QUICK_FIX.md`)
- **Technical deep-dive** explaining root causes
- **Support templates** for consistent user assistance

### Enhanced User Experience

- Updated CLI help text with troubleshooting hints
- Added pipx installation recommendation
- Platform-specific setup guides (Windows/Mac/Linux)
- Improved PyPI package description

### For Users Experiencing "telos is unrecognized" Error

**Quick Fix:**
```bash
python -m telos_tracker.cli
```

**Best Solution:**
```bash
pip install pipx
pipx install telos-tracker
telos
```

See the [Installation Troubleshooting Guide](./client/INSTALLATION_TROUBLESHOOTING.md) for complete solutions.

## Installation

```bash
pip install telos-tracker
telos setup
```

Or with pipx (recommended):
```bash
pipx install telos-tracker
telos setup
```

## Full Changelog

See [CHANGELOG.md](./client/CHANGELOG.md)
```

5. Attach files (optional):
   - `dist/telos_tracker-0.1.3-py3-none-any.whl`
   - `dist/telos_tracker-0.1.3.tar.gz`

6. Click "Publish release"

### 10. Update Documentation Sites

If you have any documentation websites, update them to reference v0.1.3.

### 11. Announce Release

**Consider announcing on:**
- [ ] Twitter/X: "Released telos v0.1.3 with comprehensive installation troubleshooting!"
- [ ] Reddit r/Python or r/productivity
- [ ] Discord/Slack communities
- [ ] LinkedIn
- [ ] Product Hunt (if not already launched)

**Sample announcement:**
```
🎉 telos v0.1.3 is out!

This release focuses on helping users resolve common installation issues:
✅ Comprehensive troubleshooting guide
✅ pipx recommendation for hassle-free install
✅ Enhanced CLI help text

Install: pip install telos-tracker
Or with pipx: pipx install telos-tracker

#Python #Productivity #OpenSource
```

### 12. Cherry-pick to Production Branch (Your Workflow)

```bash
git checkout prod-monorepo
git cherry-pick v0.1.3
git push origin prod-monorepo
```

## Rollback Plan (If Needed)

If something goes wrong:

1. **You cannot delete versions from PyPI**
2. **Instead, release v0.1.4 with fixes**
3. **Or mark v0.1.3 as yanked:**
   ```bash
   # Not common, but available if critical issue
   # Contact PyPI admins or use web interface
   ```

## Quick Release Script (Future Use)

For next time, you can use the provided scripts:

**Windows:**
```powershell
.\publish.ps1 0.1.4 "Description of changes"
```

**Mac/Linux:**
```bash
./publish.sh 0.1.4 "Description of changes"
```

## Success Criteria

Release is successful when:
- [x] PyPI shows v0.1.3
- [ ] `pip install telos-tracker` installs v0.1.3
- [ ] `telos --version` shows 0.1.3
- [ ] Updated help text is visible in `telos help`
- [ ] No critical bug reports within 24 hours

## Notes

- **This is a patch release** - safe to upgrade
- **No breaking changes** - existing users won't be affected
- **Documentation-focused** - improves user experience without code changes

---

**Ready to release? Follow the steps above in order!** ✅

