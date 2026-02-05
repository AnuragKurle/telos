"""Welcome carousel screen showing app features."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center, Horizontal
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.reactive import reactive


class WelcomeCarouselScreen(Screen):
    """Carousel welcome screen showing major features."""
    
    BINDINGS = [
        Binding("left", "prev_slide", "Previous", show=False),
        Binding("right", "next_slide", "Next", show=False),
        Binding("enter", "continue", "Get Started", show=True),
        Binding("escape", "quit_app", "Quit", show=True),
    ]
    
    # Feature slides content
    SLIDES = [
        {
            "icon": "🔍",
            "title": "AI-Powered Tracking",
            "description": "Understand your work patterns effortlessly"
        },
        {
            "icon": "💬",
            "title": "Chat With Your Data",
            "description": "Ask questions about how you spent your time"
        },
        {
            "icon": "📊",
            "title": "Daily Reports",
            "description": "Insights delivered to your inbox every day"
        },
        {
            "icon": "🔒",
            "title": "Privacy First",
            "description": "Your data stays on your device"
        }
    ]
    
    current_slide: reactive[int] = reactive(0)
    
    CSS = """
    WelcomeCarouselScreen {
        align: center middle;
    }
    
    #welcome-container {
        width: 80;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 3 4;
    }
    
    #logo {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #tagline {
        text-align: center;
        color: $text;
        margin-bottom: 3;
        text-style: italic;
    }
    
    #slide-container {
        height: 12;
        margin-bottom: 2;
        border: solid $panel;
        background: $panel;
        padding: 2 3;
    }
    
    #slide-icon {
        text-align: center;
        margin-bottom: 2;
    }
    
    #slide-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #slide-description {
        text-align: center;
        color: $text-muted;
    }
    
    #nav-container {
        height: auto;
        margin-bottom: 2;
    }
    
    #nav-dots {
        text-align: center;
        color: $text-muted;
    }
    
    #nav-buttons {
        height: auto;
        align: center middle;
    }
    
    .nav-btn {
        width: 12;
        min-width: 8;
        margin: 0 1;
    }
    
    #button-container {
        height: auto;
        margin-top: 2;
    }
    
    #button-container Button {
        width: 100%;
        margin-top: 1;
    }
    
    #beta-notice {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
        text-style: italic;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the welcome carousel screen."""
        with Center():
            with Vertical(id="welcome-container"):
                yield Static("✨ TELOS ✨", id="logo")
                yield Static("Know where your time goes", id="tagline")
                
                # Slide container
                with Container(id="slide-container"):
                    slide = self.SLIDES[0]
                    yield Static(slide["icon"], id="slide-icon")
                    yield Static(slide["title"], id="slide-title")
                    yield Static(slide["description"], id="slide-description")
                
                # Navigation
                with Container(id="nav-container"):
                    yield Static("● ○ ○ ○", id="nav-dots")
                    with Horizontal(id="nav-buttons"):
                        yield Button("◀", variant="default", classes="nav-btn", id="prev-btn")
                        yield Button("▶", variant="default", classes="nav-btn", id="next-btn")
                
                # Action buttons
                with Container(id="button-container"):
                    yield Button("Get Started", variant="success", id="continue-btn")
                
                yield Static("7-day free trial · no credit card needed", id="beta-notice")
    
    def watch_current_slide(self, new_slide: int) -> None:
        """Update displayed slide when current_slide changes."""
        slide = self.SLIDES[new_slide]
        
        # Update slide content
        self.query_one("#slide-icon", Static).update(slide["icon"])
        self.query_one("#slide-title", Static).update(slide["title"])
        self.query_one("#slide-description", Static).update(slide["description"])
        
        # Update dots indicator
        dots = ["●" if i == new_slide else "○" for i in range(len(self.SLIDES))]
        self.query_one("#nav-dots", Static).update(" ".join(dots))
    
    def action_prev_slide(self) -> None:
        """Go to previous slide."""
        self.current_slide = (self.current_slide - 1) % len(self.SLIDES)
    
    def action_next_slide(self) -> None:
        """Go to next slide."""
        self.current_slide = (self.current_slide + 1) % len(self.SLIDES)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "prev-btn":
            self.action_prev_slide()
        elif event.button.id == "next-btn":
            self.action_next_slide()
        elif event.button.id == "continue-btn":
            self.action_continue()
    
    def action_continue(self) -> None:
        """Continue to next screen."""
        self.dismiss(True)
    
    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()
