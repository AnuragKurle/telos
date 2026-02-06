"""
Local Dashboard Server

Serves an interactive web dashboard for exploring Telos tracking data.
Reads directly from the local SQLite database.

Started as a background worker alongside the TUI/service.
Accessible at http://localhost:5555/dashboard
"""

import json
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, jsonify, Response


# Suppress Flask's noisy request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


def create_app(db_path: str) -> Flask:
    """Create and configure the Flask dashboard app."""
    app = Flask(__name__)
    app.config['DB_PATH'] = db_path

    def get_db():
        """Get a read-only database connection."""
        conn = sqlite3.connect(app.config['DB_PATH'], timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    # ──────────────────────────────────────────────
    #  Dashboard page
    # ──────────────────────────────────────────────

    @app.route('/dashboard')
    def dashboard():
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        return Response(render_dashboard_html(date), mimetype='text/html')

    # ──────────────────────────────────────────────
    #  API Endpoints
    # ──────────────────────────────────────────────

    @app.route('/api/stats')
    def api_stats():
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT simple_category, COUNT(*) as cnt FROM captures WHERE timestamp LIKE ? GROUP BY simple_category",
                (date + '%',)
            ).fetchall()

            stats = {'work': 0, 'learning': 0, 'browsing': 0, 'entertainment': 0, 'idle': 0}
            for r in rows:
                cat = (r['simple_category'] or 'browsing').lower()
                if cat in stats:
                    stats[cat] = r['cnt'] * 30  # each capture = 30 seconds
                else:
                    stats['browsing'] += r['cnt'] * 30

            total_captures = conn.execute(
                "SELECT COUNT(*) as cnt FROM captures WHERE timestamp LIKE ?", (date + '%',)
            ).fetchone()['cnt']

            stats['total_captures'] = total_captures

            # Summary data
            summary = conn.execute(
                "SELECT * FROM daily_summaries WHERE date LIKE ? LIMIT 1", (date + '%',)
            ).fetchone()

            if summary:
                stats['productivity_score'] = summary['productivity_score']
                stats['daily_narrative'] = summary['daily_narrative']
                stats['context_switches'] = summary['context_switches']
                stats['key_learnings_json'] = summary['key_learnings_json']
            else:
                stats['productivity_score'] = None
                stats['daily_narrative'] = None

            return jsonify(stats)
        finally:
            conn.close()

    @app.route('/api/apps')
    def api_apps():
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT app_name, simple_category, COUNT(*) as cnt
                FROM captures
                WHERE timestamp LIKE ?
                GROUP BY app_name
                ORDER BY cnt DESC
                LIMIT 20
            """, (date + '%',)).fetchall()

            apps = []
            for r in rows:
                apps.append({
                    'name': r['app_name'] or 'Unknown',
                    'minutes': round(r['cnt'] * 30 / 60),
                    'category': r['simple_category'] or 'browsing',
                    'captures': r['cnt']
                })

            return jsonify(apps)
        finally:
            conn.close()

    @app.route('/api/sessions')
    def api_sessions():
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT id, start_time, end_time, category, primary_task,
                       apps_used, detailed_summary, focus_score, duration_seconds
                FROM sessions
                WHERE start_time LIKE ?
                ORDER BY start_time ASC
            """, (date + '%',)).fetchall()

            sessions = []
            for r in rows:
                sessions.append({
                    'id': r['id'],
                    'start_time': r['start_time'],
                    'end_time': r['end_time'],
                    'category': r['category'],
                    'primary_task': r['primary_task'],
                    'apps_used': r['apps_used'],
                    'detailed_summary': r['detailed_summary'],
                    'focus_score': r['focus_score'],
                    'duration_seconds': r['duration_seconds']
                })

            return jsonify(sessions)
        finally:
            conn.close()

    @app.route('/api/heatmap')
    def api_heatmap():
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT timestamp, simple_category
                FROM captures
                WHERE timestamp LIKE ?
                ORDER BY timestamp ASC
            """, (date + '%',)).fetchall()

            # Build 48 half-hour blocks (24 hours x 2)
            blocks = []
            for h in range(24):
                for half in range(2):
                    blocks.append({
                        'hour': h,
                        'half': half,
                        'label': f"{h:02d}:{half*30:02d}",
                        'work': 0, 'learning': 0, 'browsing': 0,
                        'entertainment': 0, 'idle': 0, 'total': 0
                    })

            for r in rows:
                try:
                    ts = datetime.fromisoformat(r['timestamp'])
                    idx = ts.hour * 2 + (1 if ts.minute >= 30 else 0)
                    cat = (r['simple_category'] or 'browsing').lower()
                    if cat in blocks[idx]:
                        blocks[idx][cat] += 1
                    else:
                        blocks[idx]['browsing'] += 1
                    blocks[idx]['total'] += 1
                except (ValueError, IndexError):
                    pass

            return jsonify(blocks)
        finally:
            conn.close()

    @app.route('/api/range')
    def api_range():
        today = datetime.now().strftime('%Y-%m-%d')
        from_date = request.args.get('from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        to_date = request.args.get('to', today)
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT date, work_seconds, learning_seconds, browsing_seconds,
                       entertainment_seconds, idle_seconds, productivity_score,
                       context_switches
                FROM daily_summaries
                WHERE date >= ? AND date <= ?
                ORDER BY date ASC
            """, (from_date, to_date)).fetchall()

            days = []
            for r in rows:
                days.append({
                    'date': r['date'],
                    'work': r['work_seconds'] or 0,
                    'learning': r['learning_seconds'] or 0,
                    'browsing': r['browsing_seconds'] or 0,
                    'entertainment': r['entertainment_seconds'] or 0,
                    'idle': r['idle_seconds'] or 0,
                    'score': r['productivity_score'],
                    'switches': r['context_switches']
                })

            return jsonify(days)
        finally:
            conn.close()

    @app.route('/api/available-dates')
    def api_available_dates():
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT DISTINCT substr(timestamp, 1, 10) as date
                FROM captures
                ORDER BY date DESC
                LIMIT 90
            """).fetchall()
            dates = [r['date'] for r in rows]
            return jsonify(dates)
        finally:
            conn.close()

    return app


class DashboardServer:
    """Runs the Flask dashboard in a background thread."""

    def __init__(self, db_path: str, port: int = 5555):
        self.db_path = db_path
        self.port = port
        self._thread = None
        self._app = None

    def start(self):
        """Start the dashboard server in a background thread."""
        self._app = create_app(self.db_path)
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name='dashboard-server'
        )
        self._thread.start()
        print(f"[Dashboard] Running at http://localhost:{self.port}/dashboard")

    def _run(self):
        """Run the Flask server (blocking)."""
        try:
            self._app.run(
                host='127.0.0.1',
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except OSError as e:
            if 'Address already in use' in str(e) or '10048' in str(e):
                print(f"[Dashboard] Port {self.port} in use, trying {self.port + 1}")
                self._app.run(
                    host='127.0.0.1',
                    port=self.port + 1,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            else:
                print(f"[Dashboard] Failed to start: {e}")
        except Exception as e:
            print(f"[Dashboard] Error: {e}")

    def stop(self):
        """Stop the dashboard (thread is daemon, will die with process)."""
        pass


def render_dashboard_html(initial_date: str) -> str:
    """Render the full dashboard HTML with embedded JS and Chart.js."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Telos Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #0a0a0a; --bg1: #111; --bg2: #1a1a1a; --border: #222;
  --text: #ededed; --dim: #737373; --dimmer: #525252;
  --green: #22c55e; --blue: #3b82f6; --purple: #a855f7;
  --gray: #6b7280; --amber: #f59e0b; --red: #ef4444;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; line-height:1.5; }}
