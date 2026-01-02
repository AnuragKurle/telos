"""
Windows Service Wrapper

Runs Screen Time Tracker as a Windows Service using pywin32.
"""

import sys
import os
import servicemanager
import win32event
import win32service
import win32serviceutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config_manager import load_config
from utils.hash_utils import ScreenshotHasher
from core.database import Database
from core.capture import ActivityMonitor, ScreenshotCapture
from core.analyzer import GeminiAnalyzer
from core.goal_manager import AnalysisGoalManager
from core.session_builder import SessionBuilder
from core.daily_aggregator import DailyAggregator
from core.email_reporter import EmailReporter
from core.service_daemon import ServiceDaemon


class TelosService(win32serviceutil.ServiceFramework):
    """Windows Service for Telos."""

    _svc_name_ = "Telos"
    _svc_display_name_ = "Telos"
    _svc_description_ = "AI-powered screen time tracker with intelligent activity analysis"

    def __init__(self, args):
        """Initialize Windows service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.daemon = None

    def SvcStop(self):
        """Handle service stop request."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

        # Stop daemon
        if self.daemon:
            self.daemon.stop()

    def SvcDoRun(self):
        """Main service execution."""
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )

            self.main()

        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")
            raise

    def main(self):
        """Service main logic."""
        try:
            # Load configuration
            config = load_config()

            # Initialize database
            db_path = config.get('storage', 'database_path')
            db = Database(db_path)

            # Initialize Gemini analyzer
            api_key = config.get('gemini', 'api_key')
            model = config.get('gemini', 'model')
            analyzer = GeminiAnalyzer(api_key, model)

            # Initialize goal manager
            goal_manager = AnalysisGoalManager(db)

            # Initialize capture components
            quality = config.get('capture', 'screenshot_quality', default=85)
            capturer = ScreenshotCapture(quality)
            hasher = ScreenshotHasher()

            # Initialize activity monitor
            idle_timeout = config.get('capture', 'idle_timeout_seconds', default=60)
            activity_monitor = ActivityMonitor(idle_timeout)

            # Initialize session builder
            session_builder = SessionBuilder(db, analyzer, goal_manager)

            # Initialize daily aggregator
            daily_aggregator = DailyAggregator(db, analyzer, goal_manager)

            # Initialize email reporter (if enabled)
            email_reporter = None
            email_enabled = config.get('email', 'enabled', default=False)
            if email_enabled:
                email_reporter = EmailReporter(
                    smtp_host=config.get('email', 'smtp_host'),
                    smtp_port=config.get('email', 'smtp_port'),
                    sender_email=config.get('email', 'sender_email'),
                    sender_password=config.get('email', 'sender_password'),
                    recipient_email=config.get('email', 'recipient_email')
                )

            # Create and start service daemon
            self.daemon = ServiceDaemon(
                config=config,
                db=db,
                analyzer=analyzer,
                goal_manager=goal_manager,
                capturer=capturer,
                activity_monitor=activity_monitor,
                hasher=hasher,
                session_builder=session_builder,
                daily_aggregator=daily_aggregator,
                email_reporter=email_reporter
            )

            self.daemon.start()

            servicemanager.LogInfoMsg("Telos service started successfully")

            # Wait for stop signal
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

            servicemanager.LogInfoMsg("Telos service stopped")

        except Exception as e:
            servicemanager.LogErrorMsg(f"Service initialization error: {e}")
            raise


def install_service():
    """Install Windows service."""
    try:
        # Check if running as administrator
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Error: Administrator privileges required to install service")
            print("Please run this command as Administrator")
            return False

        # Install service
        sys.argv = [
            sys.argv[0],
            '--startup=auto',  # Auto-start on boot
            'install'
        ]
        win32serviceutil.HandleCommandLine(TelosService)

        print("\n✓ Service installed successfully")
        print(f"  Name: {TelosService._svc_name_}")
        print(f"  Display Name: {TelosService._svc_display_name_}")
        print("\nYou can now start the service with:")
        print("  python main.py start-service")
        print("\nOr start it from Windows Services (services.msc)")

        return True

    except Exception as e:
        print(f"✗ Failed to install service: {e}")
        return False


