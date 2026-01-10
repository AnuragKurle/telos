"""Goal setup screen for onboarding."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center, ScrollableContainer
from textual.widgets import Static, Button, Input
from textual.binding import Binding


class GoalSetupScreen(Screen):
    """Goal selection screen during onboarding."""
    
    BINDINGS = [
        Binding("escape", "skip", "Skip", show=True),
    ]
    
    # Goal presets
    GOALS = {
        "time_tracking": {
            "name": "🕐 How I spend my time",
            "description": "Understand your daily patterns and where time goes"
        },
        "client_work": {
            "name": "💼 Track work for clients/billing",
            "description": "Detailed activity logs for invoicing and reporting"
        },
        "learning": {
            "name": "📚 Understand my learning habits",
            "description": "Track study sessions and skill development"
        },
        "custom": {
            "name": "✏️ Something else (custom)",
            "description": "Define your own tracking focus"
        }
    }
    
    CSS = """
    GoalSetupScreen {
        align: center middle;
    }
    
    #goal-container {
        width: 80;
        height: auto;
        max-height: 35;
        border: solid $accent;
        background: $surface;
        padding: 2 3;
    }
    
    #goal-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #goal-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
        text-style: italic;
    }
    
    #goals-scroll {
        height: 20;
        margin-bottom: 1;
    }
    
    .goal-button {
        width: 100%;
        margin: 1 0;
        padding: 1 2;
        text-align: left;
        min-height: 5;
    }
    
    #custom-input-container {
        margin-top: 1;
        display: none;
    }
    
    #custom-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #button-container {
        height: auto;
        margin-top: 1;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    """
    
    def __init__(self, user_name: str = ""):
        super().__init__()
        self.user_name = user_name
        self.selected_goal = None
        self.custom_text = ""
    
    def compose(self) -> ComposeResult:
        """Compose the goal setup screen."""
        # Personalize title if name is provided
        title = f"What do you want to understand, {self.user_name}?" if self.user_name else "What do you want to understand?"
        
        with Center():
            with Vertical(id="goal-container"):
                yield Static(title, id="goal-title")
                yield Static("(Optional - you can change this later)", id="goal-subtitle")
                
                with ScrollableContainer(id="goals-scroll"):
                    for goal_id, goal_data in self.GOALS.items():
                        yield Button(
                            f"{goal_data['name']}\n{goal_data['description']}", 
                            id=f"goal-{goal_id}",
                            classes="goal-button"
                        )
                
                with Container(id="custom-input-container"):
                    yield Input(placeholder="Describe what you want to track...", id="custom-input")
                
                with Container(id="button-container"):
                    yield Button("Skip for Now", variant="default", id="skip-btn")
    
    def select_goal(self, goal_id: str) -> None:
        """Select a goal and proceed.
        
        Args:
            goal_id: ID of selected goal
        """
        self.selected_goal = goal_id
        
        if goal_id == "custom":
            # Show custom input
            custom_container = self.query_one("#custom-input-container", Container)
            custom_container.styles.display = "block"
            self.query_one("#custom-input", Input).focus()
        else:
            # Immediately proceed with preset goal
            self.dismiss({"goal": goal_id, "custom_text": None})
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle custom goal input submission."""
        if event.input.id == "custom-input":
            self.custom_text = event.value.strip()
            if self.custom_text:
                self.dismiss({"goal": "custom", "custom_text": self.custom_text})
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "skip-btn":
            self.action_skip()
        elif event.button.id and event.button.id.startswith("goal-"):
            goal_id = event.button.id.replace("goal-", "")
            self.select_goal(goal_id)
    
    def action_skip(self) -> None:
        """Skip goal setup."""
        self.dismiss(None)

