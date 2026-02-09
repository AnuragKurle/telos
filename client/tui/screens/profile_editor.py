"""Profile editor modal for updating name and email."""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding


class ProfileEditorModal(ModalScreen):
    """Modal for editing user profile (name and email)."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel"),
    ]

    CSS = """
    ProfileEditorModal {
        align: center middle;
    }

    #profile-dialog {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $accent;
        padding: 1 2;
    }

    #profile-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .profile-label {
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }

    .profile-input {
        width: 100%;
        margin-bottom: 1;
    }

    #profile-hint {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
        margin-bottom: 1;
    }

    #profile-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    .profile-button {
        margin: 0 1;
    }
    """

    def __init__(self, current_name: str = "", current_email: str = ""):
        super().__init__()
        self.current_name = current_name or ""
        self.current_email = current_email or ""

    def compose(self) -> ComposeResult:
        with Container(id="profile-dialog"):
            yield Static("Edit Profile", id="profile-title")
            yield Static("Name", classes="profile-label")
            yield Input(
                value=self.current_name,
                placeholder="Enter your name",
                id="name-input",
                classes="profile-input"
            )
            yield Static("Email", classes="profile-label")
            yield Input(
                value=self.current_email,
                placeholder="Enter your email",
                id="email-input",
                classes="profile-input"
            )
            yield Static(
                "Note: Changing email won't affect your Firebase authentication.",
                id="profile-hint"
            )
            with Horizontal(id="profile-buttons"):
                yield Button("Save", variant="primary", id="save-btn", classes="profile-button")
                yield Button("Cancel", variant="default", id="cancel-btn", classes="profile-button")

    def on_mount(self) -> None:
        """Focus the name input on mount."""
        self.query_one("#name-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            name_input = self.query_one("#name-input", Input)
            email_input = self.query_one("#email-input", Input)
            
            name = name_input.value.strip()
            email = email_input.value.strip()
            
            # Basic validation
            if not name:
                self.app.notify("Name cannot be empty", severity="warning")
                name_input.focus()
                return
            
            if not email:
                self.app.notify("Email cannot be empty", severity="warning")
                email_input.focus()
                return
            
            # Basic email validation
            if "@" not in email or "." not in email:
                self.app.notify("Please enter a valid email address", severity="warning")
                email_input.focus()
                return
            
            # Return the values
            self.dismiss({"name": name, "email": email})
        else:
            self.dismiss(None)
