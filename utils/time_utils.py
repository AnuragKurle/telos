"""Time formatting and manipulation utilities."""

from datetime import datetime, timedelta
from typing import Optional


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration.

    Args:
        seconds: Number of seconds

    Returns:
        Formatted string like "2h 15m" or "45m 30s"
    """
    if seconds < 0:
        return "0s"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and hours == 0:
        parts.append(f"{secs}s")

    return " ".join(parts) if parts else "0s"


def format_timestamp(dt: datetime, include_seconds: bool = False) -> str:
    """Format datetime as readable timestamp.

    Args:
        dt: Datetime object
        include_seconds: Whether to include seconds

    Returns:
        Formatted string like "14:35" or "14:35:23"
    """
    fmt = "%H:%M:%S" if include_seconds else "%H:%M"
    return dt.strftime(fmt)


def format_time_range(start: datetime, end: datetime) -> str:
    """Format time range.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        Formatted string like "14:35 - 14:40"
    """
    return f"{format_timestamp(start)} - {format_timestamp(end)}"


def seconds_until_midnight() -> int:
    """Get number of seconds until midnight."""
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


def get_today_date() -> datetime:
    """Get today's date at midnight."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats.

    Args:
        date_str: Date string (e.g., "2025-01-15", "today", "yesterday")

    Returns:
        Datetime object or None if invalid
    """
    date_str = date_str.lower().strip()

    if date_str == "today":
        return get_today_date()
    elif date_str == "yesterday":
        return get_today_date() - timedelta(days=1)

    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
