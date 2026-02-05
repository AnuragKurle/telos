"""One-time welcome screen for new Pro users."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Center
from textual.widgets import Static, Button
from textual.binding import Binding


class WelcomeProScreen(ModalScreen):
    """Shown once after a user upgrades to Pro for the first time."""
    
    BINDINGS = [
        Binding("escape", "dismiss_welcome", "Continue", show=True),
        Binding("enter", "dismiss_welcome", "Continue", show=False),
    ]
    
    CSS = """
    WelcomeProScreen {
        align: center middle;
        background: $surface 80%;
    }
    
    #welcome-pro-container {
        width: 70;
        height: auto;
        border: solid $accent;
        background: $panel;
        padding: 3 4;
    }
    
    #welcome-pro-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    #welcome-pro-subtitle {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    
    .pro-benefit {
        color: $text;
        margin-bottom: 1;
        padding-left: 2;
    }
    
    #welcome-pro-thanks {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-top: 2;
        margin-bottom: 2;
    }
    
    #continue-btn {
        width: 100%;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="welcome-pro-container"):
                yield Static("Welcome to Telos Pro", id="welcome-pro-title")
                yield Static(
                    "Thank you for supporting independent development.",
                    id="welcome-pro-subtitle"
                )
                
                yield Static("Here's what's unlocked for you:", classes="pro-benefit")
                yield Static("  [bold]Unlimited History[/bold] -- All your data, forever. No 7-day limit.", classes="pro-benefit")
                yield Static("  [bold]Full AI Insights[/bold] -- Complete daily summaries and analysis.", classes="pro-benefit")
                yield Static("  [bold]Data Export[/bold] -- Export your activity data as CSV or JSON.", classes="pro-benefit")
                yield Static("  [bold]Priority Support[/bold] -- Direct access to the developer.", classes="pro-benefit")
                yield Static("  [bold]No Upgrade Prompts[/bold] -- A clean, distraction-free experience.", classes="pro-benefit")
                
                yield Static(
                    "Your tracking is fully active. Everything just works.",
                    id="welcome-pro-thanks"
                )
                
                yield Button("Let's Go", variant="success", id="continue-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "continue-btn":
            self.action_dismiss_welcome()
    
    def action_dismiss_welcome(self) -> None:
        """Dismiss and mark as shown."""
        # Mark that welcome was shown so it doesn't appear again
        try:
            config = self.app.config
            account = config.config.get('account', {})
            account['show_pro_welcome'] = False
            account['pro_welcome_shown'] = True
            config.config['account'] = account
            config.save(config.config)
        except Exception:
            pass
        self.dismiss()
