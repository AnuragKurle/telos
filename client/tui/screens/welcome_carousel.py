"""Welcome carousel screen showing app features."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
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
    
    # Condensed to 4 slides (merged related features)
    SLIDES = [
        {
            "icon": "🔍",
            "title": "AI Tracks Your Time Automatically",
            "description": (
                "Telos watches your screen and uses AI to understand\n"
                "what you're working on — automatically.\n\n"
                '"You spent 3h 12m coding, 47m in Slack, 1h browsing.\n'
                ' Your peak focus window was 10am-12pm."'
            ),
        },
        {
            "icon": "💬",
            "title": "Chat With Your Work History",
            "description": (
                'Ask things like "What did I do yesterday?" or\n'
                '"How much time did I spend on the redesign this week?"\n\n'
                "Get real answers from your own data, instantly."
            ),
        },
        {
            "icon": "📧",
            "title": "AI Tools & Daily Briefing",
            "description": (
                "Get an AI-written summary of your day in your inbox.\n"
                "Like having a personal assistant review your work.\n\n"
                "Connect to Claude, Cursor, or any MCP-compatible tool."
            ),
        },
        {
            "icon": "🔒",
            "title": "Privacy First — Always",
            "description": (
                "Screenshots are analyzed and immediately deleted.\n"
                "Your data is encrypted. No tracking. No telemetry.\n\n"
                "Your data stays on your machine. Always."
            ),
        },
    ]
    
    current_slide: reactive[int] = reactive(0)
    _auto_advance_timer = None
    
    CSS = """
    WelcomeCarouselScreen {
        align: center middle;
    }
    
    #welcome-container {
        width: 80;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2 4;
    }
    
    #logo {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 0;
    }

    #trial-notice {
        text-align: center;
        color: $success;
        margin-bottom: 1;
    }
    
    #tagline {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
        text-style: italic;
    }
    
    #slide-container {
        height: 12;
        margin-bottom: 1;
        border: solid $panel;
        background: $panel;
        padding: 2 3;
    }
    
    #slide-icon {
        text-align: center;
        margin-bottom: 1;
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
    
    #nav-dots {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #button-container {
        height: auto;
    }
    
    #button-container Button {
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the welcome carousel screen."""
        with Center():
            with Vertical(id="welcome-container"):
                yield Static("TELOS", id="logo")
                yield Static("7-day free trial · no credit card needed", id="trial-notice")
                yield Static("Know where your time goes", id="tagline")
                
                # Slide container
                with Container(id="slide-container"):
                    slide = self.SLIDES[0]
                    yield Static(slide["icon"], id="slide-icon")
                    yield Static(slide["title"], id="slide-title")
                    yield Static(slide["description"], id="slide-description")
                
                # Navigation dots only (arrow keys work, no buttons needed)
                dots_str = " ".join(["●"] + ["○"] * (len(self.SLIDES) - 1))
                yield Static(dots_str, id="nav-dots")
                
                # Action button
                with Container(id="button-container"):
                    yield Button("Get Started →", variant="success", id="continue-btn")

    def on_mount(self) -> None:
        """Start auto-advance timer."""
        self._start_auto_advance()
    
    def _start_auto_advance(self) -> None:
        """Start or restart the auto-advance timer (5 seconds per slide)."""
        if self._auto_advance_timer is not None:
            self._auto_advance_timer.stop()
        self._auto_advance_timer = self.set_interval(5.0, self._auto_next_slide)

    def _auto_next_slide(self) -> None:
        """Auto-advance to next slide."""
        self.current_slide = (self.current_slide + 1) % len(self.SLIDES)

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
        """Go to previous slide (pauses auto-advance)."""
        self._start_auto_advance()  # Reset timer on interaction
        self.current_slide = (self.current_slide - 1) % len(self.SLIDES)
    
    def action_next_slide(self) -> None:
        """Go to next slide (pauses auto-advance)."""
        self._start_auto_advance()  # Reset timer on interaction
        self.current_slide = (self.current_slide + 1) % len(self.SLIDES)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "continue-btn":
            self.action_continue()
    
    def action_continue(self) -> None:
        """Continue to next screen."""
        if self._auto_advance_timer is not None:
            self._auto_advance_timer.stop()
        self.dismiss(True)
    
    def action_quit_app(self) -> None:
        """Quit the application."""
        if self._auto_advance_timer is not None:
            self._auto_advance_timer.stop()
        self.app.exit()