def uninstall_service():
    """Uninstall Windows service."""
    try:
        # Check if running as administrator
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Error: Administrator privileges required to uninstall service")
            print("Please run this command as Administrator")
            return False

        # Uninstall service
        sys.argv = [sys.argv[0], 'remove']
        win32serviceutil.HandleCommandLine(TelosService)

        print("\n✓ Service uninstalled successfully")

        return True

    except Exception as e:
        print(f"✗ Failed to uninstall service: {e}")
        return False


def start_service():
    """Start Windows service."""
    try:
        win32serviceutil.StartService(TelosService._svc_name_)
        print(f"✓ Service '{TelosService._svc_display_name_}' started successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to start service: {e}")
        print("\nMake sure the service is installed:")
        print("  python main.py install-service")
        return False


def stop_service():
    """Stop Windows service."""
    try:
        win32serviceutil.StopService(TelosService._svc_name_)
        print(f"✓ Service '{TelosService._svc_display_name_}' stopped successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to stop service: {e}")
        return False


def service_status():
    """Check Windows service status."""
    try:
        status = win32serviceutil.QueryServiceStatus(TelosService._svc_name_)

        status_map = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "STARTING",
            win32service.SERVICE_STOP_PENDING: "STOPPING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "RESUMING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSING",
            win32service.SERVICE_PAUSED: "PAUSED"
        }

        status_str = status_map.get(status[1], "UNKNOWN")

        print(f"Service Status: {status_str}")
        return True

    except Exception as e:
        print(f"Service Status: NOT INSTALLED")
        print(f"\nTo install the service, run:")
        print("  python main.py install-service")
        return False


def run_console_mode():
    """Run service in console mode (for testing)."""
    print("=== Telos - Console Mode ===")
    print("Running service in console (not as Windows Service)")
    print("Press Ctrl+C to stop\n")

    try:
        # Load configuration
        config = load_config()

        # Initialize database
        db_path = config.get('storage', 'database_path')
        db = Database(db_path)

        # Initialize Gemini analyzer
        api_key = config.get('gemini', 'api_key')
        model = config.get('gemini', 'model')
        analyzer = GeminiAnalyzer(api_key, model)

        # Initialize goal manager
        goal_manager = AnalysisGoalManager(db)

        # Initialize capture components
        quality = config.get('capture', 'screenshot_quality', default=85)
        capturer = ScreenshotCapture(quality)
        hasher = ScreenshotHasher()

        # Initialize activity monitor
        idle_timeout = config.get('capture', 'idle_timeout_seconds', default=60)
        activity_monitor = ActivityMonitor(idle_timeout)

        # Initialize session builder
        session_builder = SessionBuilder(db, analyzer, goal_manager)

        # Initialize daily aggregator
        daily_aggregator = DailyAggregator(db, analyzer, goal_manager)

        # Initialize email reporter (if enabled)
        email_reporter = None
        email_enabled = config.get('email', 'enabled', default=False)
        if email_enabled:
            email_reporter = EmailReporter(
                smtp_host=config.get('email', 'smtp_host'),
                smtp_port=config.get('email', 'smtp_port'),
                sender_email=config.get('email', 'sender_email'),
                sender_password=config.get('email', 'sender_password'),
                recipient_email=config.get('email', 'recipient_email')
            )

        # Create and start service daemon
        daemon = ServiceDaemon(
            config=config,
            db=db,
            analyzer=analyzer,
            goal_manager=goal_manager,
            capturer=capturer,
            activity_monitor=activity_monitor,
            hasher=hasher,
            session_builder=session_builder,
            daily_aggregator=daily_aggregator,
            email_reporter=email_reporter
        )

        daemon.start()

        # Run forever
        daemon.run_forever()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun setup first: python main.py setup")

    except ValueError as e:
        print(f"Configuration error: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    # If called directly, handle Windows service commands
    if len(sys.argv) == 1:
        # Called by Windows Service Manager
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TelosService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command line
        win32serviceutil.HandleCommandLine(TelosService)

