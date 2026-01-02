# Quick Guide: Build and Share Telos

## 🔨 Building the Executable

### One-Command Build
```bash
cd client
python build_installer.py
```

**That's it!** The script will:
- ✅ Install PyInstaller if needed
- ✅ Bundle all dependencies
- ✅ Create standalone .exe
- ✅ Generate README for users
- ✅ Create distribution .zip file

### Output Files
```
client/
├── Telos-v0.1.0-beta-Windows.zip  ← Share this file
│   ├── Telos.exe                   ← Standalone executable
│   └── README.txt                  ← User instructions
└── dist/
    └── Telos.exe                   ← Test this first
```

---

## 🧪 Testing Locally

Before sharing with your friend:

```bash
cd client/dist
.\Telos.exe
```

**Test checklist:**
- [ ] App launches without errors
- [ ] Onboarding wizard works
- [ ] Can track activity
- [ ] Dashboard displays data
- [ ] System tray icon appears
- [ ] Can pause/resume tracking
- [ ] Can exit cleanly

---

## 📤 Sharing with Beta Testers

### Option 1: Google Drive (Recommended)
1. Upload `Telos-v0.1.0-beta-Windows.zip` to Google Drive
2. Right-click → Get link → Anyone with the link can view
3. Share the link

### Option 2: Dropbox
1. Upload to Dropbox
2. Create sharing link
3. Share with your friend

### Option 3: WeTransfer
1. Go to wetransfer.com
2. Upload the .zip file
3. Send download link

### Option 4: Direct File Transfer
- USB drive
- Email (if under 25MB)
- Messaging apps (WhatsApp, Telegram, etc.)

---

## 📧 Message Template for Your Friend

```
Hey! I built this productivity tracker called Telos and would love your feedback.

Download: [insert link here]

It's a Windows app that runs in the background and shows you how you spend your time.

Quick setup:
1. Download and extract the .zip
2. Run Telos.exe (Windows might show a security warning - click "Run anyway")
3. Follow the setup wizard

Let me know what you think! It's still beta so expect some bugs 😅

Instructions are in the README.txt file included in the download.
```

---

## 🔄 Updating the Beta

When you fix bugs or add features:

1. **Make changes in code**
2. **Test locally**
   ```bash
   cd client
   python main.py
   ```

3. **Rebuild executable**
   ```bash
   python build_installer.py
   ```

4. **Update version** (in build_installer.py):
   ```python
   VERSION = "0.1.1-beta"  # Increment this
   ```

5. **Share new version**
   - Upload new .zip
   - Tell users what changed

---

## 📊 Build Stats

Typical build times:
- First build: 2-3 minutes (downloads dependencies)
- Subsequent builds: 30-60 seconds

Typical file sizes:
- Telos.exe: ~80-100 MB
- .zip file: ~40-50 MB (compressed)

---

## 🐛 Build Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Module not found during build"
Add to `HIDDEN_IMPORTS` in `build_installer.py`:
```python
HIDDEN_IMPORTS = [
    'your_missing_module',
    # ... other imports
]
```

### "Build succeeds but .exe crashes"
1. Test without `--windowed` flag (shows console errors)
2. Check logs: `%APPDATA%\Telos\logs\`
3. Add `--debug all` flag for verbose output

### ".exe is too large"
This is normal for PyInstaller. To reduce size:
- Use `--exclude-module` for unused packages
- Use UPX compression (optional)

---

## 🎯 Pre-Release Checklist

Before sharing with beta testers:

### Code
- [ ] All features work locally
- [ ] No critical bugs
- [ ] Proper error handling
- [ ] Logs don't expose sensitive data

### Build
- [ ] Build completes successfully
- [ ] .exe runs on your machine
- [ ] Test on fresh Windows install (if possible)
- [ ] Test with Windows Defender enabled

### Documentation
- [ ] Update BETA_TESTING_GUIDE.md
- [ ] Include setup instructions
- [ ] List known issues
- [ ] Provide contact info

### Distribution
- [ ] Upload to sharing platform
- [ ] Test download link
- [ ] Create shareable message
- [ ] Prepare for feedback

---

## 🔐 Security Notes

### Windows Defender Warning
**Expected behavior**: First-time users will see a SmartScreen warning

**Why?**: Unsigned executables are flagged by Windows

**Solutions**:
1. **Tell users**: Click "More info" → "Run anyway"
2. **Code signing** (costs $100-300/year): Eliminates warnings
3. **Build reputation**: After enough users run it, warnings decrease

### Antivirus False Positives
Some antivirus software may flag PyInstaller apps:
- **Normal**: New .exe files are often flagged
- **Solution**: Build reputation over time
- **If serious**: Get code signing certificate

---

## 📈 Beta Feedback Loop

1. **Release beta** → Share .exe
2. **Collect feedback** → Email, messages
3. **Fix issues** → Update code
4. **Rebuild** → New .exe
5. **Repeat** → Until stable

---

## 🚀 Moving to Production

When ready for wider release:

### Phase 1: Improved Beta
- [ ] Get code signing certificate
- [ ] Add auto-update check
- [ ] Set up crash reporting

### Phase 2: Public Launch
- [ ] Create website landing page
- [ ] Host downloads on your domain
- [ ] Publish to PyPI: `pip install telos`
- [ ] Create proper Windows installer (.msi)

### Phase 3: Scale
- [ ] Microsoft Store listing
- [ ] Chocolatey package
- [ ] WinGet package
- [ ] Marketing & launch

---

## 💡 Pro Tips

1. **Version numbers**: Use semantic versioning (0.1.0, 0.1.1, 0.2.0)
2. **Changelog**: Keep a list of changes between versions
3. **Backup builds**: Save each .exe version for rollback
4. **Test matrix**: Test on Windows 10 and 11 if possible
5. **User analytics**: Track which features are used most

---

## 🆘 Need Help?

### Build Issues
1. Check PyInstaller docs: https://pyinstaller.org/
2. Google the error message
3. Check PyInstaller GitHub issues

### Distribution Issues
1. Test download link yourself
2. Ask friend to describe exactly what they see
3. Request screenshots of any errors

---

**You're all set! Build and share your beta today! 🎉**

