# GitHub Actions Quick Start - Automated Builds

## 🚀 Get macOS and Windows builds without owning a Mac!

### What You Get

After setup (5 minutes), every time you push code:
- ✅ Automatic Windows `.exe` build (~5 min)
- ✅ Automatic macOS `.app` + `.dmg` build (~8 min)
- ✅ Download links for both
- ✅ **Completely FREE** for public repos
- ✅ **No Mac required!**

---

## Step-by-Step Setup (5 minutes)

### 1️⃣ Push to GitHub

```bash
# If not already on GitHub:
git add .
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### 2️⃣ Enable Actions

1. Go to your GitHub repo
2. Click **"Actions"** tab at the top
3. If asked, click **"I understand my workflows, go ahead and enable them"**

Done! That's the entire setup.

### 3️⃣ Trigger a Build

**Option A: Push code (automatic)**
```bash
git push origin main
```

**Option B: Manual trigger**
1. Go to **Actions** tab
2. Click **"Build Desktop Apps"**
3. Click **"Run workflow"** → **"Run workflow"**

### 4️⃣ Watch It Build

Go to **Actions** tab → Click the running workflow

You'll see:
```
✓ Build Windows  (5-7 minutes)
✓ Build macOS    (8-10 minutes)
```

Both run in parallel!

### 5️⃣ Download Your Apps

When complete:
1. Scroll to bottom of workflow run
2. See **"Artifacts"** section
3. Download:
   - `Telos-Windows-[version].zip` (contains Telos.exe)
   - `Telos-macOS-DMG-[version].zip` (contains .dmg installer)

Unzip and you have your apps! 🎉

---

## Creating Releases (for users to download)

### Quick Release

```bash
# Tag your version
git tag v0.1.0-beta
git push origin v0.1.0-beta
```

**That's it!**

GitHub will:
1. ✅ Build Windows + macOS versions
2. ✅ Create a Release page
3. ✅ Attach installers to the release
4. ✅ Generate release notes

### Share with Users

Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest`

Users click → Download → Install. No GitHub account needed!

---

## Testing Your Build

### Windows
```bash
# Unzip and run
Telos.exe
```

Should work without Python installed!

### macOS
```bash
# Open DMG
open Telos-v0.1.0-beta-macOS.dmg

# Drag to Applications
# Right-click → Open (first time)
```

Should work on any Mac!

---

## Customization

### Only Build on Releases (Save Minutes)

Edit `.github/workflows/build-desktop-apps.yml`:

Change:
```yaml
on:
  push:
    branches: [ main, master, develop ]
```

To:
```yaml
on:
  push:
    tags:
      - 'v*'
```

Now builds only when you push a version tag.

### Add Build Status Badge

Add to your README.md:
```markdown
![Build](https://github.com/USERNAME/REPO/actions/workflows/build-desktop-apps.yml/badge.svg)
```

Shows: ![passing](https://img.shields.io/badge/build-passing-brightgreen)

---

## Troubleshooting

### Build Fails

1. Go to **Actions** tab
2. Click failed workflow
3. Click failed job (red ❌)
4. Expand failed step
5. Read error message

Common fixes:
- **Windows**: Check `build_installer.py` runs locally
- **macOS**: Check `build_macos.py` syntax
- **Both**: Check all files are committed

### Artifacts Not Appearing

Check the build actually creates files:
1. View workflow run
2. Look at "Build [Platform]" job
3. Check build completed successfully
4. Verify files in `dist/` folder

### Slow Builds

First builds are slower (~10-15 min each). Subsequent builds are faster (~5-8 min) due to caching.

---

## Costs

### Public Repository
- ✅ **Unlimited builds**
- ✅ **Unlimited minutes**
- ✅ **FREE forever**

### Private Repository
- ✅ **2,000 minutes/month** free
- ✅ Each build uses ~15 minutes
- ✅ **~130 builds/month free**
- 💰 $0.008/minute after that

**Most projects never hit the limit!**

---

## What's Next?

After your first successful build:

1. ✅ Download and test both apps
2. ✅ Create a release tag: `git tag v0.1.0 && git push origin v0.1.0`
3. ✅ Share release link with testers
4. ✅ Push updates and get new builds automatically

**That's it! You now have professional CI/CD for your desktop app.**

---

## Advanced (Optional)

### Code Signing
- Windows: Requires code signing certificate (~$100/year)
- macOS: Requires Apple Developer account ($99/year)

Not needed for testing or personal use.

### Build Multiple Versions
See `.github/GITHUB_ACTIONS_SETUP.md` for:
- Multiple Python versions
- Scheduled builds
- Slack/Discord notifications
- Security scanning

---

## Support

**Full documentation:**
- `.github/workflows/README.md` - Workflow details
- `.github/GITHUB_ACTIONS_SETUP.md` - Complete guide
- GitHub Actions docs: https://docs.github.com/actions

**Questions?** Open an issue on GitHub!

---

## Summary

You just got:
- ✅ Free cloud Mac access
- ✅ Automated Windows + macOS builds
- ✅ Professional release system
- ✅ No hardware purchase needed

**Total setup time:** 5 minutes  
**Total cost:** $0

Enjoy your automated builds! 🚀🎉

