"""Status banner widget showing capture loop status."""

from textual.widgets import Static
from textual.reactive import reactive


class StatusBanner(Static):
    """Top status bar showing loop status, idle time, and API quota.
    
    Compact single-line display.
    """

    def on_mount(self) -> None:
        """Start timer to update status every second."""
        self.set_interval(1.0, self.refresh_status)
        self.refresh_status()

    def refresh_status(self) -> None:
        """Update status display."""
        app = self.app

        # Status emoji and text
        status_map = {
            "active": ("🟢", "ACTIVE"),
            "idle": ("🟡", "IDLE"),
            "stopped": ("🔴", "STOPPED"),
            "paused": ("🟠", "PAUSED"),
            "rate_limited": ("🔴", "LIMITED"),
            "error": ("🔴", "ERROR"),
        }

        emoji, status_text = status_map.get(app.loop_status, ("⚪", "UNKNOWN"))

        # API usage percentage
        if app.api_calls_max > 0:
            api_percent = int((app.api_calls_used / app.api_calls_max) * 100)
        else:
            api_percent = 0
            
        # Format idle time compactly
        idle = app.idle_seconds
        if idle < 60:
            idle_str = f"{idle}s"
        else:
            idle_str = f"{idle//60}m {idle%60}s"

        # Build status line with clearer separation
        # Uses wide spacing
        source_indicator = ""
        if app.last_analysis_source == "backend":
            source_indicator = "   •   ☁️ Cloud"
        elif app.last_analysis_source == "local":
            source_indicator = "   •   💻 Local"

        status_line = f" {emoji} {status_text}   •   Idle: {idle_str}   •   API: {app.api_calls_used}/{app.api_calls_max} ({api_percent}%){source_indicator} "

        self.update(status_line)
