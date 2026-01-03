# Technical Explanation: "telos is unrecognized" Error

## Root Cause Analysis

When users report "telos is unrecognized" after `pip install telos-tracker`, there's a **system PATH issue**, not a packaging bug.

### What Happens During pip install

1. **Package Installation:**
   ```bash
   pip install telos-tracker
   ```
   
   - Downloads `telos_tracker-0.1.2-py3-none-any.whl` from PyPI
   - Extracts to `site-packages/telos_tracker/`
   - Installs dependencies (textual, google-genai, etc.)

2. **Entry Point Creation:**
   
   From `pyproject.toml`:
   ```toml
   [project.scripts]
   telos = "telos_tracker.cli:main"
   ```
   
   pip creates an executable script:
   - **Windows:** `Scripts/telos.exe` (wrapper that calls `telos_tracker.cli:main()`)
   - **Mac/Linux:** `bin/telos` (Python script with shebang)

3. **Installation Location:**
   
   - **Global install:** `C:\Python312\Scripts\` or `/usr/local/bin/`
   - **User install (--user):** `~/.local/bin/` or `%APPDATA%\Python\Scripts\`
   - **Virtual env:** `venv/Scripts/` or `venv/bin/`

### Why the Command Isn't Found

The shell searches for commands in directories listed in the `PATH` environment variable. If Python's Scripts directory isn't in PATH, the shell can't find `telos`.

**Check PATH:**
```bash
# Windows
echo %PATH%

# Mac/Linux
echo $PATH
```

If you don't see something like `.../Python312/Scripts` or `.../.local/bin`, that's the problem.

### Why This Happens

**Common scenarios:**

1. **Python installed without "Add to PATH" checkbox** (Windows installer)
2. **User-level pip install** (`pip install --user`) but `~/.local/bin` not in PATH
3. **Multiple Python versions** with mixed PATH configurations
4. **Fresh terminal session needed** after PATH modification
5. **Corporate/restricted environments** that lock PATH modifications

## Why Your Packaging Is Actually Correct

Your `pyproject.toml` configuration is **standard and correct**:

```toml
[project.scripts]
telos = "telos_tracker.cli:main"
```

This is the proper way to create console scripts in Python. The issue is **environmental**, not a packaging defect.

### Proof: Alternative Installation Methods Work

```bash
# This always works (uses Python directly, bypasses PATH)
python -m telos_tracker.cli

# This works if PATH is configured (what pip creates)
telos
```

Both run the same code. If the first works but the second doesn't, it's a PATH issue.

## The Package Structure Issue (Secondary)

While investigating, we also discovered a **packaging best practice issue** (not causing the "unrecognized" error, but worth fixing):

### Current Structure:

```toml
[tool.hatch.build.targets.wheel]
packages = ["telos_tracker", "core", "tui", "utils"]
```

This exports `core`, `tui`, and `utils` as **top-level packages**. While functional, it:

1. **Pollutes global namespace** - Other packages might also have `utils` or `core`
2. **Causes potential conflicts** - If another package has `from core import X`, which `core`?
3. **Violates PEP 8 guidance** - Namespace packages should be explicit

### Why It Currently Works:

All your code uses:
```python
from core.database import Database
from tui.screens import DashboardScreen
from utils.config_manager import load_config
```

These imports work because `core/`, `tui/`, and `utils/` are in `sys.path` as top-level packages.

### Better Structure (Future Refactor):

Move everything under `telos_tracker`:

```
telos_tracker/
├── __init__.py
├── cli.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   └── ...
├── tui/
│   ├── __init__.py
│   └── ...
└── utils/
    ├── __init__.py
    └── ...
```

Then change imports to:
```python
from telos_tracker.core.database import Database
from telos_tracker.tui.screens import DashboardScreen
from telos_tracker.utils.config_manager import load_config
```

And `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["telos_tracker"]  # Only one top-level package
```

**However:** This is a **nice-to-have refactor**, not urgent. The current structure works fine and doesn't cause the "unrecognized" error.

## Solutions for Users

### Immediate (No System Changes):

```bash
python -m telos_tracker.cli setup
python -m telos_tracker.cli
```

### Permanent (Fix PATH):

**Windows:**
1. Find Scripts directory: `python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))"`
2. Add to PATH via System Properties → Environment Variables
3. Restart terminal

**Mac/Linux:**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Recommended (Use pipx):

```bash
pip install pipx
pipx ensurepath
pipx install telos-tracker
telos setup
```

pipx handles PATH automatically and isolates CLI tools.

## Comparison with Other Python CLI Tools

This is **not unique to telos**. Many Python CLI tools have the same issue:

| Tool | Package Name | Command | Same Issue? |
|------|--------------|---------|-------------|
| Black | `black` | `black` | ✅ Yes |
| Pytest | `pytest` | `pytest` | ✅ Yes |
| Poetry | `poetry` | `poetry` | ✅ Yes (recommends pipx) |
| AWS CLI | `awscli` | `aws` | ✅ Yes |
| Jupyter | `jupyter` | `jupyter` | ✅ Yes |

**Industry solution:** Recommend `pipx` for CLI tools, or document PATH requirements.

## Action Items

### For Users (Documentation):
- ✅ Added `INSTALLATION_TROUBLESHOOTING.md` - Comprehensive guide
- ✅ Updated `client/README.md` - Added troubleshooting section
- ✅ Updated `cli.py` help text - Mentions `python -m` workaround
- ✅ Updated `PUBLISHING.md` - Notes for future releases

### For Package (Optional Improvements):

1. **Add post-install message** (shown after `pip install`):
   ```python
   # In setup.py or pyproject.toml hooks
   print("✅ Installed telos-tracker!")
   print("   Run: telos setup")
   print("   If 'telos' not found: python -m telos_tracker.cli")
   ```

2. **Detect PATH issue in cli.py:**
   ```python
   # In cli.py main()
   if not shutil.which("telos"):
       print("⚠️  'telos' not in PATH. Recommend: pipx install telos-tracker")
   ```

3. **Create .bat/.sh launcher scripts** (less ideal, but works):
   ```bash
   # telos.bat (Windows)
   @echo off
   python -m telos_tracker.cli %*
   ```

4. **Restructure package** (long-term, for namespace cleanliness):
   - Move `core/`, `tui/`, `utils/` under `telos_tracker/`
   - Update all imports
   - Bump major version (breaking change)

### For Distribution:

Consider also distributing via:
- **PyPI** ✅ (current)
- **pipx** ✅ (recommend in docs)
- **Standalone executables** ✅ (you have PyInstaller builds)
- **Homebrew** (macOS: `brew install telos`)
- **Scoop** (Windows: `scoop install telos`)
- **APT/YUM packages** (Linux distros)

Standalone executables bypass the Python/PATH issue entirely.

## Conclusion

**The "telos is unrecognized" error is:**
- ✅ Expected for Python CLI tools with improper PATH
- ✅ User environment issue, not a package bug
- ✅ Easily solved with documentation
- ✅ Best prevented with pipx recommendation

**Your package is correctly structured.** The issue is PATH configuration on user systems, which affects **all** Python CLI applications.

**Recommended messaging:**
> "Telos is installed! If you see 'command not found', either add Python's Scripts directory to PATH, or run `python -m telos_tracker.cli`. For easiest installation, use `pipx install telos-tracker`."

This is an industry-standard problem with industry-standard solutions. Your package is fine. 🎉

