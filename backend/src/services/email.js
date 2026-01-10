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
  const displayName = userName.includes('@') ? userName.split('@')[0] : (userName || 'there');

  const dateObj = new Date(summary.date);
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
  const fullDate = dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const workMin = Math.floor(summary.work_seconds / 60);
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const browsingMin = Math.floor(summary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(summary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  const workPct = Math.round(workMin / Math.max(totalMin, 1) * 100);
  const browsePct = Math.round(browsingMin / Math.max(totalMin, 1) * 100);

  const narrative = summary.daily_narrative || 'No summary available for this day.';
  const apps = summary.apps || [];
  const timeline = summary.timeline || [];

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

  // Generate Timeline HTML
  const timelineHtml = timeline.slice(0, 6).map(item => {
    const catColor = { 'work': '#3b82f6', 'learning': '#a855f7', 'browsing': '#6b7280', 'entertainment': '#f59e0b' }[item.category] || '#6b7280';
    const icon = getAppIcon(item.app, item.category);
    const taskText = item.task || 'Activity';
    return `
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 10px; background-color: #1a1a1a; border-left: 3px solid ${catColor}; border-radius: 0 8px 8px 0;" bgcolor="#1a1a1a">
                                <tr>
                                    <td style="padding: 12px 14px;" bgcolor="#1a1a1a">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="28" style="font-size: 16px; vertical-align: top;" bgcolor="#1a1a1a">${icon}</td>
                                                <td style="padding-left: 8px;" bgcolor="#1a1a1a">
                                                    <div style="font-weight: 600; color: #ededed; font-size: 14px;">${item.app}</div>
                                                    <div style="font-size: 12px; color: #a3a3a3; margin-top: 2px;">${taskText.substring(0, 50)}${taskText.length > 50 ? '...' : ''}</div>
                                                </td>
                                                <td width="50" style="text-align: right; vertical-align: top;" bgcolor="#1a1a1a">
                                                    <span style="font-family: monospace; font-size: 11px; color: #888888;">${item.start}</span>
                                                    <div style="font-family: monospace; font-size: 12px; color: #22c55e; margin-top: 2px;">${item.duration_mins}m</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>`;
  }).join('');

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
                    
                    <!-- Timeline Section -->
                    ${timeline.length > 0 ? `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Your Day
                            </p>
                            ${timelineHtml}
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
export async function sendDailyReports() {
  console.log('[EMAIL] Checking for reports to send...');

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

    let sentCount = 0;
    let errorCount = 0;

    for (const userDoc of usersSnapshot.docs) {
      const user = userDoc.data();
      const userEmail = userDoc.id;
      const prefs = user.emailReports || {};

      // Check if it's time to send for this user based on their timezone
      if (shouldSendEmail(prefs, currentHour)) {
        try {
          // Get yesterday's summary
          const yesterday = new Date(now);
          yesterday.setDate(yesterday.getDate() - 1);
          const dateStr = yesterday.toISOString().split('T')[0];

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

            const generated = await generateSummaryFromUsage(userEmail, user.uid, dateStr);

            if (!generated) {
              console.log(`[EMAIL] Could not generate summary for ${userEmail} - no usage data for ${dateStr}`);
              continue; // Skip this user
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
              console.log(`[EMAIL] Summary already sent to ${userEmail} for ${dateStr}`);
              continue;
            }
            summaryData = doc.data().summary;
            summaryRef = doc.ref;
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
            console.log(`[EMAIL] ✓ Sent report to ${userEmail}`);
          } else {
            errorCount++;
            console.error(`[EMAIL] ✗ Failed to send to ${userEmail}`);
          }
        } catch (error) {
          errorCount++;
          console.error(`[EMAIL] Error sending to ${userEmail}:`, error);
        }
      }
    }

    console.log(`[EMAIL] Batch complete: ${sentCount} sent, ${errorCount} errors`);

  } catch (error) {
    console.error('[EMAIL] Error in sendDailyReports:', error);
  }
}

/**
 * Check if we should send email to user based on timezone
 */
function shouldSendEmail(prefs, currentUTCHour) {
  const timezone = prefs.timezone || 'UTC';

  // Support both preferredHour (number) and sendTime (string) formats
  let sendHour;
  if (typeof prefs.preferredHour === 'number') {
    sendHour = prefs.preferredHour;
  } else if (prefs.sendTime) {
    sendHour = parseInt(prefs.sendTime.split(':')[0], 10);
  } else {
    sendHour = 9; // Default to 9 AM
  }

  // Get timezone offset (simple approach - use full timezone library for production)
  const timezoneOffsets = {
    'UTC': 0,
    'America/New_York': -5,
    'America/Los_Angeles': -8,
    'Europe/London': 0,
    'Europe/Paris': 1,
    'Asia/Kolkata': 5.5,
    'Asia/Tokyo': 9,
    'Australia/Sydney': 11,
    // Add more as needed
  };

  const offset = timezoneOffsets[timezone] || 0;

  // Convert user's preferred local hour to UTC
  // If user wants 21:00 IST (offset +5.5), that's 15:30 UTC
  const targetUTCHour = (sendHour - offset + 24) % 24;

  // Check if current UTC hour matches (accounting for half-hour offsets)
  const hourMatches = Math.floor(targetUTCHour) === currentUTCHour;

  console.log(`[EMAIL] Time check for ${timezone}: preferredHour=${sendHour}, targetUTC=${targetUTCHour.toFixed(1)}, currentUTC=${currentUTCHour}, match=${hourMatches}`);

  return hourMatches;
}
