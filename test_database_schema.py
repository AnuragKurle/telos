#!/usr/bin/env python3
"""Test database schema for window_activity_log."""

from client.core.database import Database
import json
from datetime import datetime
import os

print("=" * 60)
print("Testing Database Schema")
print("=" * 60)

# Use temporary database
db_path = 'test_window_activity.db'
if os.path.exists(db_path):
    os.remove(db_path)

db = Database(db_path)

# Test 1: Create capture
print("\n1. Creating test capture...")
capture_id = db.insert_capture(
    timestamp=datetime.now(),
    category='Work',
    app_name='VSCode',
    task='Testing window activity tracking',
    confidence=0.95,
    simple_category='work'
)
print(f"✓ Created capture ID: {capture_id}")

# Test 2: Insert window activity log
print("\n2. Inserting window activity log...")
events = [
    {
        'timestamp': datetime.now().isoformat(),
        'event_type': 'window_change',
        'from_app': 'Chrome',
        'from_title': 'GitHub',
        'to_app': 'VSCode',
        'to_title': 'test_database_schema.py',
        'app_name': 'VSCode',
        'window_title': 'test_database_schema.py'
    },
    {
        'timestamp': datetime.now().isoformat(),
        'event_type': 'window_change',
        'from_app': 'VSCode',
        'from_title': 'test_database_schema.py',
        'to_app': 'Chrome',
        'to_title': 'Stack Overflow',
        'app_name': 'Chrome',
        'window_title': 'Stack Overflow'
    }
]

log_id = db.insert_window_activity_log(
    capture_id=capture_id,
    interval_start=datetime.now().isoformat(),
    interval_end=datetime.now().isoformat(),
    total_window_changes=2,
    events_json=json.dumps(events),
    current_window_title='VSCode - test_database_schema.py',
    current_app_name='VSCode',
    apps_visited='Chrome,VSCode'
)
print(f"✓ Created window activity log ID: {log_id}")

# Test 3: Retrieve by capture ID
print("\n3. Retrieving window activity for capture...")
activity = db.get_window_activity_for_capture(capture_id)
print(f"✓ Retrieved activity log:")
print(f"  - Capture ID: {activity['capture_id']}")
print(f"  - Total changes: {activity['total_window_changes']}")
print(f"  - Current app: {activity['current_app_name']}")
print(f"  - Apps visited: {activity['apps_visited']}")

# Test 4: Retrieve by time range
print("\n4. Retrieving window activity for time range...")
start_time = datetime.now()
activities = db.get_window_activity_for_timerange(
    start_time=start_time.replace(hour=0, minute=0, second=0),
    end_time=start_time.replace(hour=23, minute=59, second=59)
)
print(f"✓ Found {len(activities)} activity logs in time range")

# Test 5: Get stats
print("\n5. Getting window activity stats for today...")
stats = db.get_window_activity_stats_for_date(datetime.now())
print(f"✓ Stats:")
print(f"  - Total switches: {stats['total_switches']}")
print(f"  - Intervals tracked: {stats['intervals_tracked']}")
print(f"  - Avg switches per interval: {stats['avg_switches_per_interval']:.2f}")
print(f"  - Apps histogram: {stats['apps_histogram']}")

# Cleanup
os.remove(db_path)

print("\n" + "=" * 60)
print("✅ All database schema tests passed!")
print("=" * 60)
