import time
import win32gui
import win32process
import os

def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        try:
            # Method 1: using psutil if available (preferred but not in requirements)
            import psutil
            process = psutil.Process(pid)
            app_name = process.name()
        except ImportError:
            # Method 2: using simpler approach or ignoring exact exe name for now
            # Without psutil, getting exe name from PID in python with just pywin32 is verbose
            # but we can try basic heuristics or just use the title
            app_name = "Unknown (psutil missing)"
            
        print(f"Active Window: '{title}'")
        print(f"PID: {pid}")
        print(f"App: {app_name}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Capturing window info in 3 seconds (switch to another window)...")
    time.sleep(3)
    get_active_window_info()
