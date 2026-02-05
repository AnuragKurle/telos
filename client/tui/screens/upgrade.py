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
                    yield Static("No credit card required", classes="tier-features")
                
                with Container(classes="pricing-tier"):
                    yield Static("⭐ Telos Pro", classes="tier-name")
                    yield Static("$3/month", classes="tier-price")
                    yield Static("Unlimited tracking • Priority support • Cancel anytime", classes="tier-features")
                
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
        """Open upgrade URL in browser and schedule status polling."""
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
            
            plan = 'monthly'
            
            # Create checkout session
            response = backend.create_checkout_session(plan=plan, email=email)
            
            checkout_url = response.get('url')
            if checkout_url:
                webbrowser.open(checkout_url)
                self.app.notify("Opening checkout... We'll detect your upgrade automatically.", severity="information")
                # Schedule polling to detect upgrade
                self._schedule_status_refresh()
            else:
                self.app.notify("Failed to create checkout session", severity="error")
                
        except Exception as e:
            self.app.notify(f"Error: {str(e)}", severity="error")
        
        self.dismiss()
    
    def _schedule_status_refresh(self) -> None:
        """Schedule delayed status refresh attempts after checkout."""
        import asyncio
        
        async def poll_for_upgrade():
            """Poll backend for upgrade status with backoff."""
            from core.trial_manager import TrialManager
            
            delays = [15, 30, 60, 120]
            for delay in delays:
                await asyncio.sleep(delay)
                try:
                    config = self.app.config
                    backend_url = config.get('backend', 'url', default='')
                    firebase_api_key = config.get('firebase', 'api_key', default='')
                    
                    if not backend_url or not firebase_api_key:
                        return
                    
                    trial_manager = TrialManager(config)
                    result = await asyncio.to_thread(
                        trial_manager.refresh_account_status,
                        backend_url,
                        firebase_api_key
                    )
                    
                    if result and trial_manager.is_pro():
                        self.app.notify(
                            "Welcome to Telos Pro! All features are now unlocked.",
                            severity="information",
                            timeout=10
                        )
                        # Refresh UI elements
                        self._apply_pro_ui_refresh()
                        # Mark pro welcome for next screen
                        config.config.setdefault('account', {})['show_pro_welcome'] = True
                        config.save(config.config)
                        return
                except Exception as e:
                    print(f"[UPGRADE] Status refresh failed: {e}")
        
        asyncio.create_task(poll_for_upgrade())
    
    def _apply_pro_ui_refresh(self) -> None:
        """Update all visible UI elements to reflect Pro status."""
        try:
            from tui.widgets.status_banner import StatusBanner
            for banner in self.app.query(StatusBanner):
                banner.refresh_status()
            
            from tui.screens.dashboard import DashboardScreen
            for screen in self.app.screen_stack:
                if isinstance(screen, DashboardScreen):
                    screen._update_upgrade_binding()
                    break
            
            # Start workers if they weren't running (expired trial upgrade)
            if not self.app.capture_worker or self.app.capture_worker.done():
                import asyncio
                from tui.workers import capture_worker_task, db_polling_worker
                from tui.workers.session_worker import session_worker_task
                self.app.capture_worker = asyncio.create_task(capture_worker_task(self.app))
                self.app.db_worker = asyncio.create_task(db_polling_worker(self.app))
                self.app.session_worker = asyncio.create_task(session_worker_task(self.app))
                self.app.loop_status = "active"
        except Exception as e:
            print(f"[UPGRADE] UI refresh error: {e}")
    
    def action_dismiss_screen(self) -> None:
        """Dismiss the screen."""
        # Record that prompt was shown
        prompt_type = self.trial_manager.should_show_upgrade_prompt()
        if prompt_type:
            self.trial_manager.record_upgrade_prompt_shown(prompt_type)
        
        self.dismiss()

