"""
Analysis Goals Manager

Manages user-defined analysis goals for AI enrichment.
Provides preset goals and custom goal support.
"""

import json
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.database import Database


class AnalysisGoalManager:
    """Manages user-defined analysis goals for AI enrichment."""

    PRESET_GOALS = {
        "productivity": {
            "name": "Productivity Tracking",
            "focus": "Time management, focus patterns, productive vs unproductive activities",
            "questions": [
                "What were the most productive activities?",
                "How often did context switching occur?",
                "What patterns indicate deep work?"
            ]
        },
        "learning": {
            "name": "Learning Documentation",
            "focus": "Skills learned, resources used, learning progress",
            "questions": [
                "What new concepts or technologies were explored?",
                "What documentation or tutorials were referenced?",
                "What practical application occurred?"
            ]
        },
        "project_tracking": {
            "name": "Project Progress",
            "focus": "Project milestones, code changes, problem-solving steps",
            "questions": [
                "What project tasks were completed?",
                "What technical challenges were encountered?",
                "What solutions or approaches were tried?"
            ]
        },
        "habits": {
            "name": "Habit Analysis",
            "focus": "Time allocation, app usage patterns, behavior trends",
            "questions": [
                "What time was spent on each app/category?",
                "What patterns suggest good or bad habits?",
                "What distractions occurred most frequently?"
            ]
        },
        "custom": {
            "name": "Custom Goals",
            "focus": "",  # User-provided
            "questions": []  # User-provided
        }
    }

    def __init__(self, db: 'Database'):
        """Initialize goal manager.

        Args:
            db: Database instance for storing goals
        """
        self.db = db

    def get_active_goals(self) -> Dict[str, Any]:
        """Get currently active analysis goals.

        Returns:
            Dict with 'preset' and 'custom_text' keys
        """
        goals_json = self.db.get_config_value('analysis_goals')
        if goals_json:
            try:
                return json.loads(goals_json)
            except json.JSONDecodeError:
                # Corrupted data, return default
                return {"preset": "productivity", "custom_text": ""}

        # Default to productivity tracking
        return {"preset": "productivity", "custom_text": ""}

    def set_goals(self, preset: str, custom_text: str = "") -> None:
        """Set analysis goals.

        Args:
            preset: Preset goal name (productivity, learning, project_tracking, habits, custom)
            custom_text: Custom goal text (used when preset='custom')

        Raises:
            ValueError: If preset is invalid
        """
        if preset not in self.PRESET_GOALS:
            raise ValueError(f"Invalid preset: {preset}. Must be one of {list(self.PRESET_GOALS.keys())}")

        goals = {"preset": preset, "custom_text": custom_text}
        self.db.set_config_value('analysis_goals', json.dumps(goals))

    def build_session_prompt_context(self) -> str:
        """Build additional context for session analysis based on goals.

        Returns:
            String to inject into Gemini prompt
        """
        goals = self.get_active_goals()
        preset = goals.get("preset", "productivity")
        custom = goals.get("custom_text", "")

        if preset == "custom" and custom:
            return f"\nUser's analysis focus: {custom}"

        goal_config = self.PRESET_GOALS.get(preset, self.PRESET_GOALS["productivity"])

        return f"""
User's analysis focus: {goal_config['focus']}
Pay attention to: {', '.join(goal_config['questions'])}
"""

    def get_preset_info(self, preset: str) -> Dict[str, Any]:
        """Get information about a specific preset.

        Args:
            preset: Preset goal name

        Returns:
            Dict with preset configuration

        Raises:
            ValueError: If preset is invalid
        """
        if preset not in self.PRESET_GOALS:
            raise ValueError(f"Invalid preset: {preset}")

        return self.PRESET_GOALS[preset]

    def list_presets(self) -> Dict[str, str]:
        """List all available presets with their names.

        Returns:
            Dict mapping preset keys to display names
        """
        return {key: config["name"] for key, config in self.PRESET_GOALS.items()}

    def get_current_goal(self) -> Dict[str, Any]:
        """Get the full context of the currently active goal.

        Returns:
            Dict containing 'name', 'focus', and 'questions'
        """
        active = self.get_active_goals()
        preset_key = active.get("preset", "productivity")
        custom_text = active.get("custom_text", "")

        if preset_key == "custom":
            return {
                "name": "Custom Goal",
                "focus": custom_text,
                "questions": []
            }

        return self.PRESET_GOALS.get(preset_key, self.PRESET_GOALS["productivity"]).copy()
