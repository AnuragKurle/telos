"""Query engine for searching and retrieving user activity data."""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.database import Database


class QueryEngine:
    """Searches through captures, sessions, and summaries to answer user queries."""

    def __init__(self, db: Database):
        """Initialize query engine.

        Args:
            db: Database instance
        """
        self.db = db

    def get_context_for_query(self, query: str, days_back: int = 7) -> Dict[str, Any]:
        """Get relevant context from the database for a user query.

        Args:
            query: User's question/request
            days_back: How many days back to search (default 7)

        Returns:
            Dictionary with structured context for the AI
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        # Get recent captures with detailed context
        captures = self._get_recent_captures_with_context(cutoff_date)

        # Get sessions with summaries
        sessions = self._get_recent_sessions(cutoff_date)

        # Get daily summaries
        summaries = self._get_recent_summaries(days_back)

        # Build context object
        context = {
            'query': query,
            'time_range': f'Last {days_back} days',
            'total_captures': len(captures),
            'total_sessions': len(sessions),
            'captures': captures[:50],  # Limit to prevent context overflow
            'sessions': sessions,
            'daily_summaries': summaries,
            'metadata': self._generate_metadata(captures, sessions)
        }

        return context

    def _get_recent_captures_with_context(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Get recent captures with their detailed context.

        Args:
            cutoff_date: Only get captures after this date

        Returns:
            List of capture dictionaries with parsed detailed_context
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, category, category_emoji, app_name, task,
                       confidence, detailed_context
                FROM captures
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 200
            ''', (cutoff_date,))

            captures = []
            for row in cursor.fetchall():
                capture = dict(row)

                # Parse detailed_context JSON
                if capture.get('detailed_context'):
                    try:
                        capture['detailed_context'] = json.loads(capture['detailed_context'])
                    except (json.JSONDecodeError, TypeError):
                        capture['detailed_context'] = {}

                captures.append(capture)

            return captures

    def _get_recent_sessions(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Get recent sessions with enrichment data.

        Args:
            cutoff_date: Only get sessions after this date

        Returns:
            List of session dictionaries
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, start_time, end_time, duration_seconds, category,
                       primary_task, apps_used, detailed_summary, learnings, focus_score
                FROM sessions
                WHERE start_time >= ?
                ORDER BY start_time DESC
                LIMIT 50
            ''', (cutoff_date,))

            return [dict(row) for row in cursor.fetchall()]

    def _get_recent_summaries(self, days_back: int) -> List[Dict[str, Any]]:
        """Get daily summaries for recent days.

        Args:
            days_back: Number of days to retrieve

        Returns:
            List of daily summary dictionaries
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, work_seconds, learning_seconds, browsing_seconds,
                       entertainment_seconds, productivity_score, context_switches,
                       key_learnings_json, focus_blocks_json, daily_narrative
                FROM daily_summaries
                ORDER BY date DESC
                LIMIT ?
            ''', (days_back,))

            summaries = []
            for row in cursor.fetchall():
                summary = dict(row)

                # Parse JSON fields
                if summary.get('key_learnings_json'):
                    try:
                        summary['key_learnings'] = json.loads(summary['key_learnings_json'])
                    except (json.JSONDecodeError, TypeError):
                        summary['key_learnings'] = []

                if summary.get('focus_blocks_json'):
                    try:
                        summary['focus_blocks'] = json.loads(summary['focus_blocks_json'])
                    except (json.JSONDecodeError, TypeError):
                        summary['focus_blocks'] = []

                summaries.append(summary)

            return summaries

    def _generate_metadata(self, captures: List[Dict], sessions: List[Dict]) -> Dict[str, Any]:
        """Generate metadata about the user's activity.

        Args:
            captures: List of captures
            sessions: List of sessions

        Returns:
            Metadata dictionary
        """
        # Count categories
        category_counts = {}
        for capture in captures:
            cat = capture.get('category', 'unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Count apps
        app_counts = {}
        for capture in captures:
            app = capture.get('app_name', 'unknown')
            app_counts[app] = app_counts.get(app, 0) + 1

        # Get top apps and categories
        top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'top_apps': [{'app': app, 'count': count} for app, count in top_apps],
            'top_categories': [{'category': cat, 'count': count} for cat, count in top_categories],
            'total_sessions': len(sessions),
            'avg_focus_score': sum(s.get('focus_score', 0) for s in sessions if s.get('focus_score')) / len(sessions) if sessions else 0
        }

    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context into a readable string for the LLM.

        Args:
            context: Context dictionary from get_context_for_query

        Returns:
            Formatted string for LLM prompt
        """
        lines = [
            f"# User Activity Data ({context['time_range']})",
            "",
            f"Total captures: {context['total_captures']}",
            f"Total sessions: {context['total_sessions']}",
            "",
        ]

        # Add metadata
        meta = context.get('metadata', {})
        if meta.get('top_apps'):
            lines.append("## Most Used Apps")
            for item in meta['top_apps']:
                lines.append(f"  - {item['app']}: {item['count']} captures")
            lines.append("")

        if meta.get('top_categories'):
            lines.append("## Activity Categories")
            for item in meta['top_categories']:
                lines.append(f"  - {item['category']}: {item['count']} captures")
            lines.append("")

        # Add daily summaries
        summaries = context.get('daily_summaries', [])
        if summaries:
            lines.append("## Daily Summaries")
            for summary in summaries:
                lines.append(f"\n### {summary['date']}")
                lines.append(f"Productivity Score: {summary.get('productivity_score', 0):.1f}/100")

                if summary.get('daily_narrative'):
                    lines.append(f"Summary: {summary['daily_narrative']}")

                if summary.get('key_learnings'):
                    lines.append("Key Learnings:")
                    for learning in summary['key_learnings']:
                        lines.append(f"  - {learning}")
            lines.append("")

        # Add sessions
        sessions = context.get('sessions', [])
        if sessions:
            lines.append("## Recent Sessions")
            for session in sessions[:10]:  # Limit to 10 most recent
                duration_min = session.get('duration_seconds', 0) // 60
                start_time = session.get('start_time', '')
                if isinstance(start_time, str):
                    try:
                        start_dt = datetime.fromisoformat(start_time)
                        start_str = start_dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        start_str = start_time
                else:
                    start_str = str(start_time)

                lines.append(f"\n{start_str} - {duration_min}min - {session.get('category', 'unknown')}")
                lines.append(f"  Task: {session.get('primary_task', 'N/A')}")
                lines.append(f"  Apps: {session.get('apps_used', 'N/A')}")

                if session.get('detailed_summary'):
                    lines.append(f"  Summary: {session['detailed_summary']}")

                if session.get('focus_score') is not None:
                    lines.append(f"  Focus Score: {session['focus_score']:.2f}")
            lines.append("")

        # Add detailed captures (most recent)
        captures = context.get('captures', [])
        if captures:
            lines.append("## Recent Detailed Captures (Last 20)")
            for capture in captures[:20]:
                timestamp = capture.get('timestamp', '')
                if isinstance(timestamp, str):
                    try:
                        ts_dt = datetime.fromisoformat(timestamp)
                        ts_str = ts_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        ts_str = timestamp
                else:
                    ts_str = str(timestamp)

                emoji = capture.get('category_emoji', '📝')
                category = capture.get('category', 'unknown')
                app = capture.get('app_name', 'unknown')
                task = capture.get('task', 'N/A')

                lines.append(f"\n{ts_str} {emoji} [{category}] {app}")
                lines.append(f"  Task: {task}")

                # Add detailed context if available
                dc = capture.get('detailed_context', {})
                if dc:
                    if dc.get('file_name'):
                        lines.append(f"  File: {dc['file_name']}")
                    if dc.get('cursor_position'):
                        lines.append(f"  Position: {dc['cursor_position']}")
                    if dc.get('browser_url'):
                        lines.append(f"  URL: {dc['browser_url']}")
                    if dc.get('full_description'):
                        lines.append(f"  Details: {dc['full_description']}")
                    if dc.get('progress_from_last'):
                        lines.append(f"  Progress: {dc['progress_from_last']}")
                    if dc.get('ai_observations'):
                        lines.append(f"  AI Notes: {dc['ai_observations']}")

        return "\n".join(lines)
