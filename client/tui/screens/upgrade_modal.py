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
                    yield Button("I'm Interested ($10/mo)", variant="success", id="upgrade-btn")
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
        """Record intent asynchronously."""
        try:
            import asyncio
            # Run the blocking request in a thread
            success = await asyncio.to_thread(self.backend_client.record_payment_intent, self.email)
            
            if success:
                self.app.notify("✓ Interest recorded!", severity="information")
            else:
                self.app.notify("⚠️ Could not reach server, but we'll show acknowledgment anyway.", severity="warning")
        except Exception as e:
            self.app.notify(f"Error: {str(e)}", severity="error")
            
        self.dismiss(True)
        self.app.push_screen(UpgradeSuccessModal())

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