.wrap {{ max-width:900px; margin:0 auto; padding:24px 20px 60px; }}
.top {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; flex-wrap:wrap; gap:12px; }}
.logo {{ font-family:monospace; font-size:13px; color:var(--green); font-weight:600; letter-spacing:0.05em; }}
.nav {{ display:flex; align-items:center; gap:8px; }}
.nav button {{ background:var(--bg1); border:1px solid var(--border); color:var(--text); padding:6px 14px; border-radius:6px; cursor:pointer; font-size:13px; }}
.nav button:hover {{ background:var(--bg2); }}
.nav input[type=date] {{ background:var(--bg1); border:1px solid var(--border); color:var(--text); padding:6px 10px; border-radius:6px; font-size:13px; font-family:monospace; }}
.date-label {{ font-family:monospace; font-size:11px; color:var(--dimmer); text-transform:uppercase; letter-spacing:0.1em; }}
h1 {{ font-size:20px; font-weight:600; }}
h1 .accent {{ color:var(--green); }}
h2 {{ font-size:12px; font-family:monospace; color:var(--dimmer); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px; }}

/* Score */
.score-row {{ display:flex; gap:16px; margin-bottom:20px; flex-wrap:wrap; }}
.score-card {{ background:var(--bg1); border-radius:12px; padding:20px; flex:1; min-width:180px; }}
.score-num {{ font-family:monospace; font-size:48px; font-weight:800; line-height:1; }}
.score-sub {{ font-size:10px; color:var(--dimmer); text-transform:uppercase; letter-spacing:0.08em; margin-top:4px; }}
.score-bar {{ width:100%; height:4px; background:var(--bg2); border-radius:2px; margin-top:10px; overflow:hidden; }}
.score-bar div {{ height:100%; border-radius:2px; transition:width 0.4s; }}
.stat-card {{ background:var(--bg1); border-radius:12px; padding:16px 20px; text-align:center; flex:1; min-width:100px; }}
.stat-val {{ font-family:monospace; font-size:22px; font-weight:700; }}
.stat-label {{ font-size:10px; color:var(--dimmer); text-transform:uppercase; letter-spacing:0.05em; margin-top:2px; }}

