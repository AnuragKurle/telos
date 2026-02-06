"""Settings screen - configuration with structured layout."""

from pathlib import Path
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer
from textual.binding import Binding

from core.trial_manager import TrialManager
from core.database import Database
from core.goal_manager import AnalysisGoalManager
from tui.screens.goal_editor import GoalEditorModal
from tui.screens.email_settings_modal import EmailSettingsModal
from tui.screens.upgrade_modal import UpgradeModal
from tui.feedback_mixin import FeedbackMixin


class SettingsScreen(FeedbackMixin, Screen):
    """Settings view with configuration."""

    BINDINGS = [
        Binding("g", "edit_goals", "Edit Goals"),
        Binding("e", "edit_email", "Email Settings"),
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "app.quit", "Quit"),
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
            self.update_settings()
            self.app.notify("Goals updated!", severity="information", timeout=3)

        self.app.push_screen(GoalEditorModal(self.app.config, on_save=on_goals_saved))

    def action_edit_email(self) -> None:
        """Open email settings modal."""
        def on_email_saved():
            self.update_settings()
            self.app.notify("Email settings saved!", severity="information", timeout=3)

        self.app.push_screen(EmailSettingsModal(self.app.config, on_save=on_email_saved))

    def update_settings(self) -> None:
        """Update the settings display."""
        config = self.app.config
        trial_manager = TrialManager(config)
        
        # Account info
        name = config.get('account', 'name', default='User')
        email = config.get('account', 'email', default='Not set')
        is_pro = trial_manager.is_pro()
        is_byok = trial_manager.is_byok_mode()
        
        # Plan status
        if is_byok:
            plan_line = "Plan:  [green]Local Mode[/green] (free, unlimited)"
            mode_line = "  Mode:  Bring Your Own Key"
        elif is_pro:
            plan_line = "Plan:  [green]PRO[/green]"
            mode_line = "  Mode:  Cloud"
        else:
            try:
                trial_days = trial_manager.get_days_remaining()
                if trial_days > 0:
                    plan_line = f"Plan:  [yellow]Trial ({trial_days}d left)[/yellow]"
                else:
                    plan_line = "Plan:  [red]Trial Expired[/red]"
            except:
                plan_line = "Plan:  [yellow]Trial[/yellow]"
            mode_line = "  Mode:  Cloud"

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

        # Data & Privacy
        db_path = config.get('storage', 'database_path')
        try:
            db_size = Path(db_path).stat().st_size
            if db_size > 1_000_000:
                size_str = f"{db_size / 1_000_000:.1f} MB"
            else:
                size_str = f"{db_size / 1_000:.0f} KB"
        except:
            size_str = "Unknown"

        # API Key display for BYOK users
        api_key_line = ""
        if is_byok:
            raw_key = config.get('gemini', 'api_key', default='')
            if raw_key and raw_key not in ('', 'YOUR_GEMINI_API_KEY_HERE', 'BACKEND_MODE_NO_KEY_NEEDED'):
                masked = raw_key[:6] + "..." + raw_key[-4:] if len(raw_key) > 10 else "****"
                api_key_line = f"  API Key:        {masked} (stored locally)"
            else:
                api_key_line = "  API Key:        [yellow]Not configured[/yellow]"

        # MCP Integration
        mcp_server_path = Path(__file__).resolve().parents[2] / "mcp_server.py"
        mcp_exists = mcp_server_path.exists()
        if mcp_exists:
            mcp_status = "[green]Available[/green]"
            mcp_path = str(mcp_server_path).replace("\\", "/")
        else:
            mcp_status = "[yellow]Not Found[/yellow]"
            mcp_path = "Not detected"

        # Upgrade section
        if is_byok:
            upgrade_section = """
───────────────────────────────────────────────────────────────────────────
💡 Want Cloud Features?
   Email reports, zero setup, no API key needed.
   Run [bold]telos setup[/bold] and choose Cloud mode.
"""
        elif is_pro:
            upgrade_section = """
───────────────────────────────────────────────────────────────────────────
[green]Thank you for supporting Telos![/green] 💙
"""
        else:
            upgrade_section = """
───────────────────────────────────────────────────────────────────────────
[bold]Press U to Upgrade to Pro[/bold] — $3/month, all features unlocked
"""

        settings_text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                 SETTINGS                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

👤 ACCOUNT
  Name:  {name}
  Email: {email}
  {plan_line}
{mode_line}

📧 EMAIL PREFERENCES
  Daily Report: {email_enabled}
  Report Time:  {send_time}

  [ Press E to Edit Email Settings ]

🎯 ANALYSIS GOALS
  Current Focus: {preset_name}

  [ Press G to Change Goals ]

🔒 DATA & PRIVACY
  Database Size:  {size_str}
  Storage:        Local (SQLite)
  Screenshots:    Deleted after analysis
{api_key_line}

🔌 AI INTEGRATIONS (MCP)
  Status: {mcp_status}
  Server: {mcp_path}

  Add to Claude Desktop or Cursor MCP config:
  {{
    "telos": {{
      "command": "python",
      "args": ["{mcp_path}"]
    }}
  }}

  7 tools: get_activity_today, get_sessions, get_daily_summary,
           query_activity, get_recent_captures, get_productivity_trends,
           get_top_apps

  Example: "What did I work on this morning?"

ℹ️  ABOUT
  Version:  0.2.1-beta
  Support:  anuragkurle27@gmail.com
  Feedback: Press F from any screen
{upgrade_section}
Press ESC to go Back
"""
        self.query_one("#settings-content").update(settings_text)

    def action_show_upgrade(self) -> None:
        """Show upgrade modal."""
        from core.backend_client import BackendClient

        trial_manager = TrialManager(self.app.config)
        if trial_manager.is_pro():
            self.app.notify("You're already a Pro user!", severity="information")
            return

        email = self.app.config.get('account', 'email', default="")
        backend_url = self.app.config.get('backend', 'url', default="")
        firebase_api_key = self.app.config.get('firebase', 'api_key', default="")
        backend_client = BackendClient(backend_url, firebase_api_key)

        self.app.push_screen(UpgradeModal(backend_client, email))
