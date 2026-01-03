# Installation Troubleshooting Guide

## Problem: "telos is unrecognized" after pip install

If you see this error after running `pip install telos-tracker`:

```bash
$ telos
'telos' is not recognized as an internal or external command...
# or
bash: telos: command not found
```

### Root Cause

When you install a Python package with `pip`, it places executable scripts (like `telos`) in Python's Scripts directory. If this directory is not in your system's PATH environment variable, your shell won't be able to find the command.

### Solution 1: Run via Python Module (Quick Fix)

Instead of typing `telos`, run:

```bash
python -m telos_tracker.cli
```

This works immediately without any PATH changes. You can create an alias for convenience:

**Windows (PowerShell):**
```powershell
# Add to your PowerShell profile
function telos { python -m telos_tracker.cli $args }
```

**Mac/Linux (Bash/Zsh):**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias telos='python -m telos_tracker.cli'
```

### Solution 2: Add Python Scripts to PATH (Permanent Fix)

#### Windows

1. **Find your Python Scripts directory:**
   ```powershell
   python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))"
   ```
   
   Typical location: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\Scripts`

2. **Add to PATH:**
   - Press `Win + X` → System → Advanced system settings
   - Click "Environment Variables"
   - Under "User variables", select `Path` → Edit
   - Click "New" and paste the Scripts directory path
   - Click OK on all dialogs

3. **Restart your terminal** (important!)

4. **Verify:**
   ```powershell
   telos --version
   ```

#### Mac/Linux

1. **Find your Python Scripts directory:**
   ```bash
   python3 -m site --user-base
   ```
   
   The Scripts directory is usually `<result>/bin`, e.g., `/Users/you/.local/bin`

2. **Add to PATH:**
   
   **For Bash (add to `~/.bashrc`):**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```
   
   **For Zsh (add to `~/.zshrc`):**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **Verify:**
   ```bash
   telos --version
   ```

### Solution 3: Use pipx (Recommended for CLI Tools)

`pipx` is designed specifically for installing Python CLI applications. It automatically handles PATH configuration and isolates each tool in its own virtual environment.

1. **Install pipx:**
   ```bash
   pip install pipx
   pipx ensurepath
   ```

2. **Install telos-tracker with pipx:**
   ```bash
   pipx install telos-tracker
   ```

3. **Use immediately:**
   ```bash
   telos --version
   ```

**Benefits of pipx:**
- Automatic PATH configuration
- Isolated environments (no dependency conflicts)
- Easy upgrades: `pipx upgrade telos-tracker`
- Easy uninstall: `pipx uninstall telos-tracker`

### Solution 4: Virtual Environment (Development)

If you're using a virtual environment, make sure it's activated:

```bash
# Create virtual environment
python -m venv telos_env

# Activate it
# Windows:
telos_env\Scripts\activate
# Mac/Linux:
source telos_env/bin/activate

# Install
pip install telos-tracker

# Now 'telos' works (while venv is active)
telos setup
```

## Verifying Installation

### Check if package is installed:
```bash
pip show telos-tracker
```

Expected output:
```
Name: telos-tracker
Version: 0.1.2
Summary: AI-powered screen time tracker...
Location: .../site-packages
```

### Check where the executable is:
```bash
# Windows
where telos

# Mac/Linux
which telos
```

If this command finds nothing, the PATH issue is confirmed.

### Check Python's Scripts directory:
```bash
# Windows
dir %USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts\telos*

# Mac/Linux
ls ~/.local/bin/telos*
```

If you see the `telos` executable here, it's installed correctly, just not in PATH.

## Still Having Issues?

### Issue: Multiple Python Installations

If you have multiple Python versions installed (e.g., Python 3.10, 3.11, 3.12), make sure you're using the same one:

```bash
# Check which Python you're using
python --version
# or
python3 --version

# Install with the specific version
python3.12 -m pip install telos-tracker
python3.12 -m telos_tracker.cli
```

### Issue: Permission Errors

If you see "Permission denied" errors:

**Don't use sudo/admin** - instead, install for your user only:
```bash
pip install --user telos-tracker
```

This installs to your user directory (usually `~/.local` on Mac/Linux).

### Issue: Package Not Found on PyPI

If `pip install telos-tracker` says the package doesn't exist:

1. **Check your PyPI availability:**
   ```bash
   pip search telos-tracker
   # or visit: https://pypi.org/project/telos-tracker/
   ```

2. **Update pip:**
   ```bash
   pip install --upgrade pip
   ```

3. **Install from source (if package not yet published):**
   ```bash
   git clone https://github.com/AnuragKurle/telos.git
   cd telos/client
   pip install .
   ```

## Platform-Specific Notes

### Windows
- Use PowerShell or Command Prompt (not Git Bash for PATH issues)
- Some users need to restart Windows (not just terminal) for PATH changes
- Windows Defender may scan on first run (causes slight delay)

### macOS
- May need to use `python3` instead of `python`
- Grant Screen Recording permissions: System Settings → Privacy & Security → Screen Recording
- Grant Accessibility permissions: System Settings → Privacy & Security → Accessibility

### Linux
- May need to use `python3` instead of `python`
- Install `python3-pip` if pip is not available
- Some distros require `python3-venv` package for virtual environments

## Quick Reference

| Problem | Solution |
|---------|----------|
| Command not found | `python -m telos_tracker.cli` |
| Want permanent fix | Add Scripts to PATH (see above) |
| Want cleanest install | Use `pipx install telos-tracker` |
| Multiple Python versions | Use `python3.12 -m pip install ...` |
| Permission errors | Use `pip install --user ...` |

## Getting Help

If none of these solutions work:

1. **Check your setup:**
   ```bash
   python --version
   pip --version
   pip show telos-tracker
   echo $PATH  # Mac/Linux
   echo %PATH%  # Windows
   ```

2. **Report the issue:**
   - GitHub: https://github.com/AnuragKurle/telos/issues
   - Include the output from the commands above

3. **Temporary workaround:**
   ```bash
   # Always works, just longer to type
   python -m telos_tracker.cli setup
   python -m telos_tracker.cli
   ```

