"""Email setup screen for onboarding."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center, ScrollableContainer
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding


class EmailSetupScreen(Screen):
    """Email configuration screen during onboarding."""
    
    BINDINGS = [
        Binding("escape", "skip", "Skip", show=True),
    ]
    
    CSS = """
    EmailSetupScreen {
        align: center middle;
    }
    
    #email-container {
        width: 80;
        height: auto;
        max-height: 38;
        border: solid $accent;
        background: $surface;
        padding: 2 3;
    }
    
    #email-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #email-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
        text-style: italic;
    }
    
    #email-description {
        color: $text;
        margin-bottom: 2;
        text-align: center;
    }
    
    #form-container {
        margin-bottom: 2;
    }
    
    .form-field {
        margin: 1 0;
    }
    
    .form-label {
        color: $text;
        margin-bottom: 1;
    }
    
    Input {
        width: 100%;
    }
    
    #help-text {
        color: $text-muted;
        margin-top: 1;
        padding: 1;
        border: solid $panel;
        background: $panel;
    }
    
    .help-line {
        margin: 1 0;
    }
    
    #button-container {
        height: auto;
        margin-top: 2;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    
    #status-message {
        text-align: center;
        margin-top: 1;
        color: $warning;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the email setup screen."""
        with Center():
            with Vertical(id="email-container"):
                yield Static("📧 Email Reports", id="email-title")
                yield Static("(Optional - you can configure this later)", id="email-subtitle")
                yield Static("Receive beautiful daily summaries via email", id="email-description")
                
                with ScrollableContainer(id="form-container"):
                    with Container(classes="form-field"):
                        yield Label("Gmail Address:", classes="form-label")
                        yield Input(placeholder="your-email@gmail.com", id="email-input")
                    
                    with Container(classes="form-field"):
                        yield Label("Gmail App Password:", classes="form-label")
                        yield Input(placeholder="16-character app password", password=True, id="password-input")
                    
                    with Container(classes="form-field"):
                        yield Label("Report Time (24h format):", classes="form-label")
                        yield Input(placeholder="21:00", value="21:00", id="time-input")
                    
                    with Container(id="help-text"):
                        yield Static("📝 Gmail Setup Instructions:", classes="help-line")
                        yield Static("1. Go to myaccount.google.com/apppasswords", classes="help-line")
                        yield Static("2. Create a new app password for 'Mail'", classes="help-line")
                        yield Static("3. Copy the 16-character password here", classes="help-line")
                        yield Static("4. Never use your regular Gmail password", classes="help-line")
                
                yield Static("", id="status-message")
                
                with Container(id="button-container"):
                    yield Button("Save & Test", variant="success", id="save-btn")
                    yield Button("Skip for Now", variant="default", id="skip-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "skip-btn":
            self.action_skip()
    
    def action_save(self) -> None:
        """Save email configuration."""
        email = self.query_one("#email-input", Input).value.strip()
        password = self.query_one("#password-input", Input).value.strip()
        send_time = self.query_one("#time-input", Input).value.strip()
        
        status_msg = self.query_one("#status-message", Static)
        
        # Basic validation
        if not email or not password:
            status_msg.update("⚠️ Please fill in all required fields")
            return
        
        if "@" not in email:
            status_msg.update("⚠️ Invalid email address")
            return
        
        if len(password) < 10:
            status_msg.update("⚠️ App password should be at least 16 characters")
            return
        
        # Validate time format
        try:
            hour, minute = send_time.split(":")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError
        except:
            status_msg.update("⚠️ Invalid time format (use HH:MM)")
            return
        
        # Return configuration
        self.dismiss({
            "email": email,
            "password": password,
            "send_time": send_time
        })
    
    def action_skip(self) -> None:
        """Skip email setup."""
        self.dismiss(None)