/* Charts */
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }}
@media (max-width:700px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:var(--bg1); border-radius:12px; padding:20px; }}
.card.wide {{ grid-column:1/-1; }}
.chart-wrap {{ position:relative; height:220px; }}
.chart-wrap.tall {{ height:300px; }}

/* Narrative */
.narrative {{ background:var(--bg1); border-radius:12px; padding:20px; margin-bottom:20px; font-size:14px; color:#a3a3a3; line-height:1.7; }}
.narrative em {{ color:var(--text); font-style:normal; font-weight:500; }}

/* Sessions */
.session {{ padding:12px 16px; border-left:3px solid; background:var(--bg1); border-radius:0 10px 10px 0; margin-bottom:6px; cursor:pointer; transition:background 0.15s; }}
.session:hover {{ background:var(--bg2); }}
.session-head {{ display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }}
.session-task {{ font-weight:600; font-size:13px; }}
.session-time {{ font-size:11px; color:var(--dimmer); }}
.session-dur {{ font-family:monospace; font-size:13px; font-weight:600; margin-left:auto; }}
.session-detail {{ font-size:12px; color:var(--dim); margin-top:4px; display:none; }}
.session.open .session-detail {{ display:block; }}

/* Heatmap */
.heatmap {{ display:flex; gap:2px; flex-wrap:wrap; }}
.heatmap-cell {{ width:calc(100%/24 - 2px); min-width:16px; height:32px; border-radius:3px; position:relative; }}
.heatmap-label {{ position:absolute; bottom:-16px; left:0; font-size:9px; color:var(--dimmer); font-family:monospace; }}

/* Range mode */
.range-bar {{ display:flex; align-items:center; gap:8px; margin-bottom:20px; flex-wrap:wrap; }}
.range-bar label {{ font-size:12px; color:var(--dim); }}
.range-bar input {{ background:var(--bg1); border:1px solid var(--border); color:var(--text); padding:5px 8px; border-radius:6px; font-family:monospace; font-size:12px; }}
.range-bar button {{ background:var(--green); border:none; color:var(--bg); padding:6px 16px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; }}

.tabs {{ display:flex; gap:4px; margin-bottom:20px; }}
.tab {{ padding:8px 16px; background:var(--bg1); border:1px solid var(--border); border-radius:6px; cursor:pointer; font-size:12px; color:var(--dim); }}
.tab.active {{ background:var(--green); color:var(--bg); border-color:var(--green); font-weight:600; }}

.loading {{ text-align:center; color:var(--dimmer); padding:40px; font-size:14px; }}
.footer {{ text-align:center; margin-top:32px; padding-top:20px; border-top:1px solid var(--border); }}
.footer p {{ font-size:11px; color:#333; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div>
      <div class="logo">telos</div>
      <div class="date-label" id="dateLabel"></div>
    </div>
    <div class="nav">
      <button onclick="prevDay()" title="Previous day">&#9664;</button>
      <input type="date" id="datePicker" onchange="goToDate(this.value)">
      <button onclick="nextDay()" title="Next day">&#9654;</button>
      <button onclick="goToday()" style="color:var(--green)">Today</button>
    </div>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('day')" id="tabDay">Daily Report</div>
    <div class="tab" onclick="switchTab('range')" id="tabRange">Date Range</div>
  </div>

  <!-- Day view -->
  <div id="dayView">
    <div id="scoreRow" class="score-row"></div>
    <div id="narrativeBox" class="narrative" style="display:none"></div>
    <div class="grid">
      <div class="card"><h2>Time Distribution</h2><div class="chart-wrap"><canvas id="donutChart"></canvas></div></div>
      <div class="card"><h2>Top Apps</h2><div class="chart-wrap tall"><canvas id="appsChart"></canvas></div></div>
      <div class="card wide"><h2>Hourly Activity</h2><div class="chart-wrap"><canvas id="heatmapChart"></canvas></div></div>
    </div>
    <h2>Sessions Timeline</h2>
    <div id="sessionsList"></div>
  </div>

  <!-- Range view -->
  <div id="rangeView" style="display:none">
    <div class="range-bar">
      <label>From</label><input type="date" id="rangeFrom">
      <label>To</label><input type="date" id="rangeTo">
      <button onclick="loadRange()">Load</button>
    </div>
    <div class="grid">
      <div class="card wide"><h2>Productivity Trend</h2><div class="chart-wrap"><canvas id="trendChart"></canvas></div></div>
      <div class="card wide"><h2>Category Breakdown Over Time</h2><div class="chart-wrap tall"><canvas id="stackChart"></canvas></div></div>
    </div>
  </div>

  <div class="footer">
    <p><span style="color:var(--green);font-weight:600;font-family:monospace;">telos</span> &middot; local dashboard</p>
    <p>All data stays on your machine. Nothing leaves localhost.</p>
  </div>
</div>

<script>
const C = {{ green:'#22c55e', blue:'#3b82f6', purple:'#a855f7', gray:'#6b7280', amber:'#f59e0b', red:'#ef4444', bg1:'#111111', bg2:'#1a1a1a', dim:'#525252' }};
const catColor = {{ work:C.blue, learning:C.purple, browsing:C.gray, entertainment:C.amber, idle:'#333' }};
let currentDate = '{initial_date}';
let charts = {{}};

Chart.defaults.color = '#737373';
Chart.defaults.borderColor = '#1a1a1a';
Chart.defaults.font.family = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";
Chart.defaults.font.size = 11;

function fmt(secs) {{
  const m = Math.floor(secs/60);
  if (m >= 60) {{ const h = Math.floor(m/60); return h+'h '+(m%60)+'m'; }}
  return m+'m';
}}

function fmtMin(mins) {{
  if (mins >= 60) {{ const h = Math.floor(mins/60); return h+'h '+(mins%60)+'m'; }}
  return mins+'m';
}}

function dayName(dateStr) {{
  return new Date(dateStr+'T12:00:00').toLocaleDateString('en-US', {{ weekday:'long', month:'long', day:'numeric', year:'numeric' }});
}}

// ── Navigation ──
function prevDay() {{
  const d = new Date(currentDate+'T12:00:00');
  d.setDate(d.getDate()-1);
  goToDate(d.toISOString().slice(0,10));
}}
function nextDay() {{
  const d = new Date(currentDate+'T12:00:00');
  d.setDate(d.getDate()+1);
  goToDate(d.toISOString().slice(0,10));
}}
function goToday() {{ goToDate(new Date().toISOString().slice(0,10)); }}
function goToDate(d) {{
  currentDate = d;
  document.getElementById('datePicker').value = d;
  document.getElementById('dateLabel').textContent = dayName(d);
  loadDay(d);
}}

// ── Tabs ──
function switchTab(tab) {{
  document.getElementById('dayView').style.display = tab==='day'?'block':'none';
  document.getElementById('rangeView').style.display = tab==='range'?'block':'none';
  document.getElementById('tabDay').className = 'tab'+(tab==='day'?' active':'');
  document.getElementById('tabRange').className = 'tab'+(tab==='range'?' active':'');
  if (tab==='range') initRange();
}}

// ── Day View ──
async function loadDay(date) {{
  const [stats, apps, heatmap, sessions] = await Promise.all([
    fetch('/api/stats?date='+date).then(r=>r.json()),
    fetch('/api/apps?date='+date).then(r=>r.json()),
    fetch('/api/heatmap?date='+date).then(r=>r.json()),
    fetch('/api/sessions?date='+date).then(r=>r.json())
  ]);
  renderScore(stats);
  renderNarrative(stats);
  renderDonut(stats);
  renderApps(apps);
  renderHeatmap(heatmap);
  renderSessions(sessions);
}}

function renderScore(s) {{
  const score = s.productivity_score != null ? Math.round(s.productivity_score * 100) : null;
  const total = (s.work||0)+(s.learning||0)+(s.browsing||0)+(s.entertainment||0);
  const sc = score >= 70 ? C.green : score >= 45 ? C.amber : score != null ? C.red : C.dim;
  const distPct = total > 0 ? Math.round(s.entertainment/total*100) : 0;

  let html = '';
  if (score != null) {{
    html += `<div class="score-card"><div class="score-num" style="color:${{sc}}">${{score}}</div><div class="score-sub">productivity score</div><div class="score-bar"><div style="width:${{score}}%;background:${{sc}}"></div></div></div>`;
  }}
  html += `<div class="stat-card"><div class="stat-val" style="color:${{C.blue}}">${{fmt(s.work||0)}}</div><div class="stat-label">Work</div></div>`;
  html += `<div class="stat-card"><div class="stat-val" style="color:${{C.purple}}">${{fmt(s.learning||0)}}</div><div class="stat-label">Learning</div></div>`;
  html += `<div class="stat-card"><div class="stat-val">${{fmt(total)}}</div><div class="stat-label">Total</div></div>`;
  html += `<div class="stat-card"><div class="stat-val">${{s.total_captures||0}}</div><div class="stat-label">Captures</div></div>`;
  document.getElementById('scoreRow').innerHTML = html;
}}

function renderNarrative(s) {{
  const box = document.getElementById('narrativeBox');
  if (s.daily_narrative) {{
    box.style.display = 'block';
    box.innerHTML = s.daily_narrative;
  }} else {{
    box.style.display = 'none';
  }}
}}

function renderDonut(s) {{
  const data = [s.work||0, s.learning||0, s.browsing||0, s.entertainment||0];
  if (charts.donut) charts.donut.destroy();
  charts.donut = new Chart(document.getElementById('donutChart'), {{
    type: 'doughnut',
    data: {{
      labels: ['Work','Learning','Browsing','Entertainment'],
      datasets: [{{ data, backgroundColor:[C.blue,C.purple,C.gray,C.amber], borderWidth:0 }}]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false, cutout:'65%',
      plugins: {{
        legend: {{ position:'bottom', labels:{{ padding:12, usePointStyle:true, pointStyle:'rectRounded' }} }},
        tooltip: {{ callbacks: {{ label: ctx => ctx.label+': '+fmt(ctx.raw) }} }}
      }}
    }}
  }});
}}

function renderApps(apps) {{
  if (charts.apps) charts.apps.destroy();
  const top = apps.slice(0,12);
  charts.apps = new Chart(document.getElementById('appsChart'), {{
    type: 'bar',
    data: {{
      labels: top.map(a=>a.name.length>22?a.name.slice(0,20)+'…':a.name),
      datasets: [{{
        data: top.map(a=>a.minutes),
        backgroundColor: top.map(a=>catColor[a.category]||C.gray),
        borderWidth: 0, borderRadius: 4, barPercentage: 0.7
      }}]
    }},
    options: {{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ display:false }}, tooltip:{{ callbacks:{{ label: ctx=>ctx.raw+'m' }} }} }},
      scales: {{ x:{{ grid:{{ color:'#1a1a1a' }}, ticks:{{ callback:v=>v+'m' }} }}, y:{{ grid:{{ display:false }} }} }}
    }}
  }});
}}

