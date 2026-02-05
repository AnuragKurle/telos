"""Data export functionality for Pro users.

Exports captures and sessions to CSV or JSON format.
"""

import csv
import json
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.database import Database


class DataExporter:
    """Exports user activity data to CSV or JSON."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def export_today_captures_csv(self, output_path: str) -> int:
        """Export today's captures to CSV.
        
        Args:
            output_path: File path to write CSV
            
        Returns:
            Number of rows exported
        """
        captures = self.db.get_captures_for_date(datetime.now())
        return self._write_captures_csv(captures, output_path)
    
    def export_today_sessions_csv(self, output_path: str) -> int:
        """Export today's sessions to CSV.
        
        Args:
            output_path: File path to write CSV
            
        Returns:
            Number of rows exported
        """
        sessions = self.db.get_sessions_for_date(datetime.now())
        return self._write_sessions_csv(sessions, output_path)
    
    def export_date_range_csv(self, start_date: datetime, end_date: datetime, 
                               output_path: str, data_type: str = "captures") -> int:
        """Export data for a date range to CSV.
        
        Args:
            start_date: Start date
            end_date: End date
            output_path: File path to write CSV
            data_type: "captures" or "sessions"
            
        Returns:
            Number of rows exported
        """
        all_data = []
        current = start_date
        while current <= end_date:
            if data_type == "captures":
                all_data.extend(self.db.get_captures_for_date(current))
            else:
                all_data.extend(self.db.get_sessions_for_date(current))
            current += timedelta(days=1)
        
        if data_type == "captures":
            return self._write_captures_csv(all_data, output_path)
        else:
            return self._write_sessions_csv(all_data, output_path)
    
    def export_today_json(self, output_path: str) -> int:
        """Export today's data (captures + sessions) to JSON.
        
        Args:
            output_path: File path to write JSON
            
        Returns:
            Total number of records exported
        """
        captures = self.db.get_captures_for_date(datetime.now())
        sessions = self.db.get_sessions_for_date(datetime.now())
        
        data = {
            "export_date": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "captures_count": len(captures),
            "sessions_count": len(sessions),
            "captures": self._clean_for_json(captures),
            "sessions": self._clean_for_json(sessions),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return len(captures) + len(sessions)
    
    def _write_captures_csv(self, captures: List[Dict], output_path: str) -> int:
        """Write captures to CSV file."""
        if not captures:
            return 0
        
        fieldnames = ['timestamp', 'app_name', 'category', 'task', 'confidence']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for cap in captures:
                writer.writerow(cap)
        
        return len(captures)
    
    def _write_sessions_csv(self, sessions: List[Dict], output_path: str) -> int:
        """Write sessions to CSV file."""
        if not sessions:
            return 0
        
        fieldnames = ['start_time', 'end_time', 'duration_seconds', 'category', 
                      'primary_task', 'apps_used', 'focus_score']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for session in sessions:
                writer.writerow(session)
        
        return len(sessions)
    
    def _clean_for_json(self, records: List[Dict]) -> List[Dict]:
        """Clean records for JSON serialization (remove non-serializable fields)."""
        cleaned = []
        for record in records:
            clean = {}
            for key, value in record.items():
                # Skip binary or internal fields
                if key in ('screenshot_hash', 'image_hash'):
                    continue
                clean[key] = value
            cleaned.append(clean)
        return cleaned
