"""Telos - Main entry point."""

import sys
import os
import time
import json
import shutil
from datetime import datetime
from pathlib import Path

from utils.config_manager import load_config, ConfigManager
from utils.hash_utils import ScreenshotHasher
from core.database import Database
from core.capture import ActivityMonitor, ScreenshotCapture
from core.analyzer import GeminiAnalyzer, RateLimitError
from core.goal_manager import AnalysisGoalManager
from core.session_builder import SessionBuilder
from core.daily_aggregator import DailyAggregator


def setup_config():
    """Interactive setup wizard for first-time configuration."""
    print("=== Telos Setup ===\n")

    config_path = Path("config.yaml")

    if config_path.exists():
        print(f"Configuration file already exists at {config_path}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return

    example_path = Path("config.yaml.example")
    if not example_path.exists():
        print("Error: config.yaml.example not found!")
        return

    api_key = input("\nEnter your Gemini API key: ").strip()

    if not api_key:
        print("Error: API key cannot be empty")
        return

    shutil.copy(example_path, config_path)

    config_manager = ConfigManager(str(config_path))
    config_manager.load()
    config_manager.config['gemini']['api_key'] = api_key
    config_manager.save(config_manager.config)

    print(f"\n✓ Configuration saved to {config_path}")
    print("✓ Setup complete! You can now run: python main.py test")


def test_capture_loop():
    """Test the core capture -> analyze -> store -> delete loop."""
    print("=== Testing Core Capture Loop ===\n")

    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun setup first: python main.py setup")
        return
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    db_path = config.get('storage', 'database_path')
    db = Database(db_path)

    api_key = config.get('gemini', 'api_key')
    model = config.get('gemini', 'model')
    analyzer = GeminiAnalyzer(api_key, model)

    quality = config.get('capture', 'screenshot_quality', default=85)
    capturer = ScreenshotCapture(quality)

    hasher = ScreenshotHasher()

    interval = config.get('capture', 'interval_seconds', default=30)
    idle_timeout = config.get('capture', 'idle_timeout_seconds', default=60)
    max_daily_requests = config.get('capture', 'max_daily_requests', default=1500)

    activity_monitor = ActivityMonitor(idle_timeout)
    activity_monitor.start()

    print(f"Database: {db_path}")
    print(f"Capture interval: {interval}s")
    print(f"Idle timeout: {idle_timeout}s")
    print(f"Max daily API calls: {max_daily_requests}")
    print("\nStarting capture loop... (Press Ctrl+C to stop)\n")

    try:
        iteration = 0
        while True:
            iteration += 1

            if activity_monitor.is_idle():
                idle_time = activity_monitor.seconds_since_activity()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] IDLE - No activity for {idle_time}s")
                time.sleep(5)
                continue

            api_usage = db.get_api_usage_today()
            if api_usage >= max_daily_requests:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] QUOTA EXCEEDED - {api_usage}/{max_daily_requests} API calls used")
                time.sleep(interval)
                continue

            print(f"\n--- Iteration {iteration} [{datetime.now().strftime('%H:%M:%S')}] ---")

            print("Capturing screenshot...")
            screenshot_path = capturer.capture()
            print(f"✓ Screenshot saved: {screenshot_path}")

            if hasher.is_duplicate(screenshot_path):
                print("⊘ Duplicate screenshot detected - skipping Gemini analysis")
                capturer.cleanup_screenshot(screenshot_path)
                print(f"✓ Screenshot deleted")
                time.sleep(interval)
                continue

            # Get previous 2 captures for context (Phase 5)
            previous_captures = db.get_previous_captures(limit=2)

            print("Analyzing with Gemini Vision API (with context)...")

            try:
                result = analyzer.analyze_with_fallback(screenshot_path, previous_captures)

                if result:
                    print(f"✓ Analysis complete:")
                    print(f"  Category: {result.get('category_emoji', '📝')} {result['category']}")
                    print(f"  App:      {result['app']}")
                    print(f"  Task:     {result['task']}")
                    print(f"  Confidence: {result['confidence']:.2f}")

                    # Show detailed context if available
                    detailed_context = result.get('detailed_context', {})
                    if detailed_context:
                        print(f"\n  --- Detailed Context ---")
                        for key, value in detailed_context.items():
                            if value:
                                print(f"  {key}: {value}")
                        print(f"  ------------------------\n")

                    # Store with detailed context
                    detailed_context_json = json.dumps(detailed_context) if detailed_context else None

                    capture_id = db.insert_capture(
                        timestamp=datetime.now(),
                        category=result['category'],
                        app_name=result['app'],
                        task=result['task'],
                        confidence=result['confidence'],
                        detailed_context=detailed_context_json,
                        category_emoji=result.get('category_emoji'),
                        category_color=result.get('category_color')
                    )
                    print(f"✓ Saved to database (ID: {capture_id})")

                    db.increment_api_usage()
                    new_usage = db.get_api_usage_today()
                    print(f"  API usage: {new_usage}/{max_daily_requests}")
                else:
                    print("✗ Analysis failed")

            except RateLimitError as e:
                print(f"\n🛑 RATE LIMIT EXCEEDED - API quota exhausted")
                print(f"The API returned: {str(e)}")
                print(f"\nRecommendations:")
                print(f"  1. Wait for quota to reset (usually at midnight UTC)")
                print(f"  2. Check your quota at: https://ai.dev/usage?tab=rate-limit")
                print(f"  3. Consider using a paid tier for higher limits")
                print(f"\nPausing capture loop for {e.retry_after} seconds...")

                capturer.cleanup_screenshot(screenshot_path)
                time.sleep(e.retry_after)
                continue

            capturer.cleanup_screenshot(screenshot_path)
            print(f"✓ Screenshot deleted")

            print(f"\nWaiting {interval} seconds...")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nStopping capture loop...")
    finally:
        activity_monitor.stop()
        capturer.cleanup_all()
        print("✓ Cleanup complete")


