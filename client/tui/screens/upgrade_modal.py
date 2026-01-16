"""Upgrade intent modal screen."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Center, Horizontal
from textual.widgets import Static, Button, Label

class UpgradeModal(ModalScreen):
    """Modal to capture payment intent."""
    
    CSS = """
    UpgradeModal {
        align: center middle;
        background: $surface 50%;
    }
    
    #upgrade-container {
        width: 60;
        height: auto;
        border: solid $accent;
        padding: 2 4;
        background: $panel;
    }
    
    #title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
        content-align: center middle;
    }
    
    .benefit {
        margin-bottom: 1;
        color: $text;
        text-align: center;
    }
    
    #buttons {
        margin-top: 2;
        align: center middle;
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, backend_client, email: str):
        super().__init__()
        self.backend_client = backend_client
        self.email = email
    
    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="upgrade-container"):
                yield Static("✨ Upgrade to Telos Pro", id="title")
                
                yield Static("⭐ Unlimited History Retention", classes="benefit")
                yield Static("⭐ Priority Support", classes="benefit")
                yield Static("⭐ Advanced AI Insights", classes="benefit")
                
                yield Static("\nSupport indie development!", classes="benefit")
                
                with Horizontal(id="buttons"):
                    yield Button("I'm Interested ($9/mo)", variant="success", id="upgrade-btn")
                    yield Button("Maybe Later", variant="default", id="cancel-btn")
                    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "upgrade-btn":
            self.action_upgrade()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)
            
    def action_upgrade(self) -> None:
        """Handle upgrade intent."""
        if not self.email:
             self.app.notify("Error: No account email found. Please activate first.", severity="error")
             self.dismiss(False)
             return

        self.query_one("#upgrade-btn", Button).disabled = True
        self.query_one("#title", Static).update("Contacting Server...")
        
        # Run in worker
        self.run_worker(self._record_intent_async())
            
    async def _record_intent_async(self) -> None:
        """Record intent and open checkout asynchronously."""
        import webbrowser
        try:
            import asyncio
            # Try to create a checkout session
            response = await asyncio.to_thread(
                self.backend_client.create_checkout_session,
                plan='monthly',
                email=self.email
            )
            
            checkout_url = response.get('url')
            if checkout_url:
                # Open the checkout URL in browser
                webbrowser.open(checkout_url)
                self.app.notify("Opening Dodo Payments checkout...", severity="information")
                
                # Schedule delayed status refresh after checkout
                # User might complete payment in ~10-30 seconds
                self._schedule_status_refresh()
                
                self.dismiss(True)
                return
            else:
                # Fallback: record intent only
                await asyncio.to_thread(self.backend_client.record_payment_intent, self.email)
                self.app.notify("⚠️ Could not create checkout session", severity="warning")
                
        except Exception as e:
            # Fallback: just record intent
            try:
                import asyncio
                await asyncio.to_thread(self.backend_client.record_payment_intent, self.email)
                self.app.notify(f"✓ Interest recorded! (Checkout error: {str(e)[:50]})", severity="warning")
            except:
                self.app.notify(f"Error: {str(e)}", severity="error")
            
        self.dismiss(True)
    
    def _schedule_status_refresh(self) -> None:
        """Schedule a delayed status refresh after checkout."""
        import asyncio
        
        async def delayed_refresh():
            """Wait then refresh status."""
            await asyncio.sleep(15)  # Wait for payment processing
            await self._refresh_and_notify()
        
        # Schedule the refresh
        asyncio.create_task(delayed_refresh())
    
    async def _refresh_and_notify(self) -> None:
        """Refresh account status and notify if upgraded."""
        import asyncio
        from core.trial_manager import TrialManager
        
        try:
            config = self.app.config
            backend_url = config.get('backend', 'url', default='')
            firebase_api_key = config.get('firebase', 'api_key', default='')
            
            if not backend_url or not firebase_api_key:
                return
            
            trial_manager = TrialManager(config)
            
            # Run refresh in thread to avoid blocking
            result = await asyncio.to_thread(
                trial_manager.refresh_account_status,
                backend_url,
                firebase_api_key
            )
            
            if result and trial_manager.is_pro():
                self.app.notify(
                    "🎉 Welcome to Pro! Restart for full access.",
                    severity="information",
                    timeout=10
                )
        except Exception as e:
            # Silently fail - this is a best-effort refresh
            print(f"[UPGRADE] Status refresh failed: {e}")

class UpgradeSuccessModal(ModalScreen):
    """Simple acknowledgement modal."""
    
    CSS = """
    UpgradeSuccessModal {
        align: center middle;
        background: $surface 50%;
    }
    #success-container {
        width: 50;
        background: $panel;
        border: solid $success;
        padding: 2;
        text-align: center;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="success-container"):
                yield Static("[bold green]🎉 Request Received![/]", classes="success-title")
                yield Static("\nWe are onboarding Pro users manually during beta.")
                yield Static("We will email you shortly with setup instructions.\n")
                yield Button("Okay", variant="primary", id="ok-btn")
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
