# GitHub Actions Setup Guide

Complete guide to set up automated Windows and macOS builds for Telos.

## Prerequisites

1. ✅ GitHub repository (public or private)
2. ✅ Code pushed to GitHub
3. ✅ That's it! No Mac or special setup needed

## Setup Steps

### Step 1: Push Workflow Files

The workflow files are already in your repo at:
```
.github/workflows/build-desktop-apps.yml
```

If not already pushed:
```bash
git add .github/
git commit -m "Add GitHub Actions for automated builds"
git push origin main
```

### Step 2: Enable Actions

1. Go to your GitHub repository
2. Click the "Actions" tab
3. If prompted, click "I understand my workflows, go ahead and enable them"

That's it! Actions are now enabled.

### Step 3: Trigger Your First Build

**Option A: Push to main branch**
```bash
git push origin main
```

**Option B: Manual trigger**
1. Go to Actions tab
2. Click "Build Desktop Apps" workflow
3. Click "Run workflow" dropdown
4. Click green "Run workflow" button

**Option C: Create a tag (for releases)**
```bash
git tag v0.1.0-beta
git push origin v0.1.0-beta
```

### Step 4: Watch the Build

1. Go to Actions tab
2. Click on the running workflow
3. Watch progress in real-time
4. See logs for each step

Expected output:
```
Build Windows     ✓ (5-7 minutes)
Build macOS       ✓ (8-10 minutes)
```

### Step 5: Download Your Apps

Once builds complete:

1. Scroll to bottom of workflow run page
2. See "Artifacts" section
3. Download:
   - **Telos-Windows-[version].zip** - Contains Telos.exe
   - **Telos-macOS-DMG-[version].zip** - Contains .dmg installer

4. Extract and test!

## Workflow Configuration

### Current Configuration

Builds automatically on:
- ✅ Push to `main`, `master`, or `develop` branches
- ✅ Pull requests to `main` or `master`
- ✅ Version tags (e.g., `v1.0.0`)
- ✅ Manual trigger

### Customizing Triggers

Edit `.github/workflows/build-desktop-apps.yml`:

**Only build releases:**
```yaml
on:
  push:
    tags:
      - 'v*'
```

**Only build on main:**
```yaml
on:
  push:
    branches: [ main ]
```

**Add scheduled builds (nightly):**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
```

## Creating Releases

For official releases with download links:

### Step 1: Tag Your Version

```bash
# Make sure everything is committed
git add .
git commit -m "Release v0.1.0"

# Create version tag
git tag v0.1.0-beta

# Push code and tag
git push origin main
git push origin v0.1.0-beta
```

### Step 2: Automatic Release

The workflow will:
1. ✅ Build Windows version
2. ✅ Build macOS version
3. ✅ Create GitHub Release
4. ✅ Upload installers to release
5. ✅ Generate release notes

### Step 3: Share Release Link

1. Go to your repo
2. Click "Releases" tab
3. Copy release URL
4. Share: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest`

Users can download installers directly!

## Testing the Builds

### Test Windows Build

Download the artifact and run on Windows:
```bash
# Extract Telos-Windows-*.zip
Telos.exe
```

Should:
- ✅ Launch without requiring Python
- ✅ Show onboarding if first run
- ✅ Request permissions
- ✅ Function normally

### Test macOS Build

Download the DMG and install on Mac:
```bash
# Open the DMG
open Telos-v0.1.0-beta-macOS.dmg

# Drag to Applications
# Right-click → Open (first time)
```

Should:
- ✅ Open without errors
- ✅ Request permissions
- ✅ Function normally

## Monitoring Builds

### Status Badges

Add to your README.md to show build status:

```markdown
# Telos

![Build Status](https://github.com/USERNAME/REPO/actions/workflows/build-desktop-apps.yml/badge.svg)

...
```

Shows: ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

### Email Notifications

GitHub sends emails when:
- ✅ Build succeeds (after previous failure)
- ❌ Build fails

Configure in: Settings → Notifications → Actions

### Slack/Discord Notifications

Add to workflow for team notifications:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Build ${{ job.status }}: ${{ github.ref }}"
      }
