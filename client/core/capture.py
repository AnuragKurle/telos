"""Screenshot capture and activity detection."""

import os
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import Optional, Callable, Dict, Any

import mss
from PIL import Image
from pynput import mouse, keyboard

try:
    if sys.platform == 'win32':
        import win32gui
        import win32process
        import psutil
except ImportError:
    pass

class WindowMonitor:
    """Monitors active window and application."""
    
    def get_active_window_info(self) -> Dict[str, str]:
        """Get active window title and app name.
        
        Returns:
            Dict with 'title' and 'app_name' (empty strings if not available)
        """
        info = {'title': '', 'app_name': '', 'process_name': ''}
        
        if sys.platform != 'win32':
            return info
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            info['title'] = win32gui.GetWindowText(hwnd)
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid > 0:
                try:
                    process = psutil.Process(pid)
                    info['app_name'] = process.name()
                    info['process_name'] = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"Window monitor error: {e}")
            
        return info


class WindowEventTracker:
    """Tracks window and tab changes between screenshots.
    
    This class monitors window switches during the capture interval (typically 30s)
    and provides a summary of all window activity for LLM context enrichment.
    """
    
    def __init__(self, window_monitor: WindowMonitor):
        """Initialize window event tracker.
        
        Args:
            window_monitor: WindowMonitor instance for getting window info
        """
        self.window_monitor = window_monitor
        self.events: list = []  # Buffer for current interval
        self.interval_start_time: Optional[str] = None
        self._last_window_state: Dict[str, str] = {}
        
    def start_interval(self) -> None:
        """Start tracking for a new screenshot interval."""
        self.events = []
        self.interval_start_time = datetime.now().isoformat()
        # Capture initial window state
        self._last_window_state = self.window_monitor.get_active_window_info()
        
    def poll_window_changes(self) -> None:
        """Poll for window changes. Call frequently (e.g., every 1-2 seconds)."""
        current_window = self.window_monitor.get_active_window_info()
        
        # Check if window has changed
        if self._has_window_changed(current_window):
            self.events.append({
                'timestamp': datetime.now().isoformat(),
                'event_type': 'window_change',
                'from_app': self._last_window_state.get('app_name', ''),
                'from_title': self._last_window_state.get('title', ''),
                'to_app': current_window.get('app_name', ''),
                'to_title': current_window.get('title', ''),
                'window_title': current_window.get('title', ''),
                'app_name': current_window.get('app_name', ''),
                'process_name': current_window.get('process_name', '')
            })
            self._last_window_state = current_window.copy()
            
    def _has_window_changed(self, current_window: Dict[str, str]) -> bool:
        """Check if window has changed from last known state.
        
        Args:
            current_window: Current window info dict
            
        Returns:
            True if window/app changed, False otherwise
        """
        if not self._last_window_state:
            return True
            
        # Check if app name or window title has changed
        return (
            current_window.get('app_name') != self._last_window_state.get('app_name') or
            current_window.get('title') != self._last_window_state.get('title')
        )
        
    def get_interval_summary(self) -> Dict[str, Any]:
        """Get summary of all window changes in current interval.
        
        Returns:
            Dict with interval info, total changes, events list, and current window
        """
        current_window = self.window_monitor.get_active_window_info()
        
        return {
            'interval_start': self.interval_start_time,
            'interval_end': datetime.now().isoformat(),
            'total_changes': len(self.events),
            'events': self.events.copy(),
            'current_window': current_window,
            # Summary for quick access
            'apps_visited': list(set(e.get('app_name', '') for e in self.events if e.get('app_name'))),
        }
        
    def get_limited_events(self, limit: int = 5) -> list:
        """Get limited number of most recent events for API payload.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events (most recent last)
        """
        return self.events[-limit:] if self.events else []


class ActivityMonitor:
    """Monitors mouse and keyboard activity to detect idle state."""

    def __init__(self, idle_timeout: int = 60):
        """Initialize activity monitor.

        Args:
            idle_timeout: Seconds of inactivity before considered idle
        """
        self.idle_timeout = idle_timeout
        self.last_activity: float = time.time()
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._running = False
        
        # Activity metrics (rate counters)
        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_distance = 0.0
        self._last_mouse_pos = (0, 0)

    def get_and_reset_metrics(self) -> Dict[str, Any]:
        """Get accumulated metrics and reset counters.
        
        Returns:
            Dict with 'keystrokes', 'mouse_clicks', 'mouse_distance'
        """
        metrics = {
            'keystrokes': self.keystroke_count,
            'mouse_clicks': self.mouse_click_count,
            'mouse_distance': int(self.mouse_move_distance)
        }
        
        # Reset counters
        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_distance = 0.0
        
        return metrics

    def _on_activity(self) -> None:
        """Called when any activity is detected."""
        self.last_activity = time.time()

    def _on_mouse_move(self, x: int, y: int) -> None:
        """Mouse move callback."""
        self._on_activity()
        
        # Calculate distance
        if self._last_mouse_pos != (0, 0):
            dist = ((x - self._last_mouse_pos[0])**2 + (y - self._last_mouse_pos[1])**2)**0.5
            self.mouse_move_distance += dist
        self._last_mouse_pos = (x, y)

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Mouse click callback."""
        if pressed:
            self.mouse_click_count += 1
        self._on_activity()

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Mouse scroll callback."""
        self._on_activity()

    def _on_keyboard_press(self, key) -> None:
        """Keyboard press callback."""
        self.keystroke_count += 1
        self._on_activity()

    def start(self) -> None:
        """Start monitoring activity."""
        if self._running:
            return

        self._running = True
        self.last_activity = time.time()

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._mouse_listener.start()

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_keyboard_press
        )
        self._keyboard_listener.start()

    def stop(self) -> None:
        """Stop monitoring activity."""
        if not self._running:
            return

        self._running = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def is_idle(self) -> bool:
        """Check if user is currently idle.

        Returns:
            True if no activity for idle_timeout seconds
        """
        return (time.time() - self.last_activity) > self.idle_timeout

    def seconds_since_activity(self) -> int:
        """Get seconds since last activity."""
        return int(time.time() - self.last_activity)


class ScreenshotCapture:
    """Handles screenshot capture."""

    def __init__(self, quality: int = 85):
        """Initialize screenshot capturer.

        Args:
            quality: JPEG quality (1-100)
        """
        self.quality = quality
        # Use absolute path in user data directory
        user_data_dir = Path.home() / ".telos"
        self.temp_dir = user_data_dir / "temp_screenshots"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> str:
        """Capture screenshot and save to temp file.

        Returns:
            Path to the saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = self.temp_dir / f"screenshot_{timestamp}.jpg"

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Resize if needed (max 1024x1024)
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Save as JPEG
            img.save(str(output_path), "JPEG", quality=self.quality)

        return str(output_path)

    def cleanup_screenshot(self, screenshot_path: str) -> None:
        """Delete screenshot file.

        Args:
            screenshot_path: Path to screenshot to delete
        """
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Warning: Could not delete screenshot {screenshot_path}: {e}")

    def cleanup_all(self) -> None:
        """Delete all screenshots in temp directory."""
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("screenshot_*"):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete {file}: {e}")
