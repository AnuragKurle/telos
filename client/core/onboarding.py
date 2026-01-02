"""Onboarding state manager.

Handles first-run detection, onboarding progress tracking, and trial management.
Stores state in ~/.telos/onboarding_state.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class OnboardingManager:
    """Manages onboarding state and progress."""
    
    # Onboarding steps
    STEP_WELCOME = "welcome"
    STEP_PRIVACY = "privacy"
    STEP_AUTH = "auth"
    STEP_BACKEND_TEST = "backend_test"
    STEP_GOALS = "goals"
    STEP_EMAIL = "email"
    STEP_COMPLETE = "complete"
    
    def __init__(self, storage_dir: str = "~/.telos"):
        """Initialize onboarding manager.
        
        Args:
            storage_dir: Directory to store onboarding state
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.storage_dir / "onboarding_state.json"
        self.complete_flag = self.storage_dir / "onboarding_complete"
        
        self._state: Optional[Dict[str, Any]] = None
    
    def is_first_run(self) -> bool:
        """Check if this is the first run of the application.
        
        Returns:
            True if onboarding has not been completed
        """
        return not self.complete_flag.exists()
    
    def is_onboarding_complete(self) -> bool:
        """Check if onboarding has been completed.
        
        Returns:
            True if onboarding is complete
        """
        return self.complete_flag.exists()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current onboarding state.
        
        Returns:
            Onboarding state dict
        """
        if self._state is None:
            self._load_state()
        return self._state.copy()
    
    def get_current_step(self) -> str:
        """Get the current onboarding step.
        
        Returns:
            Current step name
        """
        state = self.get_state()
        return state.get('current_step', self.STEP_WELCOME)
    
    def set_step(self, step: str) -> None:
        """Set the current onboarding step.
        
        Args:
            step: Step name to set
        """
        state = self.get_state()
        state['current_step'] = step
        state['last_updated'] = datetime.now().isoformat()
        self._save_state(state)
    
    def complete_step(self, step: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Mark a step as complete and optionally store data.
        
        Args:
            step: Step name
            data: Optional data to store for this step
        """
        state = self.get_state()
        
        if 'completed_steps' not in state:
            state['completed_steps'] = []
        
        if step not in state['completed_steps']:
            state['completed_steps'].append(step)
        
        if data:
            if 'step_data' not in state:
                state['step_data'] = {}
            state['step_data'][step] = data
        
        state['last_updated'] = datetime.now().isoformat()
        self._save_state(state)
    
    def is_step_complete(self, step: str) -> bool:
        """Check if a specific step is complete.
        
        Args:
            step: Step name to check
            
        Returns:
            True if step is complete
        """
        state = self.get_state()
        completed = state.get('completed_steps', [])
        return step in completed
    
    def get_step_data(self, step: str) -> Optional[Dict[str, Any]]:
        """Get data stored for a specific step.
        
        Args:
            step: Step name
            
        Returns:
            Step data if exists, None otherwise
        """
        state = self.get_state()
        step_data = state.get('step_data', {})
        return step_data.get(step)
    
    def mark_complete(self) -> None:
        """Mark onboarding as complete."""
        state = self.get_state()
        state['current_step'] = self.STEP_COMPLETE
        state['completed_at'] = datetime.now().isoformat()
        self._save_state(state)
        
        # Create completion flag file
        self.complete_flag.touch()
    
    def reset(self) -> None:
        """Reset onboarding state (for testing/debugging)."""
        if self.state_file.exists():
            self.state_file.unlink()
        if self.complete_flag.exists():
            self.complete_flag.unlink()
        self._state = None
    
    def _load_state(self) -> None:
        """Load onboarding state from disk."""
        if not self.state_file.exists():
            self._state = {
                'current_step': self.STEP_WELCOME,
                'completed_steps': [],
                'step_data': {},
                'started_at': datetime.now().isoformat(),
            }
            return
        
        try:
            with open(self.state_file, 'r') as f:
                self._state = json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted state, reset
            self._state = {
                'current_step': self.STEP_WELCOME,
                'completed_steps': [],
                'step_data': {},
                'started_at': datetime.now().isoformat(),
            }
    
    def _save_state(self, state: Dict[str, Any]) -> None:
        """Save onboarding state to disk.
        
        Args:
            state: State to save
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            self._state = state
        except IOError as e:
            print(f"Warning: Failed to save onboarding state: {e}")

