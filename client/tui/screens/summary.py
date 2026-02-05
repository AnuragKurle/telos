"""Summary screen - daily overview with AI insights."""

import json
import asyncio
from datetime import datetime
from typing import Optional
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, LoadingIndicator
from textual.containers import ScrollableContainer, Vertical

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager
from core.daily_aggregator import DailyAggregator
from core.session_builder import SessionBuilder
from core.trial_manager import TrialManager
from tui.screens.feedback_modal import FeedbackModal


class SummaryScreen(Screen):
    """Summary view showing daily insights with AI-generated narrative."""

    BINDINGS = [
        ("r", "regenerate", "Regenerate"),
        ("b", "rebuild_sessions", "Rebuild Sessions"),
        ("e", "export_json", "Export JSON"),
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        with ScrollableContainer():
            with Vertical(id="summary-container"):
                yield LoadingIndicator(id="summary-loader")
                yield Static("", id="summary-content")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.title = "Daily Summary"
        self.sub_title = "AI-Powered Insights"

        # Hide loader initially
        self.query_one("#summary-loader").display = False

        # Store current summary for feedback
        self.current_summary = None

        # Generate summary on first view
        self.run_worker(self.generate_summary_async())

    def action_regenerate(self) -> None:
        """Regenerate daily summary (force regeneration)."""
        self.run_worker(self.generate_summary_async(force=True))

    def action_export_json(self) -> None:
        """Export today's data as JSON (Pro-only feature)."""
        trial_manager = TrialManager(self.app.config)
        
        if not trial_manager.is_pro() and not trial_manager.is_trial_active():
            self.query_one("#summary-content").update(
                "[bold yellow]Export is a Pro Feature[/bold yellow]\n\n"
                "Upgrade to Pro to export your\n"
                "activity data as JSON.\n\n"
                "[dim]Your data is safely preserved.\n"
                "Press U on Dashboard to upgrade.[/dim]"
            )
            return
        
        if not trial_manager.is_pro():
            self.app.notify(
                "Export is available during your trial. Upgrade to keep it.",
                severity="information",
                timeout=5
            )
        
        self.run_worker(self._export_json_async())
    
    async def _export_json_async(self) -> None:
        """Export data as JSON in background."""
        from pathlib import Path
        
        try:
            config = self.app.config
            db = Database(config.get('storage', 'database_path'))
            
            from core.data_exporter import DataExporter
            exporter = DataExporter(db)
            
            export_dir = Path.home() / "Telos Exports"
            export_dir.mkdir(exist_ok=True)
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"telos_data_{today_str}.json"
            filepath = str(export_dir / filename)
            
            count = await asyncio.to_thread(exporter.export_today_json, filepath)
            
            if count > 0:
                self.query_one("#summary-content").update(
                    f"[bold green]Export Complete[/bold green]\n\n"
                    f"Exported {count} records to:\n"
                    f"[dim]{filepath}[/dim]\n\n"
                    f"[dim]Press R to regenerate summary | ESC to go back[/dim]"
                )
            else:
                self.query_one("#summary-content").update(
                    "[bold yellow]No Data to Export[/bold yellow]\n\n"
                    "No data found for today."
                )
        except Exception as e:
            self.query_one("#summary-content").update(
                f"[bold red]Export Failed[/bold red]\n\n"
                f"Error: {str(e)}"
            )

    def action_rebuild_sessions(self) -> None:
        """Rebuild sessions from scratch for today."""
        self.run_worker(self.rebuild_sessions_async())

    async def rebuild_sessions_async(self) -> None:
        """Rebuild all sessions for today from captures."""
        loader = self.query_one("#summary-loader")
        content = self.query_one("#summary-content")
        loader.display = True
        
        content.update(
            "🔄 [bold yellow]Rebuilding sessions...[/]\n\n"
            "This will:\n"
            "1. Delete existing sessions for today\n"
            "2. Re-group captures into proper sessions\n"
            "3. Enrich sessions with AI analysis\n"
            "4. Generate new daily summary"
        )

        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        analyzer = GeminiAnalyzer(
            config.get('gemini', 'api_key'),
            config.get('gemini', 'model')
        )
        goal_manager = AnalysisGoalManager(db)
        session_builder = SessionBuilder(db, analyzer, goal_manager)
        
        today = datetime.now()

        # Step 1: Reset sessions for today
        content.update(
            "🔄 [bold yellow]Step 1/4: Resetting Data[/]\n\n"
            "Cleaning up old session records..."
        )
        deleted_count = await asyncio.to_thread(db.reset_sessions_for_date, today)
        content.update(
            f"✅ Step 1 Complete: Deleted {deleted_count} old sessions\n"
            "🔄 [bold yellow]Step 2/4: Grouping Activity[/]\n\n"
            "Analyzing timestamps to group activity into sessions..."
        )

        # Step 2: Build new sessions
        session_ids = await asyncio.to_thread(session_builder.build_sessions)
        content.update(
            f"✅ Step 2 Complete: Created {len(session_ids)} new sessions\n"
            "🔄 [bold yellow]Step 3/4: AI Analysis[/]\n\n"
            "Sending sessions to AI for detailed categorization..."
        )

        # Step 3: Enrich sessions (limit to avoid API spam)
        enriched = 0
        max_enrich = min(len(session_ids), 5)  # Limit to 5 sessions
        for i, session_id in enumerate(session_ids[:max_enrich]):
            content.update(
                f"✅ Step 2 Complete: Created {len(session_ids)} new sessions\n"
                "🔄 [bold yellow]Step 3/4: AI Analysis[/]\n\n"
                f"Analyzing session {i+1} of {max_enrich}..."
            )
            try:
                success = await asyncio.to_thread(session_builder.enrich_session, session_id)
                if success:
                    enriched += 1
                    await asyncio.to_thread(db.increment_api_usage)
                    await asyncio.sleep(0.5)  # Small delay
            except Exception as e:
                print(f"Enrichment failed for session {session_id}: {e}")

        content.update(
            f"✅ Step 3 Complete: Enriched {enriched} sessions\n"
            "🔄 [bold yellow]Step 4/4: Generating Summary[/]\n\n"
            "Synthesizing daily insights and narrative..."
        )

        # Step 4: Generate new daily summary
        await self.generate_summary_async(force=True)

    async def generate_summary_async(self, force: bool = False) -> None:
        """Generate and display daily summary asynchronously.

        Args:
            force: If True, regenerate even if summary exists
        """
        # Show loader
        self.query_one("#summary-loader").display = True
        self.query_one("#summary-content").update(
            "Generating daily summary...\n\n"
            "⏳ Analyzing sessions and extracting insights..."
        )

        config = self.app.config
        db = Database(config.get('storage', 'database_path'))
        analyzer = GeminiAnalyzer(
            config.get('gemini', 'api_key'),
            config.get('gemini', 'model')
        )
        goal_manager = AnalysisGoalManager(db)
        aggregator = DailyAggregator(db, analyzer, goal_manager)

        today = datetime.now()

        # Check if summary exists
        summary = await asyncio.to_thread(db.get_daily_summary, today)

        if not summary or force:
            # Generate new summary in background thread
            summary_id = await asyncio.to_thread(aggregator.generate_daily_summary, today, force=force)

            if summary_id:
                await asyncio.to_thread(db.increment_api_usage)
                summary = await asyncio.to_thread(db.get_daily_summary, today)

        # Hide loader
        self.query_one("#summary-loader").display = False

        if summary:
            self.current_summary = summary
            self.display_summary(summary)
            # Show a subtle nudge after summary generation (non-blocking)
            self._show_summary_nudge()
        else:
            self.current_summary = None
            self.query_one("#summary-content").update(
                "No data available for today.\n\n"
                "Start using the app and sessions will be created automatically.\n"
                "Then come back to view your daily summary!"
            )

    def display_summary(self, summary: dict) -> None:
        """Format and display summary.

        Shows full summary for Pro/trial users, truncated for expired trial.

        Args:
            summary: Summary dictionary from database
        """
        # Check subscription status
        trial_manager = TrialManager(self.app.config)
        is_expired = trial_manager.is_trial_expired() and not trial_manager.is_pro()

        # Parse learnings
        learnings_json = summary.get('key_learnings_json', '[]')
        try:
            learnings = json.loads(learnings_json)
        except (json.JSONDecodeError, TypeError):
            learnings = []

        learnings_text = "\n".join(f"  • {l}" for l in learnings) if learnings else "  None identified"

        # Parse focus blocks
        focus_blocks_json = summary.get('focus_blocks_json', '[]')
        try:
            focus_blocks = json.loads(focus_blocks_json)
        except (json.JSONDecodeError, TypeError):
            focus_blocks = []

        if focus_blocks:
            focus_text = "\n".join(
                f"  • {datetime.fromisoformat(b['start']).strftime('%H:%M')} - "
                f"{b['duration_minutes']}min: {b['task'][:40]}"
                for b in focus_blocks
            )
        else:
            focus_text = "  None identified (sessions >30min with focus score ≥0.7)"

        # Format time - use summary values if available, otherwise get from today's stats
        work_sec = summary.get('work_seconds', 0)
        learning_sec = summary.get('learning_seconds', 0)
        browsing_sec = summary.get('browsing_seconds', 0)
        entertainment_sec = summary.get('entertainment_seconds', 0)
        
        # If all values are 0, fall back to get_today_stats (captures-based)
        if work_sec == 0 and learning_sec == 0 and browsing_sec == 0 and entertainment_sec == 0:
            config = self.app.config
            db = Database(config.get('storage', 'database_path'))
            today_stats = db.get_today_stats()
            work_sec = today_stats.get('work', 0)
            learning_sec = today_stats.get('learning', 0)
            browsing_sec = today_stats.get('browsing', 0)
            entertainment_sec = today_stats.get('entertainment', 0)
        
        work_min = work_sec // 60
        learning_min = learning_sec // 60
        browsing_min = browsing_sec // 60
        entertainment_min = entertainment_sec // 60

        # Format productivity score
        productivity = summary.get('productivity_score', 0.0)
        # Convert 0-1 range to 0-100 if needed
        if productivity <= 1.0:
            productivity *= 100
        productivity_bar = self._create_progress_bar(productivity, width=30)

        if is_expired:
            # Truncated view for expired trial users
            # Show the time breakdown (which they can already see on dashboard)
            # but hide narrative, learnings, and focus blocks
            narrative_preview = summary.get('daily_narrative', '')
            # Show first ~100 chars as a teaser
            if len(narrative_preview) > 120:
                narrative_preview = narrative_preview[:120] + "..."
            
            content = f"""
[bold reverse] DAILY SUMMARY - {summary['date']} [/]

[bold cyan]PRODUCTIVITY SCORE[/]
{productivity_bar} [bold]{productivity:.1f}/100[/]

[bold cyan]TIME BREAKDOWN[/]
  💼 [bold white]Work:[/]          {work_min}m
  📚 [bold white]Learning:[/]      {learning_min}m
  🌐 [bold white]Browsing:[/]      {browsing_min}m
  🎮 [bold white]Entertainment:[/] {entertainment_min}m

[bold cyan]ACTIVITY PATTERNS[/]
  Context Switches: [bold white]{summary.get('context_switches', 0)}[/]

[bold cyan]AI-GENERATED NARRATIVE[/]
───────────────────────────────────────────────────────────────────────────
[dim]{narrative_preview}[/dim]

[bold yellow]Upgrade to Pro to see your full AI insights.[/bold yellow]

  Full daily narrative and analysis
  Key learnings and insights
  Focus block identification
  Historical summary access

[dim]Your data is preserved. Upgrade to unlock the complete summary.[/dim]
───────────────────────────────────────────────────────────────────────────
[dim]Press U on Dashboard to upgrade | ESC to go back[/dim]
"""
        else:
            # Full summary for Pro/active trial users
            content = f"""
[bold reverse] DAILY SUMMARY - {summary['date']} [/]

[bold cyan]PRODUCTIVITY SCORE[/]
{productivity_bar} [bold]{productivity:.1f}/100[/]

[bold cyan]TIME BREAKDOWN[/]
  💼 [bold white]Work:[/]          {work_min}m
  📚 [bold white]Learning:[/]      {learning_min}m
  🌐 [bold white]Browsing:[/]      {browsing_min}m
  🎮 [bold white]Entertainment:[/] {entertainment_min}m

[bold cyan]ACTIVITY PATTERNS[/]
  Context Switches: [bold white]{summary.get('context_switches', 0)}[/]

[bold cyan]FOCUS BLOCKS[/] (30+ minutes of sustained focus)
{focus_text}

[bold cyan]KEY LEARNINGS & INSIGHTS[/]
{learnings_text}

[bold cyan]AI-GENERATED NARRATIVE[/]
───────────────────────────────────────────────────────────────────────────
{summary.get('daily_narrative', 'No narrative available.')}

───────────────────────────────────────────────────────────────────────────
[dim]Press R to regenerate summary | B to rebuild sessions | ESC to go back[/dim]
"""
        self.query_one("#summary-content").update(content)

    def _show_summary_nudge(self) -> None:
        """Show a subtle contextual nudge after summary generation."""
        try:
            trial_manager = TrialManager(self.app.config)
            nudge = trial_manager.get_contextual_nudge("summary")
            if nudge:
                self.app.notify(nudge, severity="information", timeout=8)
        except Exception:
            pass

    def action_show_feedback(self) -> None:
        """Show feedback modal for current summary."""
        if not self.current_summary:
            # Show message if no summary available
            self.query_one("#summary-content").update(
                "No summary available to provide feedback on.\n\n"
                "Generate a summary first, then you can provide feedback."
            )
            return

        # Check if backend is enabled (but still show modal even if not - user can type feedback)
        config = self.app.config
        backend_enabled = config.get('backend', 'enabled', default=False)
        
        # Create feedback modal with context
        context = {
            'type': 'summary',
            'screen': 'summary',
            'summary_id': self.current_summary.get('id'),
            'date': self.current_summary.get('date'),
        }
        
        def handle_feedback(result: Optional[str]) -> None:
            """Handle feedback submission."""
            if not result or not result.strip():
                return
            
            if not backend_enabled:
                self.query_one("#summary-content").update(
                    "[bold yellow]Feedback collected but backend not configured.[/bold yellow]\n\n"
                    "Your feedback: " + result[:100] + "\n\n"
                    "Please configure backend in settings to submit feedback."
                )
                return
            
            # Submit feedback asynchronously
            self.run_worker(self._submit_feedback_async(result.strip(), context))

        try:
            # Push modal - this should show immediately
            self.app.push_screen(FeedbackModal(context), handle_feedback)
        except Exception as e:
            # Show error if modal fails to open
            self.query_one("#summary-content").update(
                f"[bold red]Error opening feedback modal: {str(e)}[/bold red]\n\n"
                "Please check console for details."
            )

    async def _submit_feedback_async(self, feedback_text: str, context: dict) -> None:
        """Submit feedback to backend asynchronously."""
        try:
            from core.backend_client import BackendClient
            
            config = self.app.config
            backend_url = config.get('backend', 'url')
            firebase_api_key = config.get('firebase', 'api_key')
            
            backend_client = BackendClient(
                backend_url=backend_url,
                firebase_api_key=firebase_api_key
            )
            
            metadata = {
                'screen': 'summary',
                'app_version': '0.1.0',
            }
            
            result = await asyncio.to_thread(
                backend_client.submit_feedback,
                feedback_type='summary',
                feedback_text=feedback_text,
                context=context,
                metadata=metadata
            )
            
            # Show success message with Slack status
            if result.get('slack_notified', True):  # Default True for backward compat
                self.query_one("#summary-content").update(
                    f"[bold green]✓ Feedback submitted successfully![/bold green]\n\n"
                    f"Thank you for helping improve Telos.\n\n"
                    f"Press ESC to return to summary."
                )
            else:
                self.query_one("#summary-content").update(
                    f"[bold yellow]⚠️ Feedback saved (Slack notification failed)[/bold yellow]\n\n"
                    f"Your feedback is saved to Firestore.\n"
                    f"Dev will check for failed notifications.\n\n"
                    f"Press ESC to return to summary."
                )
            
        except Exception as e:
            # Show error message
            self.query_one("#summary-content").update(
                f"[bold red]✗ Failed to submit feedback[/bold red]\n\n"
                f"Error: {str(e)}\n\n"
                f"Please try again or check your backend connection."
            )

    def _create_progress_bar(self, value: float, width: int = 30) -> str:
        """Create a simple ASCII progress bar.

        Args:
            value: Value (0-100)
            width: Width of the bar in characters

        Returns:
            ASCII progress bar string
        """
        filled = int((value / 100) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
