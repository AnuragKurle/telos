# Git Workflow for Telos Development

## Branch Strategy

### 🔵 `main-monorepo` (Development Branch)
**Purpose:** Active development and testing
**Usage:** 
- All new features are developed here
- Test changes thoroughly before promoting to production
- Can be unstable or have experimental features
- Deploy to dev environment for testing

### 🟢 `prod-monorepo` (Production Branch)
**Purpose:** Stable, production-ready code
**Usage:**
- Only contains tested, stable code
- This branch is used for releases and deployments
- Cherry-pick commits from `main-monorepo` after testing
- Deploy to production Cloud Run from this branch

---

## Development Workflow

### 1️⃣ **Working on New Features** (main-monorepo)

```bash
# Ensure you're on dev branch
git checkout main-monorepo

# Make your changes...

# Commit your changes
git add .
git commit -m "feat: Your feature description"

# Push to remote
git push origin main-monorepo
```

### 2️⃣ **Testing Your Changes**

```bash
# Run local tests
cd client
python main.py

# Test backend deployment (dev environment)
cd backend
.\deploy-anywhere.ps1
```

### 3️⃣ **Promoting to Production** (After Testing)

**Option A: Cherry-pick specific commits (Recommended)**
```bash
# Switch to production branch
git checkout prod-monorepo

# Cherry-pick the tested commits from dev
git cherry-pick <commit-hash>

# Or cherry-pick multiple commits
git cherry-pick <commit-hash-1> <commit-hash-2>

# Push to production
git push origin prod-monorepo
```

**Option B: Merge all changes**
```bash
# Switch to production branch
git checkout prod-monorepo

# Merge dev into prod
git merge main-monorepo

# Push to production
git push origin prod-monorepo
```

### 4️⃣ **Deploy Production**

```bash
# Make sure you're on prod branch
git checkout prod-monorepo

# Deploy backend to production
cd backend
.\deploy-anywhere.ps1

# Build client installer for users
cd ../client
python setup_build.py
```

---

## Quick Reference

### Check Current Branch
```bash
git branch
```

### View Commit History
```bash
git log --oneline --graph --all
```

### Find Commit Hash for Cherry-picking
```bash
# Show recent commits on dev branch
git log main-monorepo --oneline -10
```

### Undo Local Changes (Not Committed)
```bash
git restore <file>
# Or restore all files
git restore .
```

### View Changes Between Branches
```bash
git diff prod-monorepo..main-monorepo
```

---

## Release Checklist

Before promoting to production:

- [ ] ✅ All features tested locally
- [ ] ✅ Backend deployed to dev and verified working
- [ ] ✅ Client tested with dev backend
- [ ] ✅ No critical bugs or errors in logs
- [ ] ✅ Update version numbers if needed
- [ ] ✅ Cherry-pick or merge to `prod-monorepo`
- [ ] ✅ Deploy backend from `prod-monorepo`
- [ ] ✅ Build and test client installer
- [ ] ✅ Tag release: `git tag v0.1.0`
- [ ] ✅ Push tag: `git push origin v0.1.0`

---

## Emergency Rollback

If production breaks:

```bash
# Option 1: Revert to previous commit
git checkout prod-monorepo
git revert <bad-commit-hash>
git push origin prod-monorepo

# Option 2: Hard reset (use with caution!)
git reset --hard <last-good-commit-hash>
git push --force origin prod-monorepo

# Redeploy
cd backend
.\deploy-anywhere.ps1
```

---

## Tips

1. **Always test on `main-monorepo` first**
2. **Use descriptive commit messages**: `feat:`, `fix:`, `docs:`, `refactor:`
3. **Cherry-pick only tested commits** to production
4. **Tag releases** for easy rollback: `git tag v0.1.0`
5. **Keep prod stable** - never experiment on `prod-monorepo`

---

## Current Setup Summary

- **Dev Branch**: `main-monorepo` 
- **Prod Branch**: `prod-monorepo`
- **Backend**: Deployed via `backend/deploy-anywhere.ps1`
- **Client**: Built via installer scripts (see DISTRIBUTION.md)

