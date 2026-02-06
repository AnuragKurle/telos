"""Getting-started overlay shown on the dashboard after onboarding completes.
Dismisses itself once the user presses any key or clicks the button."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button
from textual.binding import Binding


class GettingStartedScreen(Screen):
    """Transient overlay that appears on the dashboard's first launch
    after onboarding, explaining what happens next."""

    BINDINGS = [
        Binding("enter", "dismiss_screen", "Close", show=True),
        Binding("escape", "dismiss_screen", "Close", show=False),
        Binding("a", "open_chat", "AI Chat", show=False),
    ]

    CSS = """
    GettingStartedScreen {
        align: center middle;
        background: $surface 85%;
    }

    #gs-container {
        width: 68;
        height: auto;
        border: solid $success;
        background: $surface;
        padding: 2 4;
    }

    #gs-title {
        text-align: center;
        color: $success;
        text-style: bold;
        margin-bottom: 2;
    }

    .gs-section {
        margin: 1 0;
    }

    .gs-section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    .gs-line {
        color: $text;
        margin: 0;
    }

    .gs-muted {
        color: $text-muted;
        margin: 0;
    }

    #gs-status {
        text-align: center;
        color: $success;
        text-style: bold;
        margin: 1 0;
    }

    #gs-btn-container {
        height: auto;
        margin-top: 2;
    }

    #gs-btn-container Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="gs-container"):
                yield Static("You're all set!", id="gs-title")

                yield Static("✓ Tracking active", id="gs-status")

                with Container(classes="gs-section"):
                    yield Static("What's happening now:", classes="gs-section-title")
                    yield Static("  Telos is watching your screen in the background.", classes="gs-line")
                    yield Static("  Your first insights will appear in a few minutes.", classes="gs-line")
                    yield Static("  Just keep working normally — we handle the rest.", classes="gs-line")

                with Container(classes="gs-section"):
                    yield Static("Explore while you wait:", classes="gs-section-title")
                    yield Static("  A — AI Chat: ask about your work patterns", classes="gs-line")
                    yield Static("  T — Timeline: see activity feed in real-time", classes="gs-line")
                    yield Static("  S — Summary: daily insights and stats", classes="gs-line")
                    yield Static("  H — Help: all keyboard shortcuts", classes="gs-line")

                with Container(classes="gs-section"):
                    yield Static("🔌 Works with your AI tools:", classes="gs-section-title")
                    yield Static("  Telos has an MCP server — connect it to Claude,", classes="gs-line")
                    yield Static("  Cursor, or any MCP-compatible assistant.", classes="gs-line")
                    yield Static("  See Settings → AI Integrations for setup.", classes="gs-muted")

                with Container(id="gs-btn-container"):
                    yield Button("Got it", variant="success", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.action_dismiss_screen()

    def action_dismiss_screen(self) -> None:
        self.dismiss(True)

    def action_open_chat(self) -> None:
        self.dismiss("chat")
