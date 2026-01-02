"""Feedback Modal - Quick feedback submission for AI analysis corrections."""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, Button, Input
from textual.containers import Vertical, Horizontal
from typing import Optional, Dict, Any


class FeedbackModal(ModalScreen[Optional[str]]):
    """Modal screen for submitting feedback on AI analysis."""

    DEFAULT_CSS = """
    FeedbackModal {
        align: center middle;
    }

    #feedback-dialog {
        width: 80;
        height: auto;
        max-height: 30;
        border: thick $accent 80%;
        background: $surface;
        padding: 1 2;
    }

    #feedback-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }
    
    #feedback-buttons Button {
        min-width: 16;
        margin: 0 1;
    }

    #feedback-context {
        color: $text-muted;
        padding: 0 1;
        margin-bottom: 1;
        border-bottom: solid $panel;
        padding-bottom: 1;
    }

    #feedback-input {
        width: 100%;
        height: 8;
    }

    .feedback-label {
        color: $text;
        margin-bottom: 1;
    }
    """

    def __init__(self, context: Dict[str, Any]):
        """Initialize feedback modal.

        Args:
            context: Context about what's being feedbacked on
                    e.g., {"type": "summary", "summary_id": 123, "date": "2024-01-03"}
                    or {"type": "session", "session_id": 456, "task": "Coding"}
        """
        super().__init__()
        self.context = context

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical(id="feedback-dialog"):
            yield Static("📝 Submit Feedback", classes="dialog-title")
            yield Static("")
            
            # Show context
            context_text = self._format_context()
            yield Static(context_text, id="feedback-context")
            yield Static("")
            
            yield Static("Describe the issue or correction:", classes="feedback-label")
            yield Input(
                placeholder="e.g., 'Category should be Learning, not Browsing' or 'Summary is inaccurate'...",
                id="feedback-input"
            )
            yield Static("")
            yield Static("[dim]Your feedback helps improve Telos AI accuracy[/dim]", classes="feedback-label")
            yield Static("")

            with Horizontal(id="feedback-buttons"):
                yield Button("Submit", variant="primary", id="submit-btn")
                yield Button("Cancel", id="cancel-btn")

    def _format_context(self) -> str:
        """Format context information for display.

        Returns:
            Formatted context string
        """
        feedback_type = self.context.get('type', 'general')
        screen = self.context.get('screen', 'unknown')
        
        if feedback_type == 'summary':
            date = self.context.get('date', 'Unknown')
            return f"[bold]Feedback on Daily Summary[/bold]\nDate: {date}\nScreen: {screen}"
        elif feedback_type == 'session':
            session_id = self.context.get('session_id')
            task = self.context.get('task', 'Unknown task')
            return f"[bold]Feedback on Session[/bold]\nTask: {task}\nID: {session_id}\nScreen: {screen}"
        elif feedback_type == 'capture':
            app = self.context.get('app', 'Unknown app')
            task = self.context.get('task', 'Unknown task')
            return f"[bold]Feedback on Current Activity[/bold]\nApp: {app}\nTask: {task}\nScreen: {screen}"
        elif feedback_type == 'chat':
            return f"[bold]Feedback on AI Chat[/bold]\nScreen: {screen}"
        else:
            return f"[bold]General Feedback[/bold]\nScreen: {screen}"

    def on_mount(self) -> None:
        """Called when modal is mounted - focus input."""
        try:
            self.query_one("#feedback-input").focus()
        except Exception:
            pass  # Input might not be ready yet

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            feedback_text = self.query_one("#feedback-input").value.strip()
            if feedback_text:
                self.dismiss(feedback_text)
            else:
                # Show error or just dismiss without feedback
                self.dismiss(None)
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

