# Text-Only Data Enhancements

**Goal:** Extract more value WITHOUT saving screenshots
**Storage:** All options combined = ~10-50 MB/year (minimal!)

---

## 🎯 High-Value Text-Only Additions

### 1. **Window Titles (Full Detail)** ⭐ EASY WIN
**Current:** We get app name from Gemini analysis
**Add:** Capture actual window title directly from OS

**Storage:** ~50-100 bytes per capture → ~1-2 MB/year

**Examples:**
- VSCode: "database.py - Telos - Visual Studio Code"
- Chrome: "Python async tutorial - Stack Overflow"
- Terminal: "~/projects/Telos - bash"

**Value:**
- Exact file names without AI analysis
- Browser page titles (know what docs you read)
- Terminal working directories
- Document titles

**Implementation:**
```python
import win32gui  # Already have pywin32
title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
```

**Effort:** 1 hour

---

### 2. **Clipboard History (Text Only)** 📋
**What:** Everything you copy/paste (text only, ignore images)

**Storage:** ~100-200 KB/day = ~36-73 MB/year

**Value:**
- Recall code snippets you copied
- Find commands you pasted
- Track ideas and notes
- "What was that regex I copied yesterday?"

**Privacy:**
- Exclude passwords (detect clipboard from password managers)
- Option to disable temporarily
- Auto-clear after X days

**Effort:** 2-3 hours

---

