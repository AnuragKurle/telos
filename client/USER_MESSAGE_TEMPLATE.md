# Copy-Paste Response for Users Reporting "telos is unrecognized"

Use this template when users report the command not found error:

---

## Response Template

Hi! This is a PATH configuration issue, not a bug with the package. Here's how to fix it:

### Quick Fix (Works Immediately):

Instead of `telos`, run:
```bash
python -m telos_tracker.cli setup
python -m telos_tracker.cli
```

This works without any system changes.

### Best Solution (Permanent):

Install with `pipx` instead of `pip`:
```bash
pip install pipx
pipx install telos-tracker
telos setup
```

pipx handles PATH automatically and is designed for Python CLI tools.

### Alternative: Fix PATH Manually

**Windows:**
1. Run: `python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))"`
2. Add that directory to your PATH (System Properties → Environment Variables → Path → New)
3. Restart terminal

**Mac/Linux:**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

(Use `~/.zshrc` if on macOS with Zsh)

### Why This Happens

When `pip` installs a Python CLI tool, it places the executable in Python's Scripts directory. If that directory isn't in your system's PATH environment variable, your shell can't find the command.

This is a common issue with all Python CLI tools (pytest, black, poetry, etc.), not specific to telos.

**Full troubleshooting guide:** https://github.com/YOUR_REPO/blob/main/client/INSTALLATION_TROUBLESHOOTING.md

---

## For GitHub Issues

**Title:** "telos command not found" after pip install

**Response:**

Thanks for reporting this! This is a PATH configuration issue. The package installed correctly, but your shell can't find the `telos` command.

**Quick workaround:**
```bash
python -m telos_tracker.cli
```

**Permanent fix - Use pipx (recommended):**
```bash
pip install pipx
pipx install telos-tracker
telos
```

**Or add Python Scripts to PATH:**
- See our troubleshooting guide: [INSTALLATION_TROUBLESHOOTING.md](./client/INSTALLATION_TROUBLESHOOTING.md)

This affects all Python CLI tools when Python's Scripts directory isn't in PATH. pipx solves this automatically.

---

## For Discord/Slack/Community

> **User:** "I installed telos but it says command not found?"

**Quick response:**
```
That's a PATH issue. Try: python -m telos_tracker.cli

Or install with pipx (better):
pip install pipx && pipx install telos-tracker && telos
```

---

## FAQ Additions

**Q: "telos is not recognized" after pip install**

A: This means Python's Scripts directory isn't in your PATH. Either:
1. Run `python -m telos_tracker.cli` instead
2. Install with `pipx install telos-tracker` (handles PATH automatically)
3. Add Scripts directory to PATH manually ([guide](./INSTALLATION_TROUBLESHOOTING.md))

**Q: Do I need to uninstall and reinstall?**

A: No! The package is installed correctly. You just need to either:
- Use the `python -m telos_tracker.cli` command, or
- Fix your PATH configuration

**Q: Is this a bug?**

A: No, this is a standard environment configuration issue that affects all Python CLI applications. The package is working correctly.

---

## Social Media Posts

### Twitter/X:

```
Installed Telos via pip but getting "command not found"?

Quick fix: python -m telos_tracker.cli

Better fix: pipx install telos-tracker

It's a PATH issue, not a bug. Full guide: [link]
```

### Reddit r/Python Post:

**Title:** PSA: "Command not found" after pip install? Use pipx for CLI tools

**Body:**
```
If you're getting "command not found" errors after `pip install` for CLI tools like telos, pytest, black, etc., it's because Python's Scripts directory isn't in your PATH.

Solutions:
1. Run via Python: `python -m package_name.cli`
2. Use pipx: `pipx install package-name` (handles PATH automatically)
3. Add Scripts to PATH manually

pipx is specifically designed for CLI tools and prevents this issue.

More: https://pipx.pypa.io/
```

---

## Email Auto-Response (Support)

Subject: Re: Telos installation - command not found

```
Hi there,

Thanks for reaching out! The "telos is unrecognized" error means Python's Scripts directory isn't in your system's PATH environment variable. The package is installed correctly, your shell just can't find it.

Here's the quickest fix:

Instead of typing 'telos', use:
  python -m telos_tracker.cli

For a permanent solution, I recommend using pipx:
  pip install pipx
  pipx install telos-tracker
  telos

pipx is designed for Python CLI applications and handles PATH configuration automatically.

For detailed troubleshooting: [link to INSTALLATION_TROUBLESHOOTING.md]

Let me know if you need any help!

Best,
[Your Name]
```

---

## Documentation Website FAQ Section

### Installation Issues

#### Command not found after pip install

**Problem:** After running `pip install telos-tracker`, the command `telos` is not recognized.

**Cause:** Python's Scripts directory is not in your system PATH.

**Solutions:**

1. **Use Python module syntax** (works immediately):
   ```bash
   python -m telos_tracker.cli
   ```

2. **Install with pipx** (recommended):
   ```bash
   pip install pipx
   pipx install telos-tracker
   telos
   ```

3. **Add to PATH manually**:
   - [Windows Guide](#windows-path)
   - [Mac/Linux Guide](#mac-linux-path)

**Read more:** [Complete Troubleshooting Guide →](./INSTALLATION_TROUBLESHOOTING.md)

---

Use these templates to provide consistent, helpful responses to users! 📋

