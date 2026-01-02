"""
macOS-specific permission checks and handling

macOS requires explicit user permission for:
1. Screen Recording - Required for screenshot capture (macOS 10.15+)
2. Accessibility - Required for keyboard/mouse monitoring

This module checks permissions and guides users to enable them.
"""

import sys
import subprocess
import time
from pathlib import Path


def is_macos():
    """Check if running on macOS."""
    return sys.platform == 'darwin'


def get_macos_version():
    """Get macOS version as tuple (major, minor, patch)."""
    try:
        import platform
        version_str = platform.mac_ver()[0]
        parts = version_str.split('.')
        return tuple(int(p) for p in parts)
    except:
        return (0, 0, 0)


def check_screen_recording_permission():
    """
    Check if app has screen recording permission.
    
    Returns:
        bool: True if permission granted, False otherwise
    """
    if not is_macos():
        return True
    
    try:
        # Try to capture a screenshot
        import mss
        with mss.mss() as sct:
            # Attempt to grab the main monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # On macOS 10.15+, this will fail if permission not granted
            # Check if we got valid data
            if screenshot.size[0] > 0 and screenshot.size[1] > 0:
                return True
            else:
                return False
                
    except Exception as e:
        # Any exception likely means permission denied
        return False


def check_accessibility_permission():
    """
    Check if app has accessibility permission.
    
    Note: This is harder to check programmatically. We'll try to
    detect mouse/keyboard events as a proxy.
    
    Returns:
        bool: True if likely granted (best effort), False if clearly denied
    """
    if not is_macos():
        return True
    
    try:
        # Try to use pynput to check if we can monitor events
        from pynput import keyboard
        
        # Attempt to create a listener (doesn't actually start it)
        listener = keyboard.Listener(on_press=lambda k: None)
        
        # If we can create it without errors, permission is likely granted
        return True
        
    except Exception as e:
        # If there's an error, permission might be denied
        return False


def open_screen_recording_preferences():
    """Open macOS System Preferences to Screen Recording settings."""
    try:
        # macOS 13 (Ventura) and later use different URL
        version = get_macos_version()
        
        if version[0] >= 13:
            # macOS 13+ (Ventura and later)
            url = 'x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture'
        else:
            # macOS 12 and earlier
            url = 'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'
        
        subprocess.run(['open', url], check=False)
        return True
    except Exception as e:
        print(f"Could not open System Preferences: {e}")
        return False


def open_accessibility_preferences():
    """Open macOS System Preferences to Accessibility settings."""
    try:
        # macOS 13 (Ventura) and later use different URL
        version = get_macos_version()
        
        if version[0] >= 13:
            # macOS 13+ (Ventura and later)
            url = 'x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility'
        else:
            # macOS 12 and earlier
            url = 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        
        subprocess.run(['open', url], check=False)
        return True
    except Exception as e:
        print(f"Could not open System Preferences: {e}")
        return False


def show_permission_instructions(permission_type="screen_recording"):
    """
    Show user instructions for enabling permissions.
    
    Args:
        permission_type: "screen_recording" or "accessibility"
    """
    if permission_type == "screen_recording":
        print("\n" + "="*60)
        print("  🔒 Screen Recording Permission Required")
        print("="*60 + "\n")
        print("Telos needs Screen Recording permission to capture")
        print("screenshots for activity analysis.\n")
        print("To enable:\n")
        print("  1. Open System Preferences/Settings")
        print("  2. Go to Security & Privacy → Privacy")
        print("  3. Select 'Screen Recording' from the list")
        print("  4. Check the box next to 'Telos' or 'Python'")
        print("  5. Restart Telos\n")
        print("Opening System Preferences now...")
        open_screen_recording_preferences()
        
    elif permission_type == "accessibility":
        print("\n" + "="*60)
        print("  🔒 Accessibility Permission Required")
        print("="*60 + "\n")
        print("Telos needs Accessibility permission to monitor")
        print("keyboard and mouse activity for idle detection.\n")
        print("To enable:\n")
        print("  1. Open System Preferences/Settings")
        print("  2. Go to Security & Privacy → Privacy")
        print("  3. Select 'Accessibility' from the list")
        print("  4. Check the box next to 'Telos' or 'Python'")
        print("  5. Restart Telos\n")
        print("Opening System Preferences now...")
        open_accessibility_preferences()


