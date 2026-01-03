# Quick Fix: "telos is unrecognized" Error

## TL;DR

If `telos` command isn't found after `pip install telos-tracker`, use this:

```bash
python -m telos_tracker.cli setup
python -m telos_tracker.cli
```

Or install with pipx (better):
```bash
pip install pipx
pipx install telos-tracker
telos setup
```

## What's the Problem?

**It's a PATH issue, not a bug.** 

When you run `pip install telos-tracker`, it puts the `telos` command in Python's Scripts directory. If that directory isn't in your system's PATH environment variable, your shell can't find it.

## Permanent Fix

### Windows:
1. Run: `python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))"`
2. Copy that path (e.g., `C:\Users\You\AppData\Local\Programs\Python\Python312\Scripts`)
3. Press Win+X → System → Advanced → Environment Variables
4. Edit "Path" under User variables → Add new → Paste the path
5. Restart terminal and try `telos --version`

### Mac/Linux:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
telos --version
```

(Use `~/.zshrc` instead if you're on Mac with Zsh)

## Best Solution: Use pipx

pipx is designed for Python CLI apps and handles PATH automatically:

```bash
pip install pipx
pipx ensurepath
pipx install telos-tracker
telos setup
telos
```

## More Info

- **Full troubleshooting guide:** See `INSTALLATION_TROUBLESHOOTING.md`
- **Technical explanation:** See `docs/INSTALLATION_ISSUES_EXPLAINED.md`
- **Your package is fine!** This affects all Python CLI tools (pytest, black, poetry, etc.)

## For Package Maintainers

This is documented and not a bug. Consider:
1. Adding pipx recommendation to PyPI description
2. Showing post-install message with `python -m` hint
3. Adding to README/docs (already done!)

