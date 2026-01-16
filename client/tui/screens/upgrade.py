"""Upgrade screen for trial expiration."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button
from textual.binding import Binding
import webbrowser


class UpgradeScreen(Screen):
    """Upgrade prompt screen."""
    
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
    ]
    
    CSS = """
    UpgradeScreen {
        align: center middle;
    }
    
    #upgrade-container {
        width: 80;
        height: auto;
        border: solid $warning;
        background: $surface;
        padding: 3 4;
    }
    
    #upgrade-title {
        text-align: center;
        color: $warning;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #upgrade-message {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    
    .pricing-tier {
        margin: 1 0;
        padding: 1 2;
        border: solid $accent;
        background: $panel;
    }
    
    .tier-name {
        color: $accent;
        text-style: bold;
    }
    
    .tier-price {
        color: $success;
        text-style: bold;
        margin-top: 1;
    }
    
    .tier-features {
        color: $text-muted;
        margin-top: 1;
    }
    
    #button-container {
        height: auto;
        margin-top: 2;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    
    #trial-info {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
        text-style: italic;
    }
    """
    
    def __init__(self, trial_manager):
        """Initialize upgrade screen.
        
        Args:
            trial_manager: TrialManager instance
        """
        super().__init__()
        self.trial_manager = trial_manager
    
    def compose(self) -> ComposeResult:
        """Compose the upgrade screen."""
        info = self.trial_manager.get_trial_info()
        days_remaining = info['days_remaining']
        
        if info['is_expired']:
            title = "⏰ Trial Expired"
            message = "Your 7-day trial has ended. Upgrade to continue using Telos."
        elif days_remaining == 1:
            title = "⏰ Last Day of Trial"
            message = "Your trial ends tomorrow. Upgrade now to keep tracking."
        elif days_remaining <= 3:
            title = "⏰ Trial Ending Soon"
            message = f"You have {days_remaining} days left in your trial."
        else:
            title = "✨ Upgrade to Pro"
            message = "Unlock unlimited tracking and support development."
        
        with Center():
            with Vertical(id="upgrade-container"):
                yield Static(title, id="upgrade-title")
                yield Static(message, id="upgrade-message")
                
                with Container(classes="pricing-tier"):
                    yield Static("🆓 Free Trial", classes="tier-name")
                    yield Static("7 days, all features", classes="tier-price")
                    yield Static("Perfect for trying Telos", classes="tier-features")
                
                with Container(classes="pricing-tier"):
                    yield Static("⭐ Pro Monthly", classes="tier-name")
                    yield Static("$9/month", classes="tier-price")
                    yield Static("Unlimited tracking • Priority support", classes="tier-features")
                
                with Container(classes="pricing-tier"):
                    yield Static("💎 Pro Yearly", classes="tier-name")
                    yield Static("$79/year (save 26%)", classes="tier-price")
                    yield Static("Best value • All features • Cancel anytime", classes="tier-features")
                
                with Container(id="button-container"):
                    yield Button("Upgrade Now", variant="success", id="upgrade-btn")
                    yield Button("Maybe Later", variant="default", id="later-btn")
                
                yield Static(f"Trial: {days_remaining} days remaining", id="trial-info")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "upgrade-btn":
            self.action_upgrade()
        elif event.button.id == "later-btn":
            self.action_dismiss_screen()
    
    def action_upgrade(self) -> None:
        """Open upgrade URL in browser."""
        # Call backend to create Stripe Checkout session
        config = self.app.config
        backend_url = config.get('backend', 'url')
        
        if not backend_url:
            self.app.notify("Backend not configured. Cannot process upgrade.", severity="error")
            return
        
        try:
            from core.backend_client import BackendClient
            firebase_api_key = config.get('firebase', 'api_key')
            email = config.get('account', 'email', default=None)
            
            if not email:
                self.app.notify("Email not found. Please complete onboarding.", severity="error")
                return
            
            backend = BackendClient(backend_url, firebase_api_key)
            
            # TODO: Add plan selection UI (monthly vs yearly)
            # For now, default to yearly
            plan = 'yearly'
            
            # Create checkout session
            response = backend.create_checkout_session(plan=plan, email=email)
            
            checkout_url = response.get('url')
            if checkout_url:
                webbrowser.open(checkout_url)
                self.app.notify("Opening Stripe Checkout...", severity="information")
            else:
                self.app.notify("Failed to create checkout session", severity="error")
                
        except Exception as e:
            self.app.notify(f"Error: {str(e)}", severity="error")
        
        self.dismiss()
    
    def action_dismiss_screen(self) -> None:
        """Dismiss the screen."""
        # Record that prompt was shown
        prompt_type = self.trial_manager.should_show_upgrade_prompt()
        if prompt_type:
            self.trial_manager.record_upgrade_prompt_shown(prompt_type)
        
        self.dismiss()

