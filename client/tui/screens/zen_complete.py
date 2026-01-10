"""Zen of Telos completion screen - philosophy and final setup."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button, Input, Label
from textual.reactive import reactive


class ZenCompleteScreen(Screen):
    """The Zen of Telos - completion screen with philosophy."""
    
    CSS = """
    ZenCompleteScreen {
        align: center middle;
        background: $surface;
    }
    
    #zen-container {
        width: 70;
        height: auto;
        padding: 2 6;
    }
    
    #zen-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
        margin-top: 1;
    }
    
    .philosophy-line {
        text-align: center;
        color: $text;
        margin: 1 0;
    }
    
    .philosophy-line.emphasis {
        color: $accent;
        text-style: italic;
    }
    
    #time-section {
        margin-top: 2;
        margin-bottom: 2;
        padding: 1 0;
    }
    
    #time-label {
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }
    
    #time-input-container {
        align: center middle;
        height: auto;
    }
    
    #time-input {
        width: 20;
    }
    
    #begin-container {
        margin-top: 2;
        height: auto;
    }
    
    Button {
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the Zen completion screen."""
        with Center():
            with Vertical(id="zen-container"):
                # Title
                yield Static("The Zen of Telos", id="zen-title")
                
                # Philosophy text with generous spacing
                yield Static("", classes="philosophy-line")  # Spacing
                yield Static("A great product disappears into the background.", classes="philosophy-line")
                yield Static("", classes="philosophy-line")  # Spacing
                yield Static("Telos will quietly observe and understand.", classes="philosophy-line")
                yield Static("You'll receive your daily insights by email.", classes="philosophy-line")
                yield Static("Visit anytime to explore, chat, or reflect.", classes="philosophy-line")
                yield Static("", classes="philosophy-line")  # Spacing
                yield Static("Now, go do meaningful work.", classes="philosophy-line emphasis")
                yield Static("We'll be here when you need us.", classes="philosophy-line emphasis")
                yield Static("", classes="philosophy-line")  # Spacing
                
                # Time preference section
                with Container(id="time-section"):
                    yield Static("When would you like your daily report?", id="time-label")
                    with Container(id="time-input-container"):
                        yield Input(placeholder="21:00", value="21:00", id="time-input")
                
                # Begin button
                with Container(id="begin-container"):
                    yield Button("Begin", variant="success", id="begin-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "begin-btn":
            self.action_begin()
    
    def action_begin(self) -> None:
        """Finish onboarding and start the app."""
        time_input = self.query_one("#time-input", Input).value.strip()
        
        # Validate time format
        if not time_input:
            time_input = "21:00"
        
        try:
            hour, minute = time_input.split(":")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                # Invalid time, use default
                time_input = "21:00"
        except:
            # Invalid format, use default
            time_input = "21:00"
        
        # Return the time preference
        self.dismiss({"send_time": time_input})
