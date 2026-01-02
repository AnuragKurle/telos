# Telos Installation Flow

## 🎯 User Experience (Your Friend's Perspective)

### Step 1: Download
Your friend receives a link and downloads: **`TelosSetup-v0.1.0.exe`** (~50 MB)

### Step 2: Run the Installer
Double-click `TelosSetup.exe`

**Windows SmartScreen Warning (First Time):**
```
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.

[More info]  [Don't run]
```

- Click **"More info"**
- Click **"Run anyway"**

**Why this happens:** The app isn't code-signed yet (requires $100-300/year certificate)

### Step 3: Installation Wizard

**Welcome Screen**
```
┌─────────────────────────────────────┐
│  Welcome to Telos Setup             │
│                                     │
│  This will install Telos on your   │
│  computer.                          │
│                                     │
│  [Next]  [Cancel]                  │
└─────────────────────────────────────┘
```

**Installation Location**
```
┌─────────────────────────────────────┐
│  Select Destination Location        │
│                                     │
│  Where should Telos be installed?   │
│                                     │
│  C:\Program Files\Telos             │
│  [Browse...]                        │
│                                     │
│  [< Back]  [Next]  [Cancel]        │
└─────────────────────────────────────┘
```

**Additional Options**
```
┌─────────────────────────────────────┐
│  Select Additional Tasks            │
│                                     │
│  ☐ Create a desktop icon            │
│  ☐ Create a Quick Launch icon       │
│  ☑ Start Telos when Windows starts  │
│                                     │
│  [< Back]  [Install]  [Cancel]     │
└─────────────────────────────────────┘
```

**Installing**
```
┌─────────────────────────────────────┐
│  Installing Telos                   │
│                                     │
│  [████████████░░░░░░░] 75%         │
│                                     │
│  Extracting files...                │
└─────────────────────────────────────┘
```

**Completion**
```
┌─────────────────────────────────────┐
│  Completing Telos Setup             │
│                                     │
│  Telos has been installed!          │
│                                     │
│  ☑ Launch Telos                     │
│                                     │
│  [Finish]                           │
└─────────────────────────────────────┘
```

### Step 4: First Launch (if selected)
Telos opens automatically and shows the onboarding wizard:
1. Welcome screen
2. Privacy notice
3. Email setup (optional)
4. Goal setting
5. Quick tutorial

### Step 5: Running in Background
- Telos icon appears in system tray
- App runs quietly in the background
- Click icon to open dashboard

---

## 📁 What Gets Installed?

### Files Installed:
```
C:\Program Files\Telos\
├── Telos.exe                    ← Main application
├── config.yaml.example          ← Configuration template
├── README.txt                   ← Quick reference
├── docs\
│   └── PRIVACY_POLICY.txt      ← Privacy information
└── prompts\                     ← AI prompt templates
    ├── screenshot_analysis.txt
    ├── daily_summary.txt
    └── session_enrichment.txt
```

### User Data Location:
```
C:\Users\[Username]\AppData\Roaming\Telos\
├── config.yaml                  ← User configuration
├── telos.db                     ← Activity database
└── logs\                        ← Application logs
    └── latest.log
```

### Shortcuts Created:
- **Start Menu**: Windows Start → Telos
- **Desktop** (optional): Desktop icon
- **Startup** (optional): Auto-starts with Windows

---

## 🔄 Uninstallation

### How User Uninstalls:

**Option 1: Windows Settings**
```
Settings → Apps → Apps & features → Telos → Uninstall
```

**Option 2: Start Menu**
```
Start Menu → Telos → Uninstall Telos
```

**Option 3: Control Panel**
```
Control Panel → Programs → Uninstall a program → Telos → Uninstall
```

### What Gets Removed:
- ✅ Application files (C:\Program Files\Telos\)
- ✅ Start menu shortcuts
- ✅ Desktop shortcut (if created)
- ✅ Startup entry (if enabled)
- ⚠️ **User data preserved** (C:\Users\...\AppData\Roaming\Telos\)

