"""Category breakdown widget with improved formatting."""

from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult
from rich.table import Table
from rich.text import Text
from rich.progress_bar import ProgressBar
from rich.console import RenderableType

from tui.theme import CATEGORY_COLORS, CATEGORY_EMOJIS, format_duration


class CategoryBreakdown(Container):
    """Widget showing today's time breakdown by category.
    
    Displays cleanly aligned progress bars and percentages.
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("TODAY'S BREAKDOWN", id="breakdown-title")
        yield Static("", id="breakdown-content")

    def on_mount(self) -> None:
        """Start timer to update every second."""
        self.set_interval(1.0, self.update_breakdown)
        # Initial update
        self.update_breakdown()

    def update_breakdown(self) -> None:
        """Update the breakdown display with a clean table-like layout."""
        app = self.app

        # Get all seconds
        work_sec = app.work_seconds
        learning_sec = app.learning_seconds
        browsing_sec = app.browsing_seconds
        entertainment_sec = app.entertainment_seconds
        
        # Calculate total (excluding idle)
        total_sec = work_sec + learning_sec + browsing_sec + entertainment_sec
        if total_sec == 0:
            total_sec = 1  # Avoid division by zero

        # Data structure using unified theme colors
        categories = [
            ("work", "Work", work_sec),
            ("learning", "Learning", learning_sec),
            ("browsing", "Browsing", browsing_sec),
            ("entertainment", "Entertainment", entertainment_sec),
        ]

        lines = []

        # Total active time header
        active_total = work_sec + learning_sec + browsing_sec + entertainment_sec
        total_str = format_duration(active_total)
        lines.append(f"[bold]Active: {total_str}[/bold]")
        lines.append("")

        for key, name, seconds in categories:
            color = CATEGORY_COLORS.get(key, '#ffffff')
            emoji = CATEGORY_EMOJIS.get(key, '📝')
            pct = int((seconds / total_sec) * 100) if total_sec > 1 else 0
            time_str = format_duration(seconds)
                
            # Create bar
            bar_width = 16
            filled_len = int((pct / 100) * bar_width)
            filled_len = max(0, min(filled_len, bar_width))
            
            bar_filled = "█" * filled_len
            bar_empty = "░" * (bar_width - filled_len)

            # Format: "💼 Work       [████░░░░]  1h 20m  (45%)"
            line = f"{emoji} [{color}]{name:<13}[/] [{color}]{bar_filled}[/][dim]{bar_empty}[/] {time_str:>7} ({pct:>2}%)"
            lines.append(line)

        content = "\n".join(lines)
        self.query_one("#breakdown-content").update(content)