def request_permission_with_wait(permission_type="screen_recording", wait_time=5):
    """
    Request permission and wait for user to grant it.
    
    Args:
        permission_type: "screen_recording" or "accessibility"
        wait_time: Seconds to wait between checks
        
    Returns:
        bool: True if permission granted, False if user cancelled
    """
    show_permission_instructions(permission_type)
    
    print(f"\nWaiting for permission to be granted...")
    print("Press Ctrl+C to cancel\n")
    
    try:
        check_count = 0
        max_checks = 60  # 5 minutes max wait
        
        while check_count < max_checks:
            time.sleep(wait_time)
            check_count += 1
            
            # Check if permission granted
            if permission_type == "screen_recording":
                if check_screen_recording_permission():
                    print("\n✅ Screen Recording permission granted!")
                    return True
            elif permission_type == "accessibility":
                if check_accessibility_permission():
                    print("\n✅ Accessibility permission granted!")
                    return True
            
            # Show progress
            if check_count % 3 == 0:
                print(f"  Still waiting... ({check_count * wait_time}s elapsed)")
        
        print("\n⏱️  Timeout waiting for permission")
        return False
        
    except KeyboardInterrupt:
        print("\n\n❌ Permission request cancelled")
        return False


def check_and_request_permissions():
    """
    Check all required permissions and request if missing.
    
    Returns:
        bool: True if all permissions granted, False otherwise
    """
    if not is_macos():
        return True
    
    print("\n🔍 Checking macOS permissions...\n")
    
    # Check Screen Recording
    if not check_screen_recording_permission():
        print("❌ Screen Recording permission: NOT GRANTED")
        
        response = input("\nWould you like to grant Screen Recording permission now? (y/N): ").strip().lower()
        if response == 'y':
            if not request_permission_with_wait("screen_recording"):
                print("\n⚠️  Telos cannot function without Screen Recording permission")
                return False
        else:
            print("\n⚠️  Telos cannot function without Screen Recording permission")
            return False
    else:
        print("✅ Screen Recording permission: GRANTED")
    
    # Check Accessibility
    if not check_accessibility_permission():
        print("❌ Accessibility permission: NOT GRANTED")
        
        response = input("\nWould you like to grant Accessibility permission now? (y/N): ").strip().lower()
        if response == 'y':
            request_permission_with_wait("accessibility")
            # Continue even if not granted - this is less critical
    else:
        print("✅ Accessibility permission: GRANTED")
    
    print("\n✅ Permission check complete\n")
    return True


def check_permissions_silent():
    """
    Silently check permissions without prompting.
    
    Returns:
        dict: Status of each permission
    """
    if not is_macos():
        return {
            'screen_recording': True,
            'accessibility': True,
            'all_granted': True
        }
    
    screen_recording = check_screen_recording_permission()
    accessibility = check_accessibility_permission()
    
    return {
        'screen_recording': screen_recording,
        'accessibility': accessibility,
        'all_granted': screen_recording and accessibility
    }


# Convenience function for startup checks
def ensure_permissions():
    """
    Ensure all required permissions are granted.
    Shows instructions and exits if critical permissions missing.
    """
    if not is_macos():
        return
    
    status = check_permissions_silent()
    
    if not status['screen_recording']:
        show_permission_instructions("screen_recording")
        print("\n❌ Telos cannot start without Screen Recording permission")
        print("Please grant the permission and restart Telos\n")
        sys.exit(1)
    
    if not status['accessibility']:
        print("\n⚠️  Warning: Accessibility permission not granted")
        print("Idle detection may not work correctly\n")


if __name__ == "__main__":
    # Test permission checking
    print("Testing macOS permissions...\n")
    
    status = check_permissions_silent()
    
    print("Permission Status:")
    print(f"  Screen Recording: {'✅ GRANTED' if status['screen_recording'] else '❌ DENIED'}")
    print(f"  Accessibility:    {'✅ GRANTED' if status['accessibility'] else '❌ DENIED'}")
    print(f"  All Granted:      {'✅ YES' if status['all_granted'] else '❌ NO'}")
    
    if not status['all_granted']:
        print("\nTo grant permissions:")
        check_and_request_permissions()

