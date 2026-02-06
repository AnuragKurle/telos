"""Settings screen - clean, structured configuration view."""

from pathlib import Path
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer, Vertical, Horizontal
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
        Binding("r", "show_referral", "Referral Link"),
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "app.quit", "Quit"),
    ]

    CSS = """
    SettingsScreen {
        layout: vertical;
        background: $surface;
    }

    #settings-scroll {
        scrollbar-size: 1 1;
    }

    #settings-body {
        padding: 1 3;
        max-width: 80;
    }

    .section-title {
        color: $accent;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    .section-card {
        background: $panel;
        border: tall $surface-lighten-2;
        padding: 1 2;
        margin-bottom: 1;
    }

    .section-content {
        color: $text;
    }

    .section-hint {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
    }

    .divider {
        color: $surface-lighten-2;
        margin: 0;
    }

    #upgrade-banner {
        background: $panel;
        border: wide $accent;
        padding: 1 2;
        margin-top: 1;
        margin-bottom: 1;
        text-align: center;
    }

    #footer-note {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(id="settings-scroll"):
            with Vertical(id="settings-body"):
                # Account
                yield Static("ACCOUNT", classes="section-title")
                yield Static("", id="account-card", classes="section-card")

                # Email
                yield Static("EMAIL REPORTS", classes="section-title")
                yield Static("", id="email-card", classes="section-card")
                yield Static("  [dim]Press[/dim] [bold]E[/bold] [dim]to edit[/dim]", classes="section-hint")

                # Goals
                yield Static("ANALYSIS GOALS", classes="section-title")
                yield Static("", id="goals-card", classes="section-card")
                yield Static("  [dim]Press[/dim] [bold]G[/bold] [dim]to change[/dim]", classes="section-hint")

                # Data
                yield Static("DATA & PRIVACY", classes="section-title")
                yield Static("", id="data-card", classes="section-card")

                # MCP
                yield Static("AI INTEGRATIONS", classes="section-title")
                yield Static("", id="mcp-card", classes="section-card")

                # Referral
                yield Static("INVITE FRIENDS", classes="section-title")
                yield Static("", id="referral-card", classes="section-card")
                yield Static("  [dim]Press[/dim] [bold]R[/bold] [dim]to copy your link[/dim]", classes="section-hint")

                # Upgrade / About
                yield Static("", id="upgrade-banner")
                yield Static("", id="footer-note")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Settings"
        self.sub_title = "Configuration"
        self.refresh_display()

    def action_edit_goals(self) -> None:
        def on_goals_saved():
            self.refresh_display()
            self.app.notify("Goals updated!", severity="information", timeout=3)
        self.app.push_screen(GoalEditorModal(self.app.config, on_save=on_goals_saved))

    def action_edit_email(self) -> None:
        def on_email_saved():
            self.refresh_display()
            self.app.notify("Email settings saved!", severity="information", timeout=3)
        self.app.push_screen(EmailSettingsModal(self.app.config, on_save=on_email_saved))

    def action_show_referral(self) -> None:
        """Fetch and display referral code, copy to clipboard."""
        from core.backend_client import BackendClient, BackendError

        try:
            backend_url = self.app.config.get('backend', 'url', default="")
            firebase_api_key = self.app.config.get('firebase', 'api_key', default="")

            if not backend_url or not firebase_api_key:
                self.app.notify("Backend not configured", severity="error")
                return

            backend_client = BackendClient(backend_url, firebase_api_key)
            result = backend_client.get_referral_code()

            if result and result.get('referralCode'):
                code = result['referralCode']
                link = result['shareLink']
                stats = result.get('stats', {})

                referred = stats.get('referralCount', 0)
                earned = stats.get('proCreditsEarned', 0)
                stats_line = f"Friends signed up: {referred} | Pro months earned: {earned}"

                try:
                    import pyperclip
                    pyperclip.copy(link)
                    self.app.notify(
                        f"Copied to clipboard — ready to share!\n"
                        f"{link}\n"
                        f"Each friend who signs up = 1 month of Pro free for you.\n"
                        f"{stats_line}",
                        severity="information",
                        timeout=10
                    )
                except Exception:
                    self.app.notify(
                        f"Your referral link (copy manually):\n"
                        f"{link}\n"
                        f"Each friend who signs up = 1 month of Pro free for you.\n"
                        f"{stats_line}",
                        severity="information",
                        timeout=12
                    )
            else:
                self.app.notify("Could not generate referral code", severity="error")

        except BackendError as e:
            self.app.notify(f"Error: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Error fetching referral code: {e}", severity="error")

    def action_show_upgrade(self) -> None:
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

    def refresh_display(self) -> None:
        """Refresh all settings cards."""
        config = self.app.config
        trial_manager = TrialManager(config)

        name = config.get('account', 'name', default='User')
        email = config.get('account', 'email', default='Not set')
        is_pro = trial_manager.is_pro()
        is_byok = trial_manager.is_byok_mode()

        # ── Account card ──────────────────────────────────────────
        if is_byok:
            plan_tag = "[green]Local Mode[/green]  (free, unlimited)"
            mode_tag = "Bring Your Own Key"
        elif is_pro:
            plan_tag = "[green]Pro[/green]"
            mode_tag = "Cloud"
        else:
            try:
                days = trial_manager.get_days_remaining()
                if days > 0:
                    plan_tag = f"[yellow]Trial[/yellow]  ({days} days left)"
                else:
                    plan_tag = "[red]Trial Expired[/red]"
            except Exception:
                plan_tag = "[yellow]Trial[/yellow]"
            mode_tag = "Cloud"

        api_line = ""
        if is_byok:
            raw_key = config.get('gemini', 'api_key', default='')
            if raw_key and raw_key not in ('', 'YOUR_GEMINI_API_KEY_HERE', 'BACKEND_MODE_NO_KEY_NEEDED'):
                masked = raw_key[:6] + "..." + raw_key[-4:] if len(raw_key) > 10 else "****"
                api_line = f"\n  API Key    {masked}"
            else:
                api_line = "\n  API Key    [yellow]Not set[/yellow]"

        self.query_one("#account-card").update(
            f"  Name       {name}\n"
            f"  Email      {email}\n"
            f"  Plan       {plan_tag}\n"
            f"  Mode       {mode_tag}{api_line}"
        )

        # ── Email card ────────────────────────────────────────────
        send_time = config.get('email', 'send_time', default='21:00')
        enabled = config.get('email', 'enabled', default=False)
        status = "[green]Enabled[/green]" if enabled else "[dim]Disabled[/dim]"

        self.query_one("#email-card").update(
            f"  Status     {status}\n"
            f"  Send at    {send_time}"
        )

        # ── Goals card ────────────────────────────────────────────
        db = Database(config.get('storage', 'database_path'))
        goal_manager = AnalysisGoalManager(db)
        active_goals = goal_manager.get_active_goals()
        preset = active_goals.get('preset', 'productivity')
        preset_info = AnalysisGoalManager.PRESET_GOALS.get(preset, {})
        preset_name = preset_info.get('name', preset)

        self.query_one("#goals-card").update(
            f"  Focus      {preset_name}"
        )

        # ── Data card ─────────────────────────────────────────────
        db_path = config.get('storage', 'database_path')
        try:
            db_size = Path(db_path).stat().st_size
            size_str = f"{db_size / 1_000_000:.1f} MB" if db_size > 1_000_000 else f"{db_size / 1_000:.0f} KB"
        except Exception:
            size_str = "Unknown"

        self.query_one("#data-card").update(
            f"  Database   {size_str}\n"
            f"  Storage    Local (SQLite)\n"
            f"  Privacy    Screenshots deleted after analysis"
        )

        # ── MCP card ──────────────────────────────────────────────
        mcp_path = Path(__file__).resolve().parents[2] / "mcp_server.py"
        if mcp_path.exists():
            path_str = str(mcp_path).replace("\\", "/")
            self.query_one("#mcp-card").update(
                f"  MCP Server   [green]Available[/green]\n"
                f"  Path         {path_str}\n"
                f"  Tools        7 (activity, sessions, summary, query, captures, trends, apps)"
            )
        else:
            self.query_one("#mcp-card").update(
                f"  MCP Server   [yellow]Not found[/yellow]"
            )

        # ── Referral card ─────────────────────────────────────────
        self.query_one("#referral-card").update(
            f"  Share Telos with friends, earn [bold]1 month of Pro[/bold] per signup.\n"
            f"  Up to 12 months free — that's a full year."
        )

        # ── Upgrade / About ───────────────────────────────────────
        if is_byok:
            self.query_one("#upgrade-banner").update(
                "Want cloud features? Email reports, zero setup, no API key.\n"
                "Run [bold]telos setup[/bold] and choose Cloud mode."
            )
        elif is_pro:
            self.query_one("#upgrade-banner").update(
                "[green]Thank you for supporting Telos.[/green]"
            )
        else:
            self.query_one("#upgrade-banner").update(
                "[bold]Press U to upgrade to Pro[/bold]  —  $3/month, all features"
            )

        self.query_one("#footer-note").update(
            "v0.2.1-beta  |  support: anuragkurle27@gmail.com  |  Press F for feedback"
        )
