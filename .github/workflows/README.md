# GitHub Actions Workflows

This directory contains automated workflows for building and releasing Telos.

## Build Desktop Apps Workflow

**File:** `build-desktop-apps.yml`

Automatically builds Telos for Windows and macOS whenever code is pushed.

### When It Runs

1. **On Push** - Builds when you push to:
   - `main` branch
   - `master` branch  
   - `develop` branch

2. **On Pull Request** - Builds to test PRs

3. **On Tag** - Creates a release when you push a version tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. **Manual** - Can trigger manually from GitHub Actions tab

### What It Does

**Windows Build:**
- ✅ Installs Python 3.11
- ✅ Installs dependencies
- ✅ Runs `build_installer.py`
- ✅ Uploads `Telos.exe` and installer
- ⏱️ Takes ~5-7 minutes

**macOS Build:**
- ✅ Installs Python 3.11
- ✅ Installs dependencies
- ✅ Runs `build_macos.py`
- ✅ Creates `Telos.app` bundle
- ✅ Creates DMG installer
- ✅ Uploads both
- ⏱️ Takes ~8-10 minutes

**Both run in parallel!**

### How to Use

#### Option 1: Download from Actions Tab

1. Go to your GitHub repo
2. Click "Actions" tab
3. Click on a workflow run
4. Scroll to "Artifacts" section
5. Download:
   - `Telos-Windows-[version]` - Windows executable
   - `Telos-macOS-DMG-[version]` - macOS installer

#### Option 2: Create a Release

**For official releases:**

```bash
# Tag your version
git tag v0.1.0-beta
git push origin v0.1.0-beta
```

The workflow will:
1. Build Windows and macOS versions
2. Create a GitHub Release
3. Attach installers to the release
4. Generate release notes automatically

**Then share the release link with users!**

### Artifacts

After each build, you can download:

**Windows:**
- `Telos.exe` - Standalone executable (~50-80 MB)
- `TelosSetup-v*.exe` - Inno Setup installer (if Inno Setup available)
- `README.txt` - User instructions

**macOS:**
- `Telos.app` - App bundle (~60-90 MB compressed)
- `Telos-v*-macOS.dmg` - Disk image installer (~40-60 MB)

### Build Time

- **Windows**: ~5-7 minutes
- **macOS**: ~8-10 minutes
- **Total**: ~10 minutes (parallel)

### Cost

**FREE** for public repos!

**Private repos:**
- 2,000 minutes/month free
- Each build uses ~15 minutes
- Can do ~130 builds/month for free

### Customization

To change build triggers, edit the `on:` section:

```yaml
on:
  push:
    branches: [ main ]  # Only build on main
  
  # Or for releases only:
  push:
    tags:
      - 'v*'  # Only build on version tags
```

### Troubleshooting

**Build fails on Windows:**
- Check `build_installer.py` runs locally on Windows
- Check all dependencies in `requirements.txt`
- View logs in Actions tab

**Build fails on macOS:**
- Check `build_macos.py` syntax
- Ensure PyInstaller spec is valid
- View logs in Actions tab

**Artifacts not uploading:**
- Check paths in workflow match build output
- Ensure build actually creates files
- Check `dist/` directory contents in logs

**Release not created:**
- Must push a tag starting with `v` (e.g., `v1.0.0`)
- Both Windows and macOS builds must succeed
- Check `GITHUB_TOKEN` permissions

### Local Testing

Before pushing, test the build scripts locally:

**Windows:**
```bash
cd client
python build_installer.py
# Should create dist/Telos.exe
```

**macOS:**
```bash
cd client
python build_macos.py
# Should create dist/Telos.app and .dmg
```

### CI/CD Best Practices

1. **Test locally first** - Don't rely on CI to catch build errors
2. **Use semantic versioning** - `v1.0.0`, `v1.0.1`, etc.
3. **Tag releases** - Only create releases for tested versions
4. **Monitor Actions** - Check build status regularly
5. **Cache dependencies** - Already enabled with `cache: 'pip'`

### Next Steps

After setup:
1. ✅ Push code to GitHub
2. ✅ Go to Actions tab
3. ✅ Watch the build run
4. ✅ Download artifacts
5. ✅ Test the built apps
6. ✅ Create a release tag when ready

## Status Badges

Add to your README.md:

```markdown
![Build Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-desktop-apps.yml/badge.svg)
```

This shows if the latest build passed or failed.

