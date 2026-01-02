"""Recent timeline widget showing last 5 captures."""

from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult

from utils.time_utils import format_timestamp


class RecentTimeline(Container):
    """Widget showing recent 5 captures.

    Displays:
    14:35  [Work] VSCode - Writing tests
    14:30  [Work] Chrome - Reading docs
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("RECENT TIMELINE", id="timeline-title")
        yield Static("", id="timeline-content")

    def on_mount(self) -> None:
        """Start timer to update every second."""
        self.set_interval(1.0, self.update_timeline)
        self.update_timeline()

    def _normalize_emoji(self, emoji_str: str) -> str:
        """Helper to handle hex codes or missing emojis in display."""
        if not emoji_str or emoji_str == "None" or emoji_str == "null":
            return "📝"
        
        # Strip potential string artifacts from DB/AI
        emoji_str = emoji_str.strip().replace('"', '').replace("'", "")
        
        if not emoji_str:
            return "📝"

        # If it's a hex code like u1f4f1
        if len(emoji_str) >= 4 and all(c in "0123456789abcdefABCDEF" for c in emoji_str.lower().replace('u+', '').replace('u', '')):
            try:
                clean_hex = emoji_str.lower().replace('u+', '').replace('u', '').strip()
                return chr(int(clean_hex, 16))
            except:
                pass
                
        return emoji_str[0]

    def update_timeline(self) -> None:
        """Update the timeline display."""
        app = self.app
        recent = app.recent_captures

        if not recent:
            self.query_one("#timeline-content").update("No recent activity")
            return

        # Build timeline lines
        lines = []
        for capture in recent:
            # Extract time from timestamp string
            timestamp = capture['timestamp']
            if isinstance(timestamp, str):
                time_part = timestamp.split(' ')[1] if ' ' in timestamp else timestamp
                timestamp_str = time_part[:5]  # HH:MM
            else:
                timestamp_str = format_timestamp(timestamp)

            category = capture['category']
            app_name = capture['app_name']
            task = capture['task']

            # Use emoji from data if available, with robust normalization
            raw_emoji = capture.get('category_emoji')
            emoji = self._normalize_emoji(str(raw_emoji))
            
            # Use color if available, ensure it's not "None"
            raw_color = capture.get('category_color')
            color = str(raw_color) if (raw_color and raw_color != "None") else "#ffffff"
            
            # Truncate app name and task for cleaner display
            # Max width depends on terminal but let's be safe
            if len(app_name) > 20:
                app_name = app_name[:19] + "…"
            
            if len(task) > 40:
                task = task[:39] + "…"
            
            # Escape Rich tags
            safe_task = task.replace("[", r"\[")
            safe_app = app_name.replace("[", r"\[")

            # Format: "14:30  📝 VSCode - Writing..."
            # Using fixed width for alignment
            line = f"[dim]{timestamp_str}[/]  [{color}]{emoji}[/] [bold]{safe_app:<20}[/] {safe_task}"
            lines.append(line)

        content = "\n".join(lines)
        self.query_one("#timeline-content").update(content)
