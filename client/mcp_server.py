"""
Telos MCP Server

Exposes your local Telos screen-tracking data to any MCP-compatible client
(Claude Desktop, Cursor, etc.) so AI assistants can answer questions about
your work activity, productivity, and time usage.

Usage:
    python mcp_server.py                    # stdio transport (default)
    python mcp_server.py --transport http   # HTTP transport

Configuration (Claude Desktop / Cursor):
    {
        "mcpServers": {
            "telos": {
                "command": "python",
                "args": ["<path-to>/client/mcp_server.py"]
            }
        }
    }
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

# Add parent directory so core/ imports work when run standalone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from core.database import Database
from core.query_engine import QueryEngine

# ── Logging (stderr only -- stdout is for MCP JSON-RPC) ─────────────
logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="[telos-mcp] %(message)s")
log = logging.getLogger("telos-mcp")

# ── Database discovery ───────────────────────────────────────────────

def _find_database() -> str:
    """Locate the Telos SQLite database.
    
    Checks, in order:
        1. TELOS_DB_PATH environment variable
        2. ~/.telos/tracker.db  (default location)
    """
    env_path = os.environ.get("TELOS_DB_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    default_path = Path.home() / ".telos" / "tracker.db"
    if default_path.exists():
        return str(default_path)

    raise FileNotFoundError(
        "Telos database not found. "
        "Set TELOS_DB_PATH or ensure ~/.telos/tracker.db exists."
    )


def _get_db() -> Database:
    """Get a Database instance (created fresh per call for thread safety)."""
    return Database(_find_database())


def _get_query_engine() -> QueryEngine:
    """Get a QueryEngine wired to the local database."""
    return QueryEngine(_get_db())


# ── MCP Server ───────────────────────────────────────────────────────

mcp = FastMCP(
    "Telos",
    instructions=(
        "Access your Telos screen-tracking data. "
        "Query your work activity, sessions, daily summaries, "
        "productivity stats, and app usage from your local database."
    ),
)


# ── Tools ────────────────────────────────────────────────────────────

@mcp.tool()
def get_activity_today() -> str:
    """Get a summary of today's screen activity including time breakdown,
    top apps, total captures, and current status.
    
    Use this when the user asks about what they did today, how their day
    is going, or wants a quick status check.
    """
    db = _get_db()
    stats = db.get_today_stats()
    sessions = db.get_sessions_for_date(datetime.now())
    captures = db.get_captures_for_date(datetime.now())

    work_min = stats.get('work', 0) // 60
    learning_min = stats.get('learning', 0) // 60
    browsing_min = stats.get('browsing', 0) // 60
    entertainment_min = stats.get('entertainment', 0) // 60
    total_captures = stats.get('total_captures', 0)

    # Top apps
    app_counts: dict[str, int] = {}
    for cap in captures:
        app = cap.get('app_name', 'Unknown')
        app_counts[app] = app_counts.get(app, 0) + 1
    top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Latest activity
    latest = captures[-1] if captures else None
    latest_str = ""
    if latest:
        ts = latest.get('timestamp', '')
        latest_str = (
            f"\nLatest activity: {latest.get('app_name')} - "
            f"{latest.get('task')} ({ts})"
        )

    return (
        f"Today's Activity ({datetime.now().strftime('%A, %B %d %Y')})\n"
        f"{'=' * 50}\n"
        f"Total captures: {total_captures}\n"
        f"Sessions: {len(sessions)}\n\n"
        f"Time Breakdown:\n"
        f"  Work:          {work_min} min\n"
        f"  Learning:      {learning_min} min\n"
        f"  Browsing:      {browsing_min} min\n"
        f"  Entertainment: {entertainment_min} min\n\n"
        f"Top Apps:\n" +
        "\n".join(f"  {app}: {count} captures" for app, count in top_apps) +
        latest_str
    )


@mcp.tool()
def get_sessions(date: Optional[str] = None, limit: int = 10) -> str:
    """Get work sessions for a specific date.
    
    Each session is a continuous block of activity with an AI-generated
    summary, category, apps used, and focus score.
    
    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
        limit: Maximum number of sessions to return (default 10).
    
    Use this when the user asks about their work sessions, focus blocks,
    or wants to know what they worked on during a specific time.
    """
    db = _get_db()
    target_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
    sessions = db.get_sessions_for_date(target_date)

    if not sessions:
        return f"No sessions found for {target_date.strftime('%Y-%m-%d')}."

    lines = [f"Sessions for {target_date.strftime('%A, %B %d %Y')} ({len(sessions)} total)\n"]

    for s in sessions[:limit]:
        start = datetime.fromisoformat(s['start_time']).strftime('%H:%M')
        end = datetime.fromisoformat(s['end_time']).strftime('%H:%M')
        dur = s['duration_seconds'] // 60
        focus = s.get('focus_score')
        focus_str = f" | Focus: {focus:.0%}" if focus is not None else ""

        lines.append(f"--- {start} - {end} ({dur} min){focus_str} ---")
        lines.append(f"  Category: {s['category']}")
        lines.append(f"  Task: {s['primary_task']}")
        lines.append(f"  Apps: {s.get('apps_used', 'N/A')}")
        if s.get('detailed_summary'):
            lines.append(f"  Summary: {s['detailed_summary']}")
        if s.get('learnings'):
            lines.append(f"  Learnings: {s['learnings']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_daily_summary(date: Optional[str] = None) -> str:
    """Get the AI-generated daily summary for a specific date.
    
    Includes productivity score, time breakdown, key learnings,
    focus blocks, and a narrative of the day.
    
    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
    
    Use this when the user asks for an overview of a particular day,
    their productivity score, or key insights.
    """
    db = _get_db()
    target_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
    summary = db.get_daily_summary(target_date)

    if not summary:
        return f"No daily summary available for {target_date.strftime('%Y-%m-%d')}."

    productivity = summary.get('productivity_score', 0)
    if productivity <= 1.0:
        productivity *= 100

    work_min = summary.get('work_seconds', 0) // 60
    learning_min = summary.get('learning_seconds', 0) // 60
    browsing_min = summary.get('browsing_seconds', 0) // 60
    entertainment_min = summary.get('entertainment_seconds', 0) // 60

    # Parse key learnings
    learnings = []
    try:
        learnings = json.loads(summary.get('key_learnings_json', '[]'))
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse focus blocks
    focus_blocks = []
    try:
        focus_blocks = json.loads(summary.get('focus_blocks_json', '[]'))
    except (json.JSONDecodeError, TypeError):
        pass

    lines = [
        f"Daily Summary - {summary['date']}",
        f"{'=' * 50}",
        f"Productivity Score: {productivity:.0f}/100",
        f"",
        f"Time Breakdown:",
        f"  Work:          {work_min} min",
        f"  Learning:      {learning_min} min",
        f"  Browsing:      {browsing_min} min",
        f"  Entertainment: {entertainment_min} min",
        f"  Context Switches: {summary.get('context_switches', 0)}",
        "",
    ]

    if focus_blocks:
        lines.append("Focus Blocks:")
        for fb in focus_blocks:
            start = datetime.fromisoformat(fb['start']).strftime('%H:%M')
            lines.append(f"  {start} - {fb['duration_minutes']}min: {fb.get('task', 'N/A')}")
        lines.append("")

    if learnings:
        lines.append("Key Learnings:")
        for l in learnings:
            lines.append(f"  - {l}")
        lines.append("")

    narrative = summary.get('daily_narrative', '')
    if narrative:
        lines.append("Narrative:")
        lines.append(narrative)

    return "\n".join(lines)


@mcp.tool()
def query_activity(question: str, days_back: int = 7) -> str:
    """Search through your activity data using a natural language question.
    
    This is the most powerful tool -- it pulls together captures, sessions,
    and daily summaries to provide rich context for any question about your
    work patterns, habits, or specific activities.
    
    Args:
        question: Natural language question about your activity.
            Examples:
            - "How much time did I spend coding this week?"
            - "What were my most productive hours?"
            - "Which apps did I use the most?"
            - "What did I work on yesterday afternoon?"
        days_back: How many days of history to search (default 7, max 30).
    
    Use this for any open-ended question about the user's activity.
    """
    days_back = min(days_back, 30)
    qe = _get_query_engine()
    context = qe.get_context_for_query(question, days_back=days_back)
    formatted = qe.format_context_for_llm(context)
    return formatted


@mcp.tool()
def get_recent_captures(hours: int = 1, limit: int = 20) -> str:
    """Get the most recent individual screen captures.
    
    Each capture is a single screenshot analysis with the detected app,
    task, category, and detailed context (files, URLs, cursor position).
    
    Args:
        hours: How many hours back to look (default 1).
        limit: Maximum captures to return (default 20).
    
    Use this when the user asks what they were just doing, wants to see
    granular activity, or needs details about recent work.
    """
    db = _get_db()
    captures = db.get_recent_captures(hours=hours, limit=limit)

    if not captures:
        return f"No captures found in the last {hours} hour(s)."

    lines = [f"Recent Captures (last {hours}h, showing {len(captures)})\n"]

    for cap in captures:
        ts = cap.get('timestamp', '')
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
            except Exception:
                pass

        emoji = cap.get('category_emoji', '')
        app = cap.get('app_name', 'Unknown')
        task = cap.get('task', 'N/A')
        category = cap.get('category', 'unknown')
        conf = cap.get('confidence', 0)

        lines.append(f"{ts} {emoji} [{category}] {app}")
        lines.append(f"  Task: {task} (confidence: {conf:.0%})")

        # Rich context
        dc = cap.get('detailed_context')
        if dc and isinstance(dc, str):
            try:
                dc = json.loads(dc)
            except Exception:
                dc = None
        if dc and isinstance(dc, dict):
            if dc.get('file_name'):
                lines.append(f"  File: {dc['file_name']}")
            if dc.get('browser_url'):
                lines.append(f"  URL: {dc['browser_url']}")
            if dc.get('full_description'):
                lines.append(f"  Detail: {dc['full_description'][:150]}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_productivity_trends(days: int = 7) -> str:
    """Get productivity trends over multiple days.
    
    Shows daily productivity scores, time breakdowns, and patterns.
    
    Args:
        days: Number of days to analyze (default 7, max 30).
    
    Use this when the user asks about trends, patterns over time,
    or wants to compare productivity across days.
    """
    days = min(days, 30)
    db = _get_db()

    lines = [f"Productivity Trends (last {days} days)\n"]
    lines.append(f"{'Date':<12} {'Score':>6} {'Work':>6} {'Learn':>6} {'Browse':>6} {'Entertain':>9}")
    lines.append("-" * 58)

    found_any = False
    for i in range(days):
        target = datetime.now() - timedelta(days=i)
        summary = db.get_daily_summary(target)
        if summary:
            found_any = True
            prod = summary.get('productivity_score', 0)
            if prod <= 1.0:
                prod *= 100
            date_str = summary['date']
            w = summary.get('work_seconds', 0) // 60
            l = summary.get('learning_seconds', 0) // 60
            b = summary.get('browsing_seconds', 0) // 60
            e = summary.get('entertainment_seconds', 0) // 60
            lines.append(f"{date_str:<12} {prod:>5.0f}% {w:>5}m {l:>5}m {b:>5}m {e:>8}m")

    if not found_any:
        lines.append("No daily summaries found. Generate summaries in the Telos app first.")

    return "\n".join(lines)


@mcp.tool()
def get_top_apps(days: int = 7) -> str:
    """Get the most-used applications over a time period.
    
    Args:
        days: Number of days to analyze (default 7, max 30).
    
    Use this when the user asks which apps they use most,
    or wants to understand their tool usage patterns.
    """
    days = min(days, 30)
    db = _get_db()

    app_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for i in range(days):
        target = datetime.now() - timedelta(days=i)
        captures = db.get_captures_for_date(target)
        for cap in captures:
            app = cap.get('app_name', 'Unknown')
            app_counts[app] = app_counts.get(app, 0) + 1
            cat = cap.get('simple_category') or cap.get('category', 'unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1

    if not app_counts:
        return f"No activity data found for the last {days} days."

    top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

    total = sum(app_counts.values())

    lines = [f"App Usage (last {days} days, {total} total captures)\n"]
    lines.append("Top Applications:")
    for app, count in top_apps:
        pct = (count / total) * 100
        bar = "█" * int(pct / 3) + "░" * (33 - int(pct / 3))
        lines.append(f"  {app:<25} {count:>5} ({pct:>4.1f}%) {bar}")

    lines.append("\nCategory Breakdown:")
    for cat, count in top_cats:
        pct = (count / total) * 100
        lines.append(f"  {cat:<20} {count:>5} ({pct:>4.1f}%)")

    return "\n".join(lines)


# ── Resources ────────────────────────────────────────────────────────

@mcp.resource("telos://status")
def get_status() -> str:
    """Current Telos tracking status and database info."""
    try:
        db_path = _find_database()
        db = Database(db_path)
        stats = db.get_today_stats()
        total = stats.get('total_captures', 0)
        return json.dumps({
            "status": "running",
            "database": db_path,
            "today_captures": total,
            "timestamp": datetime.now().isoformat(),
        }, indent=2)
    except FileNotFoundError:
        return json.dumps({
            "status": "database_not_found",
            "message": "Telos database not found. Is the app running?",
        }, indent=2)


# ── Entry point ──────────────────────────────────────────────────────

def main():
    """Run the Telos MCP server."""
    transport = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    log.info(f"Starting Telos MCP server (transport={transport})")

    try:
        db_path = _find_database()
        log.info(f"Database: {db_path}")
    except FileNotFoundError as e:
        log.warning(str(e))

    if transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
