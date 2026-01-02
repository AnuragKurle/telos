"""Summary screen - daily overview with AI insights."""

import json
import asyncio
from datetime import datetime
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, LoadingIndicator
from textual.containers import ScrollableContainer, Vertical

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager
from core.daily_aggregator import DailyAggregator
from core.session_builder import SessionBuilder


class SummaryScreen(Screen):
    """Summary view showing daily insights with AI-generated narrative."""

    BINDINGS = [
        ("r", "regenerate", "Regenerate"),
        ("b", "rebuild_sessions", "Rebuild Sessions"),
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

        # Generate summary on first view
        self.run_worker(self.generate_summary_async())

    def action_regenerate(self) -> None:
        """Regenerate daily summary (force regeneration)."""
        self.run_worker(self.generate_summary_async(force=True))

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
            self.display_summary(summary)
        else:
            self.query_one("#summary-content").update(
                "No data available for today.\n\n"
                "Start using the app and sessions will be created automatically.\n"
                "Then come back to view your daily summary!"
            )

    def display_summary(self, summary: dict) -> None:
        """Format and display summary.

        Args:
            summary: Summary dictionary from database
        """
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
