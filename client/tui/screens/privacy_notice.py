"""Privacy guarantee screen for onboarding."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, ScrollableContainer, Center
from textual.widgets import Static, Button, Markdown
from textual.binding import Binding


class PrivacyNoticeScreen(Screen):
    """Privacy guarantee screen."""
    
    BINDINGS = [
        Binding("enter", "accept", "I Understand", show=True),
        Binding("escape", "back", "Back", show=True),
    ]
    
    CSS = """
    PrivacyNoticeScreen {
        align: center middle;
    }
    
    #privacy-container {
        width: 90;
        height: 32;
        border: solid $success;
        background: $surface;
        padding: 1 2;
    }
    
    #privacy-title {
        text-align: center;
        color: $success;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid $success;
        padding-bottom: 1;
    }
    
    #privacy-content {
        height: 1fr;
        margin-bottom: 1;
    }
    
    .guarantee-item {
        margin: 1 0;
        color: $text;
    }
    
    #button-container {
        height: auto;
        padding-top: 1;
        border-top: solid $panel;
    }
    
    Button {
        width: 100%;
        margin: 1 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the privacy notice screen."""
        with Center():
            with Vertical(id="privacy-container"):
                yield Static("🔒 Privacy Guarantee", id="privacy-title")
                
                with ScrollableContainer(id="privacy-content"):
                    yield Static("Telos is built privacy-first. Here's what that means:", classes="guarantee-item")
                    yield Static("", classes="guarantee-item")
                    yield Static("✅ Screenshots are analyzed and immediately discarded", classes="guarantee-item")
                    yield Static("✅ Activity data is encrypted (AES-256) before storage", classes="guarantee-item")
                    yield Static("✅ Your data is stored under an anonymous ID, not linked to your email", classes="guarantee-item")
                    yield Static("✅ No tracking, no telemetry, no analytics", classes="guarantee-item")
                    yield Static("✅ Export or delete your data anytime", classes="guarantee-item")
                    yield Static("", classes="guarantee-item")
                    yield Static("Your data is yours. Always.", classes="guarantee-item")
                    yield Static("", classes="guarantee-item")
                    yield Static("Read our full Privacy Policy at gen-lang-client-0772617718.web.app/privacy", classes="guarantee-item")
                
                with Container(id="button-container"):
                    yield Button("I Understand", variant="success", id="accept-btn")
                    yield Button("Back", variant="default", id="back-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "accept-btn":
            self.action_accept()
        elif event.button.id == "back-btn":
            self.action_back()
    
    def action_accept(self) -> None:
        """Accept and continue."""
        self.dismiss(True)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.dismiss(False)

