"""Sample data preview screen — shows a pre-filled mock dashboard so users 
know what to expect before they start tracking."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal, Center
from textual.widgets import Static, Button
from textual.binding import Binding


class SamplePreviewScreen(Screen):
    """Shows a mock dashboard with sample data so users see
    what Telos looks like after a real day of tracking."""

    BINDINGS = [
        Binding("enter", "continue", "Continue", show=True),
        Binding("escape", "continue", "Continue", show=False),
    ]

    def __init__(self, user_name: str = "Alex"):
        super().__init__()
        self.user_name = user_name

    CSS = """
    SamplePreviewScreen {
        align: center middle;
        background: $surface;
    }

    #preview-outer {
        width: 96;
        height: auto;
        max-height: 42;
        padding: 1 2;
    }

    #preview-header {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    #preview-subheader {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    /* --- mock dashboard --- */
    #mock-dashboard {
        border: solid $accent;
        background: $panel;
        padding: 1 2;
        margin-bottom: 1;
    }

    #mock-greeting {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        padding: 0 1;
        background: $surface-lighten-1;
        border-bottom: wide $accent;
    }

    #mock-current {
        height: 3;
        border: solid $secondary;
        background: $surface;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    #mock-current-title {
        color: $accent;
        text-style: bold;
        text-align: center;
    }

    #mock-current-text {
        color: $text;
        text-align: center;
    }

    #mock-middle {
        height: 14;
        margin-bottom: 1;
    }

    #mock-categories {
        width: 40%;
        border: solid $secondary;
        background: $surface;
        padding: 1;
        margin-right: 1;
    }

    #mock-cat-title {
        color: $accent;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
        border-bottom: solid $secondary;
        padding-bottom: 1;
    }

    .mock-cat-row {
        color: $text;
        margin: 0;
    }

    .mock-bar {
        color: $success;
    }

    #mock-heatmap {
        width: 60%;
        border: solid $secondary;
        background: $surface;
        padding: 1;
    }

    #mock-heat-title {
        color: $accent;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
        border-bottom: solid $secondary;
        padding-bottom: 1;
    }

    .mock-heat-row {
        color: $text;
        margin: 0;
    }

    #mock-timeline {
        height: auto;
        border: solid $secondary;
        background: $surface;
        padding: 1;
    }

    #mock-tl-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid $secondary;
        padding-bottom: 1;
    }

    .mock-tl-row {
        color: $text;
        margin: 0;
    }

    /* --- ai insight --- */
    #mock-ai-insight {
        border: solid $success;
        background: $surface;
        padding: 1 2;
        margin-bottom: 1;
    }

    #mock-ai-title {
        color: $success;
        text-style: bold;
        margin-bottom: 1;
    }

    #mock-ai-text {
        color: $text;
        text-style: italic;
    }

    #preview-footer {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
        text-style: italic;
    }

    #preview-btn-container {
        height: auto;
    }

    #preview-btn-container Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="preview-outer"):
                yield Static("Here's what a day with Telos looks like", id="preview-header")
                yield Static("(sample data — your real dashboard populates in minutes)", id="preview-subheader")

                # ---- Mock Dashboard ----
                with Container(id="mock-dashboard"):
                    yield Static(f"Good morning ☀️, {self.user_name}", id="mock-greeting")

                    # Current Activity
                    with Container(id="mock-current"):
                        yield Static("Now Tracking", id="mock-current-title")
                        yield Static("💻  VS Code — Editing main.py  (coding)", id="mock-current-text")

                    with Horizontal(id="mock-middle"):
                        # Category breakdown
                        with Container(id="mock-categories"):
                            yield Static("Today's Breakdown", id="mock-cat-title")
                            yield Static("💻 Coding        3h 12m  ████████████░░ 52%", classes="mock-cat-row")
                            yield Static("💬 Communication    47m  ████░░░░░░░░░░ 13%", classes="mock-cat-row")
                            yield Static("🌐 Browsing       1h 5m  █████░░░░░░░░░ 18%", classes="mock-cat-row")
                            yield Static("📝 Writing          38m  ███░░░░░░░░░░░ 10%", classes="mock-cat-row")
                            yield Static("☕ Break            25m  ██░░░░░░░░░░░░  7%", classes="mock-cat-row")

                        # Heatmap
                        with Container(id="mock-heatmap"):
                            yield Static("Activity Heatmap — Today", id="mock-heat-title")
                            yield Static("        8   9  10  11  12   1   2   3   4", classes="mock-heat-row")
                            yield Static("       ┌──┬──┬──┬──┬──┬──┬──┬──┬──┐", classes="mock-heat-row")
                            yield Static("       │░░│▓▓│██│██│░░│▒▒│▓▓│██│▒▒│", classes="mock-heat-row")
                            yield Static("       └──┴──┴──┴──┴──┴──┴──┴──┴──┘", classes="mock-heat-row")
                            yield Static("       low ░░  med ▒▒  high ▓▓  peak ██", classes="mock-heat-row")
                            yield Static("", classes="mock-heat-row")
                            yield Static("  Peak focus: 10am – 12pm (deep coding)", classes="mock-heat-row")

                    # Recent timeline
                    with Container(id="mock-timeline"):
                        yield Static("Recent Activity", id="mock-tl-title")
                        yield Static("  3:42 PM  💻  VS Code — Editing main.py", classes="mock-tl-row")
                        yield Static("  3:30 PM  🌐  Chrome — Stack Overflow", classes="mock-tl-row")
                        yield Static("  3:12 PM  💬  Slack — #engineering channel", classes="mock-tl-row")
                        yield Static("  2:55 PM  💻  VS Code — Writing tests", classes="mock-tl-row")

                # ---- AI Insight blurb ----
                with Container(id="mock-ai-insight"):
                    yield Static("💡 AI Insight", id="mock-ai-title")
                    yield Static(
                        '"You had a strong deep-work block from 10am to noon today — 2 hours of '
                        'uninterrupted coding on the API refactor. Your afternoons tend to fragment '
                        'across Slack and browsing. Consider blocking 2–3pm for focused work too."',
                        id="mock-ai-text",
                    )

                yield Static("This is your data, presented your way.", id="preview-footer")

                with Container(id="preview-btn-container"):
                    yield Button("Looks great, continue →", variant="success", id="continue-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-btn":
            self.action_continue()

    def action_continue(self) -> None:
        self.dismiss(True)
