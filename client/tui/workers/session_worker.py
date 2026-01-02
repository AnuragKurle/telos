"""Async session worker - runs session processing in background."""

import asyncio
from datetime import datetime
from pathlib import Path

from core.database import Database
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager
from core.session_builder import SessionBuilder


async def session_worker_task(app):
    """Background task for session building and enrichment.

    Triggers:
    - Every 2 hours while active
    - After 5 minutes of idle time

    Args:
        app: The Textual application instance
    """
    # Get configuration
    config = app.config
    db_path = config.get('storage', 'database_path')
    api_key = config.get('gemini', 'api_key')
    model = config.get('gemini', 'model')

    # Get intelligence configuration (with defaults)
    check_interval_seconds = config.get('intelligence', 'check_interval_seconds', default=60)
    max_enrichment_per_trigger = config.get('intelligence', 'max_enrichment_per_trigger', default=3)

    # Initialize Phase 3 components
    db = Database(db_path)
    analyzer = GeminiAnalyzer(api_key, model)
    goal_manager = AnalysisGoalManager(db)
    session_builder = SessionBuilder(db, analyzer, goal_manager)

    try:
        while not app.shutting_down:
            try:
                # Check if processing should trigger (run in thread to avoid blocking)
                should_process = await asyncio.to_thread(session_builder.should_trigger_processing)

                if should_process:
                    # Build sessions from unprocessed captures
                    session_ids = await asyncio.to_thread(session_builder.build_sessions)

                    # Update total session count for today
                    today_sessions = await asyncio.to_thread(db.get_sessions_for_date, datetime.now())
                    app.sessions_today = len(today_sessions)

                    if session_ids:
                        # Enrich sessions (limited to avoid API spam)
                        # Only enrich up to max_enrichment_per_trigger sessions per trigger
                        for session_id in session_ids[:max_enrichment_per_trigger]:
                            try:
                                success = await asyncio.to_thread(
                                    session_builder.enrich_session,
                                    session_id
                                )

                                if success:
                                    # Increment API usage counter
                                    await asyncio.to_thread(db.increment_api_usage)

                                    # Small delay for rate limiting (analyzer already has 4s delay)
                                    await asyncio.sleep(1)

                            except Exception as e:
                                # Log error but continue with other sessions
                                print(f"Session enrichment error for session {session_id}: {e}")
                                continue

            except Exception as e:
                # Log error but don't crash worker
                print(f"Session worker error: {e}")

            # Wait before next check
            await asyncio.sleep(check_interval_seconds)

    except asyncio.CancelledError:
        # Handle graceful shutdown
        pass
