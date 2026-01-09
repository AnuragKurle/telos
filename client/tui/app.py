"""Main Textual TUI application."""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.app import App, ComposeResult
from textual.reactive import reactive

from utils.config_manager import ConfigManager
from tui.workers import capture_worker_task, db_polling_worker
from tui.workers.session_worker import session_worker_task
from tui.screens import (
    DashboardScreen, TimelineScreen, SummaryScreen, SettingsScreen, ChatScreen,
    HelpScreen, UpgradeScreen
)
from tui.widgets import TrialBanner
from core.trial_manager import TrialManager


class TelosApp(App):
    """Main TUI application for Telos."""

    # Reactive properties - state that auto-updates UI
    # Capture loop status
    loop_status: reactive[str] = reactive("stopped")
    idle_seconds: reactive[int] = reactive(0)
    error_message: reactive[str] = reactive("")

    # Current activity
    current_category: reactive[str] = reactive("idle")
    current_emoji: reactive[str] = reactive("💤")
    current_color: reactive[str] = reactive("#95a5a6")
    current_app: reactive[str] = reactive("None")
    current_task: reactive[str] = reactive("No activity")
    last_analysis_source: reactive[str] = reactive("none")  # backend, local, none
    activity_start_time: reactive[Optional[datetime]] = reactive(None)

    # Today's stats (in seconds)
    total_captures: reactive[int] = reactive(0)
    work_seconds: reactive[int] = reactive(0)
    learning_seconds: reactive[int] = reactive(0)
    browsing_seconds: reactive[int] = reactive(0)
    entertainment_seconds: reactive[int] = reactive(0)
    idle_seconds_total: reactive[int] = reactive(0)

    # API quota
    api_calls_used: reactive[int] = reactive(0)

    # Styling for the application
    CSS = """
    #session-table {
        width: 60%;
        height: 100%;
    }
    #detail-panel {
        width: 40%;
        height: 100%;
        border-left: solid #333;
        padding: 1 2;
        background: #1a1a1a;
    }
    #detail-title {
        color: #ffaa00;
        text-style: bold;
        margin-bottom: 1;
        border-bottom: solid #333;
    }
    #detail-content {
        color: #ddd;
        overflow-y: scroll;
    }
    """

    # Recent captures (list of dicts)
    recent_captures: reactive[List[Dict[str, Any]]] = reactive([])

    # Phase 3: Session tracking
    sessions_today: reactive[int] = reactive(0)
    daily_productivity_score: reactive[float] = reactive(0.0)

    BINDINGS = [
        ("d", "show_dashboard", "Dashboard"),
        ("t", "show_timeline", "Timeline"),
        ("s", "show_summary", "Summary"),
        ("c", "show_settings", "Settings"),
        ("a", "show_chat", "AI Chat"),
        ("h", "show_help", "Help"),
        ("q", "quit", "Quit"),
        ("f", "show_feedback", "Feedback"),
    ]

    def __init__(self, config: ConfigManager):
        """Initialize the TUI application.

        Args:
            config: Configuration manager instance
        """
        super().__init__()
        self.config = config

        # Store max API calls as regular attribute (not reactive)
        self.api_calls_max = config.get('capture', 'max_daily_requests', default=1500)

        # Worker shutdown flag and task handles
        self.shutting_down = False
        self.capture_worker = None
        self.db_worker = None
        self.session_worker = None
        self.email_worker_task = None
        
        # Trial manager
        self.trial_manager = TrialManager(config, trial_duration_days=7)
        self.trial_banner = None

    def on_mount(self) -> None:
        """Called when app is mounted - start background workers."""
        self.title = "Telos"
        self.sub_title = "Live Activity Dashboard"

        # Push the Dashboard screen
        self.push_screen(DashboardScreen())
        
        # Check for upgrade prompts
        prompt_type = self.trial_manager.should_show_upgrade_prompt()
        if prompt_type:
            self.set_timer(2, lambda: self.push_screen(UpgradeScreen(self.trial_manager)))

        # Start background workers
        self.capture_worker = asyncio.create_task(capture_worker_task(self))
        self.db_worker = asyncio.create_task(db_polling_worker(self))
        self.session_worker = asyncio.create_task(session_worker_task(self))
        
        # Start email worker if enabled
        email_enabled = self.config.get('email', 'enabled', default=False)
        if email_enabled:
            from tui.workers.email_worker import EmailWorker
            from core.email_reporter import EmailReporter
            from core.database import Database
            from core.analyzer import GeminiAnalyzer
            from core.goal_manager import AnalysisGoalManager
            from core.daily_aggregator import DailyAggregator
            
            # Initialize components for email worker
            db = Database(self.config.get('storage', 'database_path'))
            analyzer = GeminiAnalyzer(
                self.config.get('gemini', 'api_key'),
                self.config.get('gemini', 'model'),
                user_email=self.config.get('account', 'email', default=None)
            )
            goal_manager = AnalysisGoalManager(db)
            daily_aggregator = DailyAggregator(db, analyzer, goal_manager)
            email_reporter = EmailReporter(
                smtp_host=self.config.get('email', 'smtp_host'),
                smtp_port=self.config.get('email', 'smtp_port'),
                sender_email=self.config.get('email', 'sender_email'),
                sender_password=self.config.get('email', 'sender_password'),
                recipient_email=self.config.get('email', 'recipient_email')
            )
            
            email_worker = EmailWorker(
                db=db,
                daily_aggregator=daily_aggregator,
                email_reporter=email_reporter,
                send_time=self.config.get('email', 'send_time', default='21:00')
            )
            self.email_worker_task = asyncio.create_task(email_worker.start())

    async def on_unmount(self) -> None:
        """Called when app is being unmounted (shutdown)."""
        self.shutting_down = True

        # Cancel workers if they're still running
        if self.capture_worker and not self.capture_worker.done():
            self.capture_worker.cancel()
            try:
                await self.capture_worker
            except asyncio.CancelledError:
                pass

        if self.db_worker and not self.db_worker.done():
            self.db_worker.cancel()
            try:
                await self.db_worker
            except asyncio.CancelledError:
                pass

        if self.session_worker and not self.session_worker.done():
            self.session_worker.cancel()
            try:
                await self.session_worker
            except asyncio.CancelledError:
                pass
        
        if self.email_worker_task and not self.email_worker_task.done():
            self.email_worker_task.cancel()
            try:
                await self.email_worker_task
            except asyncio.CancelledError:
                pass

    def action_show_dashboard(self) -> None:
        """Show the dashboard screen."""
        self.switch_screen(DashboardScreen())

    def action_show_timeline(self) -> None:
        """Show the timeline screen."""
        self.push_screen(TimelineScreen())

    def action_show_summary(self) -> None:
        """Show the summary screen."""
        self.push_screen(SummaryScreen())

    def action_show_settings(self) -> None:
        """Show the settings screen."""
        self.push_screen(SettingsScreen())

    def action_show_chat(self) -> None:
        """Show the AI chat screen."""
        self.push_screen(ChatScreen())
    
    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())
    
    def action_show_feedback(self) -> None:
        """Show feedback modal from any screen."""
        from tui.screens.feedback_modal import FeedbackModal
        from typing import Optional
        
        # Get current screen for context
        current_screen = self.screen
        screen_name = current_screen.__class__.__name__.replace('Screen', '').lower()
        
        context = {
            'type': 'general',
            'screen': screen_name,
        }
        
        def handle_feedback(result: Optional[str]) -> None:
            """Handle feedback submission."""
            if not result or not result.strip():
                return
            
            # Check if backend is enabled
            backend_enabled = self.config.get('backend', 'enabled', default=False)
            
            if not backend_enabled:
                self.notify(
                    "Feedback collected but backend not configured.",
                    severity="warning",
                    timeout=5
                )
                return
            
            # Submit feedback - delegate to current screen if it has the method
            if hasattr(current_screen, '_submit_feedback_async'):
                current_screen.run_worker(current_screen._submit_feedback_async(result.strip(), context))
            else:
                self.notify(
                    "Feedback submitted (no handler on this screen)",
                    severity="information",
                    timeout=3
                )
        
        try:
            self.push_screen(FeedbackModal(context), handle_feedback)
        except Exception as e:
            self.notify(
                f"Error opening feedback modal: {str(e)}",
                severity="error",
                timeout=5
            )
