"""
Telos CLI - Entry point for pip-installed package.

Handles user data directory initialization and delegates to main modules.
"""

import os
import sys
import shutil
from pathlib import Path

# Determine if we're running from pip install or development
def get_package_root() -> Path:
    """Get the root directory of the installed package."""
    return Path(__file__).parent.parent


def get_user_data_dir() -> Path:
    """Get user data directory (~/.telos)."""
    return Path.home() / ".telos"


def get_prompts_dir() -> Path:
    """Get prompts directory (user data or package bundled)."""
    user_prompts = get_user_data_dir() / "prompts"
    if user_prompts.exists():
        return user_prompts
    
    # Fall back to package bundled prompts
    package_prompts = get_package_root() / "prompts"
    if package_prompts.exists():
        return package_prompts
    
    # Development mode - prompts in same directory as script
    return Path(__file__).parent.parent / "prompts"


def ensure_user_data_dir():
    """Create user data directory and copy default files if needed."""
    user_dir = get_user_data_dir()
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Create prompts subdirectory
    prompts_dir = user_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    
    # Create temp_screenshots directory
    temp_dir = user_dir / "temp_screenshots"
    temp_dir.mkdir(exist_ok=True)
    
    return user_dir


def get_bundled_resource_dir() -> Path:
    """Get directory containing bundled resources (for pip-installed package)."""
    # Check if we're in the telos_tracker package (pip installed)
    package_dir = Path(__file__).parent
    if (package_dir / "config.yaml.example").exists():
        return package_dir
    
    # Fall back to parent (development mode)
    return package_dir.parent


def copy_default_config():
    """Copy default config.yaml.example to user directory."""
    user_dir = get_user_data_dir()
    user_config = user_dir / "config.yaml"
    
    if user_config.exists():
        return user_config
    
    # Look for config.yaml.example in bundled resources
    bundled_dir = get_bundled_resource_dir()
    example_config = bundled_dir / "config.yaml.example"
    
    if example_config.exists():
        shutil.copy(example_config, user_config)
        print(f"Created config at: {user_config}")
    else:
        # Create minimal config
        minimal_config = '''gemini:
  api_key: "YOUR_GEMINI_API_KEY_HERE"
  model: "gemini-2.5-flash"

capture:
  interval_seconds: 30
  idle_timeout_seconds: 60
  screenshot_quality: 85
  max_daily_requests: 1500
  use_previous_context: true
  detailed_analysis: true

storage:
  database_path: "~/.telos/tracker.db"
  captures_retention_days: 365
  sessions_retention_days: 90

display:
  refresh_rate_ms: 1000
  theme: "dark"

intelligence:
  session_trigger_hours: 2
  session_trigger_idle_minutes: 5
  check_interval_seconds: 60
  max_enrichment_per_trigger: 3
  min_session_captures: 2
  session_gap_seconds: 300

email:
  enabled: false
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender_email: ""
  sender_password: ""
  recipient_email: ""
  send_time: "21:00"

backend:
  enabled: false
  url: ""
  fallback_to_local: true

trial:
  start_date: ""
  duration_days: 7
  upgrade_prompts_shown: 0

account:
  auth_type: "anonymous"
  user_id: ""
  email: ""

schema_version: 2
'''
        user_config.write_text(minimal_config)
        print(f"Created default config at: {user_config}")
    
    return user_config


def copy_default_prompts():
    """Copy default prompts to user directory if not present."""
    user_prompts = get_user_data_dir() / "prompts"
    user_prompts.mkdir(exist_ok=True)
    
    # Look for bundled prompts in package directory
    bundled_dir = get_bundled_resource_dir()
    package_prompts = bundled_dir / "prompts"
    
    if not package_prompts.exists():
        return
    
    for prompt_file in package_prompts.glob("*.txt"):
        user_prompt = user_prompts / prompt_file.name
        if not user_prompt.exists():
            shutil.copy(prompt_file, user_prompt)


def setup_environment():
    """Set up environment for pip-installed package."""
    user_dir = ensure_user_data_dir()
    
    # Add package root to path so imports work
    package_root = get_package_root()
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    
    # Change to user data directory for relative paths
    os.chdir(user_dir)
    
    return user_dir


def interactive_setup():
    """Interactive setup wizard for first-time users."""
    print("=== Telos Setup ===\n")
    
    user_dir = ensure_user_data_dir()
    config_path = user_dir / "config.yaml"
    
    if config_path.exists():
        print(f"Configuration already exists at {config_path}")
        response = input("Do you want to reconfigure? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Create config from template
    copy_default_config()
    copy_default_prompts()
    
    # Prompt for API key
    api_key = input("\nEnter your Gemini API key: ").strip()
    
    if not api_key:
        print("\nNo API key entered. You can add it later to:")
        print(f"  {config_path}")
        return
    
    # Update config with API key
    import yaml
    
    config_content = config_path.read_text()
    config = yaml.safe_load(config_content)
    config['gemini']['api_key'] = api_key
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n[OK] Configuration saved to {config_path}")
    print("[OK] Setup complete! Run 'telos' to start tracking.")


def show_help():
    """Show help information."""
    print("""
Telos - AI-powered activity tracking

Usage:
    telos              - Launch TUI interface
    telos setup        - First-time setup (configure API key)
    telos test         - Test capture loop
    telos stats        - Show today's statistics
    telos help         - Show this help message

Data Location:
    ~/.telos/          - User data directory
    ~/.telos/config.yaml    - Configuration
    ~/.telos/tracker.db     - Activity database
    ~/.telos/prompts/       - AI prompts

TUI Keyboard Shortcuts:
    D - Dashboard  |  T - Timeline  |  S - Summary
    A - AI Chat    |  G - Goals     |  H - Help
    Q - Quit

For more information: https://github.com/yourusername/telos
""")


def main():
    """Main CLI entry point."""
    # Handle help before setting up environment
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('help', '--help', '-h'):
        show_help()
        return
    
    # Handle setup command
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'setup':
        interactive_setup()
        return
    
    # Set up environment for other commands
    user_dir = setup_environment()
    
    # Check if config exists, prompt setup if not
    config_path = user_dir / "config.yaml"
    if not config_path.exists():
        print("Telos is not configured yet.\n")
        response = input("Would you like to run setup now? (Y/n): ").strip().lower()
        if response != 'n':
            interactive_setup()
            return
        else:
            print("\nRun 'telos setup' when ready to configure.")
            return
    
    # Import main module and delegate
    try:
        # Try pip-installed location first
        from telos_tracker.main import main as app_main
        app_main()
    except ImportError:
        try:
            # Fall back to development mode (running from source)
            from main import main as app_main
            app_main()
        except ImportError as e:
            print(f"Import error: {e}")
            print("\nTry running from the client directory:")
            print("  cd client && python main.py")


if __name__ == "__main__":
    main()

