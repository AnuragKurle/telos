"""Current activity widget with live timer."""

from datetime import datetime
from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult

from utils.time_utils import format_duration


class CurrentActivity(Container):
    """Widget showing current activity with live timer.

    Displays: [Work] VSCode - Writing Python code ⏱️  5m 23s
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("", id="current-activity-display")

    def on_mount(self) -> None:
        """Start timer to update every second."""
        self.set_interval(1.0, self.update_display)

    def _normalize_emoji(self, emoji_str: str) -> str:
        """Helper to handle hex codes or missing emojis."""
        if not emoji_str or emoji_str == "None":
            return "📝"
        
        # If it's a hex code like u1f4f1
        if len(emoji_str) >= 4 and all(c in "0123456789abcdefABCDEF" for c in emoji_str.lower().replace('u+', '').replace('u', '')):
            try:
                clean_hex = emoji_str.lower().replace('u+', '').replace('u', '').strip()
                return chr(int(clean_hex, 16))
            except:
                pass
                
        return emoji_str[0] if emoji_str else "📝"

    def update_display(self) -> None:
        """Update the current activity display."""
        app = self.app

        # Use emoji from data if available, with normalization
        raw_emoji = getattr(app, 'current_emoji', '📝')
        emoji = self._normalize_emoji(str(raw_emoji))

        # Calculate duration if activity started
        duration_str = "0s"
        if app.activity_start_time:
            elapsed = datetime.now() - app.activity_start_time
            duration_str = format_duration(int(elapsed.total_seconds()))

        # Build display text
        category_display = app.current_category.title()
        color = getattr(app, 'current_color', '#ffffff')
        display_text = f"[{color}]{emoji} [{category_display}][/][bold] {app.current_app} - {app.current_task}[/]  ⏱️  {duration_str}"

        # Update widget
        self.query_one("#current-activity-display").update(display_text)
