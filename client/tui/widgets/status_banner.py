"""Status banner widget showing capture loop status."""

from textual.widgets import Static
from textual.reactive import reactive


class StatusBanner(Static):
    """Top status bar showing loop status and idle time.
    
    Compact single-line display.
    """

    def on_mount(self) -> None:
        """Start timer to update status every second."""
        from core.trial_manager import TrialManager
        self.trial_manager = TrialManager(self.app.config)
        self.set_interval(1.0, self.refresh_status)
        self.refresh_status()

    def refresh_status(self) -> None:
        """Update status display."""
        app = self.app
        
        # Trial Message
        trial_msg = ""
        trial_info = self.trial_manager.get_trial_info()
        if trial_info['status'] == 'trial':
            days = trial_info['days_remaining']
            color = self.trial_manager.get_banner_color()
            trial_msg = f"   •   [bold {color}]Trial: {days}d left[/]"
        elif trial_info['status'] == 'pro':
            trial_msg = "   •   [bold blue]PRO ACCOUNT[/]"
        elif trial_info['status'] == 'expired':
            trial_msg = "   •   [bold red]TRIAL EXPIRED[/]"

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

        # Format idle time compactly (only show if actually idle)
        idle_msg = ""
        if app.loop_status == "idle":
            idle = app.idle_seconds
            if idle < 60:
                idle_str = f"{idle}s"
            else:
                idle_str = f"{idle//60}m {idle%60}s"
            idle_msg = f"   •   Idle: {idle_str}"

        # Build status line with clearer separation
        # Uses wide spacing
        source_indicator = ""
        if app.last_analysis_source == "backend":
            source_indicator = "   •   ☁️ Cloud"
        elif app.last_analysis_source == "local":
            source_indicator = "   •   💻 Local"

        status_line = f" {emoji} {status_text}{idle_msg}{source_indicator}{trial_msg} "

        self.update(status_line)
