"""Reactive state model for TUI application."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.reactive import reactive


class TUIState:
    """Centralized reactive state that auto-updates UI components when changed."""

    # Capture loop status
    loop_status: reactive[str] = reactive("stopped")  # active, idle, stopped, paused, rate_limited, error
    idle_seconds: reactive[int] = reactive(0)
    error_message: reactive[str] = reactive("")

    # Current activity
    current_category: reactive[str] = reactive("idle")
    current_app: reactive[str] = reactive("None")
    current_task: reactive[str] = reactive("No activity")
    last_analysis_source: reactive[str] = reactive("none")  # backend, local, none
    activity_start_time: reactive[Optional[datetime]] = reactive(None)

    # Today's stats (in seconds)
    total_captures: reactive[int] = reactive(0)
    work_seconds: reactive[int] = reactive(0)
    learning_seconds: reactive[int] = reactive(0)
    browsing_seconds: reactive[int] = reactive(0)
    entertainment_seconds: reactive[int] = reactive(0)
    idle_seconds_total: reactive[int] = reactive(0)

    # API quota
    api_calls_used: reactive[int] = reactive(0)

    # Recent captures (list of dicts)
    recent_captures: reactive[List[Dict[str, Any]]] = reactive([])

    def __init__(self, max_daily_requests: int = 1500):
        """Initialize TUI state.

        Args:
            max_daily_requests: Maximum API calls per day
        """
        # Store max as regular attribute (not reactive since it doesn't change)
        self.api_calls_max = max_daily_requests