function renderHeatmap(blocks) {{
  if (charts.heatmap) charts.heatmap.destroy();
  // Aggregate to hourly
  const hours = [];
  for (let h=0;h<24;h++) {{
    const b1 = blocks[h*2], b2 = blocks[h*2+1];
    hours.push({{
      work:(b1.work+b2.work)*0.5, learning:(b1.learning+b2.learning)*0.5,
      browsing:(b1.browsing+b2.browsing)*0.5, entertainment:(b1.entertainment+b2.entertainment)*0.5,
      total:b1.total+b2.total
    }});
  }}
  charts.heatmap = new Chart(document.getElementById('heatmapChart'), {{
    type:'bar',
    data: {{
      labels: hours.map((_,i)=>i+'h'),
      datasets: [
        {{ label:'Work', data:hours.map(h=>h.work), backgroundColor:C.blue, borderWidth:0, borderRadius:2 }},
        {{ label:'Learning', data:hours.map(h=>h.learning), backgroundColor:C.purple, borderWidth:0, borderRadius:2 }},
        {{ label:'Browsing', data:hours.map(h=>h.browsing), backgroundColor:C.gray, borderWidth:0, borderRadius:2 }},
        {{ label:'Entertainment', data:hours.map(h=>h.entertainment), backgroundColor:C.amber, borderWidth:0, borderRadius:2 }}
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ position:'bottom', labels:{{ usePointStyle:true, pointStyle:'rectRounded', padding:10 }} }},
        tooltip:{{ mode:'index', callbacks:{{ label:ctx=>ctx.dataset.label+': '+Math.round(ctx.raw)+'m' }} }} }},
      scales: {{ x:{{ stacked:true, grid:{{ display:false }} }}, y:{{ stacked:true, grid:{{ color:'#1a1a1a' }}, ticks:{{ callback:v=>v+'m' }} }} }}
    }}
  }});
}}

