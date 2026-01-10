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

        # Calculate duration if activity started
        duration_str = "0s"
        if app.activity_start_time:
            elapsed = datetime.now() - app.activity_start_time
            duration_str = format_duration(int(elapsed.total_seconds()))

        # Get basic app info with fallbacks
        app_name = getattr(app, 'current_app', None)
        
        # If no app data at all, show waiting message
        if not app_name or app_name == 'Unknown':
            display_text = "⏳ Waiting for activity data..."
        else:
            # Check if we have enriched data or just raw capture
            has_enriched = hasattr(app, 'current_task') and app.current_task and app.current_task != 'No activity'
            
            if has_enriched:
                # Use enriched LLM data with emoji
                raw_emoji = getattr(app, 'current_emoji', '📝')
                emoji = self._normalize_emoji(str(raw_emoji))
                category_display = app.current_category.title()
                color = getattr(app, 'current_color', '#ffffff')
                display_text = f"[{color}]{emoji} [{category_display}][/][bold] {app.current_app} - {app.current_task}[/]  ⏱️  {duration_str}"
            else:
                # Show raw window/file data immediately (before LLM enrichment)
                window_title = getattr(app, 'current_window_title', 'No window')
                display_text = f"📄 [bold]{app_name}[/] - {window_title}  ⏱️  {duration_str}"

        # Update widget
        self.query_one("#current-activity-display").update(display_text)
