"""Dashboard screen - main view."""

from datetime import datetime
from typing import Optional
from textual.screen import Screen
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static
from textual.binding import Binding

from tui.widgets import StatusBanner, CurrentActivity, CategoryBreakdown, RecentTimeline
from tui.widgets.day_heatmap import DayHeatmap
from tui.widgets.activity_waveform import ActivityWaveform
from tui.screens.feedback_modal import FeedbackModal
from tui.screens.upgrade_modal import UpgradeModal
from core.trial_manager import TrialManager


class DashboardScreen(Screen):
    """Main dashboard screen showing live activity tracking."""

    # View mode: "60min" (waveform) or "day" (full day heatmap)
    graph_mode = reactive("day")

    BINDINGS = [
        Binding("v", "toggle_graph_mode", "", show=False),  # Hidden from footer (V for View)
        Binding("space", "toggle_expanded", "", show=False),  # Hidden from footer
        Binding("left", "previous_day", "", show=False),  # Hidden from footer
        Binding("right", "next_day", "", show=False),  # Hidden from footer
        Binding("u", "show_upgrade", "Upgrade to Pro", show=True),
        # Note: T for Timeline is inherited from app-level, lowercase 't' here is for "Today"
        Binding("shift+t", "jump_to_today", "", show=False),  # Shift+T for "Today" to avoid conflict
    ]

    CSS = """
    DashboardScreen {
        layout: vertical;
        overflow-y: hidden;
        background: $surface;
    }

    #status-banner {
        dock: top;
        height: 1;
        background: $surface;
        color: $text-muted;
        content-align: center middle;
    }

    #main-container {
        padding: 1;
    }

    #current-activity {
        height: 3;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    #greeting {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        padding: 1 2;
        background: $surface-lighten-1;
        border-bottom: wide $accent;
    }
    
    #current-activity-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        padding: 0;
        margin-bottom: 0;
    }

    #current-activity-display {
        content-align: left middle;
        text-style: bold;
        color: $text;
        height: 2;
    }

    #middle-section {
        height: 14;
        margin-bottom: 1;
    }

    #category-breakdown {
        width: 40%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 1;
        margin-right: 1;
    }

    DayHeatmap {
        width: 60%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
    }
    
    ActivityWaveform {
        width: 60%;
        height: 100%;
        border: solid $secondary;
        background: $panel;
        padding: 0 1;
    }
    
    .hidden {
        display: none;
    }

    #breakdown-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        padding-bottom: 1;
        margin-bottom: 1;
        text-align: center;
    }

    #breakdown-content {
        color: $text;
    }

    #recent-timeline {
        height: 1fr;
        border: solid $secondary;
        background: $panel;
        padding: 1;
    }

    #timeline-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        padding-bottom: 1;
        margin-bottom: 1;
    }

    #timeline-content {
        color: $text;
    }

    #ai-chat-hint {
        dock: bottom;
        height: auto;
        background: $boost;
        color: $success;
        padding: 0 1;
        text-align: center;
        border-top: solid $success;
    }
    
    #help-footer {
        dock: bottom;
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for dashboard."""
        yield Header(show_clock=True)
        yield StatusBanner(id="status-banner")
        
        with Container(id="main-container"):
            yield Static(self.get_greeting(), id="greeting")
            yield CurrentActivity(id="current-activity")
            
            with Horizontal(id="middle-section"):
                yield CategoryBreakdown(id="category-breakdown")
                yield ActivityWaveform(id="waveform-graph")
                yield DayHeatmap(id="day-heatmap")
            
            yield RecentTimeline(id="recent-timeline")

        yield Static("✨ Press 'A' for AI Chat", id="ai-chat-hint")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._update_graph_visibility()
        # Update greeting every minute for time-accurate greetings
        self.set_interval(60.0, self.update_greeting)
        # Hide upgrade binding if user is Pro
        self._update_upgrade_binding()
        # Show contextual nudge if applicable (delayed so it doesn't feel intrusive)
        self.set_timer(5.0, self._show_contextual_nudge)

    def watch_graph_mode(self, old_mode: str, new_mode: str) -> None:
        """Update visibility when graph mode changes."""
        self._update_graph_visibility()

    def _update_graph_visibility(self) -> None:
        """Show/hide graphs based on current mode."""
        try:
            waveform = self.query_one("#waveform-graph", ActivityWaveform)
            day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
            
            if self.graph_mode == "60min":
                waveform.remove_class("hidden")
                day_heatmap.add_class("hidden")
            else:  # "day"
                waveform.add_class("hidden")
                day_heatmap.remove_class("hidden")
        except:
            pass  # Widgets not yet mounted

    def action_toggle_graph_mode(self) -> None:
        """Toggle between 60-minute waveform and full day heatmap."""
        self.graph_mode = "day" if self.graph_mode == "60min" else "60min"

    def action_show_feedback(self) -> None:
        """Show feedback modal for current activity."""
        try:
            # Get current activity from app state
            context = {
                'type': 'capture',
                'screen': 'dashboard',
                'app': getattr(self.app, 'current_app', None) or 'Unknown',
                'task': getattr(self.app, 'current_task', None) or 'No activity',
                'category': getattr(self.app, 'current_category', None) or 'idle',
            }

            def handle_feedback(result: Optional[str]) -> None:
                """Handle feedback submission."""
                if not result or not result.strip():
                    return
                
                # Check if backend is enabled
                config = self.app.config
                backend_enabled = config.get('backend', 'enabled', default=False)
                
                if not backend_enabled:
                    self.app.notify(
                        "Feedback collected but backend not configured. Configure in settings.",
                        severity="warning",
                        timeout=5
                    )
                    return
                
                # Submit feedback asynchronously
                try:
                    self.run_worker(self._submit_feedback_async(result.strip(), context))
                except Exception as e:
                    self.app.notify(
                        f"Error submitting feedback: {str(e)}",
                        severity="error",
                        timeout=5
                    )

            # Push modal - this should show immediately
            self.app.push_screen(FeedbackModal(context), handle_feedback)
        except Exception as e:
            # Show error notification
            import traceback
            self.app.notify(
                f"Error opening feedback modal: {str(e)}",
                severity="error",
                timeout=5
            )
            print(f"Feedback modal error: {traceback.format_exc()}")

    async def _submit_feedback_async(self, feedback_text: str, context: dict) -> None:
        """Submit feedback to backend asynchronously."""
        try:
            import asyncio
            from core.backend_client import BackendClient
            
            config = self.app.config
            backend_url = config.get('backend', 'url')
            firebase_api_key = config.get('firebase', 'api_key')
            
            backend_client = BackendClient(
                backend_url=backend_url,
                firebase_api_key=firebase_api_key
            )
            
            metadata = {
                'screen': 'dashboard',
                'app_version': '0.1.0',
            }
            
            result = await asyncio.to_thread(
                backend_client.submit_feedback,
                feedback_type='capture',
                feedback_text=feedback_text,
                context=context,
                metadata=metadata
            )
            
            # Show success notification with Slack status
            if result.get('slack_notified', True):  # Default True for backward compat
                self.app.notify(
                    "✓ Feedback submitted successfully!",
                    severity="success",
                    timeout=3
                )
            else:
                self.app.notify(
                    "⚠️ Feedback saved but Slack notification failed. Dev will check Firestore.",
                    severity="warning",
                    timeout=5
                )
            
        except Exception as e:
            # Show error notification
            self.app.notify(
                f"✗ Failed to submit feedback: {str(e)}",
                severity="error",
                timeout=5
            )

    def action_toggle_expanded(self) -> None:
        """Toggle expanded view (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.toggle_expanded()
            except:
                pass

    def action_previous_day(self) -> None:
        """Go to previous day (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.previous_day()
            except:
                pass

    def action_next_day(self) -> None:
        """Go to next day (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.next_day()
            except:
                pass

    def action_jump_to_today(self) -> None:
        """Jump to today (only works in day mode)."""
        if self.graph_mode == "day":
            try:
                day_heatmap = self.query_one("#day-heatmap", DayHeatmap)
                day_heatmap.selected_date = datetime.now().date()
            except:
                pass

    def _show_contextual_nudge(self) -> None:
        """Show a subtle contextual nudge if conditions are met."""
        try:
            trial_manager = TrialManager(self.app.config)
            
            # Check for session milestone nudge
            session_count = getattr(self.app, 'sessions_today', 0)
            nudge = trial_manager.get_contextual_nudge("milestone", session_count=session_count)
            if nudge:
                self.app.notify(nudge, severity="information", timeout=8)
                return
            
            # Check for day-based dashboard nudge
            nudge = trial_manager.get_contextual_nudge("dashboard")
            if nudge:
                self.app.notify(nudge, severity="information", timeout=8)
        except Exception:
            pass

    def _update_upgrade_binding(self) -> None:
        """Refresh the footer to reflect binding changes based on Pro status."""
        try:
            footer = self.query_one(Footer)
            footer.refresh()
        except Exception:
            pass

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Conditionally disable/hide actions based on subscription status."""
        if action == "show_upgrade":
            trial_manager = TrialManager(self.app.config)
            if trial_manager.is_pro():
                return None  # Hide from footer when Pro
        return True

    def action_show_upgrade(self) -> None:
        """Show upgrade modal."""
        # Check if already pro
        trial_manager = TrialManager(self.app.config)
        if trial_manager.is_pro():
            self.app.notify("You're already a Pro user!", severity="information")
            return

        # Get email from config
        email = self.app.config.get('account', 'email', default="")
        
        # Initialize backend client
        from core.backend_client import BackendClient
        backend_url = self.app.config.get('backend', 'url', default="")
        firebase_api_key = self.app.config.get('firebase', 'api_key', default="")
        backend_client = BackendClient(backend_url, firebase_api_key)
        
        self.app.push_screen(UpgradeModal(backend_client, email))

    def update_greeting(self) -> None:
        """Update the greeting text based on current time."""
        try:
            greeting_widget = self.query_one("#greeting", Static)
            greeting_widget.update(self.get_greeting())
        except:
            pass  # Widget might not be mounted yet
    
    def get_greeting(self) -> str:
        """Get time-based creative greeting."""
        hour = datetime.now().hour
        config = self.app.config
        name = config.get('account', 'name', default='User')
        
        if 0 <= hour < 5:
            period = "Hello, Night Owl 🦉"
        elif 5 <= hour < 12:
            period = "Good morning ☀️"
        elif 12 <= hour < 17:
            period = "Good afternoon 👋"
        elif 17 <= hour < 21:
            period = "Good evening 🧑‍💻"
        else:  # 21:00 (9 PM) onwards
            period = "Working late 🌙"
            
        return f"{period}, {name}"
