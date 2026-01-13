"""Firestore Sync Worker

Syncs local SQLite captures to Firestore for backend email generation.
Runs periodically to ensure backend has fresh data for daily reports.
"""

import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from core.database import Database
    from core.firebase_auth import FirebaseAuth


class FirestoreSyncError(Exception):
    """Raised when Firestore sync fails."""
    pass


class FirestoreSync:
    """Manages syncing local SQLite data to Firestore."""

    def __init__(
        self,
        db: 'Database',
        firebase_auth: 'FirebaseAuth',
        firebase_project_id: str,
        sync_interval_hours: int = 24
    ):
        """Initialize Firestore sync.

        Args:
            db: Database instance
            firebase_auth: Firebase auth instance
            firebase_project_id: Firebase project ID
            sync_interval_hours: Hours between automatic syncs (default: 24)
        """
        self.db = db
        self.firebase_auth = firebase_auth
        self.firebase_project_id = firebase_project_id
        self.sync_interval_hours = sync_interval_hours

        # Firestore REST API base URL
        self.firestore_url = f"https://firestore.googleapis.com/v1/projects/{firebase_project_id}/databases/(default)/documents"

        # Track last sync
        self.last_sync_date: Optional[str] = None
        self.running = False

    async def start(self):
        """Start the sync worker loop."""
        self.running = True

        # Load last sync date from config
        self.last_sync_date = self.db.get_config_value('last_firestore_sync_date')

        print(f"[Firestore Sync] Starting worker (interval: {self.sync_interval_hours}h)")
        if self.last_sync_date:
            print(f"[Firestore Sync] Last sync: {self.last_sync_date}")

        # Run initial sync on startup (after short delay)
        await asyncio.sleep(60)  # Wait 1 minute after app start
        await self._run_sync()

        # Then run periodic sync
        while self.running:
            try:
                # Sleep for configured interval
                await asyncio.sleep(self.sync_interval_hours * 3600)

                # Run sync
                await self._run_sync()

            except Exception as e:
                print(f"[Firestore Sync] Error in worker loop: {e}")
                # Continue running even if sync fails
                await asyncio.sleep(600)  # Wait 10 min before retrying

    async def _run_sync(self):
        """Run a sync cycle."""
        try:
            print(f"\n[Firestore Sync] ========================================")
            print(f"[Firestore Sync] Starting sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[Firestore Sync] ========================================")

            # Determine which dates to sync
            dates_to_sync = await asyncio.to_thread(self._get_dates_to_sync)

            if not dates_to_sync:
                print(f"[Firestore Sync] No dates to sync")
                return

            print(f"[Firestore Sync] Found {len(dates_to_sync)} date(s) to sync: {', '.join(dates_to_sync)}")

            # Sync each date
            success_count = 0
            error_count = 0

            for date_str in dates_to_sync:
                try:
                    await self._sync_date(date_str)
                    success_count += 1
                    print(f"[Firestore Sync] ✓ Synced {date_str}")
                except Exception as e:
                    error_count += 1
                    print(f"[Firestore Sync] ✗ Failed to sync {date_str}: {e}")

            # Update last sync date to most recent successful sync
            if success_count > 0:
                latest_synced = max(dates_to_sync[:success_count])
                self.db.set_config_value('last_firestore_sync_date', latest_synced)
                self.last_sync_date = latest_synced
                print(f"[Firestore Sync] Updated last sync date to {latest_synced}")

            print(f"\n[Firestore Sync] ========================================")
            print(f"[Firestore Sync] Sync complete: {success_count} success, {error_count} errors")
            print(f"[Firestore Sync] ========================================\n")

        except Exception as e:
            print(f"[Firestore Sync] Error running sync: {e}")

    def _get_dates_to_sync(self) -> List[str]:
        """Get list of dates that need syncing.

        Returns:
            List of date strings (YYYY-MM-DD) sorted chronologically
        """
        today = datetime.now().date()

        # Default: sync last 3 days
        start_date = today - timedelta(days=3)

        # If we have a last sync date, start from there
        if self.last_sync_date:
            try:
                last_sync = datetime.strptime(self.last_sync_date, '%Y-%m-%d').date()
                # Sync from day after last sync, but no more than 7 days back
                start_date = max(last_sync + timedelta(days=1), today - timedelta(days=7))
            except ValueError:
                print(f"[Firestore Sync] Invalid last sync date: {self.last_sync_date}")

        # Don't sync today (wait until tomorrow to sync yesterday's complete data)
        end_date = today - timedelta(days=1)

        if start_date > end_date:
            return []

        # Generate list of dates
        dates = []
        current = start_date
        while current <= end_date:
            # Check if this date has data
            captures = self.db.get_captures_for_date(current.strftime('%Y-%m-%d'))
            if captures:
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        return dates

    async def _sync_date(self, date_str: str):
        """Sync captures for a specific date to Firestore.

        Args:
            date_str: Date in YYYY-MM-DD format

        Raises:
            FirestoreSyncError: If sync fails
        """
        # Get captures for this date
        captures = await asyncio.to_thread(
            self.db.get_captures_for_date,
            date_str
        )

        if not captures:
            print(f"[Firestore Sync] No captures found for {date_str}")
            return

        print(f"[Firestore Sync] Syncing {len(captures)} captures for {date_str}")

        # Get Firebase token
        try:
            token = await asyncio.to_thread(self.firebase_auth.get_token)
        except Exception as e:
            raise FirestoreSyncError(f"Failed to get Firebase token: {e}")

        # Get user ID from token
        user_id = await asyncio.to_thread(self._get_user_id_from_token, token)

        # Prepare captures data in Firestore format
        captures_data = [
            {
                'timestamp': cap['timestamp'],
                'category': cap['category'],
                'simple_category': cap.get('simple_category', cap['category']),
                'app_name': cap['app_name'],
                'task': cap['task'],
                'confidence': cap['confidence']
            }
            for cap in captures
        ]

        # Upload to Firestore using REST API
        await self._upload_to_firestore(user_id, date_str, captures_data, token)

    def _get_user_id_from_token(self, token: str) -> str:
        """Extract user ID from Firebase token.

        Args:
            token: Firebase ID token

        Returns:
            User ID (UID)
        """
        # Decode JWT to get user ID (simple approach)
        # Token format: header.payload.signature
        try:
            import base64
            payload_part = token.split('.')[1]
            # Add padding if needed
            padding = 4 - len(payload_part) % 4
            if padding != 4:
                payload_part += '=' * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_part))
            return payload['user_id']
        except Exception as e:
            raise FirestoreSyncError(f"Failed to decode token: {e}")

    async def _upload_to_firestore(
        self,
        user_id: str,
        date_str: str,
        captures: List[Dict[str, Any]],
        token: str
    ):
        """Upload captures to Firestore using REST API.

        Args:
            user_id: Firebase user ID
            date_str: Date string (YYYY-MM-DD)
            captures: List of capture dicts
            token: Firebase ID token
        """
        # Firestore document path: usage/{userId}
        doc_path = f"{self.firestore_url}/usage/{user_id}"

        # First, check if document exists
        try:
            response = await asyncio.to_thread(
                requests.get,
                doc_path,
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )

            existing_data = {}
            if response.status_code == 200:
                # Document exists, get current data
                doc_data = response.json()
                if 'fields' in doc_data and 'dayBucket' in doc_data['fields']:
                    # Parse existing dayBucket
                    day_bucket_field = doc_data['fields']['dayBucket']
                    if 'mapValue' in day_bucket_field and 'fields' in day_bucket_field['mapValue']:
                        existing_data = self._parse_firestore_map(day_bucket_field['mapValue']['fields'])

            elif response.status_code != 404:
                raise FirestoreSyncError(f"Failed to check document: {response.status_code} {response.text}")

        except requests.RequestException as e:
            raise FirestoreSyncError(f"Failed to check Firestore document: {e}")

        # Merge with new data
        existing_data[date_str] = {'captures': captures}

        # Convert to Firestore format
        firestore_data = {
            'fields': {
                'dayBucket': {
                    'mapValue': {
                        'fields': self._to_firestore_map(existing_data)
                    }
                }
            }
        }

        # Patch/update the document
        try:
            response = await asyncio.to_thread(
                requests.patch,
                f"{doc_path}?updateMask.fieldPaths=dayBucket",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                json=firestore_data,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                raise FirestoreSyncError(
                    f"Failed to upload to Firestore: {response.status_code} {response.text}"
                )

        except requests.RequestException as e:
            raise FirestoreSyncError(f"Failed to upload to Firestore: {e}")

    def _to_firestore_map(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python dict to Firestore map format.

        Args:
            data: Python dict

        Returns:
            Firestore-formatted map
        """
        result = {}
        for key, value in data.items():
            result[key] = self._to_firestore_value(value)
        return result

    def _to_firestore_value(self, value: Any) -> Dict[str, Any]:
        """Convert Python value to Firestore value format.

        Args:
            value: Python value

        Returns:
            Firestore-formatted value
        """
        if isinstance(value, dict):
            # Check if it's a capture array or nested dict
            if 'captures' in value:
                return {
                    'mapValue': {
                        'fields': {
                            'captures': {
                                'arrayValue': {
                                    'values': [
                                        self._to_firestore_value(cap)
                                        for cap in value['captures']
                                    ]
                                }
                            }
                        }
                    }
                }
            else:
                return {
                    'mapValue': {
                        'fields': self._to_firestore_map(value)
                    }
                }
        elif isinstance(value, list):
            return {
                'arrayValue': {
                    'values': [self._to_firestore_value(v) for v in value]
                }
            }
        elif isinstance(value, str):
            return {'stringValue': value}
        elif isinstance(value, bool):
            return {'booleanValue': value}
        elif isinstance(value, int):
            return {'integerValue': str(value)}
        elif isinstance(value, float):
            return {'doubleValue': value}
        elif value is None:
            return {'nullValue': None}
        else:
            return {'stringValue': str(value)}

    def _parse_firestore_map(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Firestore map format to Python dict.

        Args:
            fields: Firestore fields dict

        Returns:
            Python dict
        """
        result = {}
        for key, value_obj in fields.items():
            result[key] = self._parse_firestore_value(value_obj)
        return result

    def _parse_firestore_value(self, value_obj: Dict[str, Any]) -> Any:
        """Parse Firestore value format to Python value.

        Args:
            value_obj: Firestore value object

        Returns:
            Python value
        """
        if 'stringValue' in value_obj:
            return value_obj['stringValue']
        elif 'integerValue' in value_obj:
            return int(value_obj['integerValue'])
        elif 'doubleValue' in value_obj:
            return value_obj['doubleValue']
        elif 'booleanValue' in value_obj:
            return value_obj['booleanValue']
        elif 'mapValue' in value_obj:
            return self._parse_firestore_map(value_obj['mapValue'].get('fields', {}))
        elif 'arrayValue' in value_obj:
            return [
                self._parse_firestore_value(v)
                for v in value_obj['arrayValue'].get('values', [])
            ]
        elif 'nullValue' in value_obj:
            return None
        else:
            return None

    def stop(self):
        """Stop the sync worker."""
        self.running = False
        print("[Firestore Sync] Worker stopped")

    async def force_sync(self, date_str: Optional[str] = None):
        """Manually trigger a sync.

        Args:
            date_str: Specific date to sync (YYYY-MM-DD), or None for automatic selection
        """
        if date_str:
            print(f"[Firestore Sync] Force syncing {date_str}")
            await self._sync_date(date_str)
        else:
            print(f"[Firestore Sync] Force syncing recent dates")
            await self._run_sync()
