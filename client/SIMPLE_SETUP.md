# Telos - Simple Setup Guide

## For You (Building the Installer)

### 1️⃣ One-Time Setup (5 minutes)
Download and install **Inno Setup**:
- Link: https://jrsoftware.org/isdl.php
- File: `innosetup-6.x.x.exe`
- Just click through the installer (default settings)

### 2️⃣ Build the Installer (1 minute)
```bash
cd client
python build_installer.py
```

**Output:** `dist/TelosSetup-v0.1.0.exe` (~50 MB)

### 3️⃣ Test It (2 minutes)
```bash
cd dist
.\TelosSetup-v0.1.0.exe
```
Run through the installation wizard to make sure it works.

### 4️⃣ Share It (30 seconds)
1. Upload `TelosSetup-v0.1.0.exe` to Google Drive/Dropbox
2. Get shareable link
3. Send to your friend

---

## For Your Friend (Installing Telos)

### Super Simple Installation:

**Step 1:** Download `TelosSetup.exe` from the link you send them

**Step 2:** Double-click to run it

**Step 3:** If Windows shows a warning:
- Click "More info"
- Click "Run anyway"

**Step 4:** Follow the installation wizard:
- Click "Next"
- Click "Install"
- Click "Finish"

**Step 5:** Done! Telos is now installed and running.

---

## Installation Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  YOU: Build the Installer                               │
└─────────────────────────────────────────────────────────┘
                      │
                      ├─ Install Inno Setup (one-time)
                      ├─ Run: python build_installer.py
                      └─ Upload: dist/TelosSetup.exe
                      
                      ↓

┌─────────────────────────────────────────────────────────┐
│  YOUR FRIEND: Install Telos                             │
└─────────────────────────────────────────────────────────┘
                      │
                      ├─ Download TelosSetup.exe
                      ├─ Run installer
                      ├─ Click through wizard
                      ├─ Telos is now installed!
                      └─ Find it in Start Menu
```

---

## What Your Friend Sees

### 1. Download
```
TelosSetup-v0.1.0.exe (50 MB)
```

### 2. Run Installer
```
┌──────────────────────────────┐
│  Welcome to Telos Setup      │
│                              │
│  [Next]  [Cancel]           │
└──────────────────────────────┘
```

### 3. Choose Install Location
```
┌──────────────────────────────┐
│  Install to:                 │
│  C:\Program Files\Telos      │
│                              │
│  [Next]  [Cancel]           │
└──────────────────────────────┘
```

### 4. Select Options
```
┌──────────────────────────────┐
│  ☐ Desktop icon              │
│  ☑ Start with Windows        │
│                              │
│  [Install]  [Cancel]        │
└──────────────────────────────┘
```

### 5. Installing
```
┌──────────────────────────────┐
│  Installing...               │
│  [████████░░░] 80%          │
└──────────────────────────────┘
```

### 6. Complete
```
┌──────────────────────────────┐
│  Installation Complete!      │
│  ☑ Launch Telos              │
│                              │
│  [Finish]                    │
└──────────────────────────────┘
```

---

## Message Template for Your Friend

```
Hey! I built a productivity tracker and would love your feedback.

Installation:
1. Download: [your link]
2. Run the installer
3. Click "Run anyway" if Windows warns you
4. Follow the wizard

That's it! Let me know what you think.
```

---

## Troubleshooting

### Build Errors
**"Inno Setup not found"**
- Install Inno Setup from: https://jrsoftware.org/isdl.php
- Run build script again

**"PyInstaller not found"**
- Script auto-installs it, wait a moment
- Or manually: `pip install pyinstaller`

### Installation Errors
**"Windows protected your PC"**
- Normal for unsigned apps
- Click "More info" → "Run anyway"

**"Antivirus blocked it"**
- Temporarily disable antivirus
- Or add Telos to exclusions

---

## Comparison

### Before (Standalone .exe)
```
❌ Download Telos.exe
❌ Run from Downloads folder
❌ No shortcuts
❌ Not "installed"
```

### Now (Installer)
```
✅ Download TelosSetup.exe
✅ Professional installation wizard
✅ Creates shortcuts (Start Menu, Desktop)
✅ Properly installed like any Windows app
✅ Easy to uninstall
```

---

## That's It!

As simple as installing Chrome, Spotify, or any Windows app.

**For you:** Build → Upload → Share
**For them:** Download → Install → Use

Total time: ~10 minutes to launch your beta! 🚀

