/**
 * Email Service - SendGrid Integration
 * 
 * Handles sending daily report emails to users via SendGrid.
 */

import sgMail from '@sendgrid/mail';
import { getSecret } from './secrets.js';
import admin from 'firebase-admin';
import { generateSummaryFromUsage } from './summaryGenerator.js';

let isInitialized = false;

/**
 * Initialize SendGrid with API key from Secret Manager
 */
export async function initializeSendGrid() {
  if (isInitialized) return;

  try {
    const apiKey = await getSecret(process.env.SENDGRID_API_KEY_SECRET_NAME || 'SENDGRID_API_KEY');
    sgMail.setApiKey(apiKey);
    isInitialized = true;
    console.log('[EMAIL] SendGrid initialized');
  } catch (error) {
    console.error('[EMAIL] Failed to initialize SendGrid:', error);
    throw error;
  }
}

/**
 * Helper: Format duration
 */
function formatDuration(minutes) {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins ? `${hours}h ${mins}m` : `${hours}h`;
  }
  return `${minutes}m`;
}

/**
 * Generate insights and recommendations section
 */
function generateInsightsHTML(summary, workMin, totalMin, weeklyComp, focusQuality, deepWork) {
  const insights = [];

  // Deep work insight
  if (deepWork.length > 0) {
    const totalDeepWork = deepWork.reduce((sum, s) => sum + s.duration_mins, 0);
    insights.push(`⚡ You had ${deepWork.length} deep work session${deepWork.length > 1 ? 's' : ''} totaling ${totalDeepWork} minutes of sustained focus.`);
  } else if (workMin > 10) {
    insights.push(`💡 No deep work sessions detected. Try blocking 15+ minutes for focused work without switching apps.`);
  }

  // Weekly comparison insight
  if (weeklyComp.has_history) {
    if (weeklyComp.work_diff > 0) {
      insights.push(`📈 ${weeklyComp.work_diff}m more work time than your ${weeklyComp.days_compared}-day average (${weeklyComp.avg_work}m).`);
    } else if (weeklyComp.work_diff < -10) {
      insights.push(`📉 ${Math.abs(weeklyComp.work_diff)}m less work time than usual. Your ${weeklyComp.days_compared}-day average is ${weeklyComp.avg_work}m.`);
    }
  }

  // Focus quality insight
  if (focusQuality.focus_quality_score) {
    if (focusQuality.focus_quality_score >= 70) {
      insights.push(`✨ Strong focus quality (${focusQuality.focus_quality_score}/100). Average session: ${focusQuality.avg_session_length}min.`);
    } else if (focusQuality.fragmentation_ratio > 50) {
      insights.push(`🔀 High fragmentation (${focusQuality.fragmentation_ratio}% short sessions). Try longer focused blocks.`);
    }
  }

  // Context switching insight
  if (summary.context_switches > 50) {
    insights.push(`⚠️ ${summary.context_switches} context switches detected. Frequent app switching may reduce productivity.`);
  }

  // Distraction insight
  if (focusQuality.distraction_minutes > 30) {
    insights.push(`🎯 ${focusQuality.distraction_minutes}m spent on potential distractions. Consider blocking distraction time.`);
  }

  // Productive ratio insight
  const productiveMin = workMin + Math.floor(summary.learning_seconds / 60);
  const productiveRatio = Math.round(productiveMin / Math.max(totalMin, 1) * 100);
  if (productiveRatio >= 60) {
    insights.push(`🎯 ${productiveRatio}% of your time was spent on productive activities.`);
  }

  if (insights.length === 0) {
    insights.push('Keep tracking your activity to build insights over time.');
  }

  return insights.map(insight => `
                                        <div style="padding: 10px 14px; margin-bottom: 8px; background-color: #1a1a1a; border-left: 3px solid #22c55e; border-radius: 0 6px 6px 0; color: #d4d4d4; font-size: 13px; line-height: 1.5;">
                                            ${insight}
                                        </div>`).join('');
}

/**
 * Helper: Get app icon emoji
 */
