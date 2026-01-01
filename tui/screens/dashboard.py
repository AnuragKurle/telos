"""Dashboard screen - main view."""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static

from tui.widgets import StatusBanner, CurrentActivity, CategoryBreakdown, RecentTimeline
from tui.widgets.activity_waveform import ActivityWaveform


class DashboardScreen(Screen):
    """Main dashboard screen showing live activity tracking."""

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

    ActivityWaveform {
        width: 60%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
    }
    
    ActivityWaveform > .graph-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        dock: top;
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
                yield ActivityWaveform()
                
            yield RecentTimeline(id="recent-timeline")

        yield Static("✨ Press 'A' for AI Chat", id="ai-chat-hint")
        yield Footer()