function renderSessions(sessions) {{
  if (!sessions.length) {{
    document.getElementById('sessionsList').innerHTML = '<div class="loading">No sessions recorded for this day.</div>';
    return;
  }}
  let html = '';
  for (const s of sessions) {{
    const start = s.start_time ? new Date(s.start_time).toLocaleTimeString('en-US',{{hour:'numeric',minute:'2-digit',hour12:true}}) : '';
    const end = s.end_time ? new Date(s.end_time).toLocaleTimeString('en-US',{{hour:'numeric',minute:'2-digit',hour12:true}}) : 'ongoing';
    const dur = s.duration_seconds ? fmtMin(Math.round(s.duration_seconds/60)) : '';
    const cat = mapCat(s.category);
    const color = catColor[cat]||C.gray;
    html += `<div class="session" style="border-left-color:${{color}}" onclick="this.classList.toggle('open')">
      <div class="session-head">
        <span class="session-task">${{s.primary_task||s.category}}</span>
        <span class="session-time">${{start}} — ${{end}}</span>
        <span class="session-dur" style="color:${{color}}">${{dur}}</span>
      </div>
      ${{s.detailed_summary ? `<div class="session-detail">${{s.detailed_summary}}</div>` : ''}}
    </div>`;
  }}
  document.getElementById('sessionsList').innerHTML = html;
}}

