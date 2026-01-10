#!/usr/bin/env python3
"""Minimal test - can we capture at all?"""
import sys
sys.path.insert(0, 'client')

from core.capture import WindowMonitor, WindowEventTracker, ActivityMonitor, ScreenshotCapture
from datetime import datetime
import time

print("Testing basic capture components...")

# Test 1: Window Monitor
wm = WindowMonitor()
info = wm.get_active_window_info()
print(f"\n1. WindowMonitor: {info}")

# Test 2: Activity Monitor  
am = ActivityMonitor()
time.sleep(2)
print(f"\n2. ActivityMonitor idle: {am.is_idle()}")
print(f"   Seconds since activity: {am.seconds_since_activity()}")

# Test 3: WindowEventTracker
tracker = WindowEventTracker(wm)
tracker.start_interval()
print(f"\n3. WindowEventTracker started")
time.sleep(1)
tracker.poll_window_changes()
summary = tracker.get_interval_summary()
print(f"   Summary: {summary}")

# Test 4: Screenshot
sc = ScreenshotCapture()
path = sc.capture()
print(f"\n4. Screenshot captured: {path}")
sc.cleanup_screenshot(path)

print("\n✅ All basic components working!")
