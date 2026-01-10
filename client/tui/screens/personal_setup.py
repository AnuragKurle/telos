"""Personal setup screen with two-phase UI - name then account creation."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button, Input, Label
from textual.reactive import reactive


class PersonalSetupScreen(Screen):
    """Personal setup screen - collects name, email, password."""
    
    phase: reactive[int] = reactive(1)  # Phase 1: name, Phase 2: email/password
    user_name: str = ""
    
    CSS = """
    PersonalSetupScreen {
        align: center middle;
    }
    
    #setup-container {
        width: 60;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 3 4;
    }
    
    #setup-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
    }
    
    #setup-subtitle {
        text-align: center;
        color: $text;
        margin-bottom: 3;
    }
    
    .form-field {
        margin: 2 0;
    }
    
    .form-label {
        color: $text;
        margin-bottom: 1;
        text-align: center;
    }
    
    Input {
        width: 100%;
    }
    
    #status-message {
        text-align: center;
        margin-top: 1;
        color: $warning;
        height: 1;
    }
    
    #button-container {
        height: auto;
        margin-top: 2;
    }
    
    Button {
        width: 100%;
    }
    
    /* Hidden by default */
    .phase-2 {
        display: none;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the personal setup screen."""
        with Center():
            with Vertical(id="setup-container"):
                yield Static("👋 Welcome!", id="setup-title")
                yield Static("What should we call you?", id="setup-subtitle")
                
                # Phase 1: Name input
                with Container(classes="form-field phase-1"):
                    yield Label("", classes="form-label")
                    yield Input(placeholder="Your name...", id="name-input")
                
                # Phase 2: Email and password (hidden initially)
                with Container(classes="form-field phase-2", id="email-field"):
                    yield Label("Email:", classes="form-label")
                    yield Input(placeholder="email@example.com", id="email-input")
                
                with Container(classes="form-field phase-2", id="password-field"):
                    yield Label("Password:", classes="form-label")
                    yield Input(placeholder="Minimum 6 characters", password=True, id="password-input")
                
                yield Static("", id="status-message")
                
                with Container(id="button-container"):
                    yield Button("Continue", variant="success", id="continue-btn", classes="phase-1")
                    yield Button("Create Account", variant="success", id="create-btn", classes="phase-2")
    
    def watch_phase(self, new_phase: int) -> None:
        """Handle phase transitions."""
        if new_phase == 2:
            # Update title and subtitle
            self.query_one("#setup-title", Static).update(f"Nice to meet you, {self.user_name}! 🎉")
            self.query_one("#setup-subtitle", Static).update(
                "Let's create your account to save\nyour data securely."
            )
            
            # Hide phase 1 elements
            for elem in self.query(".phase-1"):
                elem.styles.display = "none"
            
            # Show phase 2 elements
            for elem in self.query(".phase-2"):
                elem.styles.display = "block"
            
            # Focus email input
            self.query_one("#email-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "name-input" and self.phase == 1:
            self.action_continue_phase_1()
        elif event.input.id == "password-input" and self.phase == 2:
            self.action_create_account()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "continue-btn":
            self.action_continue_phase_1()
        elif event.button.id == "create-btn":
            self.action_create_account()
    
    def action_continue_phase_1(self) -> None:
        """Continue from phase 1 to phase 2."""
        name = self.query_one("#name-input", Input).value.strip()
        status_msg = self.query_one("#status-message", Static)
        
        if not name:
            status_msg.update("⚠️ Please enter your name")
            return
        
        self.user_name = name
        status_msg.update("")
        self.phase = 2
    
    def action_create_account(self) -> None:
        """Create account and proceed."""
        email = self.query_one("#email-input", Input).value.strip()
        password = self.query_one("#password-input", Input).value.strip()
        status_msg = self.query_one("#status-message", Static)
        
        # Validation
        if not email or not password:
            status_msg.update("⚠️ Email and password are required")
            return
        
        if "@" not in email:
            status_msg.update("⚠️ Invalid email address")
            return
        
        if len(password) < 6:
            status_msg.update("⚠️ Password must be at least 6 characters")
            return
        
        # Return the collected data
        self.dismiss({
            "name": self.user_name,
            "email": email,
            "password": password
        })
