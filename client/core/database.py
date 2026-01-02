"""Database operations for screen time tracker."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class Database:
    """SQLite database manager for screen time tracking."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    category TEXT NOT NULL,
                    app_name TEXT,
                    task TEXT,
                    confidence REAL,
                    processed_into_session_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    duration_seconds INTEGER,
                    category TEXT NOT NULL,
                    primary_task TEXT,
                    apps_used TEXT,
                    detailed_summary TEXT,
                    learnings TEXT,
                    focus_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    work_seconds INTEGER DEFAULT 0,
                    learning_seconds INTEGER DEFAULT 0,
                    browsing_seconds INTEGER DEFAULT 0,
                    entertainment_seconds INTEGER DEFAULT 0,
                    idle_seconds INTEGER DEFAULT 0,
                    key_learnings_json TEXT,
                    productivity_score REAL,
                    context_switches INTEGER,
                    focus_blocks_json TEXT,
                    daily_narrative TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_captures_timestamp
                ON captures(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_captures_processed
                ON captures(processed_into_session_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_start_time
                ON sessions(start_time)
            ''')

            # Migration: Add detailed_context and AI autonomy columns (Phase 5)
            cursor.execute("SELECT name FROM pragma_table_info('captures')")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'detailed_context' not in columns:
                cursor.execute('ALTER TABLE captures ADD COLUMN detailed_context TEXT')
            if 'category_emoji' not in columns:
                cursor.execute('ALTER TABLE captures ADD COLUMN category_emoji TEXT')
            if 'category_color' not in columns:
                cursor.execute('ALTER TABLE captures ADD COLUMN category_color TEXT')
            
            # Migration: Add simple_category column for consistent dashboard stats
            # This stores AI's direct mapping to 5 buckets (work/learning/browsing/entertainment/idle)
            if 'simple_category' not in columns:
                cursor.execute('ALTER TABLE captures ADD COLUMN simple_category TEXT')
                # Backfill existing records using _categorize_activity logic
                cursor.execute('SELECT id, category FROM captures WHERE simple_category IS NULL')
                rows = cursor.fetchall()
                for row in rows:
                    simple_cat = self._categorize_activity(row['category'])
                    cursor.execute('UPDATE captures SET simple_category = ? WHERE id = ?', 
                                 (simple_cat, row['id']))

    def insert_capture(
        self,
        timestamp: datetime,
        category: str,
        app_name: str,
        task: str,
        confidence: float,
        detailed_context: Optional[str] = None,
        category_emoji: Optional[str] = None,
        category_color: Optional[str] = None,
        simple_category: Optional[str] = None
    ) -> int:
        """Insert a new capture record.

        Args:
            timestamp: Capture timestamp
            category: Activity category (detailed, for display)
            app_name: Application name
            task: Task description (concise, max 80 chars for display)
            confidence: AI confidence score
            detailed_context: JSON string with rich context (optional)
            category_emoji: Emoji representing the activity (optional)
            category_color: Hex color for the category (optional)
            simple_category: One of work/learning/browsing/entertainment/idle for stats (optional)

        Returns:
            Capture ID
        """
        # If simple_category not provided by AI, fall back to _categorize_activity
        if not simple_category:
            simple_category = self._categorize_activity(category)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO captures 
                (timestamp, category, app_name, task, confidence, detailed_context, category_emoji, category_color, simple_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, category, app_name, task, confidence, detailed_context, category_emoji, category_color, simple_category))
            return cursor.lastrowid

    def get_previous_captures(self, limit: int = 2) -> List[Dict[str, Any]]:
        """Get most recent captures for context.

        Args:
            limit: Number of previous captures to retrieve (default 2)

        Returns:
            List of capture dictionaries, most recent first
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_unprocessed_captures(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get captures that haven't been processed into sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                WHERE processed_into_session_id IS NULL
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_captures(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent captures within the specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (cutoff, limit))
            return [dict(row) for row in cursor.fetchall()]

    def mark_captures_processed(self, capture_ids: List[int], session_id: int) -> None:
        """Mark captures as processed into a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(capture_ids))
            cursor.execute(f'''
                UPDATE captures
                SET processed_into_session_id = ?
                WHERE id IN ({placeholders})
            ''', [session_id] + capture_ids)

    def insert_session(self, start_time: datetime, end_time: datetime,
                      category: str, primary_task: str, apps_used: str,
                      duration_seconds: int) -> int:
        """Insert a new session record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions
                (start_time, end_time, duration_seconds, category, primary_task, apps_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (start_time, end_time, duration_seconds, category, primary_task, apps_used))
            return cursor.lastrowid

    def get_sessions_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """Get all sessions for a specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time ASC
            ''', (start_of_day, end_of_day))
            return [dict(row) for row in cursor.fetchall()]

    def get_captures_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """Get all captures for a specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                WHERE timestamp >= ? AND timestamp < ?
                ORDER BY timestamp ASC
            ''', (start_of_day, end_of_day))
            return [dict(row) for row in cursor.fetchall()]

    def get_day_blocks(self, date: datetime, block_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get activity data aggregated into time blocks for a full day.
        
        Args:
            date: Date to get blocks for
            block_minutes: Size of each block in minutes (default 30)
            
        Returns:
            List of dicts with structure:
            [
                {
                    'hour': 0,
                    'block': 0,  # 0 or 1 for 30-min blocks
                    'start_time': datetime,
                    'end_time': datetime,
                    'category_counts': {'work': 5, 'browsing': 2},
                    'dominant_category': 'work',
                    'total_captures': 7,
                    'activity_level': 0.8  # 0.0-1.0
                },
                ...
            ]
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Get all captures for the day
        captures = self.get_captures_for_date(date)
        
        # Initialize blocks: 24 hours × blocks_per_hour
        blocks_per_hour = 60 // block_minutes
        total_blocks = 24 * blocks_per_hour
        blocks = []
        
        for hour in range(24):
            for block_idx in range(blocks_per_hour):
                block_start = start_of_day + timedelta(
                    hours=hour, 
                    minutes=block_idx * block_minutes
                )
                block_end = block_start + timedelta(minutes=block_minutes)
                
                blocks.append({
                    'hour': hour,
                    'block': block_idx,
                    'start_time': block_start,
                    'end_time': block_end,
                    'category_counts': {},
                    'dominant_category': None,
                    'total_captures': 0,
                    'activity_level': 0.0
                })
        
        # Bucket captures into blocks
        for capture in captures:
            ts = capture['timestamp']
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if ts.tzinfo:
                    ts = ts.replace(tzinfo=None)
            
            # Calculate which block this capture belongs to
            delta = ts - start_of_day
            total_minutes = int(delta.total_seconds() / 60)
            block_index = total_minutes // block_minutes
            
            if 0 <= block_index < total_blocks:
                block = blocks[block_index]
                
                # Use simple_category for consistent bucketing
                cat = capture.get('simple_category') or self._categorize_activity(capture['category'])
                
                block['category_counts'][cat] = block['category_counts'].get(cat, 0) + 1
                block['total_captures'] += 1
        
        # Calculate dominant category and activity level for each block
        for block in blocks:
            if block['total_captures'] > 0:
                # Find dominant category
                block['dominant_category'] = max(
                    block['category_counts'].items(), 
                    key=lambda x: x[1]
                )[0]
                
                # Activity level: captures per minute (max ~2 captures per minute at 30s interval)
                expected_captures = block_minutes / 0.5  # 30s interval = 2 per minute
                block['activity_level'] = min(1.0, block['total_captures'] / expected_captures)
            else:
                block['dominant_category'] = 'idle'
                block['activity_level'] = 0.0
        
        return blocks

    def reset_sessions_for_date(self, date: datetime) -> int:
        """Delete sessions for a date and mark captures as unprocessed.
        
        This allows sessions to be rebuilt with new grouping logic.
        
        Args:
            date: Date to reset sessions for
            
        Returns:
            Number of sessions deleted
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session IDs for the date
            cursor.execute('''
                SELECT id FROM sessions
                WHERE start_time >= ? AND start_time < ?
            ''', (start_of_day, end_of_day))
            session_ids = [row[0] for row in cursor.fetchall()]
            
            if session_ids:
                # Mark captures as unprocessed
                placeholders = ','.join('?' * len(session_ids))
                cursor.execute(f'''
                    UPDATE captures
                    SET processed_into_session_id = NULL
                    WHERE processed_into_session_id IN ({placeholders})
                ''', session_ids)
                
                # Delete sessions
                cursor.execute(f'''
                    DELETE FROM sessions
                    WHERE id IN ({placeholders})
                ''', session_ids)
            
            # Also delete the daily summary for this date
            cursor.execute('''
                DELETE FROM daily_summaries
                WHERE date = ?
            ''', (start_of_day.date(),))
            
            return len(session_ids)

    def _categorize_activity(self, detailed_category: str) -> str:
        """Map detailed AI-generated categories to simple buckets."""
        if not detailed_category:
            return 'idle'

        cat_lower = detailed_category.lower()

        # Check for exact matches first
        if cat_lower in ['work', 'learning', 'browsing', 'entertainment', 'idle']:
            return cat_lower

        # Priority check: If "browsing" or "browse" appears explicitly, it's likely browsing
        # (even if combined with "professional" like "Professional Browsing")
        if 'brows' in cat_lower or 'surf' in cat_lower or 'scroll' in cat_lower:
            # But exclude if it's clearly work-related browsing
            if not any(kw in cat_lower for kw in ['code', 'debug', 'programming', 'documentation']):
                return 'browsing'

        # Check for distraction/casual/nsfw keywords (entertainment/browsing)
        distraction_keywords = ['distraction', 'casual', 'nsfw', 'explicit', 'meme']
        for keyword in distraction_keywords:
            if keyword in cat_lower:
                return 'browsing'

        # Learning keywords (educational activities)
        learning_keywords = ['learn', 'learning', 'tutorial', 'education', 'study', 'studying',
                           'course', 'training', 'article', 'workshop',
                           'lesson', 'class', 'lecture', 'teaching', 'instruction',
                           'research', 'academic', 'university', 'school',
                           'educational', 'certification', 'exam']

        # Entertainment keywords (leisure/fun activities)
        entertainment_keywords = ['entertainment', 'game', 'gaming', 'video', 'music',
                                'stream', 'streaming', 'watch', 'watching', 'listen', 'listening',
                                'podcast', 'show', 'movie', 'film', 'series', 'tv',
                                'youtube', 'netflix', 'spotify', 'twitch',
                                'fun', 'relax', 'leisure', 'play', 'playing',
                                'anime', 'cartoon', 'comedy']

        # Work-related keywords (professional/productive activities)
        work_keywords = ['develop', 'code', 'coding', 'debug', 'debugging', 'programming', 'ai',
                        'project', 'planning', 'design', 'documentation', 'review',
                        'analysis', 'management', 'configuration', 'tool',
                        'meeting', 'email', 'call', 'presentation', 'writing', 'editing',
                        'testing', 'deployment', 'deploy', 'bug', 'issue', 'task',
                        'calendar', 'schedule', 'organizing', 'office', 'excel', 'word',
                        'spreadsheet', 'document', 'report', 'professional', 'business',
                        'work', 'job', 'career', 'productivity']

        # Social media and general browsing keywords
        browsing_keywords = ['social', 'network', 'reddit', 'twitter', 'facebook', 'instagram',
                           'google', 'search', 'searching', 'news', 'blog', 'forum',
                           'website', 'web', 'internet', 'online',
                           'chat', 'chatting', 'whatsapp', 'discord', 'slack',
                           'messaging', 'message', 'feed', 'timeline', 'post', 'comment',
                           'thread', 'discussion', 'community', 'explore', 'exploring',
                           'github', 'gitlab']

        # Check learning first (tutorials, courses are more specific)
        for keyword in learning_keywords:
            if keyword in cat_lower:
                return 'learning'

        # Then check entertainment
        for keyword in entertainment_keywords:
            if keyword in cat_lower:
                return 'entertainment'

        # Then check social/browsing (before work, to catch "social media" before "professional")
        for keyword in browsing_keywords:
            if keyword in cat_lower:
                return 'browsing'

        # Finally check work
        for keyword in work_keywords:
            if keyword in cat_lower:
                return 'work'

        # Default to browsing for unclassified categories
        return 'browsing'

    def get_today_stats(self) -> Dict[str, int]:
        """Get statistics for today.
        
        Uses simple_category column directly for consistent stats.
        Falls back to _categorize_activity for legacy records without simple_category.
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Use COALESCE to handle NULL simple_category (legacy records)
            # Group by simple_category for direct bucket stats
            cursor.execute('''
                SELECT
                    simple_category,
                    category,
                    COUNT(*) as count,
                    COUNT(*) * 30 as estimated_seconds
                FROM captures
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY COALESCE(simple_category, category)
            ''', (today, tomorrow))

            stats = {
                'work': 0,
                'learning': 0,
                'browsing': 0,
                'entertainment': 0,
                'idle': 0,
                'total_captures': 0
            }

            for row in cursor.fetchall():
                # Use simple_category if available, otherwise fall back to categorization
                simple_cat = row['simple_category']
                if not simple_cat:
                    # Legacy record without simple_category - use categorization logic
                    simple_cat = self._categorize_activity(row['category'])
                
                # Ensure valid bucket (in case of any edge cases)
                if simple_cat not in stats:
                    simple_cat = 'browsing'  # Default fallback
                    
                stats[simple_cat] += row['estimated_seconds']
                stats['total_captures'] += row['count']

            return stats

    def cleanup_old_captures(self, days: int = 1) -> int:
        """Delete captures older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM captures
                WHERE timestamp < ?
            ''', (cutoff,))
            return cursor.rowcount

    def cleanup_old_sessions(self, days: int = 90) -> int:
        """Delete sessions older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM sessions
                WHERE start_time < ?
            ''', (cutoff,))
            return cursor.rowcount

    def get_config_value(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else None

    def set_config_value(self, key: str, value: str) -> None:
        """Set a configuration value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value)
                VALUES (?, ?)
            ''', (key, value))

    def get_api_usage_today(self) -> int:
        """Get the number of API calls made today."""
        count_str = self.get_config_value('api_calls_today')
        date_str = self.get_config_value('api_calls_date')
        today = datetime.now().date().isoformat()

        if date_str != today:
            self.set_config_value('api_calls_today', '0')
            self.set_config_value('api_calls_date', today)
            return 0

        return int(count_str) if count_str else 0

    def increment_api_usage(self) -> int:
        """Increment API usage counter for today."""
        current = self.get_api_usage_today()
        new_count = current + 1
        self.set_config_value('api_calls_today', str(new_count))
        return new_count

    # Session Management Methods (Phase 3)

    def get_unprocessed_captures_for_session(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get captures that haven't been processed into sessions, ordered by timestamp.

        Args:
            limit: Maximum number of captures to return

        Returns:
            List of capture dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                WHERE processed_into_session_id IS NULL
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_last_session_end_time(self) -> Optional[datetime]:
        """Get the end time of the most recent session.

        Returns:
            Datetime of last session end, or None if no sessions exist
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT end_time FROM sessions
                ORDER BY end_time DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return datetime.fromisoformat(row['end_time'])
            return None

    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_captures_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all captures that belong to a session.

        Args:
            session_id: Session ID

        Returns:
            List of capture dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM captures
                WHERE processed_into_session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def update_session_enrichment(self, session_id: int, detailed_summary: str,
                                  learnings: str, focus_score: float) -> None:
        """Update session with AI enrichment data.

        Args:
            session_id: Session ID
            detailed_summary: AI-generated summary
            learnings: Extracted learnings
            focus_score: Focus score (0.0-1.0)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions
                SET detailed_summary = ?, learnings = ?, focus_score = ?
                WHERE id = ?
            ''', (detailed_summary, learnings, focus_score, session_id))

    def get_sessions_needing_enrichment(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions that haven't been enriched yet.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions
                WHERE detailed_summary IS NULL OR detailed_summary = ''
                ORDER BY start_time ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # Daily Summary Management Methods (Phase 3)

    def get_daily_summary(self, date: datetime) -> Optional[Dict[str, Any]]:
        """Get daily summary for a specific date.

        Args:
            date: Date to get summary for

        Returns:
            Summary dictionary or None if not found
        """
        date_str = date.date().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM daily_summaries WHERE date = ?', (date_str,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_daily_summary(self, date: datetime, **kwargs) -> int:
        """Insert a new daily summary record.

        Args:
            date: Date for summary
            **kwargs: Fields to insert (work_seconds, learning_seconds, etc.)

        Returns:
            Summary ID
        """
        date_str = date.date().isoformat()

        # Build column names and values dynamically
        columns = ['date'] + list(kwargs.keys())
        values = [date_str] + list(kwargs.values())
        placeholders = ','.join('?' * len(columns))
        columns_str = ','.join(columns)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                INSERT INTO daily_summaries ({columns_str})
                VALUES ({placeholders})
            ''', values)
            return cursor.lastrowid

    def update_daily_summary(self, summary_id: int, **kwargs) -> None:
        """Update an existing daily summary.

        Args:
            summary_id: Summary ID
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        set_clause = ', '.join(f"{key} = ?" for key in kwargs.keys())
        values = list(kwargs.values()) + [summary_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE daily_summaries
                SET {set_clause}
                WHERE id = ?
            ''', values)

    def delete_daily_summary(self, date: datetime) -> None:
        """Delete daily summary for a specific date.

        Args:
            date: Date to delete summary for
        """
        date_str = date.date().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM daily_summaries WHERE date = ?', (date_str,))
