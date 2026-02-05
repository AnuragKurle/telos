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
                    yield Button("Upgrade ($3/mo)", variant="success", id="upgrade-btn")
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
        """Schedule delayed status refresh attempts after checkout.
        
        Polls at increasing intervals: 15s, 30s, 60s, 120s.
        Payment processing can take anywhere from a few seconds to a couple minutes.
        """
        import asyncio
        
        async def poll_for_upgrade():
            """Poll backend for upgrade status with backoff."""
            delays = [15, 30, 60, 120]
            for delay in delays:
                await asyncio.sleep(delay)
                upgraded = await self._refresh_and_check()
                if upgraded:
                    return
            # After all retries, give up silently
            print("[UPGRADE] Payment not detected after polling. User may need to restart.")
        
        asyncio.create_task(poll_for_upgrade())
    
    async def _refresh_and_check(self) -> bool:
        """Refresh account status and update UI if upgraded.
        
        Returns:
            True if user is now Pro, False otherwise.
        """
        import asyncio
        from core.trial_manager import TrialManager
        
        try:
            config = self.app.config
            backend_url = config.get('backend', 'url', default='')
            firebase_api_key = config.get('firebase', 'api_key', default='')
            
            if not backend_url or not firebase_api_key:
                return False
            
            trial_manager = TrialManager(config)
            
            # Run refresh in thread to avoid blocking
            result = await asyncio.to_thread(
                trial_manager.refresh_account_status,
                backend_url,
                firebase_api_key
            )
            
            if result and trial_manager.is_pro():
                # Notify user of successful upgrade
                self.app.notify(
                    "Welcome to Telos Pro! All features are now unlocked.",
                    severity="information",
                    timeout=10
                )
                
                # Refresh the app UI state in-place
                self._apply_pro_ui_refresh()
                
                # Mark that we should show the Pro welcome on next screen switch
                config.config.setdefault('account', {})['show_pro_welcome'] = True
                config.save(config.config)
                
                return True
            return False
        except Exception as e:
            print(f"[UPGRADE] Status refresh failed: {e}")
            return False
    
    def _apply_pro_ui_refresh(self) -> None:
        """Update all visible UI elements to reflect Pro status."""
        try:
            # Refresh the status banner if visible
            from tui.widgets.status_banner import StatusBanner
            for banner in self.app.query(StatusBanner):
                banner.refresh_status()
            
            # Refresh the dashboard's upgrade binding visibility
            from tui.screens.dashboard import DashboardScreen
            for screen in self.app.screen_stack:
                if isinstance(screen, DashboardScreen):
                    screen._update_upgrade_binding()
                    break
            
            # If workers weren't started (expired trial), start them now
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
