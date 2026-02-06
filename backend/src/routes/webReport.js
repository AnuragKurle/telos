/**
 * Web Report Viewer
 * 
 * Serves daily reports as interactive web pages.
 * Accessed via a signed URL from the email CTA button.
 * 
 * Route: GET /r/:reportId?t=<hmac-token>
 * 
 * No login required -- access is controlled by an HMAC token
 * that is generated when the email is sent. The token is
 * HMAC(reportId, encryption_key) so only someone with the
 * email link can view the report.
 */

import express from 'express';
import admin from 'firebase-admin';
import crypto from 'crypto';
import { getSecret } from '../services/secrets.js';
import { decrypt, decryptFields } from '../services/encryption.js';

const SUMMARY_ENCRYPT_FIELDS = ['daily_narrative', 'key_learnings_json', 'apps', 'timeline', 'deep_work_sessions'];
const SUMMARY_JSON_FIELDS = ['apps', 'timeline', 'deep_work_sessions'];

const router = express.Router();

let tokenKey = null;

/**
 * Get or initialize the HMAC key (reuses encryption key)
 */
async function getTokenKey() {
  if (tokenKey) return tokenKey;
  const secretName = process.env.ENCRYPTION_KEY_SECRET_NAME || 'ENCRYPTION_KEY';
  try {
    const key = await getSecret(secretName);
    tokenKey = key;
    return key;
  } catch (e) {
    // Fallback for dev: use a static key
    tokenKey = process.env.ENCRYPTION_KEY || 'dev-report-viewer-key-not-for-production';
    return tokenKey;
  }
}

/**
 * Generate a view token for a report
 */
export async function generateViewToken(reportId) {
  const key = await getTokenKey();
  return crypto.createHmac('sha256', key).update(reportId).digest('hex').substring(0, 32);
}

/**
 * Verify a view token
 */
async function verifyViewToken(reportId, token) {
  const expected = await generateViewToken(reportId);
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(token));
}

/**
 * Helper: format minutes to readable duration
 */
function fmt(minutes) {
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m ? `${h}h ${m}m` : `${h}h`;
  }
  return `${minutes}m`;
}

/**
 * GET /r/:reportId
 * Serve the report as an interactive web page
 */
router.get('/:reportId', async (req, res) => {
  const { reportId } = req.params;
  const token = req.query.t;

  if (!token || token.length !== 32) {
    return res.status(403).send(renderError('Invalid or missing access token.'));
  }

  try {
    // Verify token
    const valid = await verifyViewToken(reportId, token);
    if (!valid) {
      return res.status(403).send(renderError('Invalid access token.'));
    }

    // Fetch the report from Firestore
    const db = admin.firestore();
    const doc = await db.collection('daily_summaries').doc(reportId).get();

    if (!doc.exists) {
      return res.status(404).send(renderError('Report not found.'));
    }

    const data = doc.data();
    const summary = data.summary || {};

    // Decrypt fields
    if (typeof summary === 'object') {
      decryptFields(summary, SUMMARY_ENCRYPT_FIELDS, SUMMARY_JSON_FIELDS);
    }

    // Render the web page
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.send(renderReportPage(summary, data.date));

  } catch (error) {
    console.error('[WEB-REPORT] Error:', error);
    return res.status(500).send(renderError('Something went wrong loading this report.'));
  }
});

/**
 * Render error page
 */
