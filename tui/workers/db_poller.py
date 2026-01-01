"""Database polling worker - refreshes UI with latest stats."""

import asyncio
from core.database import Database


async def db_polling_worker(app):
    """Background task that polls database for stats updates.

    Args:
        app: The Textual application instance with config and state
    """
    # Get database path from config
    config = app.config
    db_path = config.get('storage', 'database_path')
    db = Database(db_path)

    # Refresh rate from config (convert ms to seconds)
    refresh_rate_ms = config.get('display', 'refresh_rate_ms', default=1000)
    refresh_interval = refresh_rate_ms / 1000.0  # Convert to seconds

    try:
        while not app.shutting_down:
            try:
                # Get today's stats
                stats = db.get_today_stats()
                app.total_captures = stats['total_captures']
                app.work_seconds = stats['work']
                app.learning_seconds = stats['learning']
                app.browsing_seconds = stats['browsing']
                app.entertainment_seconds = stats['entertainment']
                app.idle_seconds_total = stats['idle']

                # Get API usage
                api_usage = db.get_api_usage_today()
                app.api_calls_used = api_usage

                # Get recent captures for timeline
                recent = db.get_recent_captures(hours=2, limit=5)
                app.recent_captures = recent

            except Exception as e:
                # Don't crash on DB errors, just log and continue
                # The UI will show cached data
                app.error_message = f"DB polling error: {str(e)}"

            # Wait for next refresh interval
            await asyncio.sleep(refresh_interval)

    except asyncio.CancelledError:
        # Worker was cancelled during shutdown
        pass
