"""Dashboard screen - main view."""

from datetime import datetime
from textual.screen import Screen
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from tui.widgets import StatusBanner, CurrentActivity, CategoryBreakdown, RecentTimeline
from tui.widgets.day_heatmap import DayHeatmap
from tui.widgets.activity_waveform import ActivityWaveform


class DashboardScreen(Screen):
    """Main dashboard screen showing live activity tracking."""

    # View mode: "60min" (waveform) or "day" (full day heatmap)
    graph_mode = reactive("60min")

    BINDINGS = [
        Binding("v", "toggle_graph_mode", "", show=False),  # Hidden from footer (V for View)
        Binding("space", "toggle_expanded", "", show=False),  # Hidden from footer
        Binding("left", "previous_day", "", show=False),  # Hidden from footer
        Binding("right", "next_day", "", show=False),  # Hidden from footer
        Binding("t", "jump_to_today", "", show=False),  # Hidden from footer (T for Today)
    ]

    CSS = """
    DashboardScreen {
        layout: vertical;
        overflow-y: hidden;
        background: $surface;
    }

    #status-banner {
        dock: top;
        height: 1;
        background: $surface;
        color: $text-muted;
        content-align: center middle;
    }

    #main-container {
        padding: 1;
    }

    #current-activity {
        height: 3;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
        margin-bottom: 1;
    }

    #current-activity-display {
        content-align: center middle;
        text-style: bold;
        color: $text;
        height: 100%;
    }

    #middle-section {
        height: 14;
        margin-bottom: 1;
    }

    #category-breakdown {
        width: 40%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 1;
        margin-right: 1;
    }

    DayHeatmap {
        width: 60%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
    }
    
    ActivityWaveform {
        width: 60%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
    }
    
    .hidden {
        display: none;
    }

    #breakdown-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        padding-bottom: 1;
        margin-bottom: 1;
        text-align: center;
    }

    #breakdown-content {
        color: $text;
    }

    #recent-timeline {
        height: 1fr;
        border: solid $secondary;
        background: $panel;
        padding: 1;
    }

    #timeline-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        padding-bottom: 1;
        margin-bottom: 1;
    }

    #timeline-content {
        color: $text;
    }

    #ai-chat-hint {
        dock: bottom;
        height: auto;
        background: $boost;
        color: $success;
        padding: 0 1;
        text-align: center;
        border-top: solid $success;
    }
    
    #help-footer {
        dock: bottom;
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for dashboard."""
        yield Header(show_clock=True)
        yield StatusBanner(id="status-banner")
        
        with Container(id="main-container"):
            yield CurrentActivity(id="current-activity")
            
            with Horizontal(id="middle-section"):
                yield CategoryBreakdown(id="category-breakdown")
                yield ActivityWaveform(id="waveform-graph")
                yield DayHeatmap(id="day-heatmap")
                
            yield RecentTimeline(id="recent-timeline")

        yield Static("✨ Press 'A' for AI Chat", id="ai-chat-hint")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._update_graph_visibility()

    def watch_graph_mode(self, old_mode: str, new_mode: str) -> None:
        """Update visibility when graph mode changes."""
        self._update_graph_visibility()

    def _update_graph_visibility(self) -> None:
        """Show/hide graphs based on current mode."""
        try:
            waveform = self.query_one("#waveform-graph", ActivityWaveform)
            day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
            
            if self.graph_mode == "60min":
                waveform.remove_class("hidden")
                day_heatmap.add_class("hidden")
            else:  # "day"
                waveform.add_class("hidden")
                day_heatmap.remove_class("hidden")
        except:
            pass  # Widgets not yet mounted

    def action_toggle_graph_mode(self) -> None:
        """Toggle between 60-minute waveform and full day heatmap."""
        self.graph_mode = "day" if self.graph_mode == "60min" else "60min"

    def action_toggle_expanded(self) -> None:
        """Toggle expanded view (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.toggle_expanded()
            except:
                pass

    def action_previous_day(self) -> None:
        """Go to previous day (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.previous_day()
            except:
                pass

    def action_next_day(self) -> None:
        """Go to next day (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.next_day()
            except:
                pass

    def action_jump_to_today(self) -> None:
        """Jump to today (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.selected_date = datetime.now().date()
            except:
                pass