```

## Troubleshooting

### Build Fails on Windows

**Check:**
1. Does `build_installer.py` run locally?
2. Are all dependencies in `requirements.txt`?
3. Is `pywin32` causing issues?

**View logs:**
1. Go to failed workflow
2. Click "Build Windows" job
3. Expand failed step
4. Read error message

### Build Fails on macOS

**Check:**
1. Is `build_macos.py` syntax correct?
2. Is `Telos_macos.spec` valid?
3. Are macOS-specific tools available?

**Common issues:**
- Missing `macos/` directory → Check it's committed
- Import errors → Check all dependencies installed
- PyInstaller errors → Check spec file

### Artifacts Not Uploading

**Check:**
1. Build actually creates files
2. Paths match in workflow
3. Files aren't gitignored

**View build output:**
```yaml
- name: List dist files
  run: ls -la client/dist/
```

### Slow Builds

**Optimizations already enabled:**
- ✅ Pip caching (saves ~2 minutes)
- ✅ Parallel jobs (Windows + macOS together)
- ✅ Minimal dependencies

**Further optimization:**
```yaml
# Cache PyInstaller build cache
- name: Cache PyInstaller
  uses: actions/cache@v3
  with:
    path: client/build
    key: pyinstaller-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
```

### Rate Limits

**Free tier limits:**
- Public repos: Unlimited
- Private repos: 2,000 minutes/month

**Each build uses:**
- ~15 minutes total (Windows + macOS in parallel)
- Can do ~130 builds/month on free tier

**If you hit limits:**
1. Build only on releases (not every commit)
2. Upgrade to paid plan
3. Self-host runners

## Advanced Configuration

### Build Matrix (Multiple Versions)

Build for multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Code Signing

**Windows (SignTool):**
```yaml
- name: Sign Windows executable
  run: |
    signtool sign /f cert.pfx /p ${{ secrets.CERT_PASSWORD }} dist/Telos.exe
```

**macOS (codesign):**
```yaml
- name: Sign macOS app
  run: |
    codesign --force --deep --sign "${{ secrets.APPLE_CERT }}" dist/Telos.app
```

### Notarization (macOS)

For macOS 10.15+:
```yaml
- name: Notarize macOS app
  run: |
    xcrun altool --notarize-app \
      --primary-bundle-id "dev.telos.tracker" \
      --username "${{ secrets.APPLE_ID }}" \
      --password "${{ secrets.APPLE_APP_PASSWORD }}" \
      --file dist/Telos.dmg
```

## Security Best Practices

### Secrets Management

Store sensitive data in GitHub Secrets:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secrets for:
   - API keys
   - Certificates
   - Passwords

Use in workflow:
```yaml
- name: Use secret
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: echo $API_KEY
```

### Dependency Scanning

Add security checks:
```yaml
- name: Security scan
  run: |
    pip install safety
    safety check
```

## Cost Estimation

### Free Tier (Public Repos)
- ✅ Unlimited builds
- ✅ Unlimited minutes
- ✅ No cost

### Free Tier (Private Repos)
- ✅ 2,000 minutes/month
- ✅ ~130 builds/month
- ✅ No cost if under limit

### Paid Plans
- **Team**: 3,000 minutes/month ($4/month)
- **Enterprise**: 50,000 minutes/month ($21/user/month)

## Next Steps

1. ✅ Push workflow files to GitHub
2. ✅ Enable Actions in repo settings
3. ✅ Trigger your first build
4. ✅ Download and test artifacts
5. ✅ Create a release tag
6. ✅ Share release link with users

## Support Resources

- **GitHub Actions Docs**: https://docs.github.com/actions
- **PyInstaller Docs**: https://pyinstaller.org
- **Workflow Syntax**: https://docs.github.com/actions/reference/workflow-syntax-for-github-actions

## Summary

You now have:
- ✅ Automated Windows builds
- ✅ Automated macOS builds
- ✅ Release automation
- ✅ No Mac hardware required
- ✅ Free (for public repos)
- ✅ Professional CI/CD pipeline

Just push code and GitHub builds everything automatically! 🚀