function renderError(message) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Telos Report</title>
  <style>
    body { background: #0a0a0a; color: #a3a3a3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
    .box { text-align: center; max-width: 400px; padding: 40px; }
    h1 { color: #ededed; font-size: 20px; margin: 0 0 12px; }
    p { font-size: 14px; line-height: 1.6; margin: 0; }
    .logo { color: #22c55e; font-family: monospace; font-size: 14px; margin-bottom: 20px; }
  </style>
</head>
<body>
  <div class="box">
    <div class="logo">telos</div>
    <h1>Cannot load report</h1>
    <p>${message}</p>
  </div>
</body>
</html>`;
}

/**
 * Render the full interactive report web page
 */
function renderReportPage(summary, dateStr) {
  const dateObj = new Date(dateStr || summary.date);
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
  const fullDate = dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const workMin = Math.floor((summary.work_seconds || 0) / 60);
  const learningMin = Math.floor((summary.learning_seconds || 0) / 60);
  const browsingMin = Math.floor((summary.browsing_seconds || 0) / 60);
  const entertainmentMin = Math.floor((summary.entertainment_seconds || 0) / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;
  const workPct = totalMin > 0 ? Math.round(workMin / totalMin * 100) : 0;
  const learnPct = totalMin > 0 ? Math.round(learningMin / totalMin * 100) : 0;
  const browsePct = totalMin > 0 ? Math.round(browsingMin / totalMin * 100) : 0;
  const entPct = 100 - workPct - learnPct - browsePct;

  const narrative = summary.daily_narrative || 'No narrative available.';
  const apps = summary.apps || [];
  const timeline = summary.timeline || [];
  const score = Math.round(summary.productivity_score || 0);
  const scoreColor = score >= 70 ? '#22c55e' : score >= 45 ? '#f59e0b' : '#ef4444';
  const deepWork = summary.deep_work_sessions || [];
  const focusQuality = summary.focus_quality || {};
  const weeklyComp = summary.weekly_comparison || {};

  const maxAppMin = apps.length > 0 ? apps[0].minutes : 1;

  // Build apps HTML
  const appsHtml = apps.map(app => {
    const color = { work: '#3b82f6', learning: '#a855f7', browsing: '#6b7280', entertainment: '#f59e0b' }[app.category] || '#6b7280';
    const barW = Math.max(3, Math.round(app.minutes / maxAppMin * 100));
    return `
      <div class="app-row">
        <span class="app-name">${app.name}</span>
        <div class="app-bar-track"><div class="app-bar" style="width:${barW}%; background:${color};"></div></div>
        <span class="app-time" style="color:${color}">${app.minutes}m</span>
      </div>`;
  }).join('');

  // Build timeline HTML
  const timelineHtml = timeline
    .filter(t => t.duration_mins >= 1)
    .map(item => {
      const color = { work: '#3b82f6', learning: '#a855f7', browsing: '#6b7280', entertainment: '#f59e0b' }[item.category] || '#6b7280';
      const task = item.task || 'Activity';
      return `
      <div class="tl-item" style="border-left-color:${color}">
        <div class="tl-header">
          <span class="tl-app">${item.app}</span>
          ${item.start ? `<span class="tl-time">${item.start}</span>` : ''}
          <span class="tl-dur" style="color:${color}">${fmt(item.duration_mins)}</span>
        </div>
        <div class="tl-task">${task}</div>
      </div>`;
    }).join('');

  // Weekly comparison data for chart
  let weeklyHtml = '';
  if (weeklyComp && weeklyComp.has_history) {
    weeklyHtml = `
      <section>
        <h2>Weekly Trends <span class="dim">(${weeklyComp.days_compared}-day avg)</span></h2>
        <div class="bars-section">
          <div class="bars-group">
            <div class="bars-label">Work Time</div>
            <div class="bar-pair">
              <div class="bar-row"><span class="bar-tag">Today</span><div class="bar-track"><div class="bar-fill" style="width:${Math.round(weeklyComp.current_work / Math.max(weeklyComp.current_work, weeklyComp.avg_work, 1) * 100)}%; background:#3b82f6;"></div></div><span class="bar-val" style="color:#3b82f6">${fmt(weeklyComp.current_work)}</span></div>
              <div class="bar-row"><span class="bar-tag dim">Avg</span><div class="bar-track"><div class="bar-fill" style="width:${Math.round(weeklyComp.avg_work / Math.max(weeklyComp.current_work, weeklyComp.avg_work, 1) * 100)}%; background:#1e3a5f;"></div></div><span class="bar-val dim">${fmt(weeklyComp.avg_work)}</span></div>
            </div>
            <div class="bar-diff ${weeklyComp.work_diff >= 0 ? 'up' : 'down'}">${weeklyComp.work_diff >= 0 ? '&#9650;' : '&#9660;'} ${Math.abs(weeklyComp.work_diff)}m ${weeklyComp.work_diff >= 0 ? 'more' : 'less'}</div>
          </div>
          <div class="bars-group">
            <div class="bars-label">Total Time</div>
            <div class="bar-pair">
              <div class="bar-row"><span class="bar-tag">Today</span><div class="bar-track"><div class="bar-fill" style="width:${Math.round(weeklyComp.current_total / Math.max(weeklyComp.current_total, weeklyComp.avg_total, 1) * 100)}%; background:#22c55e;"></div></div><span class="bar-val" style="color:#22c55e">${fmt(weeklyComp.current_total)}</span></div>
              <div class="bar-row"><span class="bar-tag dim">Avg</span><div class="bar-track"><div class="bar-fill" style="width:${Math.round(weeklyComp.avg_total / Math.max(weeklyComp.current_total, weeklyComp.avg_total, 1) * 100)}%; background:#0f3d1f;"></div></div><span class="bar-val dim">${fmt(weeklyComp.avg_total)}</span></div>
            </div>
            <div class="bar-diff ${weeklyComp.total_diff >= 0 ? 'up' : 'down'}">${weeklyComp.total_diff >= 0 ? '&#9650;' : '&#9660;'} ${Math.abs(weeklyComp.total_diff)}m ${weeklyComp.total_diff >= 0 ? 'more' : 'less'}</div>
          </div>
        </div>
      </section>`;
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${dayName} Report - Telos</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0a0a0a; color: #ededed; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; }
    .wrap { max-width: 640px; margin: 0 auto; padding: 32px 20px 48px; }
    .logo { font-family: monospace; font-size: 13px; color: #22c55e; font-weight: 600; margin-bottom: 24px; letter-spacing: 0.05em; }
    .date { font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }
    h1 { font-size: 22px; font-weight: 600; margin-bottom: 20px; }
    h1 span { color: #22c55e; }
    h2 { font-size: 13px; font-family: monospace; color: #525252; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 14px; }
    .dim { color: #525252; }
    section { margin-bottom: 28px; }

    /* Score hero */
    .score-card { display: flex; align-items: flex-start; gap: 24px; background: #111; border-radius: 12px; padding: 24px; margin-bottom: 28px; border: 1px solid #1a1a1a; }
    .score-num { font-family: monospace; font-size: 56px; font-weight: 800; line-height: 1; color: ${scoreColor}; }
    .score-sub { font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
    .score-bar { width: 80px; height: 4px; background: #1a1a1a; border-radius: 2px; margin-top: 10px; overflow: hidden; }
    .score-bar-fill { height: 100%; background: ${scoreColor}; border-radius: 2px; }
    .score-right { flex: 1; }
    .score-verdict { font-size: 16px; font-weight: 600; color: ${scoreColor}; margin-bottom: 8px; }
    .score-narrative { font-size: 14px; color: #a3a3a3; line-height: 1.65; }

    /* Time chart */
    .time-card { background: #111; border-radius: 10px; padding: 20px; margin-bottom: 28px; }
    .time-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .time-total { font-family: monospace; font-size: 14px; font-weight: 600; }
    .stacked-bar { display: flex; height: 16px; border-radius: 8px; overflow: hidden; margin-bottom: 16px; }
    .stacked-bar div { height: 100%; transition: width 0.3s; }
    .legend { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; }
    .legend-item { font-size: 13px; color: #a3a3a3; display: flex; align-items: center; gap: 8px; }
    .legend-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
    .legend-item strong { color: #ededed; }

    /* Apps */
    .app-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #1a1a1a; }
    .app-row:last-child { border-bottom: none; }
    .app-name { font-size: 13px; width: 120px; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .app-bar-track { flex: 1; height: 6px; background: #1a1a1a; border-radius: 3px; overflow: hidden; }
    .app-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
    .app-time { font-family: monospace; font-size: 13px; font-weight: 600; width: 44px; text-align: right; flex-shrink: 0; }

    /* Timeline */
    .tl-item { padding: 10px 14px; border-left: 3px solid; background: #111; border-radius: 0 8px 8px 0; margin-bottom: 6px; }
    .tl-header { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    .tl-app { font-weight: 600; font-size: 13px; }
    .tl-time { font-size: 11px; color: #525252; }
    .tl-dur { font-family: monospace; font-size: 13px; font-weight: 600; margin-left: auto; }
    .tl-task { font-size: 12px; color: #737373; margin-top: 3px; }

    /* Focus metrics */
    .metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .metric { background: #111; border-radius: 10px; padding: 16px; text-align: center; }
    .metric-val { font-family: monospace; font-size: 22px; font-weight: 700; }
    .metric-label { font-size: 10px; color: #525252; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

    /* Weekly bars */
    .bars-section { display: flex; flex-direction: column; gap: 20px; }
    .bars-group { background: #111; border-radius: 10px; padding: 16px; }
    .bars-label { font-size: 12px; color: #888; text-transform: uppercase; margin-bottom: 10px; }
    .bar-pair { display: flex; flex-direction: column; gap: 6px; }
    .bar-row { display: flex; align-items: center; gap: 8px; }
    .bar-tag { font-size: 11px; color: #a3a3a3; width: 38px; flex-shrink: 0; }
    .bar-track { flex: 1; height: 8px; background: #1a1a1a; border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 4px; }
    .bar-val { font-family: monospace; font-size: 12px; font-weight: 600; width: 44px; text-align: right; flex-shrink: 0; }
    .bar-diff { font-size: 11px; margin-top: 8px; }
    .bar-diff.up { color: #22c55e; }
    .bar-diff.down { color: #ef4444; }

    .footer { text-align: center; padding-top: 24px; border-top: 1px solid #1a1a1a; margin-top: 12px; }
    .footer p { font-size: 11px; color: #333; margin-bottom: 4px; }
    .footer a { color: #404040; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="logo">telos</div>
    <div class="date">${dayName}, ${fullDate}</div>
    <h1>Your <span>${dayName}</span> Report</h1>

    <!-- Score -->
    <div class="score-card">
      <div>
        <div class="score-num">${score}</div>
        <div class="score-sub">/ 100</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:${score}%"></div></div>
      </div>
      <div class="score-right">
        <div class="score-verdict">${score >= 80 ? 'Excellent day' : score >= 65 ? 'Solid day' : score >= 45 ? 'Mixed day' : score >= 25 ? 'Light day' : 'Getting started'}</div>
        <div class="score-narrative">${narrative}</div>
      </div>
    </div>

    <!-- Time Distribution -->
    <div class="time-card">
      <div class="time-header">
        <h2 style="margin:0">Time Breakdown</h2>
        <div class="time-total">${fmt(totalMin)}</div>
      </div>
      <div class="stacked-bar">
        ${workMin > 0 ? `<div style="width:${workPct}%; background:#3b82f6;"></div>` : ''}
        ${learningMin > 0 ? `<div style="width:${learnPct}%; background:#a855f7;"></div>` : ''}
        ${browsingMin > 0 ? `<div style="width:${browsePct}%; background:#6b7280;"></div>` : ''}
        ${entertainmentMin > 0 ? `<div style="width:${entPct}%; background:#f59e0b;"></div>` : ''}
      </div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>Work <strong>${fmt(workMin)}</strong> <span class="dim">${workPct}%</span></div>
        <div class="legend-item"><div class="legend-dot" style="background:#a855f7"></div>Learning <strong>${fmt(learningMin)}</strong> <span class="dim">${learnPct}%</span></div>
        <div class="legend-item"><div class="legend-dot" style="background:#6b7280"></div>Browsing <strong>${fmt(browsingMin)}</strong> <span class="dim">${browsePct}%</span></div>
        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>Entertainment <strong>${fmt(entertainmentMin)}</strong> <span class="dim">${entPct}%</span></div>
      </div>
    </div>

    <!-- Apps -->
    ${apps.length > 0 ? `
    <section>
      <h2>All Apps</h2>
      ${appsHtml}
    </section>
    ` : ''}

    <!-- Timeline -->
    ${timeline.length > 0 ? `
    <section>
      <h2>Activity Timeline</h2>
      ${timelineHtml}
    </section>
    ` : ''}

    <!-- Focus Metrics -->
    ${focusQuality.avg_session_length ? `
    <section>
      <h2>Focus Metrics</h2>
      <div class="metrics">
        <div class="metric">
          <div class="metric-val">${focusQuality.avg_session_length}m</div>
          <div class="metric-label">Avg Session</div>
        </div>
        <div class="metric">
          <div class="metric-val" style="color:${(summary.context_switches || 0) > 50 ? '#f59e0b' : '#22c55e'}">${summary.context_switches || 0}</div>
          <div class="metric-label">Switches</div>
        </div>
        <div class="metric">
          <div class="metric-val" style="color:${focusQuality.focus_quality_score >= 70 ? '#22c55e' : focusQuality.focus_quality_score >= 40 ? '#f59e0b' : '#ef4444'}">${focusQuality.focus_quality_score}</div>
          <div class="metric-label">Focus Score</div>
        </div>
      </div>
    </section>
    ` : ''}

    <!-- Weekly -->
    ${weeklyHtml}

    <div class="footer">
      <p><span style="color:#22c55e; font-weight:600; font-family:monospace;">telos</span> &middot; daily report</p>
      <p>Your data is encrypted and stored anonymously.</p>
    </div>
  </div>
</body>
</html>`;
}

export default router;
