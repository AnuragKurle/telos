"""
Migrate historical data from SQLite to Firestore.

This script extracts capture data from the local SQLite database and uploads it
to Firestore via the backend API, creating usage documents that the email scheduler
can use to generate daily summaries.
"""

import sqlite3
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

# Configuration
DB_PATH = Path.home() / '.telos' / 'tracker.db'
BACKEND_URL = 'https://telos-backend-ae7k4avtpq-el.a.run.app'
FIREBASE_PROJECT_ID = 'gen-lang-client-0772617718'

def get_captures_from_sqlite(days=7) -> List[Dict[str, Any]]:
    """Extract captures from SQLite database."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get captures from last N days
    cursor.execute("""
        SELECT 
            timestamp,
            app_name,
            task,
            category,
            simple_category,
            confidence
        FROM captures
        WHERE timestamp >= datetime('now', '-{} days')
        ORDER BY timestamp ASC
    """.format(days))
    
    captures = []
    for row in cursor.fetchall():
        captures.append({
            'timestamp': row['timestamp'],
            'app_name': row['app_name'],
            'task': row['task'] or 'Unknown',
            'category': row['category'] or 'browsing',
            'simple_category': row['simple_category'] or 'browsing',
            'confidence': row['confidence'] or 0.5
        })
    
    conn.close()
    
    print(f"✅ Extracted {len(captures)} captures from SQLite")
    return captures

def group_captures_by_day(captures: List[Dict]) -> Dict[str, List[Dict]]:
    """Group captures by date."""
    by_day = {}
    
    for cap in captures:
        try:
            ts = datetime.fromisoformat(cap['timestamp'].split('.')[0])
            date_key = ts.strftime('%Y-%m-%d')
            
            if date_key not in by_day:
                by_day[date_key] = []
            
            by_day[date_key].append(cap)
        except Exception as e:
            print(f"⚠️  Skipping invalid timestamp: {cap['timestamp']}")
            continue
    
    return by_day

def upload_to_firestore(user_id: str, captures_by_day: Dict[str, List[Dict]]):
    """Upload captures to Firestore by directly writing to the database.
    
    Note: This requires admin access. In production, you'd use a backend endpoint.
    For now, we'll use the Firebase Admin SDK directly.
    """
    try:
        # Import firebase-admin
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Initialize if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={
                'projectId': FIREBASE_PROJECT_ID
            })
        
        db = firestore.client()
        
        # Create/update usage document
        usage_ref = db.collection('usage').document(user_id)
        
        # Build dayBucket structure
        day_bucket = {}
        for date_key, captures in captures_by_day.items():
            day_bucket[date_key] = {
                'captures': captures,
                'count': len(captures)
            }
        
        # Update document
        usage_ref.set({
            'userId': user_id,
            'dayBucket': day_bucket,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        print(f"✅ Uploaded {len(captures_by_day)} days of data to Firestore")
        print(f"   User ID: {user_id}")
        print(f"   Dates: {', '.join(sorted(captures_by_day.keys()))}")
        
        return True
        
    except ImportError:
        print("❌ firebase-admin not installed")
        print("   Run: pip install firebase-admin")
        return False
    except Exception as e:
        print(f"❌ Error uploading to Firestore: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("SQLite → Firestore Migration")
    print("="*60 + "\n")
    
    # Step 1: Extract from SQLite
    print("Step 1: Extracting captures from SQLite...")
    captures = get_captures_from_sqlite(days=7)
    
    if not captures:
        print("❌ No captures found to migrate")
        return
    
    # Step 2: Group by day
    print("\nStep 2: Grouping captures by day...")
    by_day = group_captures_by_day(captures)
    print(f"✅ Grouped into {len(by_day)} days")
    
    for date, caps in sorted(by_day.items()):
        print(f"   {date}: {len(caps)} captures")
    
    # Step 3: Get user ID
    print("\nStep 3: User configuration...")
    user_id = "DuysxZoYCsgnTd4B8H2bToTcSCG2"  # Your Firebase UID
    print(f"   User ID: {user_id}")
    
    # Step 4: Upload to Firestore
    print("\nStep 4: Uploading to Firestore...")
    success = upload_to_firestore(user_id, by_day)
    
    if success:
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Verify data in Firebase Console:")
        print(f"   https://console.firebase.google.com/project/{FIREBASE_PROJECT_ID}/firestore")
        print("2. Run: node backend/test-generate-summary.js")
        print("3. Test email scheduler")
    else:
        print("\n❌ Migration failed")

if __name__ == "__main__":
    main()
