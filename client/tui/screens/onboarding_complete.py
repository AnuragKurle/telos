"""Onboarding completion screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static
from textual.reactive import reactive
import asyncio


class OnboardingCompleteScreen(Screen):
    """Celebration screen shown when onboarding is complete."""
    
    countdown: reactive[int] = reactive(3)
    
    CSS = """
    OnboardingCompleteScreen {
        align: center middle;
    }
    
    #complete-container {
        width: 70;
        height: auto;
        border: solid $success;
        background: $surface;
        padding: 3 4;
    }
    
    #celebration {
        text-align: center;
        color: $success;
        text-style: bold;
        margin-bottom: 2;
    }
    
    #message {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    
    .tutorial-hint {
        margin: 1 0;
        color: $text-muted;
        text-align: center;
    }
    
    #countdown {
        text-align: center;
        color: $accent;
        margin-top: 2;
        text-style: italic;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the completion screen."""
        with Center():
            with Vertical(id="complete-container"):
                yield Static("🎉 You're All Set! 🎉", id="celebration")
                yield Static("Telos is now tracking your screen activity.", id="message")
                yield Static("", classes="tutorial-hint")
                yield Static("Quick Tips:", classes="tutorial-hint")
                yield Static("• Press A to chat with your data", classes="tutorial-hint")
                yield Static("• Press T to see timeline", classes="tutorial-hint")
                yield Static("• Press S for daily summary", classes="tutorial-hint")
                yield Static("• Press G to adjust goals", classes="tutorial-hint")
                yield Static("• Press H for help", classes="tutorial-hint")
                yield Static("", classes="tutorial-hint")
                yield Static("Starting in 3 seconds...", id="countdown")
    
    def on_mount(self) -> None:
        """Start countdown when mounted."""
        self.set_timer(1, self.update_countdown)
    
    def update_countdown(self) -> None:
        """Update countdown and dismiss when done."""
        self.countdown -= 1
        
        countdown_widget = self.query_one("#countdown", Static)
        
        if self.countdown > 0:
            countdown_widget.update(f"Starting in {self.countdown} seconds...")
            self.set_timer(1, self.update_countdown)
        else:
            countdown_widget.update("Let's go!")
            # Don't call dismiss from timer callback - use action instead
            self.set_timer(0.5, self.action_finish)
    
    def action_finish(self) -> None:
        """Finish onboarding and dismiss screen."""
        self.dismiss(True)