function getAppIcon(appName, category) {
  const app = (appName || '').toLowerCase();
  if (app.includes('meet') || app.includes('zoom') || app.includes('teams')) return '📹';
  if (app.includes('whatsapp') || app.includes('telegram') || app.includes('discord')) return '💬';
  if (app.includes('slack')) return '💼';
  if (app.includes('code') || app.includes('vscode')) return '💻';
  if (app.includes('youtube')) return '📺';
  if (app.includes('reddit')) return '🔗';
  if (app.includes('instagram')) return '📷';
  if (app.includes('linkedin')) return '💼';
  if (app.includes('airbnb')) return '🏠';
  if (app.includes('mixpanel')) return '📊';
  if (category === 'work') return '💼';
  if (category === 'learning') return '📚';
  if (category === 'entertainment') return '🎮';
  return '🌐';
}

/**
 * Generate HTML email from daily summary data
 * Uses dark-themed Telos template with Top Apps and Timeline
 */
function generateReportHTML(summary, userName = 'there') {
  // Extract name from email if userName is email-like
  const safeName = userName || 'there';
  const displayName = safeName.includes('@') ? safeName.split('@')[0] : safeName;

  const dateObj = new Date(summary.date);
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
  const fullDate = dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const workMin = Math.floor(summary.work_seconds / 60);
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const browsingMin = Math.floor(summary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(summary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  const workPct = Math.round(workMin / Math.max(totalMin, 1) * 100);
  const learningPct = Math.round(learningMin / Math.max(totalMin, 1) * 100);
  const browsePct = Math.round(browsingMin / Math.max(totalMin, 1) * 100);
  const entertainmentPct = Math.round(entertainmentMin / Math.max(totalMin, 1) * 100);

  const narrative = summary.daily_narrative || 'No summary available for this day.';
  const apps = summary.apps || [];
  const timeline = summary.timeline || [];

  // Enhanced analytics
  const deepWork = summary.deep_work_sessions || [];
  const focusQuality = summary.focus_quality || {};
  const weeklyComp = summary.weekly_comparison || {};
  const peakHour = summary.peak_productivity_hour || 0;

  // Generate Top Apps HTML
  const topAppsHtml = apps.slice(0, 5).map((app, i) => {
    const icon = getAppIcon(app.name, app.category);
    const catColor = { 'work': '#3b82f6', 'learning': '#a855f7', 'browsing': '#6b7280', 'entertainment': '#f59e0b' }[app.category] || '#6b7280';
    const borderBottom = i < 4 ? 'border-bottom: 1px solid #222222;' : '';
    return `
                                <tr>
                                    <td style="padding: 12px 16px; ${borderBottom}" bgcolor="#111111">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="30" style="font-size: 16px; color: #ededed;" bgcolor="#111111">${icon}</td>
                                                <td style="color: #ededed; font-size: 14px;" bgcolor="#111111">${app.name}</td>
                                                <td width="50" style="text-align: right; font-family: monospace; font-size: 13px; font-weight: 600; color: ${catColor};" bgcolor="#111111">${app.minutes}m</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>`;
  }).join('');

  // Generate Timeline HTML - show top activities by duration
  const timelineHtml = timeline
    .filter(item => item.duration_mins >= 1)  // Only show >= 1 minute
    .slice(0, 8)  // Show top 8 activities
    .map(item => {
      const catColor = { 'work': '#3b82f6', 'learning': '#a855f7', 'browsing': '#6b7280', 'entertainment': '#f59e0b' }[item.category] || '#6b7280';
      const icon = getAppIcon(item.app, item.category);
      const taskText = item.task || 'Activity';

      // Format duration in a more readable way
      let durationDisplay = `${item.duration_mins}m`;
      if (item.duration_mins >= 60) {
        const hours = Math.floor(item.duration_mins / 60);
        const mins = item.duration_mins % 60;
        durationDisplay = mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
      }

      return `
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 10px; background-color: #1a1a1a; border-left: 3px solid ${catColor}; border-radius: 0 8px 8px 0;" bgcolor="#1a1a1a">
                                <tr>
                                    <td style="padding: 14px 16px;" bgcolor="#1a1a1a">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="32" style="font-size: 18px; vertical-align: top;" bgcolor="#1a1a1a">${icon}</td>
                                                <td style="padding-left: 10px;" bgcolor="#1a1a1a">
                                                    <div style="font-weight: 600; color: #ededed; font-size: 15px;">${item.app}</div>
                                                    <div style="font-size: 13px; color: #a3a3a3; margin-top: 3px; line-height: 1.4;">${taskText.substring(0, 70)}${taskText.length > 70 ? '...' : ''}</div>
                                                </td>
                                                <td width="60" style="text-align: right; vertical-align: top;" bgcolor="#1a1a1a">
                                                    <div style="font-family: monospace; font-size: 16px; font-weight: 600; color: ${catColor};">${durationDisplay}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>`;
    }).join('');

  // Generate Insights HTML
  const insightsHtml = generateInsightsHTML(summary, workMin, totalMin, weeklyComp, focusQuality, deepWork);

  // Dark-themed HTML template (email-compatible with table-based layout)
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
    <title>Telos Daily Report</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;" bgcolor="#0a0a0a">
    
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0a0a0a;" bgcolor="#0a0a0a">
        <tr>
            <td align="center" style="padding: 20px 10px;" bgcolor="#0a0a0a">
                
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; background-color: #0a0a0a;" bgcolor="#0a0a0a">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                ${dayName}, ${fullDate}
                            </p>
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #ededed;">
                                Here's your <span style="color: #22c55e;">${dayName}</span>, ${displayName}
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Summary Box -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 8px; border-left: 3px solid #22c55e;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 16px; color: #d4d4d4; font-size: 14px; line-height: 1.6;" bgcolor="#111111">
                                        ${narrative.substring(0, 280)}${narrative.length > 280 ? '...' : ''}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Metrics Row 1 -->
                    <tr>
                        <td style="padding: 0 16px 10px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #22c55e;">
                                            ${formatDuration(totalMin)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Total Tracked</div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #3b82f6;">
                                            ${formatDuration(workMin)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Work</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Metrics Row 2 -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #f59e0b;">
                                            ${browsePct}%
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Browsing</div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #a855f7;">
                                            ${formatDuration(learningMin)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Learning</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Top Apps Section -->
                    ${apps.length > 0 ? `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Top Apps
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                ${topAppsHtml}
                            </table>
                        </td>
                    </tr>
                    ` : ''}
                    
                    <!-- Top Activities Section -->
                    ${timeline.length > 0 ? `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Top Activities
                            </p>
                            <p style="margin: 0 0 12px 0; font-size: 12px; color: #737373;">
                                Your most significant activities, aggregated by app
                            </p>
                            ${timelineHtml}
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Insights & Analytics Section -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                💡 Insights & Recommendations
                            </p>
                            <p style="margin: 0 0 12px 0; font-size: 12px; color: #737373;">
                                Personalized insights from your activity patterns
                            </p>
                            ${insightsHtml}
                        </td>
                    </tr>

                    <!-- Focus & Context Section -->
                    ${focusQuality && focusQuality.avg_session_length ? `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                📊 Focus Metrics
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 14px 18px; border-bottom: 1px solid #222222;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; text-transform: uppercase; margin-bottom: 4px;">Avg Session Length</div>
                                        <div style="font-size: 18px; font-weight: 600; color: #ededed;">${focusQuality.avg_session_length}m</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 14px 18px; border-bottom: 1px solid #222222;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; text-transform: uppercase; margin-bottom: 4px;">Context Switches</div>
                                        <div style="font-size: 18px; font-weight: 600; color: ${summary.context_switches > 50 ? '#f59e0b' : '#22c55e'};">${summary.context_switches}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 14px 18px;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; text-transform: uppercase; margin-bottom: 4px;">Focus Quality</div>
                                        <div style="font-size: 18px; font-weight: 600; color: ${focusQuality.focus_quality_score >= 70 ? '#22c55e' : focusQuality.focus_quality_score >= 40 ? '#f59e0b' : '#ef4444'};">${focusQuality.focus_quality_score}/100</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Weekly Comparison Section -->
                    ${weeklyComp && weeklyComp.has_history ? `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                📈 Weekly Trends (${weeklyComp.days_compared}-Day Avg)
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; margin-bottom: 6px;">WORK TIME</div>
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #3b82f6;">${weeklyComp.current_work}m</div>
                                        <div style="font-size: 12px; color: ${weeklyComp.work_diff >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 4px;">
                                            ${weeklyComp.work_diff >= 0 ? '▲' : '▼'} ${Math.abs(weeklyComp.work_diff)}m vs avg (${weeklyComp.avg_work}m)
                                        </div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; margin-bottom: 6px;">TOTAL TIME</div>
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #22c55e;">${weeklyComp.current_total}m</div>
                                        <div style="font-size: 12px; color: ${weeklyComp.total_diff >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 4px;">
                                            ${weeklyComp.total_diff >= 0 ? '▲' : '▼'} ${Math.abs(weeklyComp.total_diff)}m vs avg (${weeklyComp.avg_total}m)
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 16px; border-top: 1px solid #262626; text-align: center;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 12px; color: #525252;">
                                <span style="color: #22c55e;">telos</span> daily report
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
  `;
}

/**
 * Generate plain text version
 */
function generatePlainText(summary) {
  const date = new Date(summary.date).toLocaleDateString();
  const workMin = Math.floor(summary.work_seconds / 60);
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const browsingMin = Math.floor(summary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(summary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  let keyLearnings = [];
  try {
    keyLearnings = JSON.parse(summary.key_learnings_json || '[]');
  } catch (e) { }

  const learningsText = keyLearnings.length > 0
    ? '\n\nKEY LEARNINGS:\n' + keyLearnings.map((l, i) => `  ${i + 1}. ${l}`).join('\n')
    : '';

  return `
DAILY ACTIVITY REPORT
${date}

PRODUCTIVITY SCORE: ${Math.round(summary.productivity_score || 0)}/100

DAILY SUMMARY:
${summary.daily_narrative || 'No summary available.'}

TIME BREAKDOWN:
  Total Active Time: ${totalMin} minutes
  
  Work: ${workMin}m
  Learning: ${learningMin}m
  Browsing: ${browsingMin}m
  Entertainment: ${entertainmentMin}m
${learningsText}

STATS:
  Context Switches: ${summary.context_switches || 0}

---
Generated by Telos Screen Tracker
  `.trim();
}

/**
 * Send daily report email
 */
export async function sendDailyReport(userEmail, summary, userName = null) {
  await initializeSendGrid();

  const date = new Date(summary.date).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });

  const msg = {
    to: userEmail,
    from: {
      email: process.env.SENDGRID_FROM_EMAIL || 'reports@telos.dev',
      name: process.env.SENDGRID_FROM_NAME || 'Telos'
    },
    replyTo: 'support@telos.dev',
    subject: `Daily Activity Report - ${date}`,
    text: generatePlainText(summary),
    html: generateReportHTML(summary, userName)
  };

  try {
    await sgMail.send(msg);
    console.log(`[EMAIL] Report sent to ${userEmail}`);
    return { success: true };
  } catch (error) {
    console.error(`[EMAIL] Failed to send to ${userEmail}:`, error);
    if (error.response) {
      console.error('[EMAIL] SendGrid error:', error.response.body);
    }
    return { success: false, error: error.message };
  }
}

/**
 * Send daily reports to all users who have email enabled
 * Called by scheduler every hour
 */
export async function sendDailyReports(force = false) {
  console.log(`\n========================================`);
  console.log(`[EMAIL] Starting daily report check`);
  console.log(`[EMAIL] Time: ${new Date().toISOString()} (UTC Hour: ${new Date().getUTCHours()})`);
  console.log(`[EMAIL] Force mode: ${force}`);
  console.log(`========================================\n`);

  const db = admin.firestore();
  const now = new Date();
  const currentHour = now.getUTCHours();

  try {
    // Get users with email reports enabled
    const usersSnapshot = await db.collection('users')
      .where('emailReports.enabled', '==', true)
      .get();

    if (usersSnapshot.empty) {
      console.log('[EMAIL] No users with email reports enabled');
      return;
    }

    console.log(`[EMAIL] Found ${usersSnapshot.size} users with email reports enabled`);
    let sentCount = 0;
    let errorCount = 0;
    let skippedCount = 0;

    for (const userDoc of usersSnapshot.docs) {
      const user = userDoc.data();
      const userEmail = userDoc.id;
      const prefs = user.emailReports || {};

      // Check if it's time to send for this user based on their timezone
      // OR if we are forcing delivery
      const shouldSend = force || shouldSendEmail(prefs, currentHour);
      console.log(`[EMAIL] User: ${userEmail}`);
      console.log(`[EMAIL]   Timezone: ${prefs.timezone || 'UTC'}, Preferred Hour: ${prefs.preferredHour || prefs.sendTime || 9}`);
      console.log(`[EMAIL]   Should send now: ${shouldSend}`);

      if (shouldSend) {
        try {
          // Get yesterday's summary (or fall back to most recent data)
          const yesterday = new Date(now);
          yesterday.setDate(yesterday.getDate() - 1);
          let dateStr = yesterday.toISOString().split('T')[0];
          const originalDateStr = dateStr; // Track what we originally wanted

          let summarySnapshot = await db.collection('daily_summaries')
            .where('userEmail', '==', userEmail)
            .where('date', '==', dateStr)
            .limit(1)
            .get();

          let summaryData;
          let summaryRef = null;

          if (summarySnapshot.empty) {
            // No summary exists - try to generate one from usage data
            console.log(`[EMAIL] No summary found for ${userEmail} on ${dateStr}, attempting to generate...`);

            let generated = await generateSummaryFromUsage(userEmail, user.uid, dateStr);

            if (!generated) {
              console.log(`[EMAIL] No usage data for ${dateStr}. Checking for most recent activity...`);

              // Fall back: Look for the most recent date with data (within last 3 days only)
              const usageDoc = await db.collection('usage').doc(user.uid).get();
              if (usageDoc.exists) {
                const dayBucket = usageDoc.data().dayBucket || {};
                const availableDates = Object.keys(dayBucket).sort().reverse();

                // Find most recent date within last 3 days (not 7, to avoid very stale data)
                const threeDaysAgo = new Date(now);
                threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
                const cutoffDate = threeDaysAgo.toISOString().split('T')[0];

                const recentDate = availableDates.find(d => d >= cutoffDate);

                if (recentDate && recentDate !== dateStr) {
                  console.log(`[EMAIL] ⚠️  Found recent data for ${recentDate}, generating catch-up email...`);
                  generated = await generateSummaryFromUsage(userEmail, user.uid, recentDate);
                  dateStr = recentDate; // Update dateStr to the date we're actually using
                }
              }

              if (!generated) {
                console.log(`[EMAIL] ⊘ Skipping ${userEmail} - no recent usage data (last 3 days)`);
                skippedCount++;
                continue; // Skip this user
              }
            }

            // Save generated summary to Firestore
            const newSummary = {
              userId: user.uid,
              userEmail: userEmail,
              date: dateStr,
              uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
              emailSent: false,
              summary: generated
            };

            summaryRef = await db.collection('daily_summaries').add(newSummary);
            summaryData = generated;

            console.log(`[EMAIL] ✓ Generated and saved summary for ${userEmail}`);

          } else {
            // Summary exists - check if already sent
            const doc = summarySnapshot.docs[0];
            if (doc.data().emailSent) {
              console.log(`[EMAIL] ⊘ Summary already sent to ${userEmail} for ${dateStr}`);
              skippedCount++;
              continue;
            }
            summaryData = doc.data().summary;
            summaryRef = doc.ref;
          }

          // Check data freshness and warn user if data is old
          const dataAge = Math.floor((new Date(originalDateStr) - new Date(dateStr)) / (1000 * 60 * 60 * 24));
          if (dataAge > 0) {
            console.log(`[EMAIL] ⚠️  Data for ${userEmail} is ${dataAge} day(s) old (${dateStr} vs ${originalDateStr})`);
            // Add a warning to the summary
            summaryData.daily_narrative = `⚠️ Note: This report uses data from ${dateStr} (${dataAge} day${dataAge > 1 ? 's' : ''} old). Recent data not available.\n\n` + summaryData.daily_narrative;
          }

          // Send email
          const result = await sendDailyReport(userEmail, summaryData);

          if (result.success) {
            // Mark as sent
            await summaryRef.update({
              emailSent: true,
              emailSentAt: admin.firestore.FieldValue.serverTimestamp()
            });
            sentCount++;
            console.log(`[EMAIL] ✓ Sent report to ${userEmail}${dataAge > 0 ? ` (data age: ${dataAge}d)` : ''}`);
          } else {
            errorCount++;
            console.error(`[EMAIL] ✗ Failed to send to ${userEmail}`);
          }
        } catch (error) {
          errorCount++;
          console.error(`[EMAIL] Error sending to ${userEmail}:`, error);
        }
      } else {
        skippedCount++;
      }
    }

    console.log(`\n[EMAIL] ========================================`);
    console.log(`[EMAIL] Batch complete:`);
    console.log(`[EMAIL]   ✓ Sent: ${sentCount}`);
    console.log(`[EMAIL]   ✗ Errors: ${errorCount}`);
    console.log(`[EMAIL]   ⊘ Skipped (timing): ${skippedCount}`);
    console.log(`[EMAIL] ========================================\n`);

  } catch (error) {
    console.error('[EMAIL] Error in sendDailyReports:', error);
  }
}

/**
 * Check if we should send email to user based on timezone
 *
 * Algorithm: Convert preferred local time to UTC, then check if current UTC time matches
 * within a 1-hour window. This ensures emails are sent once per day around the preferred time.
 *
 * The emailSent flag in sendDailyReports prevents duplicates.
 */
function shouldSendEmail(prefs, currentUTCHour) {
  const timezone = prefs.timezone || 'UTC';

  // Support both preferredHour (number) and sendTime (string) formats
  let preferredLocalHour;
  let preferredLocalMinute = 0;

  if (typeof prefs.preferredHour === 'number') {
    preferredLocalHour = prefs.preferredHour;
  } else if (prefs.sendTime) {
    const parts = prefs.sendTime.split(':');
    preferredLocalHour = parseInt(parts[0], 10);
    preferredLocalMinute = parseInt(parts[1] || '0', 10);
  } else {
    preferredLocalHour = 9; // Default to 9 AM
  }

  // Get timezone offset (simple approach - use full timezone library for production)
  const timezoneOffsets = {
    'UTC': 0,
    'America/New_York': -5,
    'America/Los_Angeles': -8,
    'America/Chicago': -6,
    'America/Denver': -7,
    'Europe/London': 0,
    'Europe/Paris': 1,
    'Europe/Berlin': 1,
    'Asia/Kolkata': 5.5,
    'Asia/Tokyo': 9,
    'Asia/Shanghai': 8,
    'Australia/Sydney': 11,
    // Add more as needed
  };

  const offset = timezoneOffsets[timezone] || 0;

  // Convert preferred local time to UTC
  // Example: 21:00 IST (UTC+5:30) -> 21 - 5.5 = 15.5 UTC
  let targetUTCHour = preferredLocalHour - offset;

  // Handle wrapping
  if (targetUTCHour < 0) targetUTCHour += 24;
  if (targetUTCHour >= 24) targetUTCHour -= 24;

  // Create a 2-hour window to account for scheduler frequency (runs every 30 min)
  // and potential delays. This ensures we catch the send time even if scheduler
  // misses the exact hour.
  const targetUTCHourLower = Math.floor(targetUTCHour);
  const targetUTCHourUpper = Math.ceil(targetUTCHour) + 1; // +1 hour buffer

  // Check if current hour is within the target window
  let shouldSend = false;

  if (targetUTCHourLower <= targetUTCHourUpper) {
    // Normal case: window doesn't wrap around midnight
    shouldSend = currentUTCHour >= targetUTCHourLower && currentUTCHour <= targetUTCHourUpper;
  } else {
    // Edge case: window wraps around midnight (e.g., 23-1)
    shouldSend = currentUTCHour >= targetUTCHourLower || currentUTCHour <= targetUTCHourUpper;
  }

  // Logging for debugging
  console.log(`[EMAIL] Timezone: ${timezone}, Preferred: ${preferredLocalHour}:${preferredLocalMinute < 10 ? '0' : ''}${preferredLocalMinute} (${prefs.sendTime || preferredLocalHour})`);
  console.log(`[EMAIL]   Offset: ${offset}, Target UTC: ${targetUTCHour.toFixed(1)} (window: ${targetUTCHourLower}-${targetUTCHourUpper})`);
  console.log(`[EMAIL]   Current UTC: ${currentUTCHour}, Should send: ${shouldSend}`);

  return shouldSend;
}
