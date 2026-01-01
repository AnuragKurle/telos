"""Category breakdown widget with improved formatting."""

from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult
from rich.table import Table
from rich.text import Text
from rich.progress_bar import ProgressBar
from rich.console import RenderableType

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
        
        # We'll handle 'idle' separately or ignore it in the breakdown 
        # (usually breakdown sums active time)
        
        # Calculate total (excluding idle)
        total_sec = work_sec + learning_sec + browsing_sec + entertainment_sec
        if total_sec == 0:
            total_sec = 1  # Avoid division by zero

        # Data structure
        categories = [
            ("Work", work_sec, "#00ddff"),
            ("Learning", learning_sec, "#aa00ff"),
            ("Browsing", browsing_sec, "#00ff88"),
            ("Entertain", entertainment_sec, "#ff8800"), # Shortened for alignment
        ]

        lines = []
        
        # Fixed width for alignment
        # Label: 10 chars
        # Bar: 15 chars
        # Time: 8 chars
        # Pct: 5 chars
        
        for name, seconds, color in categories:
            pct = int((seconds / total_sec) * 100) if total_sec > 1 else 0
            minutes = seconds // 60
            hours = minutes // 60
            mins = minutes % 60
            
            if hours > 0:
                time_str = f"{hours}h {mins}m"
            else:
                time_str = f"{mins}m"
                
            # Create bar
            bar_width = 20
            filled_len = int((pct / 100) * bar_width)
            filled_len = max(0, min(filled_len, bar_width))
            
            bar_filled = "█" * filled_len
            bar_empty = "░" * (bar_width - filled_len)
            
            # Format line using simple string formatting for alignment
            # Note: Rich tags inside f-strings need care.
            
            # Format: "Label      [|||||.....]  1h 20m  (45%)"
            
            line = f"[{color}]{name:<10}[/]  [{color}]{bar_filled}[/][dim]{bar_empty}[/]  {time_str:>7}  ({pct:>2}%)"
            lines.append(line)

        content = "\n".join(lines)
        self.query_one("#breakdown-content").update(content)
