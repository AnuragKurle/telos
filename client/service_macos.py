"""
macOS LaunchAgent Wrapper for Telos

Manages Telos as a macOS LaunchAgent for background operation.
Uses launchctl to install, start, stop, and monitor the service.
"""

import os
import sys
import subprocess
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

# LaunchAgent configuration
LAUNCH_AGENT_LABEL = "dev.telos.tracker"
LAUNCH_AGENT_PLIST = f"{LAUNCH_AGENT_LABEL}.plist"
PLIST_DIR = Path.home() / "Library/LaunchAgents"
PLIST_PATH = PLIST_DIR / LAUNCH_AGENT_PLIST


def get_app_executable():
    """Get the path to the Telos executable."""
    # Check if running from .app bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled app
        return sys.executable
    else:
        # Running as Python script
        return sys.executable


def get_script_path():
    """Get the path to main.py."""
    if getattr(sys, 'frozen', False):
        # Running as compiled app - use the executable
        return None
    else:
        # Running as Python script
        return str(Path(__file__).parent / "main.py")


def create_plist_file():
    """Create LaunchAgent plist file."""
    # Determine paths
    executable = get_app_executable()
    script_path = get_script_path()
    
    # Build program arguments
    if script_path:
        # Running as Python script
        program_args = [executable, script_path, "service-console"]
    else:
        # Running as compiled app
        program_args = [executable, "service-console"]
    
    # Create plist content
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCH_AGENT_LABEL}</string>
    
    <key>ProgramArguments</key>
    <array>
"""
    
    for arg in program_args:
        plist_content += f"        <string>{arg}</string>\n"
    
    plist_content += """    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/tmp/telos.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/telos.error.log</string>
    
    <key>WorkingDirectory</key>
    <string>""" + str(Path.home()) + """</string>
</dict>
</plist>
"""
    
    return plist_content


def install_service():
    """Install Telos as a LaunchAgent."""
    try:
        print("=== Installing Telos LaunchAgent ===\n")
        
        # Create LaunchAgents directory if it doesn't exist
        PLIST_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ LaunchAgents directory: {PLIST_DIR}")
        
        # Create plist file
        plist_content = create_plist_file()
        PLIST_PATH.write_text(plist_content, encoding='utf-8')
        print(f"✅ Created plist file: {PLIST_PATH}")
        
        # Set permissions
        os.chmod(PLIST_PATH, 0o644)
        print(f"✅ Set permissions (644)")
        
        # Load the LaunchAgent
        result = subprocess.run(
            ["launchctl", "load", str(PLIST_PATH)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ LaunchAgent installed successfully")
            print(f"   Label: {LAUNCH_AGENT_LABEL}")
            print(f"   Plist: {PLIST_PATH}")
            print("\nThe service will start automatically at login.")
            print("\nYou can now:")
            print("  python main.py start-service   - Start the service")
            print("  python main.py stop-service    - Stop the service")
            print("  python main.py service-status  - Check service status")
            return True
        else:
            print(f"\n⚠️  LaunchAgent created but not loaded")
            print(f"   Error: {result.stderr}")
            print(f"\nYou can manually load it with:")
            print(f"  launchctl load {PLIST_PATH}")
            return False
            
    except Exception as e:
        print(f"\n❌ Failed to install LaunchAgent: {e}")
        return False


def uninstall_service():
    """Uninstall Telos LaunchAgent."""
    try:
        print("=== Uninstalling Telos LaunchAgent ===\n")
        
        # Check if plist exists
        if not PLIST_PATH.exists():
            print(f"ℹ️  LaunchAgent not installed (plist not found)")
            return True
        
        # Unload the LaunchAgent
        result = subprocess.run(
            ["launchctl", "unload", str(PLIST_PATH)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ LaunchAgent unloaded")
        else:
            # It's okay if unload fails (might not be loaded)
            print(f"ℹ️  LaunchAgent was not loaded")
        
        # Remove plist file
        PLIST_PATH.unlink()
        print(f"✅ Removed plist file: {PLIST_PATH}")
        
        print("\n✅ LaunchAgent uninstalled successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to uninstall LaunchAgent: {e}")
        return False


def start_service():
    """Start Telos service."""
    try:
        # Check if service is installed
        if not PLIST_PATH.exists():
            print("❌ Service not installed")
            print("\nInstall it first with:")
            print("  python main.py install-service")
            return False
        
        result = subprocess.run(
            ["launchctl", "start", LAUNCH_AGENT_LABEL],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Service '{LAUNCH_AGENT_LABEL}' started successfully")
            print("\nLogs are available at:")
            print("  /tmp/telos.log")
            print("  /tmp/telos.error.log")
            return True
        else:
            print(f"❌ Failed to start service: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return False


def stop_service():
    """Stop Telos service."""
    try:
        result = subprocess.run(
            ["launchctl", "stop", LAUNCH_AGENT_LABEL],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Service '{LAUNCH_AGENT_LABEL}' stopped successfully")
            return True
        else:
            print(f"❌ Failed to stop service: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to stop service: {e}")
        return False


def service_status():
    """Check Telos service status."""
    try:
        # Check if plist exists
        if not PLIST_PATH.exists():
            print("Service Status: NOT INSTALLED")
            print(f"\nTo install the service, run:")
            print("  python main.py install-service")
            return False
        
        # Check if service is running using launchctl list
        result = subprocess.run(
            ["launchctl", "list", LAUNCH_AGENT_LABEL],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Service Status: RUNNING")
            print(f"\nService details:")
            print(result.stdout)
            
            print("\nLog files:")
            print("  Standard output: /tmp/telos.log")
            print("  Standard error:  /tmp/telos.error.log")
            return True
        else:
            print("Service Status: INSTALLED but NOT RUNNING")
            print(f"\nTo start the service, run:")
            print("  python main.py start-service")
            return False
            
    except Exception as e:
        print(f"Service Status: ERROR")
        print(f"Error: {e}")
        return False


def run_console_mode():
    """Run service in console mode (for testing)."""
    print("=== Telos - Console Mode (macOS) ===")
    print("Running service in console (not as LaunchAgent)")
    print("Press Ctrl+C to stop\n")
    
    # Check for macOS permissions first
    if sys.platform == 'darwin':
        try:
            from core.macos_permissions import check_and_request_permissions
            if not check_and_request_permissions():
                print("\n⚠️  Missing required permissions")
                print("The app may not work correctly without Screen Recording permission")
                response = input("\nContinue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    return
        except ImportError:
            # macos_permissions not available yet, skip check
            pass

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
        import traceback
        traceback.print_exc()

