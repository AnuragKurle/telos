"""Activation screen for beta access verification."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding
import threading

class ActivationScreen(Screen):
    """Screen for verifying beta access."""
    
    BINDINGS = [
        # No escape binding - mandatory screen
        Binding("enter", "submit", "Activate", show=True),
    ]
    
    CSS = """
    ActivationScreen {
        align: center middle;
        background: $surface;
    }
    
    #activation-container {
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
    }
    
    .instruction {
        text-align: center;
        margin-bottom: 2;
        color: $text;
    }
    
    #email-input {
        margin-bottom: 2;
    }
    
    #status-message {
        text-align: center;
        margin-bottom: 2;
        height: 1;
        color: $error;
    }
    
    Button {
        width: 100%;
    }
    """
    
    def __init__(self, backend_client, trial_manager):
        super().__init__()
        self.backend_client = backend_client
        self.trial_manager = trial_manager
    
    def compose(self) -> ComposeResult:
        """Compose the activation screen."""
        with Center():
            with Vertical(id="activation-container"):
                yield Static("🔐 Beta Activation", id="title")
                yield Static("Enter your email to activate your 7-day trial.", classes="instruction")
                
                yield Input(placeholder="user@example.com", id="email-input")
                yield Static("", id="status-message")
                
                yield Button("Activate Access", variant="primary", id="activate-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "activate-btn":
            self.action_submit()
            
    def action_submit(self) -> None:
        """Handle activation submission."""
        email = self.query_one("#email-input", Input).value.strip()
        status_msg = self.query_one("#status-message", Static)
        
        if not email:
            status_msg.update("Please enter an email address")
            return
            
        status_msg.update("Verifying access...")
        self.query_one("#activate-btn", Button).disabled = True
        
        # Run verification in worker
        self.run_worker(self._verify_access(email), exclusive=True)
        
    async def _verify_access(self, email: str) -> None:
        """Verify access with backend."""
        status_msg = self.query_one("#status-message", Static)
        btn = self.query_one("#activate-btn", Button)
        
        try:
            # We need to run the blocking request in a thread or ensure backend_client is async
            # Since backend_client is sync requests, we wrap it
            
            # NOTE: In Textual workers, simple sync calls are okay if short, 
            # but net calls should be threaded. Textual 0.50+ worker supports 'thread'.
            
            def do_request():
                return self.backend_client.verify_access(email)
            
            # Running synchronous network call in a thread via worker
            # NOTE: Creating own thread wrapper since Textual worker API nuances might differ 
            # by version, simplistic approach for now:
            
            result = do_request() # Blocking for now, might freeze UI slightly
            
            if result.get('access'):
                status_msg.update("✓ Access Granted!", )
                status_msg.styles.color = "green"
                
                # Activate trial locally
                self.trial_manager.activate_trial(
                    email,
                    result['trialStartDate'],
                    result['trialEndDate']
                )
                
                # Let user see success briefly
                import asyncio
                await asyncio.sleep(1)
                self.dismiss(True)
            else:
                status_msg.update(f"✗ {result.get('error', 'Access Denied')}")
                status_msg.styles.color = "red"
                
        except Exception as e:
            status_msg.update(f"Error: {str(e)}")
            status_msg.styles.color = "red"
        
        finally:
            btn.disabled = False
