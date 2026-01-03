# Release Management

This document covers the release process for Telos, including PyPI publishing and version control.

## Quick Release (Using Script)

### Windows

```powershell
cd client
.\publish.ps1 0.1.1 "Bug fixes and improvements"
```

### Linux/macOS

```bash
cd client
chmod +x publish.sh
./publish.sh 0.1.1 "Bug fixes and improvements"
```

The script automatically:
1. Updates version in all files
2. Updates CHANGELOG.md
3. Commits changes
4. Builds package
5. Tests installation locally
6. Uploads to PyPI
7. Creates git tag

## Manual Release Process

See `client/PUBLISHING.md` for detailed manual steps.

## Version Control Strategy

### Branch Strategy

- **main-monorepo** - Development branch
  - All new features developed here
  - Beta testing happens here
  
- **prod-monorepo** - Production branch
  - Only stable, tested releases
  - Cherry-pick from main-monorepo

### Release Workflow

```bash
# 1. Develop on main-monorepo
git checkout main-monorepo
# ... make changes, test ...

# 2. Publish to PyPI (creates tag automatically)
cd client
./publish.sh 0.1.1 "Description"

# 3. Push commits and tags
git push origin main-monorepo
git push origin v0.1.1

# 4. Cherry-pick to production (optional)
git checkout prod-monorepo
git cherry-pick v0.1.1
git push origin prod-monorepo
```

## Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):

### Version Format: `MAJOR.MINOR.PATCH`

**PATCH** (0.1.X) - Increment for:
- Bug fixes
- Documentation updates
- Performance improvements
- Security patches
- No new features

**MINOR** (0.X.0) - Increment for:
- New features
- New optional parameters
- Backward-compatible changes
- Deprecations (with warnings)

**MAJOR** (X.0.0) - Increment for:
- Breaking API changes
- Removed features
- Major architecture changes
- Changed configuration format

### Pre-release Versions

For testing before official release:

- `0.2.0a1` - Alpha 1 (internal testing)
- `0.2.0b1` - Beta 1 (limited user testing)
- `0.2.0rc1` - Release Candidate 1 (final testing)

```bash
# Publish pre-release
cd client
./publish.sh 0.2.0b1 "Beta release for testing"
```

## Automated Publishing (GitHub Actions)

If you've set up the GitHub Actions workflow:

```bash
# 1. Update version in files
# 2. Commit changes
# 3. Create and push tag
git tag v0.1.1
git push origin v0.1.1
```

The workflow automatically:
- Builds the package
- Publishes to PyPI
- Creates GitHub release with files

### Setup GitHub Actions

1. Add PyPI API token to GitHub Secrets:
   - Go to https://github.com/YOUR_USERNAME/telos/settings/secrets/actions
   - Add secret: `PYPI_API_TOKEN`
   - Value: Your PyPI token (from https://pypi.org/manage/account/token/)

2. Push the workflow file:
   ```bash
   git add .github/workflows/publish-pypi.yml
   git commit -m "Add PyPI publishing workflow"
   git push
   ```

## Testing Before Release

### Test on TestPyPI

```powershell
# Windows
.\publish.ps1 0.1.1 "Test release" -TestPyPI

# Linux/macOS
./publish.sh 0.1.1 "Test release" skip-tests testpypi
```

Then test installation:

```bash
pip install --index-url https://test.pypi.org/simple/ telos-tracker==0.1.1
```

### Local Testing

```bash
cd client

# Build
python -m build

# Test in clean environment
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# OR
.\test_env\Scripts\activate    # Windows

pip install dist/telos_tracker-0.1.1-py3-none-any.whl
telos help
telos setup

deactivate
rm -rf test_env
```

## Release Checklist

Before publishing a new version:

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in:
  - [ ] `pyproject.toml`
  - [ ] `telos_tracker/__init__.py`
- [ ] Tested locally
- [ ] Tested on TestPyPI (for major releases)
- [ ] Git tag created
- [ ] Pushed to GitHub

After publishing:

- [ ] Verified installation: `pip install telos-tracker==X.Y.Z`
- [ ] Checked PyPI page looks correct
- [ ] Created GitHub release (if not automated)
- [ ] Announced to users (if significant)

## Rollback Process

If a release has critical bugs:

1. **Don't delete from PyPI** (violates policy)
2. **Publish a patch version immediately**:
   ```bash
   ./publish.sh 0.1.2 "Hotfix: Critical bug in 0.1.1"
   ```
3. **Mark as yanked** on PyPI (prevents new installs):
   - Go to https://pypi.org/manage/project/telos-tracker/release/0.1.1/
   - Click "Options" → "Yank release"

## Monitoring Releases

- **PyPI Stats**: https://pypistats.org/packages/telos-tracker
- **GitHub Releases**: https://github.com/YOUR_USERNAME/telos/releases
- **Issues/Feedback**: https://github.com/YOUR_USERNAME/telos/issues

## Common Issues

### Package Name Conflict

If `telos-tracker` is taken:

```toml
# In pyproject.toml
name = "telos-activity-tracker"
```

### Upload Fails

```bash
# Verify package
twine check dist/*

# Check credentials
cat ~/.pypirc

# Retry
twine upload dist/*
```

### Version Mismatch

Ensure version is consistent:
```bash
grep -r "0.1.0" client/
```

Update in:
- `client/pyproject.toml`
- `client/telos_tracker/__init__.py`

## Support

For questions about releases:
- Read: `client/PUBLISHING.md`
- Check: https://packaging.python.org/

