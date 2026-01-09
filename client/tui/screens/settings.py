"""Settings screen - configuration."""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer
from typing import Optional

from core.database import Database
from core.goal_manager import AnalysisGoalManager
from core.backend_client import BackendClient, BackendError, AuthenticationError
from tui.screens.goal_editor import GoalEditorModal
from tui.screens.feedback_modal import FeedbackModal
from tui.screens.feedback_modal import FeedbackModal
from tui.screens.upgrade_modal import UpgradeModal


class SettingsScreen(Screen):
    """Settings view for configuration."""

    BINDINGS = [
        ("g", "edit_goals", "Edit Goals"),
        ("u", "show_upgrade", "Upgrade to Pro"),
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        with ScrollableContainer():
            yield Static("", id="settings-content")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.title = "Settings"
        self.sub_title = "Configuration"
        self.update_settings()

    def action_edit_goals(self) -> None:
        """Open goal editor modal."""
        def on_goals_saved():
            # Refresh settings display after saving
            self.update_settings()

        self.app.push_screen(GoalEditorModal(self.app.config, on_save=on_goals_saved))

    def update_settings(self) -> None:
        """Update settings display."""
        app = self.app
        config = app.config

        # Get analysis goals
        db = Database(config.get('storage', 'database_path'))
        goal_manager = AnalysisGoalManager(db)
        active_goals = goal_manager.get_active_goals()
        preset = active_goals.get('preset', 'productivity')
        custom_text = active_goals.get('custom_text', '')

        # Get preset info
        preset_info = AnalysisGoalManager.PRESET_GOALS.get(preset, {})
        preset_name = preset_info.get('name', 'Unknown')
        preset_focus = preset_info.get('focus', '')

        # Build available presets list
        presets_list = []
        for key, info in AnalysisGoalManager.PRESET_GOALS.items():
            marker = "→ " if key == preset else "  "
            presets_list.append(f"{marker}{info['name']}: {info.get('focus', '')[:60]}")

        presets_text = "\n".join(presets_list)

        # Intelligence settings (with defaults)
        session_trigger_hours = config.get('intelligence', 'session_trigger_hours', default=2)
        session_trigger_idle = config.get('intelligence', 'session_trigger_idle_minutes', default=5)
        max_enrichment = config.get('intelligence', 'max_enrichment_per_trigger', default=3)

        settings_text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                              CONFIGURATION                                ║
╚══════════════════════════════════════════════════════════════════════════╝

GEMINI API
  Model: {config.get('gemini', 'model')}
  Max Daily Requests: {config.get('capture', 'max_daily_requests')}

CAPTURE SETTINGS
  Interval: {config.get('capture', 'interval_seconds')}s
  Idle Timeout: {config.get('capture', 'idle_timeout_seconds')}s
  Screenshot Quality: {config.get('capture', 'screenshot_quality', default=85)}

INTELLIGENCE LAYER (Phase 3)
  Session Trigger: Every {session_trigger_hours} hours OR {session_trigger_idle} min idle
  Max Enrichments per Trigger: {max_enrichment}

  Analysis Goal: {preset_name}
  Focus: {preset_focus if preset != 'custom' else custom_text}

AVAILABLE ANALYSIS GOALS
{presets_text}

STORAGE
  Database: {config.get('storage', 'database_path')}
  Captures Retention: {config.get('storage', 'captures_retention_days', default=1)} days
  Sessions Retention: {config.get('storage', 'sessions_retention_days', default=90)} days

DISPLAY
  Refresh Rate: {config.get('display', 'refresh_rate_ms')}ms
  Theme: {config.get('display', 'theme')}

───────────────────────────────────────────────────────────────────────────
Press G to edit analysis goals (interactive)
To manually build sessions: python main.py build-sessions
To generate daily summary: python main.py generate-summary

Press ESC to return to dashboard
"""
        self.query_one("#settings-content").update(settings_text)

    def action_show_feedback(self) -> None:
        """Show feedback modal for settings screen."""
        try:
            config = self.app.config
            backend_enabled = config.get('backend', 'enabled', default=False)
            
            context = {
                'type': 'general',
                'screen': 'settings',
            }
            
            def handle_feedback(result: Optional[str]) -> None:
                """Handle feedback submission."""
                if not result or not result.strip():
                    return
                
                if not backend_enabled:
                    self.app.notify(
                        "Feedback collected but backend not configured.",
                        severity="warning",
                        timeout=5
                    )
                    return
                
                # Submit feedback asynchronously
                self.run_worker(self._submit_feedback_async(result.strip(), context))

            self.app.push_screen(FeedbackModal(context), handle_feedback)
        except Exception as e:
            self.app.notify(
                f"Error opening feedback modal: {str(e)}",
                severity="error",
                timeout=5
            )

    async def _submit_feedback_async(self, feedback_text: str, context: dict) -> None:
        """Submit feedback to backend asynchronously."""
        try:
            import asyncio
            
            config = self.app.config
            backend_url = config.get('backend', 'url')
            firebase_api_key = config.get('firebase', 'api_key')
            
            backend_client = BackendClient(
                backend_url=backend_url,
                firebase_api_key=firebase_api_key
            )
            
            metadata = {
                'screen': context.get('screen', 'settings'),
                'app_version': '0.1.0',
            }
            
            response = await asyncio.to_thread(
                backend_client.submit_feedback,
                feedback_type=context.get('type', 'general'),
                feedback_text=feedback_text,
                context=context,
                metadata=metadata
            )
            
            # Show success notification with Slack status
            if response.get('slack_notified', True):  # Default True for backward compat
                self.app.notify(
                    "✓ Feedback submitted successfully!",
                    severity="information",
                    timeout=3
                )
            else:
                self.app.notify(
                    "⚠️ Feedback saved but Slack notification failed. Dev will check Firestore.",
                    severity="warning",
                    timeout=5
                )
        except (BackendError, AuthenticationError) as e:
            self.app.notify(
                f"Failed to submit feedback: {str(e)}",
                severity="error",
                timeout=5
            )
        except Exception as e:
            self.app.notify(
                f"Unexpected error: {str(e)}",
                severity="error",
                timeout=5
            )

    def action_show_upgrade(self) -> None:
        """Show upgrade modal."""
        # Get email from config
        email = self.app.config.get('account', 'email', default="")
        
        # Initialize backend client
        backend_url = self.app.config.get('backend', 'url', default="")
        firebase_api_key = self.app.config.get('firebase', 'api_key', default="")
        backend_client = BackendClient(backend_url, firebase_api_key)
        
        self.app.push_screen(UpgradeModal(backend_client, email))