function mapCat(c) {{
  if (!c) return 'browsing';
  c = c.toLowerCase();
  if (c.includes('work')||c.includes('debug')||c.includes('develop')||c.includes('deploy')||c.includes('code')||c.includes('review')||c.includes('plan')||c.includes('admin')||c.includes('setup')||c.includes('security')||c.includes('bug')||c.includes('test')||c.includes('feature')||c.includes('project')||c.includes('product')||c.includes('meeting')||c.includes('issue')||c.includes('release')||c.includes('beta')||c.includes('api')||c.includes('bot')||c.includes('agent')||c.includes('ui/')||c.includes('frontend')||c.includes('backend')) return 'work';
  if (c.includes('learn')||c.includes('research')||c.includes('philosophy')||c.includes('career')||c.includes('resume')||c.includes('educational')) return 'learning';
  if (c.includes('entertain')||c.includes('game')||c.includes('gaming')||c.includes('video stream')||c.includes('comedy')||c.includes('music')||c.includes('youtube')||c.includes('playing')) return 'entertainment';
  return 'browsing';
}}

// ── Range View ──
function initRange() {{
  const to = new Date().toISOString().slice(0,10);
  const from = new Date(Date.now()-7*86400000).toISOString().slice(0,10);
  document.getElementById('rangeFrom').value = from;
  document.getElementById('rangeTo').value = to;
  loadRange();
}}

