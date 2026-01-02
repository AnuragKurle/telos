"""Help screen with keyboard shortcuts and documentation."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Button
from textual.binding import Binding


class HelpScreen(Screen):
    """Help and documentation screen."""
    
    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
    ]
    
    CSS = """
    HelpScreen {
        align: center middle;
    }
    
    #help-container {
        width: 90;
        height: 40;
        border: solid $accent;
        background: $surface;
        padding: 2 3;
    }
    
    #help-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid $accent;
        padding-bottom: 1;
    }
    
    #help-content {
        height: 1fr;
        margin-bottom: 1;
    }
    
    .help-section {
        margin: 1 0;
    }
    
    .section-title {
        color: $success;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .help-item {
        color: $text;
        margin: 1 0;
    }
    
    .key {
        color: $accent;
        text-style: bold;
    }
    
    #button-container {
        height: auto;
        padding-top: 1;
        border-top: solid $panel;
    }
    
    Button {
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical(id="help-container"):
            yield Static("❓ Help & Documentation", id="help-title")
            
            with ScrollableContainer(id="help-content"):
                # Keyboard Shortcuts
                with Container(classes="help-section"):
                    yield Static("⌨️ Keyboard Shortcuts", classes="section-title")
                    yield Static("D - Dashboard (main view)", classes="help-item")
                    yield Static("T - Timeline (session view)", classes="help-item")
                    yield Static("S - Summary (daily insights)", classes="help-item")
                    yield Static("C - Settings", classes="help-item")
                    yield Static("A - AI Chat (query your data)", classes="help-item")
                    yield Static("F - Submit feedback (report AI errors)", classes="help-item")
                    yield Static("G - Edit analysis goals", classes="help-item")
                    yield Static("H - Help (this screen)", classes="help-item")
                    yield Static("Q - Quit", classes="help-item")
                
                # Features
                with Container(classes="help-section"):
                    yield Static("✨ Features", classes="section-title")
                    yield Static("📸 Automatic screenshot capture every 30 seconds", classes="help-item")
                    yield Static("🤖 AI-powered analysis with Gemini Vision", classes="help-item")
                    yield Static("📊 Smart session building and grouping", classes="help-item")
                    yield Static("💬 Natural language chat with your work history", classes="help-item")
                    yield Static("📧 Daily email reports (optional)", classes="help-item")
                    yield Static("🔒 Privacy-first: screenshots deleted immediately", classes="help-item")
                
                # Privacy
                with Container(classes="help-section"):
                    yield Static("🔒 Privacy Guarantees", classes="section-title")
                    yield Static("• Screenshots analyzed and deleted within 5 seconds", classes="help-item")
                    yield Static("• Data stored locally in SQLite database", classes="help-item")
                    yield Static("• Only analysis metadata sent to backend (no images)", classes="help-item")
                    yield Static("• No tracking, telemetry, or analytics", classes="help-item")
                    yield Static("• Export your data anytime", classes="help-item")
                
                # Troubleshooting
                with Container(classes="help-section"):
                    yield Static("🔧 Troubleshooting", classes="section-title")
                    yield Static("No captures appearing?", classes="help-item")
                    yield Static("  → Check that tracking is running (status banner)", classes="help-item")
                    yield Static("  → Ensure you're not idle (move mouse/keyboard)", classes="help-item")
                    yield Static("", classes="help-item")
                    yield Static("API quota exceeded?", classes="help-item")
                    yield Static("  → Free tier: 1500 requests/day", classes="help-item")
                    yield Static("  → Adjust capture interval in settings", classes="help-item")
                    yield Static("", classes="help-item")
                    yield Static("Email reports not working?", classes="help-item")
                    yield Static("  → Use Gmail App Password (not regular password)", classes="help-item")
                    yield Static("  → Check spam/junk folder", classes="help-item")
                
                # Support
                with Container(classes="help-section"):
                    yield Static("💬 Support", classes="section-title")
                    yield Static("Documentation: client/README.md", classes="help-item")
                    yield Static("GitHub: github.com/your-repo/telos", classes="help-item")
                    yield Static("Discord: discord.gg/telos", classes="help-item")
                    yield Static("Email: support@telos.app", classes="help-item")
            
            with Container(id="button-container"):
                yield Button("Close", variant="primary", id="close-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.action_dismiss_screen()
    
    def action_dismiss_screen(self) -> None:
        """Dismiss the screen."""
        self.dismiss()

