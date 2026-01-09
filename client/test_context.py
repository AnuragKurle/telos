import time
import sys
import threading
from core.capture import WindowMonitor, ActivityMonitor

def test_monitoring():
    print("Initializing monitors...")
    
    # Initialize Monitors
    window_monitor = WindowMonitor()
    activity_monitor = ActivityMonitor()
    activity_monitor.start()
    
    print("\n--- Test Phase 1: Idle Check (3s) ---")
    print("Please DO NOT touch mouse/keyboard for 3 seconds...")
    time.sleep(3)
    
    metrics = activity_monitor.get_and_reset_metrics()
    print(f"Metrics (Should be near zero): {metrics}")
    
    print("\n--- Test Phase 2: Active Check (5s) ---")
    print("Please TYPE generic text and MOVE mouse now! (You have 5 seconds)")
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print("\nCapture!")
    
    # Capture Data
    window_info = window_monitor.get_active_window_info()
    metrics = activity_monitor.get_and_reset_metrics()
    
    print("\n=== RESULTS ===")
    print(f"Active Window Title: '{window_info.get('title')}'")
    print(f"App Name: '{window_info.get('app_name')}'")
    print(f"Activity Metrics: {metrics}")
    
    # Validation logic
    if metrics['keystrokes'] > 0 or metrics['mouse_distance'] > 0:
        print("\n✅ Activity successfully detected!")
    else:
        print("\n⚠️ No activity detected (Did you type/move?)")
        
    if window_info.get('app_name'):
        print("✅ App name detected!")
    else:
        print("⚠️ App name NOT detected (Are you on Windows?)")

    activity_monitor.stop()

if __name__ == "__main__":
    try:
        test_monitoring()
    except KeyboardInterrupt:
        pass
