#!/usr/bin/env python3
"""Manual Firestore Sync Script

Run this script to manually sync local SQLite data to Firestore.
Useful for testing or recovering from sync failures.

Usage:
    python manual_firestore_sync.py                # Sync all pending dates
    python manual_firestore_sync.py 2026-01-13     # Sync specific date
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from core.firebase_auth import FirebaseAuth
from core.firestore_sync import FirestoreSync
from utils.config_manager import ConfigManager


async def manual_sync(date_str=None):
    """Run manual Firestore sync.

    Args:
        date_str: Optional specific date to sync (YYYY-MM-DD)
    """
    print("=" * 60)
    print("MANUAL FIRESTORE SYNC")
    print("=" * 60)

    # Load config
    config = ConfigManager()

    # Check if backend is enabled
    backend_enabled = config.get('backend', 'enabled', default=False)
    if not backend_enabled:
        print("ERROR: Backend integration is not enabled in config")
        print("Please enable backend in settings first")
        return

    # Initialize components
    db_path = config.get('storage', 'database_path')
    firebase_api_key = config.get('firebase', 'api_key')
    firebase_project_id = config.get('firebase', 'project_id', default='gen-lang-client-0772617718')

    if not firebase_api_key:
        print("ERROR: Firebase API key not configured")
        return

    print(f"Database: {db_path}")
    print(f"Firebase Project: {firebase_project_id}")
    print()

    # Initialize sync components
    db = Database(db_path)
    firebase_auth = FirebaseAuth(firebase_api_key)

    firestore_sync = FirestoreSync(
        db=db,
        firebase_auth=firebase_auth,
        firebase_project_id=firebase_project_id,
        sync_interval_hours=24
    )

    # Load last sync date
    last_sync = db.get_config_value('last_firestore_sync_date')
    if last_sync:
        print(f"Last sync: {last_sync}")
    else:
        print("Last sync: Never")
    print()

    # Run sync
    if date_str:
        print(f"Syncing specific date: {date_str}")
        print("-" * 60)
        try:
            await firestore_sync.force_sync(date_str)
            print(f"✓ Successfully synced {date_str}")
        except Exception as e:
            print(f"✗ Failed to sync {date_str}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Syncing all pending dates...")
        print("-" * 60)
        try:
            await firestore_sync.force_sync()
            print()
            print("=" * 60)
            print("SYNC COMPLETE")
            print("=" * 60)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    # Parse command line args
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"ERROR: Invalid date format: {date_str}")
            print("Expected format: YYYY-MM-DD (e.g., 2026-01-13)")
            sys.exit(1)

    # Run sync
    asyncio.run(manual_sync(date_str))


if __name__ == '__main__':
    main()
