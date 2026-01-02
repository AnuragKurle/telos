"""Tutorial and contextual hints system."""

import json
from pathlib import Path
from typing import Dict, Set, Optional


class TutorialManager:
    """Manages tutorial hints and feature discovery tracking."""
    
    # Tutorial hints for different features
    HINTS = {
        "ai_chat": {
            "message": "💡 Try pressing 'A' to chat with your data!",
            "trigger_after_captures": 10,
        },
        "timeline": {
            "message": "💡 Press 'T' to see your timeline and sessions",
            "trigger_after_captures": 5,
        },
        "summary": {
            "message": "💡 Press 'S' to view your daily summary",
            "trigger_after_captures": 20,
        },
        "goals": {
            "message": "💡 Press 'G' to customize your analysis goals",
            "trigger_after_captures": 15,
        },
        "help": {
            "message": "💡 Press 'H' anytime for help and keyboard shortcuts",
            "trigger_after_captures": 3,
        }
    }
    
    def __init__(self, storage_dir: str = "~/.telos"):
        """Initialize tutorial manager.
        
        Args:
            storage_dir: Directory to store tutorial state
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.storage_dir / "tutorial_state.json"
        self._state: Optional[Dict] = None
    
    def get_state(self) -> Dict:
        """Get tutorial state.
        
        Returns:
            Tutorial state dict
        """
        if self._state is None:
            self._load_state()
        return self._state
    
    def _load_state(self) -> None:
        """Load tutorial state from disk."""
        if not self.state_file.exists():
            self._state = {
                'hints_shown': [],
                'features_used': [],
                'total_captures': 0,
                'tutorial_enabled': True,
            }
            return
        
        try:
            with open(self.state_file, 'r') as f:
                self._state = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._state = {
                'hints_shown': [],
                'features_used': [],
                'total_captures': 0,
                'tutorial_enabled': True,
            }
    
    def _save_state(self) -> None:
        """Save tutorial state to disk."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
        except IOError:
            pass  # Fail silently
    
    def is_tutorial_enabled(self) -> bool:
        """Check if tutorial is enabled.
        
        Returns:
            True if tutorial is enabled
        """
        state = self.get_state()
        return state.get('tutorial_enabled', True)
    
    def disable_tutorial(self) -> None:
        """Disable tutorial hints."""
        state = self.get_state()
        state['tutorial_enabled'] = False
        self._save_state()
    
    def enable_tutorial(self) -> None:
        """Enable tutorial hints."""
        state = self.get_state()
        state['tutorial_enabled'] = True
        self._save_state()
    
    def increment_captures(self) -> None:
        """Increment capture count."""
        state = self.get_state()
        state['total_captures'] = state.get('total_captures', 0) + 1
        self._save_state()
    
    def mark_feature_used(self, feature: str) -> None:
        """Mark a feature as used.
        
        Args:
            feature: Feature name (e.g., 'ai_chat', 'timeline')
        """
        state = self.get_state()
        features_used = state.get('features_used', [])
        
        if feature not in features_used:
            features_used.append(feature)
            state['features_used'] = features_used
            self._save_state()
    
    def mark_hint_shown(self, hint_id: str) -> None:
        """Mark a hint as shown.
        
        Args:
            hint_id: Hint identifier
        """
        state = self.get_state()
        hints_shown = state.get('hints_shown', [])
        
        if hint_id not in hints_shown:
            hints_shown.append(hint_id)
            state['hints_shown'] = hints_shown
            self._save_state()
    
    def get_next_hint(self) -> Optional[Dict]:
        """Get the next hint to show.
        
        Returns:
            Hint dict with 'id' and 'message', or None if no hint to show
        """
        if not self.is_tutorial_enabled():
            return None
        
        state = self.get_state()
        total_captures = state.get('total_captures', 0)
        hints_shown = set(state.get('hints_shown', []))
        features_used = set(state.get('features_used', []))
        
        # Check each hint
        for hint_id, hint_data in self.HINTS.items():
            # Skip if already shown
            if hint_id in hints_shown:
                continue
            
            # Skip if feature already used
            if hint_id in features_used:
                continue
            
            # Check if we've reached the trigger threshold
            if total_captures >= hint_data['trigger_after_captures']:
                return {
                    'id': hint_id,
                    'message': hint_data['message']
                }
        
        return None
    
    def reset_tutorial(self) -> None:
        """Reset tutorial state (for testing)."""
        self._state = {
            'hints_shown': [],
            'features_used': [],
            'total_captures': 0,
            'tutorial_enabled': True,
        }
        self._save_state()
    
    def get_progress(self) -> Dict:
        """Get tutorial progress information.
        
        Returns:
            Dict with progress info
        """
        state = self.get_state()
        
        total_hints = len(self.HINTS)
        hints_shown = len(state.get('hints_shown', []))
        features_used = len(state.get('features_used', []))
        
        return {
            'total_hints': total_hints,
            'hints_shown': hints_shown,
            'features_used': features_used,
            'total_captures': state.get('total_captures', 0),
            'completion_percent': int((features_used / total_hints) * 100) if total_hints > 0 else 0,
        }