### 3. **Active Browser Tabs** 🌐
**What:** Titles of all open tabs (not history, just what's currently open)

**Storage:** ~200-500 bytes per capture → ~4-10 MB/year

**Value:**
- Context of research (multiple docs open)
- Know what resources you were using
- "I had 5 tabs open about Python async"

**Examples:**
```json
{
  "browser_tabs": [
    "Python asyncio — Python 3.12 documentation",
    "Textual - TUI framework",
    "Stack Overflow - How to use asyncio.to_thread",
    "GitHub - textual issues"
  ]
}
```

**Implementation:** Browser extension or parse browser session files

**Effort:** 4-6 hours (requires browser integration)

---

### 4. **Git Context** 🔀
**What:** Current branch, uncommitted files, recent commits

**Storage:** ~100-200 bytes per capture → ~2-4 MB/year

**Value:**
- Link work to git branches
- Know what branch you were on during session
- Track uncommitted work
- "What branch was I on when I fixed that bug?"

**Examples:**
```json
{
  "git": {
    "branch": "feature/ai-chat",
    "uncommitted_files": ["tui/screens/chat.py", "core/query_engine.py"],
    "last_commit": "Add AI chat interface",
    "status": "2 files changed, 500+ insertions"
  }
}
```

**Effort:** 2-3 hours

---

### 5. **Keyboard Shortcuts Used** ⌨️
**What:** Track shortcuts (Ctrl+C, Ctrl+V, Ctrl+S, etc.)

**Storage:** ~50-100 bytes per shortcut → ~500 KB/year

**Value:**
- Identify workflow patterns
- See which features you use most
- Track keyboard-first vs mouse-heavy work
- "Did I save that file? Check shortcut history"

**Examples:**
- "Ctrl+S pressed 247 times today" (lots of saving = active coding)
- "Ctrl+C/V used 89 times" (copying code/snippets)
- "Ctrl+Shift+P" (VS Code command palette usage)

**Effort:** 3-4 hours

---

### 6. **Active IDE/Editor Info** 💻
**What:** Current file, line number, language, function (if accessible)

**Storage:** ~100-200 bytes per capture → ~2-4 MB/year

**Value:**
- Exact file and line being edited
- Programming language context
- Function/class context
- "What file was I editing during that session?"

**Examples:**
```json
{
  "editor": {
    "type": "vscode",
    "file": "tui/screens/chat.py",
    "line": 156,
    "column": 24,
    "language": "python",
    "function": "process_query"
  }
}
```

**Implementation:** VS Code extension or parse workspace state

**Effort:** 4-6 hours (requires IDE integration)

---

### 7. **Terminal Commands (History)** 🖥️
**What:** Last N commands from terminal history

**Storage:** ~100-200 KB/day → ~36-73 MB/year

**Value:**
- Track commands you ran
- Recall complex git/npm/pip commands
- "What was that docker command I ran?"
- Link terminal work to coding sessions

**Examples:**
```json
{
  "terminal_history": [
    "git status",
    "python main.py test",
    "npm install textual",
    "git commit -m 'Add chat feature'"
  ]
}
```

**Privacy:** Exclude commands with secrets/passwords

**Effort:** 2-3 hours

---

### 8. **Network Activity Summary** 🌐
**What:** Domains accessed, API calls made (no content)

**Storage:** ~50-100 bytes per domain → ~1-2 MB/year

**Value:**
- Know which APIs you were hitting
- Track research sources
- "Was I working on the Stripe integration today?"

**Examples:**
```json
{
  "domains_accessed": [
    "api.stripe.com",
    "docs.python.org",
    "stackoverflow.com",
    "github.com"
  ]
}
```

**Effort:** 3-4 hours

---

### 9. **Meeting/Call Metadata** 📞
**What:** Meeting titles, participants, duration (not transcripts)

**Storage:** ~200-500 bytes per meeting → ~500 KB/year

**Value:**
- Link work to meetings
- "Was that before or after the standup?"
- Track meeting time vs coding time

**Examples:**
```json
{
  "meeting": {
    "title": "Sprint Planning",
    "duration_minutes": 45,
    "participants": 5,
    "platform": "Zoom"
  }
}
```

**Effort:** 4-6 hours (requires calendar integration)

---

### 10. **System Resource Usage** 📊
**What:** CPU/RAM usage, battery level, active monitors

**Storage:** ~50 bytes per capture → ~1 MB/year

**Value:**
- Identify resource-heavy tasks
- Correlate performance with productivity
- "Why was my laptop slow that day?"

**Examples:**
```json
{
  "system": {
    "cpu_percent": 45,
    "memory_percent": 68,
    "battery_percent": 42,
    "monitors": 2
  }
}
```

**Effort:** 1 hour

---

## 📊 Combined Storage Impact

| Feature | Storage/Year | Value | Effort |
|---------|--------------|-------|--------|
| Window titles | 2 MB | ⭐⭐⭐ | 1h |
| Clipboard history | 50 MB | ⭐⭐⭐ | 2h |
| Browser tabs | 10 MB | ⭐⭐ | 6h |
| Git context | 4 MB | ⭐⭐⭐ | 3h |
| Keyboard shortcuts | 0.5 MB | ⭐ | 4h |
| Editor info | 4 MB | ⭐⭐⭐ | 6h |
| Terminal history | 50 MB | ⭐⭐⭐ | 3h |
| Network activity | 2 MB | ⭐ | 4h |
| Meeting metadata | 0.5 MB | ⭐⭐ | 6h |
| System resources | 1 MB | ⭐ | 1h |
| **TOTAL** | **~124 MB** | | **30-36h** |

**Still incredibly minimal!** Less than a single photo from your phone.

---

## 🎯 Recommended Priorities (Text-Only)

### Phase 1: Quick Wins (4-6 hours)
1. **Window titles** (1h) - Exact file names, page titles
2. **Clipboard history** (2h) - Code snippets, commands
3. **Git context** (3h) - Branch, uncommitted files

**Total storage:** ~56 MB/year
**Total effort:** 6 hours
**Value:** ⭐⭐⭐ High

---

### Phase 2: Developer Tools (8-9 hours)
4. **Terminal history** (3h) - Commands you ran
5. **Editor info** (6h) - Exact file/line/function

**Total storage:** +54 MB/year
**Total effort:** 9 hours
**Value:** ⭐⭐⭐ Very High (for developers)

---

### Phase 3: Context (10-16 hours)
6. **Browser tabs** (6h) - Research context
7. **Meeting metadata** (6h) - Calendar integration
8. **Network activity** (4h) - API calls, domains

**Total storage:** +13 MB/year
**Total effort:** 16 hours
**Value:** ⭐⭐ Medium

---

## 💡 Best ROI (Return on Investment)

### Top 3 for Developers:
1. **Window titles** - 1 hour, massive value
2. **Git context** - 3 hours, essential for devs
3. **Terminal history** - 3 hours, recall complex commands

**Total:** 7 hours, ~56 MB/year, ⭐⭐⭐ value

### Top 3 for Everyone:
1. **Window titles** - 1 hour, know exact files/pages
2. **Clipboard history** - 2 hours, never lose copied text
3. **Meeting metadata** - 6 hours, link work to meetings

**Total:** 9 hours, ~52 MB/year, ⭐⭐⭐ value

---

## 🚀 Quick Implementation Sketch

### Window Titles (Easiest - Start Here)
```python
# In core/capture.py
import win32gui

def get_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except:
        return ""

# Add to capture
result = analyzer.analyze_screenshot(...)
result['window_title'] = get_window_title()
```

### Git Context
```python
import subprocess
import os

def get_git_context():
    try:
        branch = subprocess.check_output(
            ['git', 'branch', '--show-current'],
            text=True
        ).strip()

        status = subprocess.check_output(
            ['git', 'status', '--short'],
            text=True
        )

        return {
            'branch': branch,
            'uncommitted_files': status.count('\n'),
            'has_changes': len(status) > 0
        }
    except:
        return None
```

### Clipboard History
```python
import pyperclip  # pip install pyperclip

def monitor_clipboard():
    last_text = ""
    while True:
        current = pyperclip.paste()
        if current != last_text and current:
            # Save to database
            db.save_clipboard(current, timestamp)
            last_text = current
        time.sleep(1)
```

---

## 🔒 Privacy Notes

**For clipboard history:**
- Detect password manager clipboard access (1Password, Bitwarden)
- Don't save if clipboard contains "password" or similar
- Add "pause clipboard" hotkey
- Auto-delete after 30 days

**For terminal history:**
- Exclude commands with `--password`, API keys
- Redact environment variables
- Option to disable for sensitive sessions

**For all features:**
- User can disable individually
- Clear history on demand
- Export control

---

## 🎯 Bottom Line

**You can add MASSIVE context with TEXT ONLY:**
- Window titles: Know exact files/pages
- Git context: Link work to branches
- Clipboard: Never lose code snippets
- Terminal: Recall complex commands

**Total storage:** ~120 MB/year (still trivial!)
**Total effort:** 30-36 hours (all features)
**Quick wins:** 7 hours gets you the best 3

**Recommendation:** Start with window titles (1 hour) and git context (3 hours). See if that's enough before adding more.

---

**See:** `CURRENT_STATUS.md` for current priorities
