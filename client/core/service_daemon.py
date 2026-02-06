"""
Service Daemon

Lightweight daemon runner for background service mode.
Runs capture, session building, and email scheduling without TUI dependencies.
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.database import Database
    from core.capture import ActivityMonitor, ScreenshotCapture, WindowMonitor
    from core.analyzer import GeminiAnalyzer
    from core.goal_manager import AnalysisGoalManager
    from core.session_builder import SessionBuilder
    from core.daily_aggregator import DailyAggregator
    from core.email_reporter import EmailReporter
    from utils.hash_utils import ScreenshotHasher
    from utils.config_manager import ConfigDict


class ServiceDaemon:
    """Manages background workers for service mode."""

    def __init__(
        self,
        config: 'ConfigDict',
        db: 'Database',
        analyzer: 'GeminiAnalyzer',
        goal_manager: 'AnalysisGoalManager',
        capturer: 'ScreenshotCapture',
        activity_monitor: 'ActivityMonitor',
        hasher: 'ScreenshotHasher',
        session_builder: 'SessionBuilder',
        daily_aggregator: 'DailyAggregator',
        email_reporter: Optional['EmailReporter'] = None
    ):
        """Initialize service daemon.

        Args:
            config: Configuration dictionary
            db: Database instance
            analyzer: Gemini analyzer instance
            goal_manager: Analysis goal manager instance
            capturer: Screenshot capture instance
            activity_monitor: Activity monitor instance
            hasher: Screenshot hasher instance
            session_builder: Session builder instance
            daily_aggregator: Daily aggregator instance
            email_reporter: Email reporter instance (optional)
        """
        self.config = config
        self.db = db
        self.analyzer = analyzer
        self.goal_manager = goal_manager
        self.capturer = capturer
        self.activity_monitor = activity_monitor
        self.hasher = hasher
        self.session_builder = session_builder
        self.daily_aggregator = daily_aggregator
        self.email_reporter = email_reporter
        
        # Initialize Window Monitor and Event Tracker (for window activity chain)
        from core.capture import WindowMonitor, WindowEventTracker
        self.window_monitor = WindowMonitor()
        self.window_event_tracker = WindowEventTracker(self.window_monitor)

        # Configuration
        self.capture_interval = config.get('capture', 'interval_seconds', default=30)
        self.max_daily_requests = config.get('capture', 'max_daily_requests', default=1500)
        self.session_trigger_hours = config.get('intelligence', 'session_trigger_hours', default=2)
        self.session_trigger_idle_minutes = config.get('intelligence', 'session_trigger_idle_minutes', default=5)
        self.session_check_interval = config.get('intelligence', 'check_interval_seconds', default=60)
        self.max_enrichment_per_trigger = config.get('intelligence', 'max_enrichment_per_trigger', default=3)

        # Email configuration
        self.email_enabled = config.get('email', 'enabled', default=False)
        self.email_send_time = config.get('email', 'send_time', default='21:00')

        # State tracking
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.session_thread: Optional[threading.Thread] = None
        self.email_thread: Optional[threading.Thread] = None
        self.last_session_build = datetime.now()
        self.last_email_date: Optional[str] = None

    def start(self):
        """Start all daemon workers."""
        if self.running:
            print("Service daemon already running")
            return

        print("Starting service daemon...")
        self.running = True

        # Start activity monitor
        self.activity_monitor.start()
        print("✓ Activity monitor started")

        # Start capture worker
        self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.capture_thread.start()
        print("✓ Capture worker started")

        # Start session worker
        self.session_thread = threading.Thread(target=self._session_worker, daemon=True)
        self.session_thread.start()
        print("✓ Session worker started")

        # Start email worker if enabled
        if self.email_enabled and self.email_reporter:
            self.email_thread = threading.Thread(target=self._email_worker, daemon=True)
            self.email_thread.start()
            print("✓ Email worker started")

        # Start local web dashboard
        try:
            from core.dashboard_server import DashboardServer
            db_path = self.config.get('storage', 'database_path')
            dashboard_port = self.config.get('dashboard', 'port', default=5555)
            self.dashboard_server = DashboardServer(db_path, port=int(dashboard_port))
            self.dashboard_server.start()
        except Exception as e:
            print(f"[Dashboard] Failed to start: {e}")

        print("✓ Service daemon running")

    def stop(self):
        """Stop all daemon workers."""
        print("Stopping service daemon...")
        self.running = False

        # Stop activity monitor
        self.activity_monitor.stop()

        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)

        if self.session_thread and self.session_thread.is_alive():
            self.session_thread.join(timeout=5)

        if self.email_thread and self.email_thread.is_alive():
            self.email_thread.join(timeout=5)

        # Cleanup
        self.capturer.cleanup_all()

        print("✓ Service daemon stopped")

    def _capture_worker(self):
        """Capture worker loop (runs every 30s)."""
        print("[Capture Worker] Started")

        while self.running:
            try:
                # Start window event tracking for this interval
                self.window_event_tracker.start_interval()
                
                # Start background polling for window changes
                poll_stop_event = threading.Event()
                poll_thread = threading.Thread(
                    target=self._poll_window_changes_bg,
                    args=(poll_stop_event,),
                    daemon=True
                )
                poll_thread.start()
                
                # Check if idle
                if self.activity_monitor.is_idle():
                    idle_time = self.activity_monitor.seconds_since_activity()
                    if idle_time % 60 == 0:  # Log every minute
                        print(f"[Capture Worker] IDLE - No activity for {idle_time}s")
                    poll_stop_event.set()
                    time.sleep(5)
                    continue

                # Check API quota
                api_usage = self.db.get_api_usage_today()
                if api_usage >= self.max_daily_requests:
                    if api_usage == self.max_daily_requests:  # Only log once
                        print(f"[Capture Worker] QUOTA EXCEEDED - {api_usage}/{self.max_daily_requests}")
                    poll_stop_event.set()
                    time.sleep(self.capture_interval)
                    continue

                # Wait for capture interval minus polling overhead
                time.sleep(max(1, self.capture_interval - 2))
                
                # Stop polling before capture
                poll_stop_event.set()
                poll_thread.join(timeout=1)
                
                # Capture screenshot
                screenshot_path = self.capturer.capture()

                # Check for duplicates
                if self.hasher.is_duplicate(screenshot_path):
                    self.capturer.cleanup_screenshot(screenshot_path)
                    continue

                # Get previous 2 captures for context
                previous_captures = self.db.get_previous_captures(limit=2)
                
                # Get window activity summary for this interval
                window_summary = self.window_event_tracker.get_interval_summary()
                
                # Gather System Context with window activity chain
                window_info = window_summary['current_window']
                activity_metrics = self.activity_monitor.get_and_reset_metrics()
                
                context_metadata = {
                    'window_title': window_info.get('title', ''),
                    'app_name': window_info.get('app_name', ''),
                    'keystrokes': activity_metrics.get('keystrokes', 0),
                    'mouse_clicks': activity_metrics.get('mouse_clicks', 0),
                    'mouse_distance': activity_metrics.get('mouse_distance', 0),
                    # Window activity chain data
                    'window_changes': window_summary['total_changes'],
                    'window_events': self.window_event_tracker.get_limited_events(limit=5),
                }
                
                # DEBUG: Write context metadata to file
                with open('debug_context.log', 'a') as f:
                    f.write(f"\n[{datetime.now()}] context_metadata: {context_metadata}\n")
                    f.write(f"  window_info: {window_info}\n")
                    f.write(f"  window_summary: {window_summary}\n")

                # Analyze with Gemini (with enriched context)
                result = self.analyzer.analyze_with_fallback(screenshot_path, previous_captures, context_metadata)

                if result:
                    # Extract detailed_context
                    detailed_context = result.get('detailed_context', {})
                    detailed_context_json = json.dumps(detailed_context) if detailed_context else None

                    # Save to database with detailed_context and AI autonomy fields
                    capture_id = self.db.insert_capture(
                        timestamp=datetime.now(),
                        category=result['category'],
                        app_name=result['app'],
                        task=result['task'],
                        confidence=result['confidence'],
                        detailed_context=detailed_context_json,
                        category_emoji=result.get('category_emoji'),
                        category_color=result.get('category_color')
                    )
                    
                    # Save window activity log
                    if window_summary['total_changes'] > 0 or window_summary['events']:
                        self.db.insert_window_activity_log(
                            capture_id=capture_id,
                            interval_start=window_summary['interval_start'],
                            interval_end=window_summary['interval_end'],
                            total_window_changes=window_summary['total_changes'],
                            events_json=json.dumps(window_summary['events']),
                            current_window_title=window_info.get('title', ''),
                            current_app_name=window_info.get('app_name', ''),
                            apps_visited=','.join(window_summary.get('apps_visited', []))
                        )

                    # Increment API usage
                    self.db.increment_api_usage()

                    print(f"[Capture Worker] Captured: [{result['category']}] {result['app']} - {result['task'][:50]} (switches: {window_summary['total_changes']})")

                # Cleanup screenshot
                self.capturer.cleanup_screenshot(screenshot_path)

            except Exception as e:
                print(f"[Capture Worker] Error: {e}")
                time.sleep(self.capture_interval)

        print("[Capture Worker] Stopped")
    
    def _poll_window_changes_bg(self, stop_event: threading.Event):
        """Background polling for window changes (1s interval)."""
        while not stop_event.is_set():
            self.window_event_tracker.poll_window_changes()
            stop_event.wait(1)  # Poll every 1 second

    def _session_worker(self):
        """Session worker loop (checks every 60s for triggers)."""
        print("[Session Worker] Started")

        while self.running:
            try:
                time.sleep(self.session_check_interval)

                # Check trigger conditions
                elapsed_hours = (datetime.now() - self.last_session_build).total_seconds() / 3600
                idle_minutes = self.activity_monitor.seconds_since_activity() / 60

                trigger_time = elapsed_hours >= self.session_trigger_hours
                trigger_idle = idle_minutes >= self.session_trigger_idle_minutes

                if not (trigger_time or trigger_idle):
                    continue

                # Build sessions
                print(f"[Session Worker] Trigger: {'time' if trigger_time else 'idle'}")
                session_ids = self.session_builder.build_sessions()

                if not session_ids:
                    print("[Session Worker] No new sessions")
                    self.last_session_build = datetime.now()
                    continue

                print(f"[Session Worker] Built {len(session_ids)} session(s)")

                # Enrich sessions (limit to avoid API quota issues)
                api_usage = self.db.get_api_usage_today()
                remaining_quota = self.max_daily_requests - api_usage
                max_enrich = min(self.max_enrichment_per_trigger, remaining_quota)

                enriched_count = 0
                for session_id in session_ids[:max_enrich]:
                    success = self.session_builder.enrich_session_with_retry(session_id)
                    if success:
                        self.db.increment_api_usage()
                        enriched_count += 1

                print(f"[Session Worker] Enriched {enriched_count}/{len(session_ids)} sessions")

                # Update last build time
                self.last_session_build = datetime.now()

            except Exception as e:
                print(f"[Session Worker] Error: {e}")

        print("[Session Worker] Stopped")

    def _email_worker(self):
        """Email worker loop (checks every minute for send time)."""
        print("[Email Worker] Started")

        while self.running:
            try:
                time.sleep(60)  # Check every minute

                now = datetime.now()
                current_time = now.strftime('%H:%M')
                current_date = now.strftime('%Y-%m-%d')

                # Check if it's time to send
                if current_time != self.email_send_time:
                    continue

                # Check if already sent today
                if self.last_email_date == current_date:
                    continue

                print(f"[Email Worker] Sending daily report for {current_date}")

                # Generate summary for today (or use existing)
                summary = self.db.get_daily_summary(now)

                if not summary:
                    print("[Email Worker] Generating daily summary...")
                    summary_id = self.daily_aggregator.generate_daily_summary(now)

                    if summary_id:
                        self.db.increment_api_usage()
                        summary = self.db.get_daily_summary(now)
                    else:
                        print("[Email Worker] Failed to generate summary (no data?)")
                        continue

                # Send email
                success = self.email_reporter.send_daily_report(summary)

                if success:
                    self.last_email_date = current_date
                    print(f"[Email Worker] ✓ Daily report sent for {current_date}")
                else:
                    print(f"[Email Worker] ✗ Failed to send daily report")

            except Exception as e:
                print(f"[Email Worker] Error: {e}")

        print("[Email Worker] Stopped")

    def run_forever(self):
        """Run daemon in foreground (blocks until stopped)."""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nReceived shutdown signal")
            self.stop()

