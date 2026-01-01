"""Goal Editor Modal - Interactive analysis goals configuration."""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, Button, Input, Select
from textual.containers import Vertical, Horizontal
from typing import Callable

from core.database import Database
from core.goal_manager import AnalysisGoalManager


class GoalEditorModal(ModalScreen[bool]):
    """Modal screen for editing analysis goals."""

    DEFAULT_CSS = """
    GoalEditorModal {
        align: center middle;
    }

    #goal-dialog {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #goal-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    .goal-description {
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, config, on_save: Callable = None):
        """Initialize goal editor.

        Args:
            config: Configuration manager instance
            on_save: Optional callback when goals are saved
        """
        super().__init__()
        self.config = config
        self.on_save = on_save

        # Load current goals
        db = Database(config.get('storage', 'database_path'))
        self.goal_manager = AnalysisGoalManager(db)
        self.current_goals = self.goal_manager.get_active_goals()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        presets = AnalysisGoalManager.PRESET_GOALS

        # Build options for select widget
        options = [
            (preset['name'], key)
            for key, preset in presets.items()
        ]

        current_preset = self.current_goals.get('preset', 'productivity')

        with Vertical(id="goal-dialog"):
            yield Static("🎯 Set Analysis Goals", classes="dialog-title")
            yield Static("")

            yield Static("Select analysis focus:", classes="label")
            yield Select(
                options=options,
                value=current_preset,
                id="preset-select"
            )

            yield Static("")
            yield Static("Custom focus (only used if 'Custom Goals' selected):", classes="label")
            yield Input(
                placeholder="Describe what you want to track...",
                value=self.current_goals.get('custom_text', ''),
                id="custom-input"
            )

            yield Static("")

            # Show description of selected preset
            current_description = presets[current_preset].get('focus', '')
            yield Static(
                f"Focus: {current_description}",
                id="preset-description",
                classes="goal-description"
            )

            yield Static("")

            with Horizontal(id="goal-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update description when preset changes."""
        if event.select.id == "preset-select":
            preset_key = event.value
            presets = AnalysisGoalManager.PRESET_GOALS
            description = presets.get(preset_key, {}).get('focus', '')

            self.query_one("#preset-description").update(f"Focus: {description}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            # Get selected values
            preset = self.query_one("#preset-select").value
            custom_text = self.query_one("#custom-input").value

            # Save to database
            self.goal_manager.set_goals(preset, custom_text)

            # Call callback if provided
            if self.on_save:
                self.on_save()

            # Dismiss modal with success
            self.dismiss(True)

        elif event.button.id == "cancel-btn":
            # Dismiss modal without saving
            self.dismiss(False)
