/**
 * Email Service - SendGrid Integration
 * 
 * Handles sending daily report emails to users via SendGrid.
 */

import sgMail from '@sendgrid/mail';
import { getSecret } from './secrets.js';
import admin from 'firebase-admin';

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
 * Generate HTML email from daily summary data
 */
function generateReportHTML(summary, userName = 'there') {
  const date = new Date(summary.date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const workMin = Math.floor(summary.work_seconds / 60);
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const browsingMin = Math.floor(summary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(summary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  const score = Math.round(summary.productivity_score || 0);
  let scoreColor = '#e74c3c';
  let scoreEmoji = '📊';
  if (score >= 75) { scoreColor = '#27ae60'; scoreEmoji = '🌟'; }
  else if (score >= 50) { scoreColor = '#f39c12'; scoreEmoji = '⭐'; }

  // Parse key learnings
  let keyLearnings = [];
  try {
    keyLearnings = JSON.parse(summary.key_learnings_json || '[]');
  } catch (e) {
    console.error('[EMAIL] Failed to parse key learnings:', e);
  }

  const learningsHTML = keyLearnings.length > 0 ? `
    <div style="margin: 25px 0;">
      <h2 style="color: #2c3e50; margin-bottom: 15px;">🎓 Key Learnings</h2>
      <ul style="color: #34495e; line-height: 1.6;">
        ${keyLearnings.map(l => `<li style="margin: 8px 0;">${l}</li>`).join('')}
      </ul>
    </div>
  ` : '';

  // Generate progress bars
  const progressBars = [
    { label: 'Work', minutes: workMin, color: '#3498db' },
    { label: 'Learning', minutes: learningMin, color: '#9b59b6' },
    { label: 'Browsing', minutes: browsingMin, color: '#95a5a6' },
    { label: 'Entertainment', minutes: entertainmentMin, color: '#e67e22' }
  ].map(({ label, minutes, color }) => {
    const percentage = totalMin > 0 ? Math.round((minutes / totalMin) * 100) : 0;
    return `
      <div style="margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span style="color: #2c3e50; font-weight: 500;">${label}</span>
          <span style="color: #7f8c8d;">${minutes}m (${percentage}%)</span>
        </div>
        <div style="background: #ecf0f1; height: 24px; border-radius: 12px; overflow: hidden;">
          <div style="background: ${color}; height: 100%; width: ${percentage}%;"></div>
        </div>
      </div>
    `;
  }).join('');

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
      <h1 style="color: white; margin: 0; font-size: 28px;">📊 Daily Activity Report</h1>
      <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">${date}</p>
    </div>
    
    <!-- Productivity Score -->
    <div style="text-align: center; padding: 30px 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
      <div style="font-size: 48px; margin-bottom: 10px;">${scoreEmoji}</div>
      <div style="font-size: 42px; font-weight: bold; color: ${scoreColor}; margin-bottom: 5px;">
        ${score}/100
      </div>
      <div style="color: #6c757d; font-size: 16px;">Productivity Score</div>
    </div>
    
    <!-- Content -->
    <div style="padding: 30px;">
      
      <!-- Daily Narrative -->
      <div style="margin-bottom: 25px;">
        <h2 style="color: #2c3e50; margin-bottom: 15px;">📝 Daily Summary</h2>
        <p style="color: #34495e; line-height: 1.7; font-size: 15px; background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
          ${summary.daily_narrative || 'No summary available.'}
        </p>
      </div>
      
      <!-- Time Breakdown -->
      <div style="margin: 25px 0;">
        <h2 style="color: #2c3e50; margin-bottom: 15px;">⏱️ Time Breakdown</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #dee2e6;">
            <span style="font-size: 32px; font-weight: bold; color: #2c3e50;">${totalMin}</span>
            <span style="color: #7f8c8d; font-size: 16px; margin-left: 5px;">minutes</span>
            <div style="color: #6c757d; font-size: 14px; margin-top: 5px;">Total Active Time</div>
          </div>
          ${progressBars}
        </div>
      </div>
      
      ${learningsHTML}
      
      <!-- Stats Footer -->
      <div style="margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">
        <div style="color: #6c757d; font-size: 14px;">
          <strong style="color: #2c3e50;">${summary.context_switches || 0}</strong> context switches
        </div>
      </div>
      
    </div>
    
    <!-- Footer -->
    <div style="background: #2c3e50; padding: 20px; text-align: center;">
      <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px;">
        Generated by Telos Screen Tracker
      </p>
      <p style="color: rgba(255,255,255,0.5); margin: 5px 0 0 0; font-size: 12px;">
        AI-powered activity insights
      </p>
    </div>
    
  </div>
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

          const summarySnapshot = await db.collection('daily_summaries')
            .where('userEmail', '==', userEmail)
            .where('date', '==', dateStr)
            .where('emailSent', '==', false)
            .limit(1)
            .get();

          if (!summarySnapshot.empty) {
            const summaryDoc = summarySnapshot.docs[0];
            const summaryData = summaryDoc.data();

            // Send email
            const result = await sendDailyReport(userEmail, summaryData.summary);

            if (result.success) {
              // Mark as sent
              await summaryDoc.ref.update({
                emailSent: true,
                emailSentAt: admin.firestore.FieldValue.serverTimestamp()
              });
              sentCount++;
              console.log(`[EMAIL] ✓ Sent report to ${userEmail}`);
            } else {
              errorCount++;
              console.error(`[EMAIL] ✗ Failed to send to ${userEmail}`);
            }
          } else {
            console.log(`[EMAIL] No unsent summary for ${userEmail} on ${dateStr}`);
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
