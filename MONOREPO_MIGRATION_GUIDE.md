# Monorepo Migration Guide

This guide helps you reorganize the current structure into a clean monorepo.

## What We're Doing

**Before (current structure):**
```
screentracker/
├─ core/
├─ tui/
├─ utils/
├─ main.py
├─ requirements.txt
└─ ...other files
```

**After (monorepo structure):**
```
telos/  (or keep as screentracker)
├─ client/         ← All current Python code moves here
│  ├─ core/
│  ├─ tui/
│  ├─ utils/
│  ├─ main.py
│  └─ requirements.txt
├─ backend/        ← New Node.js backend (already created!)
│  ├─ src/
│  ├─ package.json
│  └─ ...
├─ shared/         ← API contracts (already created!)
│  ├─ api-contract.md
│  └─ constants.json
└─ docs/           ← Project documentation (already exists!)
```

---

## Migration Steps

### Option A: Manual Move (Safest, Recommended)

#### 1. Create client directory
```powershell
mkdir client
```

#### 2. Move Python application files
```powershell
# Move core directories
mv core client/
mv tui client/
mv utils client/
mv prompts client/

# Move main Python files
mv main.py client/
mv service.py client/

# Move Python config/requirements
mv requirements.txt client/
mv config.yaml.example client/

# Keep config.yaml at root if it exists (it's in .gitignore anyway)
# Or move it: mv config.yaml client/ (if you have one)
```

#### 3. Create client README
```powershell
# We'll create this file next
```

#### 4. Test that everything still works
```powershell
cd client
python main.py --help
```

---

### Option B: PowerShell Script (Faster)

Save this as `migrate-to-monorepo.ps1`:

```powershell
# Telos Monorepo Migration Script

Write-Host "🚀 Starting monorepo migration..." -ForegroundColor Cyan

# Create client directory
Write-Host "Creating client/ directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "client" -Force | Out-Null

# Move Python application directories
$dirsToMove = @("core", "tui", "utils", "prompts")
foreach ($dir in $dirsToMove) {
    if (Test-Path $dir) {
        Write-Host "Moving $dir/ to client/" -ForegroundColor Green
        Move-Item -Path $dir -Destination "client/" -Force
    }
}

# Move Python files
$filesToMove = @(
    "main.py",
    "service.py",
    "requirements.txt",
    "config.yaml.example"
)

foreach ($file in $filesToMove) {
    if (Test-Path $file) {
        Write-Host "Moving $file to client/" -ForegroundColor Green
        Move-Item -Path $file -Destination "client/" -Force
    }
}

# Move temp_screenshots if it exists
if (Test-Path "temp_screenshots") {
    Write-Host "Moving temp_screenshots/ to client/" -ForegroundColor Green
    Move-Item -Path "temp_screenshots" -Destination "client/" -Force
}

Write-Host "✅ Migration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the client: cd client && python main.py --help"
Write-Host "2. Update any absolute paths in your code"
Write-Host "3. Read the updated README.md"
Write-Host ""
```

Run it:
```powershell
.\migrate-to-monorepo.ps1
```

---

## Post-Migration Checklist

### ✅ Verify Client Works

```powershell
cd client
python main.py --help
# Should show the normal help output
```

### ✅ Update Config Paths (if needed)

If your `config.yaml` references absolute paths, you might need to update them.

### ✅ Update Import Paths (probably not needed)

Since we're moving the entire `core/`, `tui/`, `utils/` structure together, relative imports should still work:
```python
# These should still work fine
from core.analyzer import analyze_screenshot
from tui.app import run_tui
```

### ✅ Update Database Path (if needed)

If you have a database file, it might be at `./tracking.db`. You may want to:
- Keep it at root (accessible to both client and future backend)
- Or move it to `client/tracking.db` and update the path in code

### ✅ Update .gitignore

We'll update the root `.gitignore` to account for the new structure.

---

## What Files Stay at Root?

These should remain at the repository root:
- `.git/` - Version control
- `.gitignore` - Git ignore rules
- `README.md` - Main project README (will be updated)
- `docs/` - Documentation (Phase 0 guides, etc.)
- `.cursor/` - Cursor IDE config
- Any `.db` or `*.sqlite3` files (database)

---

## Troubleshooting

### "Module not found" errors

If you get import errors after moving:

**Problem:** Working directory is wrong  
**Solution:** Run from `client/` directory or update your run commands

```powershell
# Instead of:
python main.py

# Do:
cd client
python main.py
```

### Paths to database/config are broken

**Problem:** Code looks for `./tracking.db` but it's now in parent directory  
**Solution:** Update paths to `../tracking.db` or move database into `client/`

### Can't find prompts

**Problem:** Prompts directory moved  
**Solution:** Already handled - prompts moved to `client/prompts/`

---

## Reverting (If Needed)

If something goes wrong and you want to revert:

```powershell
# Move everything back out of client/
mv client/* .
rmdir client
```

Or just restore from git:
```powershell
git checkout .
git clean -fd
```

---

## Ready to Start Backend Development?

Once migration is complete:
1. ✅ Client code is in `client/`
2. ✅ Backend skeleton is in `backend/`
3. ✅ API contracts are in `shared/`

Next: Start building the backend (Phase 1)!

```powershell
cd backend
npm install
npm run dev
```

---

**Need Help?** Check the updated `README.md` at the root of the repository for the new structure overview.

