"""Settings screen - configuration."""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer
from typing import Optional

from core.trial_manager import TrialManager

from core.database import Database
from core.goal_manager import AnalysisGoalManager
from core.backend_client import BackendClient, BackendError, AuthenticationError
from tui.screens.goal_editor import GoalEditorModal
from tui.screens.email_settings_modal import EmailSettingsModal
from tui.screens.feedback_modal import FeedbackModal
from tui.screens.upgrade_modal import UpgradeModal


class SettingsScreen(Screen):
    """Settings view for configuration."""

    BINDINGS = [
        ("g", "edit_goals", "Edit Goals"),
        ("e", "edit_email", "Email Settings"),
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

    def action_edit_email(self) -> None:
        """Open email settings modal."""
        def on_email_saved():
            # Refresh settings display after saving
            self.update_settings()

        self.app.push_screen(EmailSettingsModal(self.app.config, on_save=on_email_saved))

    def update_settings(self) -> None:
        """Update settings display."""
        app = self.app
        config = app.config
        
        # Account Info (use correct config.get API)
        name = config.get('account', 'name', default='User')
        email = config.get('account', 'email', default='Not set')
        status = config.get('account', 'status', default='trial')
        
        # Check Pro status using TrialManager
        trial_manager = TrialManager(config)
        is_pro = trial_manager.is_pro()
        
        # Format plan display
        if is_pro:
            plan = "✨ PRO"
        else:
            plan = status.upper()
        
        # Email Preferences
        send_time = config.get('email', 'send_time', default='21:00')
        email_enabled = "Enabled" if config.get('email', 'enabled', default=False) else "Disabled"

        # Analysis Goals
        db = Database(config.get('storage', 'database_path'))
        goal_manager = AnalysisGoalManager(db)
        active_goals = goal_manager.get_active_goals()
        preset = active_goals.get('preset', 'productivity')
        preset_info = AnalysisGoalManager.PRESET_GOALS.get(preset, {})
        preset_name = preset_info.get('name', preset)

        # Conditional upgrade text
        if is_pro:
            upgrade_line = "Thank you for supporting Telos! 💙"
        else:
            upgrade_line = "Press U to Upgrade to Pro"

        settings_text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                 SETTINGS                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

👤 ACCOUNT
  Name:  {name}
  Email: {email}
  Plan:  {plan}

📧 EMAIL PREFERENCES
  Daily Report: {email_enabled}
  Report Time:  {send_time}

  [ Press E to Edit Email Settings ]

🎯 ANALYSIS GOALS
  Current Focus: {preset_name}

  [ Press G to Change Goals ]

───────────────────────────────────────────────────────────────────────────
{upgrade_line}
Press ESC to Back
"""
        self.query_one("#settings-content").update(settings_text)
        
        # Dynamically update bindings based on pro status
        self._update_bindings_for_status(is_pro)
    
    def _update_bindings_for_status(self, is_pro: bool) -> None:
        """Update key bindings based on subscription status."""
        # The bindings are static at class level, but we can control action behavior
        pass  # We'll handle this via check_action

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
        # Check if already pro
        trial_manager = TrialManager(self.app.config)
        if trial_manager.is_pro():
            self.app.notify("You're already a Pro user! 🎉", severity="information")
            return
        
        # Get email from config
        email = self.app.config.get('account', 'email', default="")
        
        # Initialize backend client
        backend_url = self.app.config.get('backend', 'url', default="")
        firebase_api_key = self.app.config.get('firebase', 'api_key', default="")
        backend_client = BackendClient(backend_url, firebase_api_key)
        
        self.app.push_screen(UpgradeModal(backend_client, email))

