"""Async capture worker - runs the Phase 1 capture loop in background."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from core.database import Database
from core.analyzer import GeminiAnalyzer, RateLimitError
from core.capture import ActivityMonitor, ScreenshotCapture, WindowMonitor, WindowEventTracker
from core.backend_client import BackendClient, BackendError
from core.fallback_handler import FallbackHandler, FallbackMode
from utils.hash_utils import ScreenshotHasher


async def poll_window_changes_async(window_event_tracker, stop_event: asyncio.Event, poll_interval: float = 1.0):
    """Async background task to poll for window changes every poll_interval seconds.
    
    Args:
        window_event_tracker: WindowEventTracker instance
        stop_event: asyncio.Event to signal when to stop polling
        poll_interval: How often to poll for window changes (default 1 second)
    """
    while not stop_event.is_set():
        try:
            # Run the blocking poll in a thread to avoid blocking the async loop
            await asyncio.to_thread(window_event_tracker.poll_window_changes)
        except Exception as e:
            # Don't crash on polling errors, just continue
            pass
        
        # Wait for next poll or until stop is signaled
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
            break  # Stop event was set
        except asyncio.TimeoutError:
            pass  # Continue polling


async def capture_worker_task(app):
    """Background task that runs the capture loop.

    Args:
        app: The Textual application instance with config and state
    """
    # Get configuration
    config = app.config
    db_path = config.get('storage', 'database_path')
    api_key = config.get('gemini', 'api_key')
    model = config.get('gemini', 'model')
    quality = config.get('capture', 'screenshot_quality', default=85)
    interval = config.get('capture', 'interval_seconds', default=30)
    idle_timeout = config.get('capture', 'idle_timeout_seconds', default=60)
    max_daily_requests = config.get('capture', 'max_daily_requests', default=1500)

    # Initialize Phase 1 components
    db = Database(db_path)
    user_email = config.get('account', 'email', default=None)
    analyzer = GeminiAnalyzer(api_key, model, user_email=user_email)
    capturer = ScreenshotCapture(quality)
    hasher = ScreenshotHasher()
    activity_monitor = ActivityMonitor(idle_timeout)
    window_monitor = WindowMonitor()
    window_event_tracker = WindowEventTracker(window_monitor)  # For tracking window activity chain
    
    # Initialize Phase 2 components (backend integration)
    backend_client = None
    fallback_handler = None
    
    backend_enabled = config.get('backend', 'enabled', default=False)
    if backend_enabled:
        try:
            backend_url = config.get('backend', 'url')
            firebase_api_key = config.get('firebase', 'api_key')
            timeout = config.get('backend', 'timeout', default=30)
            fallback_mode = config.get('backend', 'fallback_mode', default='auto')
            
            backend_client = BackendClient(
                backend_url=backend_url,
                firebase_api_key=firebase_api_key,
                timeout=timeout
            )
            
            fallback_handler = FallbackHandler(
                backend_client=backend_client,
                local_analyzer=analyzer,
                fallback_mode=fallback_mode
            )
            
            print(f"[Capture Worker] Backend integration enabled (mode: {fallback_mode})")
        except Exception as e:
            print(f"[Capture Worker] Failed to initialize backend: {e}")
            print(f"[Capture Worker] Falling back to local-only mode")
    else:
        print("[Capture Worker] Backend integration disabled (using local Gemini only)")

    # Start activity monitoring
    activity_monitor.start()

    try:
        while not app.shutting_down:
            # Start window event tracking for this capture interval
            window_event_tracker.start_interval()
            
            # Create stop event for window polling
            poll_stop_event = asyncio.Event()
            
            # Start background polling for window changes (polls every 1 second)
            poll_task = asyncio.create_task(
                poll_window_changes_async(window_event_tracker, poll_stop_event)
            )
            
            try:
                # Check if idle
                if activity_monitor.is_idle():
                    idle_time = activity_monitor.seconds_since_activity()
                    app.loop_status = "idle"
                    app.idle_seconds = idle_time
                    poll_stop_event.set()
                    await poll_task
                    await asyncio.sleep(5)
                    continue

                # Check API quota
                api_usage = db.get_api_usage_today()
                app.api_calls_used = api_usage

                if api_usage >= max_daily_requests:
                    app.loop_status = "paused"
                    poll_stop_event.set()
                    await poll_task
                    await asyncio.sleep(interval)
                    continue

                # Set status to active
                app.loop_status = "active"
                app.idle_seconds = 0

                # Wait for capture interval (minus some overhead) while polling for window changes
                await asyncio.sleep(max(1, interval - 2))
                
                # Stop window polling before capture
                poll_stop_event.set()
                await poll_task

                # Capture screenshot (run in thread to avoid blocking UI)
                screenshot_path = await asyncio.to_thread(capturer.capture)

                # Check for duplicates (run in thread)
                is_duplicate = await asyncio.to_thread(hasher.is_duplicate, screenshot_path)
                if is_duplicate:
                    await asyncio.to_thread(capturer.cleanup_screenshot, screenshot_path)
                    continue

                # Get previous 2 captures for context (Phase 5)
                previous_captures = await asyncio.to_thread(db.get_previous_captures, 2)

                # Get window activity summary for this interval
                window_summary = window_event_tracker.get_interval_summary()
                
                # Gather context metadata with full window activity chain
                window_info = window_summary['current_window']
                activity_metrics = activity_monitor.get_and_reset_metrics()
                
                context_metadata = {
                    'window_title': window_info.get('title', ''),
                    'app_name': window_info.get('app_name', ''),
                    'keystrokes': activity_metrics.get('keystrokes', 0),
                    'mouse_clicks': activity_metrics.get('mouse_clicks', 0),
                    'mouse_distance': activity_metrics.get('mouse_distance', 0),
                    # Window activity chain data (last 5 window switches)
                    'window_changes': window_summary['total_changes'],
                    'window_events': window_event_tracker.get_limited_events(limit=5),
                }

                # Analyze with backend or local Gemini (Phase 2)
                try:
                    if fallback_handler:
                        # Use fallback handler (backend with local fallback)
                        result = await asyncio.to_thread(
                            fallback_handler.analyze_screenshot,
                            screenshot_path,
                            previous_captures,
                            context_metadata
                        )
                    else:
                        # Use local Gemini only
                        result = await asyncio.to_thread(
                            analyzer.analyze_with_fallback,
                            screenshot_path,
                            previous_captures,
                            context_metadata
                        )

                    if result and result.get('confidence', 0) > 0:
                        # Extract detailed_context for storage
                        detailed_context = result.get('detailed_context', {})
                        detailed_context_json = json.dumps(detailed_context) if detailed_context else None

                        # Save to database with detailed_context, AI autonomy fields, and simple_category
                        capture_id = db.insert_capture(
                            timestamp=datetime.now(),
                            category=result['category'],
                            app_name=result['app'],
                            task=result['task'],
                            confidence=result['confidence'],
                            detailed_context=detailed_context_json,
                            category_emoji=result.get('category_emoji'),
                            category_color=result.get('category_color'),
                            simple_category=result.get('simple_category')  # AI's direct bucket mapping
                        )
                        
                        # Save window activity log if there were window changes
                        if window_summary['total_changes'] > 0 or window_summary['events']:
                            try:
                                db.insert_window_activity_log(
                                    capture_id=capture_id,
                                    interval_start=window_summary['interval_start'],
                                    interval_end=window_summary['interval_end'],
                                    total_window_changes=window_summary['total_changes'],
                                    events_json=json.dumps(window_summary['events']),
                                    current_window_title=window_info.get('title', ''),
                                    current_app_name=window_info.get('app_name', ''),
                                    apps_visited=','.join(window_summary.get('apps_visited', []))
                                )
                            except Exception as log_err:
                                # Don't fail capture if window logging fails
                                pass

                        # Increment API usage
                        db.increment_api_usage()

                        # Update UI state
                        # Check if activity changed (different category or app)
                        if (result['category'] != app.current_category or
                            result['app'] != app.current_app):
                            # Reset timer for new activity
                            app.activity_start_time = datetime.now()

                        app.current_category = result['category']
                        app.current_emoji = result.get('category_emoji', '📝')
                        app.current_color = result.get('category_color', '#95a5a6')
                        app.current_app = result['app']
                        app.current_task = result['task']
                        app.last_analysis_source = result.get('_source', 'local')

                except RateLimitError as e:
                    app.loop_status = "rate_limited"
                    app.error_message = str(e)
                    await asyncio.to_thread(capturer.cleanup_screenshot, screenshot_path)
                    await asyncio.sleep(e.retry_after)
                    continue

                except Exception as e:
                    app.loop_status = "error"
                    app.error_message = str(e)
                    await asyncio.to_thread(capturer.cleanup_screenshot, screenshot_path)
                    await asyncio.sleep(10)  # Wait before retry
                    continue

                # Cleanup screenshot
                await asyncio.to_thread(capturer.cleanup_screenshot, screenshot_path)

            finally:
                # Ensure polling task is stopped even if an exception occurred
                if not poll_stop_event.is_set():
                    poll_stop_event.set()
                if not poll_task.done():
                    try:
                        await asyncio.wait_for(poll_task, timeout=1.0)
                    except asyncio.TimeoutError:
                        poll_task.cancel()

    finally:
        # Cleanup on shutdown
        activity_monitor.stop()
        capturer.cleanup_all()