def show_stats():
    """Show today's statistics."""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    db_path = config.get('storage', 'database_path')
    db = Database(db_path)

    print("=== Today's Statistics ===\n")

    stats = db.get_today_stats()

    print(f"Total captures: {stats['total_captures']}")
    print(f"\nEstimated time breakdown:")
    print(f"  Work:          {stats['work'] // 60}m")
    print(f"  Learning:      {stats['learning'] // 60}m")
    print(f"  Browsing:      {stats['browsing'] // 60}m")
    print(f"  Entertainment: {stats['entertainment'] // 60}m")
    print(f"  Idle:          {stats['idle'] // 60}m")

    api_usage = db.get_api_usage_today()
    max_daily = config.get('capture', 'max_daily_requests', default=1500)
    print(f"\nAPI usage: {api_usage}/{max_daily} ({api_usage*100//max_daily}%)")

    print("\nRecent captures:")
    recent = db.get_recent_captures(hours=2, limit=10)
    for capture in recent:
        timestamp = capture['timestamp']
        category = capture['category']
        app = capture['app_name']
        task = capture['task']
        print(f"  {timestamp} - [{category}] {app}: {task}")


def run_tui():
    """Run the interactive TUI application."""
    print("Loading TUI...")

    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun setup first: python main.py setup")
        return
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    # Check macOS permissions if on macOS
    if sys.platform == 'darwin':
        try:
            from core.macos_permissions import check_permissions_silent, show_permission_instructions
            status = check_permissions_silent()
            if not status['screen_recording']:
                show_permission_instructions("screen_recording")
                print("\n❌ Telos cannot start without Screen Recording permission")
                print("Please grant the permission and restart Telos\n")
                return
            if not status['accessibility']:
                print("\n⚠️  Warning: Accessibility permission not granted")
                print("Idle detection may not work correctly")
                print("Press Enter to continue...")
                input()
        except ImportError:
            # macos_permissions module not available, skip check
            pass

    # Check if onboarding is needed
    from core.onboarding import OnboardingManager
    onboarding_mgr = OnboardingManager()
    
    if onboarding_mgr.is_first_run():
        print("First run detected - starting onboarding...")
        run_onboarding(config, onboarding_mgr)
        
        # Check if onboarding was completed
        if not onboarding_mgr.is_onboarding_complete():
            print("Onboarding cancelled.")
            return

    # Import here to avoid loading Textual if not needed
    from tui.app import TelosApp

    app = TelosApp(config)
    app.run()


