"""Extract real data from Telos database for report generation."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

def get_data():
    db_path = Path.home() / '.telos' / 'tracker.db'
    print(f"Database path: {db_path}")
    print(f"Exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("Database not found!")
        return None
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    result = {
        'days': {},
        'config': {},
        'goal': None
    }
    
    # Get config
    try:
        cursor.execute("SELECT key, value FROM config")
        config = {row['key']: row['value'] for row in cursor.fetchall()}
        result['config'] = config
        if 'analysis_goals' in config:
            result['goal'] = json.loads(config['analysis_goals'])
            print(f"\nGoal: {result['goal']}")
    except Exception as e:
        print(f"Config error: {e}")
    
    # Get daily stats for past 7 days
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT 
            date(timestamp) as day, 
            COUNT(*) as count,
            SUM(CASE WHEN simple_category = 'work' THEN 1 ELSE 0 END) as work,
            SUM(CASE WHEN simple_category = 'learning' THEN 1 ELSE 0 END) as learning,
            SUM(CASE WHEN simple_category = 'browsing' THEN 1 ELSE 0 END) as browsing,
            SUM(CASE WHEN simple_category = 'entertainment' THEN 1 ELSE 0 END) as entertainment,
            SUM(CASE WHEN simple_category = 'idle' THEN 1 ELSE 0 END) as idle
        FROM captures 
        WHERE timestamp >= ?
        GROUP BY date(timestamp)
        ORDER BY day DESC
    """, (seven_days_ago,))
    
    print("\n" + "="*70)
    print("DAILY BREAKDOWN")
    print("="*70)
    
    days_data = {}
    for row in cursor.fetchall():
        d = dict(row)
        total_mins = d['count'] * 30 // 60
        work_mins = d['work'] * 30 // 60
        learn_mins = d['learning'] * 30 // 60
        browse_mins = d['browsing'] * 30 // 60
        fun_mins = d['entertainment'] * 30 // 60
        
        print(f"{d['day']}: Total={total_mins}m, Work={work_mins}m, Learn={learn_mins}m, Browse={browse_mins}m, Fun={fun_mins}m")
        
        days_data[d['day']] = {
            'date': d['day'],
            'total_mins': total_mins,
            'work_mins': work_mins,
            'learning_mins': learn_mins,
            'browsing_mins': browse_mins,
            'entertainment_mins': fun_mins,
            'captures': d['count']
        }
    
    result['days'] = days_data
    
    # Get detailed data for each day
    for day in list(days_data.keys())[:3]:
        print(f"\n--- {day} ---")
        
        # Top apps
        cursor.execute("""
            SELECT app_name, COUNT(*) as count, simple_category
            FROM captures 
            WHERE date(timestamp) = ?
            GROUP BY app_name
            ORDER BY count DESC
            LIMIT 8
        """, (day,))
        
        apps = []
        for row in cursor.fetchall():
            d = dict(row)
            mins = d['count'] * 30 // 60
            apps.append({
                'name': d['app_name'],
                'minutes': mins,
                'category': d['simple_category']
            })
            print(f"  App: {d['app_name']} = {mins}m ({d['simple_category']})")
        
        days_data[day]['apps'] = apps
        
        # Get tasks for top apps
        for app in apps[:5]:
            cursor.execute("""
                SELECT DISTINCT task FROM captures 
                WHERE date(timestamp) = ? AND app_name = ?
                LIMIT 5
            """, (day, app['name']))
            tasks = [row['task'] for row in cursor.fetchall() if row['task']]
            app['tasks'] = tasks[:3]
        
        # Sessions/Timeline
        cursor.execute("""
            SELECT timestamp, app_name, task, simple_category
            FROM captures 
            WHERE date(timestamp) = ?
            ORDER BY timestamp ASC
        """, (day,))
        
        captures = cursor.fetchall()
        
        if captures:
            sessions = []
            current = None
            
            for row in captures:
                cap = dict(row)
                try:
                    ts = datetime.fromisoformat(cap['timestamp'].split('.')[0])
                except:
                    continue
                
                task_key = f"{cap['app_name']}:{cap['task']}"
                
                if current is None or current['key'] != task_key:
                    if current and current['count'] >= 2:
                        sessions.append(current)
                    current = {
                        'key': task_key,
                        'start': ts,
                        'end': ts,
                        'app': cap['app_name'],
                        'task': cap['task'] or 'Unknown',
                        'category': cap['simple_category'],
                        'count': 1
                    }
                else:
                    current['end'] = ts
                    current['count'] += 1
            
            if current and current['count'] >= 2:
                sessions.append(current)
            
            timeline = []
            # Keep ALL sessions, then sample up to 12 distributed across the day
            all_sessions = [s for s in sessions if s['count'] * 30 // 60 >= 1]
            
            # Group by hour to get distribution
            hourly = {}
            for s in all_sessions:
                hour = s['start'].hour
                if hour not in hourly:
                    hourly[hour] = []
                hourly[hour].append(s)
            
            # Take up to 2 sessions from each active hour, prioritizing longer ones
            selected = []
            for hour in sorted(hourly.keys()):
                sorted_sessions = sorted(hourly[hour], key=lambda x: -x['count'])
                selected.extend(sorted_sessions[:2])
            
            # Limit to 12 total, keeping distribution
            for s in selected[:12]:
                duration = s['count'] * 30 // 60
                entry = {
                    'start': s['start'].strftime('%H:%M'),
                    'end': s['end'].strftime('%H:%M'),
                    'duration_mins': duration,
                    'app': s['app'],
                    'task': s['task'][:80],
                    'category': s['category']
                }
                timeline.append(entry)
                print(f"  Session: {entry['start']}-{entry['end']} ({duration}m) {entry['app']}")
            
            days_data[day]['timeline'] = timeline
    
    # Daily summaries
    try:
        cursor.execute("SELECT * FROM daily_summaries ORDER BY date DESC LIMIT 7")
        summaries = {}
        for row in cursor.fetchall():
            d = dict(row)
            summaries[d['date']] = {
                'work_mins': d['work_seconds'] // 60,
                'learning_mins': d['learning_seconds'] // 60,
                'productivity_score': d.get('productivity_score'),
                'narrative': d.get('daily_narrative'),
                'learnings': json.loads(d['key_learnings_json']) if d.get('key_learnings_json') else []
            }
            print(f"\nSummary {d['date']}: Work={d['work_seconds']//60}m, Narrative exists={bool(d.get('daily_narrative'))}")
        result['summaries'] = summaries
    except Exception as e:
        print(f"Summary error: {e}")
    
    conn.close()
    
    # Save to JSON
    output_path = Path(__file__).parent / 'real_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n\nData saved to: {output_path}")
    
    return result

if __name__ == "__main__":
    get_data()
