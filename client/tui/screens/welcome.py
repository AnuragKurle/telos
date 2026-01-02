"""Welcome screen for first-time users."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button
from textual.binding import Binding


class WelcomeScreen(Screen):
    """Welcome screen shown on first run."""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue", show=True),
        Binding("escape", "quit_app", "Quit", show=True),
    ]
    
    CSS = """
    WelcomeScreen {
        align: center middle;
    }
    
    #welcome-container {
        width: 80;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2 4;
    }
    
    #logo {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #tagline {
        text-align: center;
        color: $text;
        margin-bottom: 2;
        text-style: italic;
    }
    
    .value-prop {
        margin: 1 0;
        color: $text;
    }
    
    #trial-info {
        text-align: center;
        color: $success;
        margin-top: 2;
        margin-bottom: 1;
        text-style: bold;
    }
    
    #button-container {
        margin-top: 2;
        height: auto;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the welcome screen."""
        with Center():
            with Vertical(id="welcome-container"):
                yield Static("✨ TELOS ✨", id="logo")
                yield Static("Your AI Work Journal - Privacy First", id="tagline")
                
                yield Static("🤖 AI understands what you're working on", classes="value-prop")
                yield Static("🔒 Screenshots deleted instantly, data stays local", classes="value-prop")
                yield Static("💬 Chat with your work history naturally", classes="value-prop")
                
                yield Static("🎉 Free 7-Day Trial", id="trial-info")
                
                with Container(id="button-container"):
                    yield Button("Get Started", variant="success", id="continue-btn")
                    yield Button("Quit", variant="default", id="quit-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "continue-btn":
            self.action_continue()
        elif event.button.id == "quit-btn":
            self.action_quit_app()
    
    def action_continue(self) -> None:
        """Continue to next screen."""
        self.dismiss(True)
    
    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()