def set_analysis_goals():
    """Set analysis goals via CLI."""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error: {e}")
        return

    db = Database(config.get('storage', 'database_path'))
    goal_manager = AnalysisGoalManager(db)

    print("=== Set Analysis Goals ===\n")
    print("Available presets:\n")

    presets = AnalysisGoalManager.PRESET_GOALS
    for i, (key, preset) in enumerate(presets.items(), 1):
        print(f"  {i}. {preset['name']}")
        print(f"     {preset['focus']}")
        print()

    choice = input("Enter preset number (1-5): ").strip()

    try:
        choice_num = int(choice)
        preset_keys = list(presets.keys())

        if 1 <= choice_num <= len(preset_keys):
            preset = preset_keys[choice_num - 1]

            if preset == "custom":
                custom_text = input("\nDescribe what you want to track: ").strip()
                goal_manager.set_goals(preset, custom_text)
                print(f"\n✓ Analysis goals updated to: Custom")
                print(f"  Focus: {custom_text}")
            else:
                goal_manager.set_goals(preset)
                print(f"\n✓ Analysis goals updated to: {presets[preset]['name']}")
                print(f"  Focus: {presets[preset]['focus']}")
        else:
            print("Invalid choice")
            return

    except (ValueError, IndexError):
        print("Invalid input")
        return


def build_sessions():
    """Manually trigger session building."""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error: {e}")
        return

    db = Database(config.get('storage', 'database_path'))
    analyzer = GeminiAnalyzer(
        config.get('gemini', 'api_key'),
        config.get('gemini', 'model')
    )
    goal_manager = AnalysisGoalManager(db)
    builder = SessionBuilder(db, analyzer, goal_manager)

    print("=== Building Sessions ===\n")
    print("Processing unprocessed captures...")

    session_ids = builder.build_sessions()

    if not session_ids:
        print("No sessions created. Make sure you have unprocessed captures.")
        return

    print(f"✓ Created {len(session_ids)} session(s)\n")

    print("Enriching sessions with AI analysis...")
    for i, session_id in enumerate(session_ids, 1):
        print(f"  [{i}/{len(session_ids)}] Enriching session {session_id}... ", end='', flush=True)

        success = builder.enrich_session_with_retry(session_id)

        if success:
            db.increment_api_usage()
            print("✓")
        else:
            print("✗ (failed)")

    print(f"\n✓ Session building complete!")
    print(f"  API usage: {db.get_api_usage_today()}/{config.get('capture', 'max_daily_requests', default=1500)}")


