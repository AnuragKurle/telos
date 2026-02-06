"""Unified theme constants for the Telos TUI.

Single source of truth for colors, labels, and visual constants
used across all widgets and screens.
"""

# Canonical category color palette
# Used by: CategoryBreakdown, Timeline, DayHeatmap, ActivityWaveform, RecentTimeline
CATEGORY_COLORS = {
    'work': '#5eb5e0',          # Soft cyan-blue
    'learning': '#b388eb',      # Soft purple
    'browsing': '#7cd992',      # Soft green
    'entertainment': '#f4a460', # Sandy orange
    'idle': '#3d3d4d',          # Muted dark
}

# Category display labels (short, for tight layouts)
CATEGORY_LABELS = {
    'work': 'Work',
    'learning': 'Learning',
    'browsing': 'Browsing',
    'entertainment': 'Entertainment',
    'idle': 'Idle',
}

# Category emojis
CATEGORY_EMOJIS = {
    'work': '💼',
    'learning': '📚',
    'browsing': '🌐',
    'entertainment': '🎮',
    'idle': '💤',
}

# Heatmap intensity characters (low to high)
INTENSITY_CHARS = ['·', '░', '▒', '▓', '█']


def format_duration(total_seconds: int) -> str:
    """Format seconds into a human-readable duration string.

    Examples:
        0    -> "0m"
        45   -> "0m"
        120  -> "2m"
        3720 -> "1h 2m"
        7200 -> "2h 0m"
    """
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"
