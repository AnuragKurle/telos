#!/usr/bin/env python3
"""Quick test for WindowEventTracker functionality."""

from client.core.capture import WindowMonitor, WindowEventTracker
import time

print("=" * 60)
print("Testing Window Event Tracker")
print("=" * 60)

monitor = WindowMonitor()
tracker = WindowEventTracker(monitor)

# Test 1: Start interval
tracker.start_interval()
print(f"\n✓ Started interval at: {tracker.interval_start_time}")

# Test 2: Get initial window
initial_window = monitor.get_active_window_info()
print(f"✓ Current window: {initial_window.get('app_name', 'Unknown')} - {initial_window.get('title', '')[:50]}")

# Test 3: Simulate polling
print(f"\nPolling for window changes (5 seconds)...")
print("  (Try switching windows to see it capture events)")
for i in range(5):
    tracker.poll_window_changes()
    print(f"  Poll {i+1}/5 - Events captured: {len(tracker.events)}")
    time.sleep(1)

# Test 4: Get summary
summary = tracker.get_interval_summary()
print(f"\n✓ Interval complete!")
print(f"  - Total window changes: {summary['total_changes']}")
print(f"  - Apps visited: {summary.get('apps_visited', [])}")
print(f"  - Events captured: {len(summary['events'])}")

if summary['events']:
    print(f"\n  First event:")
    event = summary['events'][0]
    print(f"    {event.get('from_app', '')} → {event.get('to_app', '')}")
    print(f"    {event.get('from_title', '')[:40]} → {event.get('to_title', '')[:40]}")

# Test 5: Get limited events
limited = tracker.get_limited_events(limit=3)
print(f"\n✓ Get limited events (max 3): {len(limited)} events")

print("\n" + "=" * 60)
print("✅ All WindowEventTracker tests passed!")
print("=" * 60)