def generate_summary():
    """Generate daily summary."""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error: {e}")
        return

    db = Database(config.get('storage', 'database_path'))
    analyzer = GeminiAnalyzer(
        config.get('gemini', 'api_key'),
        config.get('gemini', 'model')
    )
    goal_manager = AnalysisGoalManager(db)
    aggregator = DailyAggregator(db, analyzer, goal_manager)

    today = datetime.now()

    print(f"=== Generating Daily Summary for {today.strftime('%Y-%m-%d')} ===\n")

    # Check for existing summary
    existing = db.get_daily_summary(today)
    if existing:
        print("A summary already exists for today.")
        response = input("Do you want to regenerate it? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return

    print("Analyzing sessions and generating summary... (This may take 10-15 seconds)")

    summary_id = aggregator.generate_daily_summary(today)

    if summary_id:
        db.increment_api_usage()
        summary = db.get_daily_summary(today)

        print(f"\n✓ Summary generated (ID: {summary_id})")
        print(f"\nProductivity Score: {summary['productivity_score']:.1f}/100")
        print(f"\nTime Breakdown:")
        print(f"  Work:          {summary['work_seconds'] // 60}m")
        print(f"  Learning:      {summary['learning_seconds'] // 60}m")
        print(f"  Browsing:      {summary['browsing_seconds'] // 60}m")
        print(f"  Entertainment: {summary['entertainment_seconds'] // 60}m")
        print(f"\nContext Switches: {summary['context_switches']}")
        print(f"\nDaily Narrative:")
        print(f"{summary['daily_narrative']}")

        print(f"\nAPI usage: {db.get_api_usage_today()}/{config.get('capture', 'max_daily_requests', default=1500)}")
    else:
        print("✗ Failed to generate summary (no sessions found?)")


def test_email():
    """Test email configuration by sending a test report."""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Check if email is configured
    email_enabled = config.get('email', 'enabled', default=False)
    if not email_enabled:
        print("Error: Email is not enabled in config.yaml")
        print("\nTo enable email reports:")
        print("  1. Edit config.yaml")
        print("  2. Set email.enabled to true")
        print("  3. Configure SMTP settings")
        return

    print("=== Testing Email Configuration ===\n")

    db = Database(config.get('storage', 'database_path'))
    analyzer = GeminiAnalyzer(
        config.get('gemini', 'api_key'),
        config.get('gemini', 'model')
    )
    goal_manager = AnalysisGoalManager(db)
    aggregator = DailyAggregator(db, analyzer, goal_manager)

    # Import email reporter
    from core.email_reporter import EmailReporter
    email_reporter = EmailReporter(
        smtp_host=config.get('email', 'smtp_host'),
        smtp_port=config.get('email', 'smtp_port'),
        sender_email=config.get('email', 'sender_email'),
        sender_password=config.get('email', 'sender_password'),
        recipient_email=config.get('email', 'recipient_email')
    )

    today = datetime.now()

    # Get or generate summary
    summary = db.get_daily_summary(today)
    if not summary:
        print("No summary exists for today. Generating...")
        summary_id = aggregator.generate_daily_summary(today)

        if summary_id:
            db.increment_api_usage()
            summary = db.get_daily_summary(today)
        else:
            print("✗ Failed to generate summary (no data yet?)")
            print("\nRun the tracker for a while to collect data first:")
            print("  python main.py test")
            return

    print(f"Sending test email to: {config.get('email', 'recipient_email')}")
    print("This may take a few seconds...\n")

    success = email_reporter.send_daily_report(summary)

    if success:
        print("\n✓ Test email sent successfully!")
        print("\nCheck your inbox. If you don't see the email:")
        print("  1. Check your spam/junk folder")
        print("  2. Verify SMTP settings in config.yaml")
        print("  3. For Gmail, make sure you're using an App Password")
    else:
        print("\n✗ Failed to send test email")
        print("\nTroubleshooting:")
        print("  1. Verify SMTP host and port in config.yaml")
        print("  2. For Gmail: Use smtp.gmail.com port 587")
        print("  3. Use Gmail App Password (not regular password)")
        print("     Create at: https://myaccount.google.com/apppasswords")


def run_service_console():
    """Run service in console mode (for testing before installing as service)."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import run_console_mode
    elif sys.platform == 'win32':  # Windows
        from service import run_console_mode
    else:
        print("Service mode not supported on this platform")
        return
    run_console_mode()


def install_service():
    """Install platform service (Windows Service or macOS LaunchAgent)."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import install_service
    elif sys.platform == 'win32':  # Windows
        from service import install_service
    else:
        print("Service mode not supported on this platform")
        return
    install_service()


def uninstall_service():
    """Uninstall platform service."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import uninstall_service
    elif sys.platform == 'win32':  # Windows
        from service import uninstall_service
    else:
        print("Service mode not supported on this platform")
        return
    uninstall_service()


def start_service():
    """Start platform service."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import start_service
    elif sys.platform == 'win32':  # Windows
        from service import start_service
    else:
        print("Service mode not supported on this platform")
        return
    start_service()


def stop_service():
    """Stop platform service."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import stop_service
    elif sys.platform == 'win32':  # Windows
        from service import stop_service
    else:
        print("Service mode not supported on this platform")
        return
    stop_service()


def service_status():
    """Check platform service status."""
    if sys.platform == 'darwin':  # macOS
        from service_macos import service_status
    elif sys.platform == 'win32':  # Windows
        from service import service_status
    else:
        print("Service mode not supported on this platform")
        return
    service_status()


def run_onboarding(config, onboarding_mgr):
    """Run the onboarding flow in TUI.
    
    Args:
        config: ConfigManager instance
        onboarding_mgr: OnboardingManager instance
    """
    from textual.app import App
    from tui.screens import (
        WelcomeScreen, PrivacyNoticeScreen, GoalSetupScreen, 
        EmailSetupScreen, OnboardingCompleteScreen
    )
    from core.trial_manager import TrialManager
    from core.backend_client import BackendClient
    from core.firebase_auth import FirebaseAuth
    from core.goal_manager import AnalysisGoalManager
    from core.database import Database
    
    class OnboardingApp(App):
        """Temporary app for onboarding flow."""
        
        def __init__(self, config, onboarding_mgr):
            super().__init__()
            self.config = config
            self.onboarding_mgr = onboarding_mgr
            self.trial_manager = TrialManager(config, trial_duration_days=7)
        
        def on_mount(self) -> None:
            """Start onboarding flow in a worker."""
            self.run_worker(self.run_onboarding_flow(), exclusive=True)
        
        async def run_onboarding_flow(self) -> None:
            """Run the complete onboarding flow."""
            # Welcome screen
            result = await self.push_screen_wait(WelcomeScreen())
            if not result:
                self.exit()
                return
            
            # Privacy notice
            result = await self.push_screen_wait(PrivacyNoticeScreen())
            if not result:
                self.exit()
                return
            
            # Start trial
            self.trial_manager.start_trial()
            
            # Backend connection test (if enabled)
            backend_enabled = self.config.get('backend', 'enabled', default=False)
            if backend_enabled:
                backend_url = self.config.get('backend', 'url', default="")
                if backend_url:
                    try:
                        # Test connection without auth
                        import requests
                        response = requests.get(f"{backend_url}/health", timeout=5)
                        if response.status_code == 200:
                            self.notify("✓ Backend connected successfully", severity="information")
                        else:
                            self.notify("⚠ Backend connection failed - using local mode", severity="warning")
                    except:
                        self.notify("⚠ Backend unreachable - using local mode", severity="warning")
            
            # Optional: Goals setup
            goal_result = await self.push_screen_wait(GoalSetupScreen())
            if goal_result:
                db = Database(self.config.get('storage', 'database_path'))
                goal_manager = AnalysisGoalManager(db)
                goal_manager.set_goals(
                    goal_result['goal'], 
                    goal_result.get('custom_text')
                )
                self.notify("✓ Goals configured", severity="success")
            
            # Optional: Email setup
            email_result = await self.push_screen_wait(EmailSetupScreen())
            if email_result:
                email_config = self.config.config.get('email', {})
                email_config['enabled'] = True
                email_config['sender_email'] = email_result['email']
                email_config['recipient_email'] = email_result['email']
                email_config['sender_password'] = email_result['password']
                email_config['send_time'] = email_result['send_time']
                self.config.config['email'] = email_config
                self.config.save(self.config.config)
                self.notify("✓ Email configured", severity="success")
            
            # Completion screen
            await self.push_screen_wait(OnboardingCompleteScreen())
            
            # Mark onboarding complete
            self.onboarding_mgr.mark_complete()
            
            self.exit()
    
    app = OnboardingApp(config, onboarding_mgr)
    app.run()


def show_usage():
    """Show usage information."""
    print("""
Telos - AI-powered activity tracking

Usage:
    python main.py                  - Run TUI interface (default)
    python main.py run              - Run TUI interface
    python main.py setup            - First-time setup (configure API key)
    python main.py test             - Test capture loop (CLI mode)
    python main.py stats            - Show today's statistics
    python main.py set-goals        - Set analysis goals (Phase 3)
    python main.py build-sessions   - Manually build sessions (Phase 3)
    python main.py generate-summary - Generate daily summary (Phase 3)
    python main.py test-email       - Test email configuration (Phase 4)
    python main.py help             - Show this help message

Service/Daemon Mode (Phase 4):
    python main.py service-console  - Run as daemon in console (test mode)
    python main.py install-service  - Install Windows service (requires admin)
    python main.py uninstall-service- Uninstall Windows service (requires admin)
    python main.py start-service    - Start Windows service
    python main.py stop-service     - Stop Windows service
    python main.py service-status   - Check service status

Phase 1 ✓ COMPLETE - Core Foundation:
  ✓ Screenshot capture with activity detection
  ✓ Idle detection (pauses when inactive)
  ✓ Perceptual hashing (skips duplicate screenshots)
  ✓ Gemini Vision API integration
  ✓ SQLite database storage
  ✓ Automatic screenshot deletion
  ✓ API quota tracking

Phase 2 ✓ COMPLETE - TUI Interface:
  ✓ Real-time Textual dashboard
  ✓ Live activity tracking
  ✓ Category breakdown with progress bars
  ✓ Timeline and summary views

Phase 3 ✓ COMPLETE - Intelligence Layer:
  ✓ Session building (smart grouping of captures)
  ✓ AI-powered session enrichment
  ✓ Customizable analysis goals
  ✓ Daily summaries with productivity scoring
  ✓ Key learnings extraction

Phase 4 - IN PROGRESS - Production Ready:
  ✓ Email reports (end-of-day summaries)
  ✓ Windows Service (daemon mode)
  - Export functionality
  - Advanced error handling
  - Performance optimization

Phase 5 ✓ COMPLETE - Rich Capture & AI Chat:
  ✓ Rich context extraction (file names, URLs, detailed descriptions)
  ✓ AI Chat interface (press 'A' in TUI)
  ✓ Natural language queries about your work
  ✓ Content generation (LinkedIn posts, tweets, etc.)
  ✓ Smart context search (7-365 days)

TUI Keyboard Shortcuts:
  D - Dashboard  |  T - Timeline  |  S - Summary  |  C - Settings
  A - AI Chat 💬 (NEW!)  |  Q - Quit
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        command = "run"  # Default to TUI
    else:
        command = sys.argv[1].lower()

    if command == "setup":
        setup_config()
    elif command == "run" or command == "tui":
        run_tui()
    elif command == "test":
        test_capture_loop()
    elif command == "stats":
        show_stats()
    elif command == "set-goals":
        set_analysis_goals()
    elif command == "build-sessions":
        build_sessions()
    elif command == "generate-summary":
        generate_summary()
    elif command == "test-email":
        test_email()
    elif command == "service-console":
        run_service_console()
    elif command == "install-service":
        install_service()
    elif command == "uninstall-service":
        uninstall_service()
    elif command == "start-service":
        start_service()
    elif command == "stop-service":
        stop_service()
    elif command == "service-status":
        service_status()
    elif command == "help":
        show_usage()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python main.py help' for usage information")


if __name__ == "__main__":
    main()