async function loadRange() {{
  const from = document.getElementById('rangeFrom').value;
  const to = document.getElementById('rangeTo').value;
  const data = await fetch(`/api/range?from=${{from}}&to=${{to}}`).then(r=>r.json());
  renderTrend(data);
  renderStack(data);
}}

function renderTrend(days) {{
  if (charts.trend) charts.trend.destroy();
  charts.trend = new Chart(document.getElementById('trendChart'), {{
    type:'line',
    data: {{
      labels: days.map(d=>d.date.slice(5)),
      datasets: [{{
        label:'Score', data:days.map(d=>d.score!=null?Math.round(d.score*100):null),
        borderColor:C.green, backgroundColor:C.green+'22', fill:true, tension:0.3,
        pointBackgroundColor:C.green, pointRadius:4
      }}]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ display:false }} }},
      scales: {{ y:{{ min:0, max:100, grid:{{ color:'#1a1a1a' }} }}, x:{{ grid:{{ display:false }} }} }}
    }}
  }});
}}

function renderStack(days) {{
  if (charts.stack) charts.stack.destroy();
  charts.stack = new Chart(document.getElementById('stackChart'), {{
    type:'bar',
    data: {{
      labels: days.map(d=>d.date.slice(5)),
      datasets: [
        {{ label:'Work', data:days.map(d=>Math.round(d.work/60)), backgroundColor:C.blue, borderWidth:0 }},
        {{ label:'Learning', data:days.map(d=>Math.round(d.learning/60)), backgroundColor:C.purple, borderWidth:0 }},
        {{ label:'Browsing', data:days.map(d=>Math.round(d.browsing/60)), backgroundColor:C.gray, borderWidth:0 }},
        {{ label:'Entertainment', data:days.map(d=>Math.round(d.entertainment/60)), backgroundColor:C.amber, borderWidth:0 }}
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{ legend:{{ position:'bottom', labels:{{ usePointStyle:true, pointStyle:'rectRounded' }} }},
        tooltip:{{ mode:'index', callbacks:{{ label:ctx=>ctx.dataset.label+': '+ctx.raw+'m' }} }} }},
      scales: {{ x:{{ stacked:true, grid:{{ display:false }} }}, y:{{ stacked:true, grid:{{ color:'#1a1a1a' }}, ticks:{{ callback:v=>v+'m' }} }} }}
    }}
  }});
}}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {{
  goToDate(currentDate);
}});
</script>
</body>
</html>''';