**To completely remove all data:**
User must manually delete: `%APPDATA%\Telos\`

---

## 🔨 Building the Installer (Your Perspective)

### Prerequisites:
1. **Python 3.9+** (you have this)
2. **PyInstaller** (auto-installed by script)
3. **Inno Setup** (free download)

### Install Inno Setup:
```
1. Download: https://jrsoftware.org/isdl.php
2. Run installer (InnoSetup-6.x.exe)
3. Install to default location (C:\Program Files (x86)\Inno Setup 6\)
```

### Build Command:
```bash
cd client
python build_installer.py
```

### What Happens:
1. ✅ Checks dependencies (installs PyInstaller if needed)
2. ✅ Cleans previous builds
3. ✅ Builds standalone .exe with PyInstaller (~80 MB)
4. ✅ Creates installer with Inno Setup (~50 MB compressed)
5. ✅ Outputs: `dist/TelosSetup-v0.1.0.exe`

### Output:
```
client/
└── dist/
    ├── Telos.exe                          ← Standalone (for testing)
    ├── TelosSetup-v0.1.0.exe             ← INSTALLER (share this!)
    └── README.txt                         ← User instructions
```

---

## 📤 Distribution Process

### 1. Build the Installer
```bash
cd client
python build_installer.py
```

### 2. Test Locally
```bash
cd dist
.\TelosSetup-v0.1.0.exe
```
- Run through full installation
- Test the installed app
- Verify shortcuts work
- Test uninstall

### 3. Upload to Sharing Service
- **Google Drive**: Upload → Get link → Share
- **Dropbox**: Upload → Share → Copy link
- **Your website**: Upload to downloads page

### 4. Share with Users
```
Hey! Try my productivity tracker:

Download: [link to TelosSetup.exe]

Installation:
1. Download TelosSetup.exe
2. Run it (might show Windows warning - click "Run anyway")
3. Follow the installation wizard
4. Done! Telos will start automatically

Let me know what you think!
```

---

## 🆚 Comparison: Installer vs Standalone

### Standalone .exe (What we had before)
```
User downloads: Telos.exe
User runs: Direct execution
Pro: One click to run
Con: No shortcuts, no uninstaller, not "installed" properly
```

### Installer .exe (What you want - NEW!)
```
User downloads: TelosSetup.exe
User runs: Installation wizard
Pro: Professional install, shortcuts, proper uninstall
Con: Extra installation step (but standard Windows UX)
```

---

## ⚡ Quick Reference

### For You (Building):
```bash
# Install Inno Setup first (one-time)
# Download from: https://jrsoftware.org/isdl.php

# Build installer
cd client
python build_installer.py

# Test installer
cd dist
.\TelosSetup-v0.1.0.exe

# Upload and share
# Upload: dist/TelosSetup-v0.1.0.exe
```

### For Your Friend (Installing):
```
1. Download TelosSetup.exe
2. Run it
3. Click "Run anyway" if warned
4. Follow installation wizard
5. Done!
```

---

## 🎯 Summary

**Installation Flow:**
1. Download TelosSetup.exe (one file, ~50 MB)
2. Run it → Standard Windows installer appears
3. Click through wizard (Next → Install → Finish)
4. App is now installed with shortcuts
5. Launch from Start Menu or Desktop

**Much better than:**
- ❌ `pip install telos` (requires Python knowledge)
- ❌ Standalone .exe (no proper installation)
- ❌ Manual setup (confusing for non-tech users)

**As simple as installing:** Chrome, Spotify, Discord, or any Windows app!

---

## 🚀 Next Steps

1. **Install Inno Setup** (5 minutes)
2. **Run build script** (1 minute)
3. **Test installer locally** (2 minutes)
4. **Share with your friend** (30 seconds)

**Total time to launch beta: ~10 minutes!**

