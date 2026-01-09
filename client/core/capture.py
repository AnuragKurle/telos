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
        info = {'title': '', 'app_name': ''}
        
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
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"Window monitor error: {e}")
            
        return info


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
