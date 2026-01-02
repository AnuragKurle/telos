"""Trial status banner widget."""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive


class TrialBanner(Static):
    """Banner showing trial status and days remaining."""
    
    days_remaining: reactive[int] = reactive(0)
    trial_status: reactive[str] = reactive("active")
    message: reactive[str] = reactive("")
    
    CSS = """
    TrialBanner {
        dock: top;
        height: 1;
        content-align: center middle;
        text-style: bold;
    }
    
    TrialBanner.green {
        background: $success;
        color: $text;
    }
    
    TrialBanner.yellow {
        background: $warning;
        color: $text;
    }
    
    TrialBanner.red {
        background: $error;
        color: $text;
    }
    
    TrialBanner.blue {
        background: $accent;
        color: $text;
    }
    
    TrialBanner.hidden {
        display: none;
    }
    """
    
    def __init__(self, trial_manager):
        """Initialize trial banner.
        
        Args:
            trial_manager: TrialManager instance
        """
        super().__init__()
        self.trial_manager = trial_manager
        self.update_status()
    
    def update_status(self) -> None:
        """Update banner status from trial manager."""
        info = self.trial_manager.get_trial_info()
        
        self.trial_status = info['status']
        self.days_remaining = info['days_remaining']
        self.message = self.trial_manager.get_banner_message()
        
        # Update display
        self.update(self.message)
        
        # Update color class
        color = self.trial_manager.get_banner_color()
        self.remove_class("green", "yellow", "red", "blue", "hidden")
        
        if info['is_upgraded']:
            self.add_class("blue")
        elif info['status'] == "not_started":
            self.add_class("hidden")
        else:
            self.add_class(color)
    
    def on_click(self) -> None:
        """Handle banner click to show upgrade screen."""
        if self.trial_status != "upgraded":
            self.app.push_screen("upgrade")

