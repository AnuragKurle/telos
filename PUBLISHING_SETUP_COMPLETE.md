# Publishing Setup Complete! 🎉

Your project is now ready to publish to PyPI with full version control.

## What Was Created

### 📄 Documentation
- **`client/QUICKSTART_PUBLISHING.md`** - Quick reference for publishing
- **`client/PUBLISHING.md`** - Comprehensive publishing guide
- **`docs/releases.md`** - Release management workflow
- **`client/CHANGELOG.md`** - Version history tracking

### 🔧 Automation Scripts
- **`client/publish.ps1`** - Windows PowerShell publishing script
- **`client/publish.sh`** - Linux/macOS Bash publishing script
- **`.github/workflows/publish-pypi.yml`** - GitHub Actions automation

### 📦 Package Files
- **`client/pyproject.toml`** - Package configuration
- **`client/telos_tracker/`** - Package module with CLI

## Next Steps to Publish

### 1. Configure PyPI Token (5 minutes)

```bash
# 1. Go to https://pypi.org/manage/account/token/
# 2. Create API token named "telos-publishing"
# 3. Copy the token (starts with pypi-)

# 4. Create ~/.pypirc file:
notepad $env:USERPROFILE\.pypirc  # Windows
# OR
nano ~/.pypirc  # Linux/macOS
```

Add this content:
```ini
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
```

### 2. Publish Your First Release

**Windows:**
```powershell
cd client
.\publish.ps1 0.1.0 "Initial PyPI release"
```

**Linux/macOS:**
```bash
cd client
chmod +x publish.sh
./publish.sh 0.1.0 "Initial PyPI release"
```

This will:
- ✅ Update version in all files
- ✅ Update CHANGELOG.md
- ✅ Build the package
- ✅ Test locally
- ✅ Upload to PyPI
- ✅ Create git tag
- ✅ Show next steps

### 3. Push to GitHub

```bash
git push origin main-monorepo
git push origin v0.1.0
```

### 4. Test Installation

```bash
pip install telos-tracker
telos help
```

## Publishing Workflow

### For Regular Updates

```bash
# Make changes, test them...

# Publish (auto-updates version, changelog, creates tag)
cd client
.\publish.ps1 0.1.1 "Bug fixes and improvements"

# Push to GitHub
git push origin main-monorepo v0.1.1
```

### For Safe Testing First

```powershell
# Publish to TestPyPI first
.\publish.ps1 0.1.1 "Testing" -TestPyPI

# Test installation
pip install --index-url https://test.pypi.org/simple/ telos-tracker

# If all good, publish to production
.\publish.ps1 0.1.1 "Bug fixes and improvements"
```

## GitHub Actions (Optional Automation)

For fully automated publishing on git tag push:

### 1. Add PyPI Token to GitHub Secrets

1. Go to `https://github.com/YOUR_USERNAME/telos/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token

### 2. Push the Workflow

```bash
git add .github/workflows/publish-pypi.yml
git commit -m "Add PyPI publishing workflow"
git push
```

### 3. Publish by Pushing a Tag

```bash
# Update version manually in pyproject.toml and __init__.py
# Then:
git add .
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main-monorepo v0.1.1

# GitHub Actions will automatically:
# - Build package
# - Upload to PyPI
# - Create GitHub Release
```

## Version Control Strategy

We follow [Semantic Versioning](https://semver.org/):

- **0.1.X** - Patch: Bug fixes, no new features
- **0.X.0** - Minor: New features, backward compatible
- **X.0.0** - Major: Breaking changes

### Git Workflow

```
main-monorepo (development)
    ↓ develop & test
    ↓ publish with script
    ↓ creates tag v0.1.1
    ↓
prod-monorepo (production)
    ↓ cherry-pick when stable
    ↓ deploy backend/apps
```

## Quick Reference

| Task | Command |
|------|---------|
| **Publish new version** | `.\publish.ps1 0.1.1 "Changes"` |
| **Test on TestPyPI** | `.\publish.ps1 0.1.1 "Test" -TestPyPI` |
| **Skip local tests** | `.\publish.ps1 0.1.1 "Quick" -SkipTests` |
| **View on PyPI** | https://pypi.org/project/telos-tracker/ |
| **Install latest** | `pip install telos-tracker` |
| **Install specific** | `pip install telos-tracker==0.1.1` |

## Documentation Locations

- 🚀 **Quick Start**: `client/QUICKSTART_PUBLISHING.md`
- 📖 **Full Guide**: `client/PUBLISHING.md`
- 🔄 **Workflow**: `docs/releases.md`
- 📝 **Changelog**: `client/CHANGELOG.md`

## Common Questions

**Q: Can I change the package name?**
A: Yes, edit `name = "telos-tracker"` in `client/pyproject.toml`

**Q: How do I unpublish a version?**
A: You can't delete from PyPI, but you can "yank" it to prevent new installs

**Q: What if publishing fails?**
A: Check `~/.pypirc` credentials and read error message. See `PUBLISHING.md` troubleshooting section.

**Q: How do I handle breaking changes?**
A: Bump major version (1.0.0) and document in CHANGELOG.md

## Support

- 📚 Read the docs in `client/PUBLISHING.md`
- 🐛 Found issues? Check `docs/releases.md`
- 💬 Questions? See https://packaging.python.org/

---

## Ready to Publish?

```powershell
cd client
.\publish.ps1 0.1.0 "Initial PyPI release - pip install telos-tracker"
```

That's it! Your package will be live on PyPI in minutes! 🚀

