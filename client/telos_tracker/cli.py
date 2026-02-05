"""
Telos CLI - Entry point for pip-installed package.

Handles user data directory initialization and delegates to main modules.
"""

import os
import sys
import shutil
import subprocess
import platform
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
        # Create minimal config with backend enabled by default (SaaS mode)
        minimal_config = '''gemini:
  api_key: "BACKEND_MODE_NO_KEY_NEEDED"
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

firebase:
  api_key: "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8"
  auth_domain: "gen-lang-client-0772617718.firebaseapp.com"
  project_id: "gen-lang-client-0772617718"

backend:
  enabled: true
  url: "https://telos-backend-ae7k4avtpq-el.a.run.app"
  fallback_to_local: false

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

    # Also add the telos_tracker directory itself for imports
    telos_tracker_dir = Path(__file__).parent.parent
    if str(telos_tracker_dir) not in sys.path:
        sys.path.insert(0, str(telos_tracker_dir))

    # Change to user data directory for relative paths
    os.chdir(user_dir)

    return user_dir


# ============================================================================
# PATH DETECTION AND FIX UTILITIES
# ============================================================================

def get_scripts_dir() -> Path:
    """Get the directory where pip installs executable scripts."""
    if sys.platform == 'win32':
        # Windows: Scripts directory in Python installation
        return Path(sys.prefix) / "Scripts"
    else:
        # Unix/Mac: .local/bin for user installs, or bin for venv
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # Virtual environment
            return Path(sys.prefix) / "bin"
        else:
            # User install
            import site
            user_base = site.getuserbase()
            return Path(user_base) / "bin"


def is_command_available(command: str = "telos") -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


def get_shell_config_file() -> Path:
    """Get the shell configuration file for the current user."""
    shell = os.environ.get('SHELL', '').split('/')[-1]
    home = Path.home()

    # Detect shell and return appropriate config file
    if shell == 'zsh' or Path(home / '.zshrc').exists():
        return home / '.zshrc'
    elif shell == 'bash':
        # Prefer .bashrc on Linux, .bash_profile on Mac
        if sys.platform == 'darwin' and (home / '.bash_profile').exists():
            return home / '.bash_profile'
        return home / '.bashrc'
    elif shell == 'fish':
        config_dir = home / '.config' / 'fish'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.fish'
    else:
        # Default to .bashrc
        return home / '.bashrc'


def fix_path_windows(scripts_dir: Path) -> bool:
    """Add Scripts directory to Windows PATH (user environment variable)."""
    try:
        # Use setx to modify user PATH
        current_path = os.environ.get('PATH', '')
        scripts_dir_str = str(scripts_dir)

        # Check if already in PATH
        if scripts_dir_str.lower() in current_path.lower():
            print(f"  {scripts_dir} is already in PATH")
            return True

        # Add to PATH using setx
        print(f"  Adding {scripts_dir} to PATH...")
        result = subprocess.run(
            ['setx', 'PATH', f'{current_path};{scripts_dir_str}'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("  [OK] PATH updated successfully")
            print("\n  IMPORTANT: Close this terminal and open a new one for changes to take effect")
            print("  Then run: telos setup")
            return True
        else:
            print(f"  [FAIL] Failed to update PATH: {result.stderr}")
            return False

    except Exception as e:
        print(f"  [FAIL] Error updating PATH: {e}")
        return False


def fix_path_unix(scripts_dir: Path) -> bool:
    """Add Scripts directory to Unix/Mac PATH via shell config file."""
    try:
        config_file = get_shell_config_file()
        scripts_dir_str = str(scripts_dir)

        # Check if alias or PATH modification already exists
        if config_file.exists():
            content = config_file.read_text()
            if 'telos' in content and scripts_dir_str in content:
                print(f"  {config_file} already contains telos configuration")
                return True

        # Add to PATH
        shell_name = config_file.name
        print(f"  Adding to {config_file}...")

        if 'fish' in shell_name:
            # Fish shell syntax
            path_cmd = f'\n# Telos CLI\nset -gx PATH {scripts_dir_str} $PATH\n'
        else:
            # Bash/Zsh syntax
            path_cmd = f'\n# Telos CLI\nexport PATH="{scripts_dir_str}:$PATH"\n'

        with open(config_file, 'a') as f:
            f.write(path_cmd)

        print(f"  [OK] Added to {config_file}")
        print(f"\n  IMPORTANT: Run this command to apply changes:")
        print(f"    source {config_file}")
        print(f"  Then run: telos setup")
        return True

    except Exception as e:
        print(f"  [FAIL] Error updating shell config: {e}")
        return False


def run_fix_path():
    """Auto-fix PATH for the current platform."""
    print("\n=== Telos PATH Fix ===\n")

    scripts_dir = get_scripts_dir()
    print(f"Python Scripts directory: {scripts_dir}")

    # Check if telos is already available
    if is_command_available('telos'):
        print("\n[OK] 'telos' command is already available in PATH")
        telos_path = shutil.which('telos')
        print(f"  Location: {telos_path}")
        return True

    print("\n[FAIL] 'telos' command not found in PATH")
    print("\nAttempting to fix...\n")

    # Platform-specific fix
    if sys.platform == 'win32':
        success = fix_path_windows(scripts_dir)
    else:
        success = fix_path_unix(scripts_dir)

    if not success:
        print("\n⚠  Auto-fix failed. Manual steps:\n")
        if sys.platform == 'win32':
            print(f"1. Press Win+X → System → Advanced system settings")
            print(f"2. Click 'Environment Variables'")
            print(f"3. Under 'User variables', select 'Path' → Edit")
            print(f"4. Click 'New' and add: {scripts_dir}")
            print(f"5. Click OK and restart your terminal")
        else:
            config_file = get_shell_config_file()
            print(f"1. Edit {config_file}")
            print(f"2. Add this line:")
            print(f'   export PATH="{scripts_dir}:$PATH"')
            print(f"3. Save and run: source {config_file}")

        print(f"\n💡 Alternative: Use Python module directly")
        print(f"   python -m telos_tracker.cli")

    return success


def is_first_run() -> bool:
    """Check if this is the first run after installation."""
    marker = get_user_data_dir() / ".install_complete"
    return not marker.exists()


def mark_install_complete():
    """Mark installation as complete."""
    marker = get_user_data_dir() / ".install_complete"
    ensure_user_data_dir()
    marker.touch()


def offer_path_fix():
    """Offer to fix PATH on first run if command not available."""
    if is_command_available('telos'):
        # Command is available, mark as complete and continue
        mark_install_complete()
        return True

    # Command not available - offer to fix
    print("\n" + "="*60)
    print("  Welcome to Telos!")
    print("="*60)
    print("\n⚠  PATH Issue Detected")
    print("\nThe 'telos' command is not available in your PATH.")
    print("This is a common issue after pip install.\n")

    print("Quick fixes available:\n")
    print("1. Auto-fix PATH (recommended)")
    print("2. Continue with 'python -m telos_tracker.cli'")
    print("3. Skip for now\n")

    response = input("Choose option (1/2/3) [1]: ").strip() or "1"

    if response == "1":
        print()
        success = run_fix_path()
        mark_install_complete()
        return success
    elif response == "2":
        print("\n💡 You can run Telos using:")
        print("   python -m telos_tracker.cli setup")
        print("   python -m telos_tracker.cli\n")
        print("To fix PATH later, run:")
        print("   python -m telos_tracker.cli fix-path\n")
        mark_install_complete()
        return False
    else:
        print("\nTo fix PATH later, run:")
        print("   python -m telos_tracker.cli fix-path\n")
        mark_install_complete()
        return False


def run_doctor():
    """Run comprehensive installation diagnostics."""
    print("\n" + "="*60)
    print("  Telos Installation Doctor")
    print("="*60 + "\n")

    checks = []

    # Check 1: Package installed
    try:
        import telos_tracker
        version = telos_tracker.__version__
        checks.append(("Package installed", True, f"v{version}"))
    except ImportError:
        checks.append(("Package installed", False, "Not found"))

    # Check 2: Command available
    telos_available = is_command_available('telos')
    telos_path = shutil.which('telos') if telos_available else None
    checks.append(("'telos' command in PATH", telos_available, telos_path or "Not found"))

    # Check 3: Python version
    py_version = sys.version_info
    is_compat = py_version >= (3, 8)
    py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
    checks.append(("Python version >= 3.8", is_compat, py_version_str))

    # Check 4: Scripts directory
    scripts_dir = get_scripts_dir()
    scripts_exists = scripts_dir.exists()
    checks.append(("Scripts directory exists", scripts_exists, str(scripts_dir)))

    # Check 5: Scripts in PATH
    path_env = os.environ.get('PATH', '')
    scripts_in_path = str(scripts_dir) in path_env
    checks.append(("Scripts directory in PATH", scripts_in_path, "Yes" if scripts_in_path else "No"))

    # Check 6: Dependencies
    deps_to_check = [
        ('textual', 'textual'),
        ('rich', 'rich'),
        ('mss', 'mss'),
        ('PIL', 'Pillow'),
        ('yaml', 'PyYAML')
    ]

    all_deps_ok = True
    for import_name, package_name in deps_to_check:
        try:
            __import__(import_name)
            checks.append((f"  - {package_name}", True, "Installed"))
        except ImportError:
            checks.append((f"  - {package_name}", False, "Missing"))
            all_deps_ok = False

    # Check 7: Config file
    config_path = get_user_data_dir() / "config.yaml"
    config_exists = config_path.exists()
    checks.append(("Config file", config_exists, str(config_path) if config_exists else "Not created"))

    # Check 8: Database
    db_path = get_user_data_dir() / "tracker.db"
    db_exists = db_path.exists()
    checks.append(("Database", db_exists, str(db_path) if db_exists else "Not created"))

    # Check 9: Display available
    display_available = os.environ.get('DISPLAY') or sys.platform == 'win32'
    checks.append(("Display available", display_available, "Yes" if display_available else "Headless"))

    # Print all checks
    print("System Information:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Platform: {sys.platform}")
    print(f"  Architecture: {platform.machine()}\n")

    print("Health Checks:\n")
    for check_name, passed, details in checks:
        status = "[OK]" if passed else "[FAIL]"
        if check_name.startswith("  -"):
            # Indent sub-checks
            print(f"  {status} {check_name}: {details}")
        else:
            print(f"{status} {check_name}: {details}")

    # Count failures
    failures = [c for c in checks if not c[1]]

    if failures:
        print("\n" + "="*60)
        print("  Issues Found - Recommended Fixes")
        print("="*60 + "\n")

        for check_name, _, _ in failures:
            if "'telos' command" in check_name or "Scripts directory in PATH" in check_name:
                print("PATH Issue:")
                print("  • Run: telos fix-path")
                print("  • OR: python -m telos_tracker.cli fix-path")
                print("  • Alternative: Always use 'python -m telos_tracker.cli'\n")
            elif "Config file" in check_name:
                print("Configuration:")
                print("  • Run: telos setup")
                print("  • OR: python -m telos_tracker.cli setup\n")
            elif "Missing" in str(check_name):
                print("Dependencies:")
                print("  • Run: pip install telos-tracker --upgrade --force-reinstall\n")
            elif "Python version" in check_name:
                print("Python Version:")
                print("  • Telos requires Python 3.8 or higher")
                print(f"  • Current version: {py_version_str}")
                print("  • Please upgrade Python\n")
    else:
        print("\n" + "="*60)
        print("  All checks passed! Installation is healthy.")
        print("="*60)

    print("\nQuick Command Reference:")
    if telos_available:
        print("  telos setup      - Configure Telos")
        print("  telos            - Launch Telos")
    else:
        print("  python -m telos_tracker.cli setup   - Configure Telos")
        print("  python -m telos_tracker.cli         - Launch Telos")
        print("  python -m telos_tracker.cli fix-path - Fix PATH issue")

    return len(failures) == 0


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
    
    # Import yaml for config updates
    import yaml
    
    config_content = config_path.read_text()
    config = yaml.safe_load(config_content)
    
    # Ask how the user wants to run Telos
    print("How would you like to use Telos?\n")
    print("1. Just get it running (Recommended) - We handle the AI, you just track")
    print("   Includes a 7-day free trial, then $3/month. Cancel anytime.")
    print()
    print("2. Bring your own API key - Use your own Gemini API key (free tier available)")
    print()
    
    mode = input("Enter choice (1 or 2) [1]: ").strip() or "1"
    
    if mode == "1":
        # Cloud mode - enable backend
        print("\n[OK] Setting things up...")
        config['backend']['enabled'] = True
        config['backend']['url'] = "https://telos-backend-ae7k4avtpq-el.a.run.app"
        config['backend']['fallback_to_local'] = False
        # Set placeholder API key (not used in backend mode)
        config['gemini']['api_key'] = "BACKEND_MODE_NO_KEY_NEEDED"
        
        # Add Firebase configuration for backend authentication
        if 'firebase' not in config:
            config['firebase'] = {}
        config['firebase']['api_key'] = "AIzaSyCf-aFrlhUGpPP09cQIYDC052wXyYPnHk8"
        config['firebase']['auth_domain'] = "gen-lang-client-0772617718.firebaseapp.com"
        config['firebase']['project_id'] = "gen-lang-client-0772617718"
        
        print("[OK] You're all set!")
        print("     Your 7-day free trial starts now. After that, it's $3/month. Cancel anytime.")
    else:
        # Local mode - prompt for API key
        print("\n    You'll need a free Gemini API key.")
        print("    Get one from: https://aistudio.google.com/app/apikey\n")
        
        api_key = input("Enter your Gemini API key: ").strip()
        
        if not api_key:
            print("\n[Warning] No API key entered. You can add it later to:")
            print(f"  {config_path}")
            config['gemini']['api_key'] = "YOUR_GEMINI_API_KEY_HERE"
        else:
            config['gemini']['api_key'] = api_key
            print("[OK] API key configured")
        
        # Disable backend for local mode
        config['backend']['enabled'] = False
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n[OK] Configuration saved to {config_path}")
    print("[OK] Setup complete! Run 'telos' to start tracking.")


def show_help():
    """Show help information."""
    from telos_tracker import __version__
    print(f"""
Telos - AI-powered activity tracking (v{__version__})

Usage:
    telos              - Launch TUI interface
    telos setup        - First-time setup (configure API key)
    telos doctor       - Run installation diagnostics
    telos fix-path     - Fix PATH issues (auto-add to PATH)
    telos --version    - Show version number
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

Troubleshooting:
    If 'telos' command is not found after pip install:
    1. Run: python -m telos_tracker.cli fix-path
    2. Or always use: python -m telos_tracker.cli

Note: The TUI requires a graphical environment. For headless servers,
use the setup command only, then run the tracker on a local machine.

For more information: https://github.com/AnuragKurle/telos
""")


def main():
    """Main CLI entry point."""
    # Handle version flag
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('--version', '-v', 'version'):
        from telos_tracker import __version__
        print(f"telos-tracker {__version__}")
        return

    # Handle help before setting up environment
    if len(sys.argv) > 1 and sys.argv[1].lower() in ('help', '--help', '-h'):
        show_help()
        return

    # Handle doctor command (diagnostics)
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'doctor':
        run_doctor()
        return

    # Handle fix-path command
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'fix-path':
        run_fix_path()
        return

    # Handle setup command
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'setup':
        interactive_setup()
        return

    # First-run detection: Offer PATH fix if needed
    if is_first_run():
        offer_path_fix()

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

    # Check if we're in a headless environment
    display_available = os.environ.get('DISPLAY') or sys.platform == 'win32'
    if not display_available:
        print("Error: Telos TUI requires a graphical environment.")
        print("\nYou appear to be in a headless environment (no display detected).")
        print("\nTelos is a desktop application that requires:")
        print("  - A terminal with display capabilities")
        print("  - Ability to capture screenshots")
        print("  - Keyboard/mouse input detection")
        print("\nTo use Telos:")
        print("  1. Install on your local machine (Windows/macOS/Linux desktop)")
        print("  2. Run: telos setup")
        print("  3. Run: telos")
        print("\nFor testing setup only, use: telos setup")
        return

    # Import main module and delegate
    try:
        # Try pip-installed location first (telos_tracker.main)
        import telos_tracker.main as main_module
        main_module.main()
    except (ImportError, AttributeError) as e1:
        try:
            # Try direct import from main.py (development mode)
            import main as main_module
            main_module.main()
        except (ImportError, AttributeError) as e2:
            # Try importing from parent directory
            try:
                sys.path.insert(0, str(get_package_root()))
                import main as main_module
                main_module.main()
            except (ImportError, AttributeError) as e3:
                print(f"Error: Could not import main module.")
                print(f"  Tried: telos_tracker.main, main")
                print(f"  Errors: {e1}, {e2}, {e3}")
                print("\nIf you installed via pip, please report this issue.")
                print("Workaround: cd to client directory and run 'python main.py'")


if __name__ == "__main__":
    main()

