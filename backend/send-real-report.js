/**
 * Generate and send mobile-responsive daily report using actual user data
 * Fixed version with proper mobile responsiveness and correct data
 */

import sgMail from '@sendgrid/mail';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Direct API key
const apiKey = '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';
sgMail.setApiKey(apiKey);

// Format helper
function formatDuration(minutes) {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins ? `${hours}h ${mins}m` : `${hours}h`;
  }
  return `${minutes}m`;
}

// Get app icon emoji
function getAppIcon(appName, category) {
  const app = appName.toLowerCase();
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

async function sendRealReport() {
  console.log('\n=== Generating Mobile-Responsive Daily Report ===\n');

  // Load fresh real data
  const dataPath = path.join(__dirname, '../client/real_data.json');
  const rawData = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));

  // Use TODAY's data (Jan 9, 2026)
  const reportDate = '2026-01-09';
  const dayData = rawData.days[reportDate];

  if (!dayData) {
    console.error('No data found for', reportDate);
    process.exit(1);
  }

  console.log('✓ Loaded data for:', reportDate);
  console.log('  - Total mins:', dayData.total_mins);
  console.log('  - Work mins:', dayData.work_mins);
  console.log('  - Timeline entries:', dayData.timeline?.length || 0);

  // Format the report date
  const dateObj = new Date(reportDate);
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
  const fullDate = dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  // Today's metrics
  const totalMins = dayData.total_mins;
  const workMins = dayData.work_mins;
  const learnMins = dayData.learning_mins;
  const browseMins = dayData.browsing_mins;
  const funMins = dayData.entertainment_mins;
  const workPct = Math.round(workMins / Math.max(totalMins, 1) * 100);
  const browsePct = Math.round(browseMins / Math.max(totalMins, 1) * 100);

  // Yesterday comparison
  const yesterdayData = rawData.days['2026-01-08'];
  let totalDelta = 0, workDelta = 0;
  if (yesterdayData) {
    totalDelta = Math.round((totalMins - yesterdayData.total_mins) / Math.max(yesterdayData.total_mins, 1) * 100);
    workDelta = Math.round((workMins - yesterdayData.work_mins) / Math.max(yesterdayData.work_mins, 1) * 100);
  }

  // Build timeline HTML (mobile-friendly single column)
  let timelineHtml = '';
  const timeline = dayData.timeline || [];

  // Sort timeline by time
  const sortedTimeline = [...timeline].sort((a, b) => a.start.localeCompare(b.start));

  for (const item of sortedTimeline.slice(0, 8)) {
    const catColor = {
      'work': '#3b82f6',
      'learning': '#a855f7',
      'browsing': '#6b7280',
      'entertainment': '#f59e0b'
    }[item.category] || '#6b7280';

    const icon = getAppIcon(item.app, item.category);
    const taskText = item.task || 'Activity';

    timelineHtml += `
        <div style="margin-bottom: 12px; padding: 14px; background: #1a1a1a; border-left: 3px solid ${catColor}; border-radius: 0 8px 8px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 18px; margin-right: 10px;">${icon}</span>
                <span style="font-weight: 600; color: #ededed; font-size: 14px;">${item.app}</span>
                <span style="margin-left: auto; font-family: monospace; font-size: 12px; color: #888;">${item.start}</span>
            </div>
            <div style="font-size: 13px; color: #a3a3a3; line-height: 1.4; padding-left: 28px;">
                ${taskText.substring(0, 60)}${taskText.length > 60 ? '...' : ''}
            </div>
            <div style="padding-left: 28px; margin-top: 4px;">
                <span style="font-family: monospace; font-size: 12px; color: #22c55e;">${item.duration_mins}m</span>
            </div>
        </div>
        `;
  }

  // Build top apps list
  let appsHtml = '';
  const apps = dayData.apps || [];
  for (const app of apps.slice(0, 5)) {
    const icon = getAppIcon(app.name, app.category);
    const catColor = {
      'work': '#3b82f6',
      'learning': '#a855f7',
      'browsing': '#6b7280',
      'entertainment': '#f59e0b'
    }[app.category] || '#6b7280';

    appsHtml += `
        <div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #222;">
            <span style="font-size: 16px; margin-right: 10px;">${icon}</span>
            <span style="color: #ededed; font-size: 14px; flex: 1;">${app.name}</span>
            <span style="font-family: monospace; font-size: 13px; color: ${catColor}; font-weight: 600;">${app.minutes}m</span>
        </div>
        `;
  }

  // Narrative (use summary if available, otherwise generate simple one)
  const summaryData = rawData.summaries?.[reportDate];
  const narrative = summaryData?.narrative ||
    `You tracked ${formatDuration(totalMins)} today with ${workPct}% focused on work. Top activities included ${apps.slice(0, 3).map(a => a.name.replace('Brave - ', '')).join(', ')}.`;

  // Email-compatible HTML with TABLE-based layout and explicit bgcolor for dark theme
  // Note: Most email clients strip CSS background-color but respect bgcolor attribute
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
    <title>Telos Daily Report</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {font-family: Arial, sans-serif !important;}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;" bgcolor="#0a0a0a">
    
    <!-- Outer wrapper table for background -->
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0a0a0a;" bgcolor="#0a0a0a">
        <tr>
            <td align="center" style="padding: 20px 10px;" bgcolor="#0a0a0a">
                
                <!-- Main content table -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; background-color: #0a0a0a;" bgcolor="#0a0a0a">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                ${dayName}, ${fullDate}
                            </p>
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #ededed;">
                                Here's your <span style="color: #22c55e;">${dayName}</span>, Anurag
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
                                            ${formatDuration(totalMins)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Total Tracked</div>
                                        ${totalDelta !== 0 ? `<div style="font-size: 11px; color: ${totalDelta >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 4px;">${totalDelta >= 0 ? '↑' : '↓'} ${Math.abs(totalDelta)}%</div>` : ''}
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #3b82f6;">
                                            ${formatDuration(workMins)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Work</div>
                                        ${workDelta !== 0 ? `<div style="font-size: 11px; color: ${workDelta >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 4px;">${workDelta >= 0 ? '↑' : '↓'} ${Math.abs(workDelta)}%</div>` : ''}
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
                                        ${browsePct > 40 ? '<div style="font-size: 11px; color: #f59e0b; margin-top: 4px;">⚠️ high</div>' : ''}
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="padding: 16px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 24px; font-weight: 700; color: #a855f7;">
                                            ${formatDuration(learnMins)}
                                        </div>
                                        <div style="font-size: 11px; color: #888888; margin-top: 4px;">Learning</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Top Apps Section -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Top Apps
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                ${apps.slice(0, 5).map((app, i) => {
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
  }).join('')}
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Timeline Section -->
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 12px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Your Day
                            </p>
                            ${sortedTimeline.slice(0, 6).map(item => {
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
  }).join('')}
                        </td>
                    </tr>
                    
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

  // Save HTML preview
  const previewPath = path.join(__dirname, 'generated_report_preview.html');
  fs.writeFileSync(previewPath, html);
  console.log('✓ Saved preview to:', previewPath);

  // Send email
  console.log('\n📧 Sending mobile-responsive email to anurag@userology.co...\n');

  const msg = {
    to: 'anurag@userology.co',
    from: {
      email: 'anuragkurle27@gmail.com',
      name: 'Telos'
    },
    subject: `📊 ${dayName}, ${fullDate} — ${formatDuration(totalMins)} tracked`,
    text: `Telos Daily Report\n${dayName}, ${fullDate}\n\nTotal: ${formatDuration(totalMins)}\nWork: ${formatDuration(workMins)} (${workPct}%)\nLearning: ${formatDuration(learnMins)}\nBrowsing: ${formatDuration(browseMins)}\n\nTop Apps:\n${apps.slice(0, 5).map(a => `- ${a.name}: ${a.minutes}m`).join('\n')}\n\n---\nGenerated by Telos`,
    html: html
  };

  try {
    await sgMail.send(msg);
    console.log('✅ SUCCESS! Email sent to anurag@userology.co');
    console.log('\n📬 Check your inbox for the mobile-friendly report!\n');
  } catch (error) {
    console.error('❌ FAILED:', error.message);
    if (error.response) {
      console.error('Details:', error.response.body);
    }
  }
}

sendRealReport().catch(console.error);
