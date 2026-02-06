/**
 * Email Service - SendGrid Integration
 * 
 * Handles sending daily report emails to users via SendGrid.
 */

import sgMail from '@sendgrid/mail';
import { getSecret } from './secrets.js';
import admin from 'firebase-admin';
import { DateTime } from 'luxon';
import { generateSummaryFromUsage } from './summaryGenerator.js';
import { encrypt, decrypt, encryptFields, decryptFields } from './encryption.js';
import { generateViewToken } from '../routes/webReport.js';

// Sensitive fields in summary objects
const SUMMARY_ENCRYPT_FIELDS = ['daily_narrative', 'key_learnings_json', 'apps', 'timeline', 'deep_work_sessions'];
const SUMMARY_JSON_FIELDS = ['apps', 'timeline', 'deep_work_sessions'];

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
 * Generate a smart, context-aware email subject line
 */
function generateSubjectLine(summary) {
  const dateObj = new Date(summary.date);
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });

  const workMin = Math.floor(summary.work_seconds / 60);
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const browsingMin = Math.floor(summary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(summary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  const deepWork = summary.deep_work_sessions || [];
  const weeklyComp = summary.weekly_comparison || {};
  const focusQuality = summary.focus_quality || {};

  // Pick the most interesting angle for the subject
  // Priority 1: Notable deep work
  if (deepWork.length >= 3) {
    return `${deepWork.length} deep work sessions -- Strong focus on ${dayName}`;
  }

  // Priority 2: Best day compared to weekly average
  if (weeklyComp.has_history && weeklyComp.work_diff > 30) {
    return `Your most productive ${dayName} this week`;
  }

  // Priority 3: High focus quality
  if (focusQuality.focus_quality_score >= 80) {
    return `${formatDuration(totalMin)} tracked -- Excellent focus on ${dayName}`;
  }

  // Priority 4: Significant productive time
  if (workMin >= 120) {
    return `${formatDuration(workMin)} of work -- Your ${dayName} Recap`;
  }

  // Priority 5: Learning-heavy day
  if (learningMin > workMin && learningMin >= 30) {
    return `${formatDuration(learningMin)} learning -- Your ${dayName} Recap`;
  }

  // Default: Total time + day
  return `${formatDuration(totalMin)} tracked -- Your ${dayName} Recap`;
}

/**
 * Generate insights and recommendations section
 * Now more actionable with comparisons, tips, peak hours, and streaks
 */
function generateInsightsHTML(summary, workMin, totalMin, weeklyComp, focusQuality, deepWork) {
  const insights = [];

  // Peak productivity time insight (use hourly data if available)
  const peakHour = summary.peak_productivity_hour;
  if (peakHour && workMin > 30) {
    const peakFormatted = peakHour > 12 ? `${peakHour - 12} PM` : peakHour === 12 ? '12 PM' : `${peakHour} AM`;
    const endHour = peakHour + 2;
    const endFormatted = endHour > 12 ? `${endHour - 12} PM` : endHour === 12 ? '12 PM' : `${endHour} AM`;
    insights.push(`🕐 Your peak productivity window was <strong>${peakFormatted} - ${endFormatted}</strong>. Schedule your most demanding work here.`);
  }

  // Deep work insight - more actionable
  if (deepWork.length > 0) {
    const totalDeepWork = deepWork.reduce((sum, s) => sum + s.duration_mins, 0);
    if (deepWork.length >= 3) {
      insights.push(`⚡ <strong>${deepWork.length} deep work sessions</strong> totaling ${formatDuration(totalDeepWork)} -- that's strong sustained focus. Keep protecting this time.`);
    } else {
      insights.push(`⚡ ${deepWork.length} deep work session${deepWork.length > 1 ? 's' : ''} (${formatDuration(totalDeepWork)}). Aim for 3+ sessions by blocking distractions during focus windows.`);
    }
  } else if (workMin > 10) {
    insights.push(`💡 No deep work detected today. Try the <strong>25-5 technique</strong>: 25 min focused work, 5 min break. Even one session makes a difference.`);
  }

  // Weekly comparison insight - with percentage change
  if (weeklyComp.has_history) {
    const pctChange = weeklyComp.avg_work > 0
      ? Math.round(((weeklyComp.current_work - weeklyComp.avg_work) / weeklyComp.avg_work) * 100)
      : 0;
    if (weeklyComp.work_diff > 15) {
      insights.push(`📈 Work time <strong>up ${Math.abs(pctChange)}%</strong> vs your ${weeklyComp.days_compared}-day average (${formatDuration(weeklyComp.avg_work)} avg). You're building momentum.`);
    } else if (weeklyComp.work_diff < -15) {
      insights.push(`📉 Work time <strong>down ${Math.abs(pctChange)}%</strong> vs your ${weeklyComp.days_compared}-day average (${formatDuration(weeklyComp.avg_work)} avg). Lighter day -- sometimes that's needed.`);
    }
  }

  // Focus quality insight - with specific advice
  if (focusQuality.focus_quality_score) {
    if (focusQuality.focus_quality_score >= 80) {
      insights.push(`✨ Excellent focus quality (<strong>${focusQuality.focus_quality_score}/100</strong>). Avg session: ${focusQuality.avg_session_length}m. This is top-tier concentration.`);
    } else if (focusQuality.focus_quality_score >= 50) {
      insights.push(`🔄 Moderate focus (${focusQuality.focus_quality_score}/100). Your avg session was ${focusQuality.avg_session_length}m. Try closing extra tabs and notifications to push past 70.`);
    } else if (focusQuality.fragmentation_ratio > 50) {
      insights.push(`🔀 High fragmentation: <strong>${focusQuality.fragmentation_ratio}% of sessions under 3 min</strong>. Close unnecessary apps and try single-tasking for 20 min blocks.`);
    }
  }

  // Context switching - with benchmark
  if (summary.context_switches > 80) {
    insights.push(`⚠️ <strong>${summary.context_switches} context switches</strong> -- that's very high. Each switch costs ~23 min of refocus time. Try batching similar tasks together.`);
  } else if (summary.context_switches > 50) {
    insights.push(`🔃 ${summary.context_switches} context switches today. Consider grouping communication (Slack, email) into 2-3 check-in windows rather than constant monitoring.`);
  }

  // Productive ratio
  const learningMin = Math.floor(summary.learning_seconds / 60);
  const productiveMin = workMin + learningMin;
  const productiveRatio = Math.round(productiveMin / Math.max(totalMin, 1) * 100);
  if (productiveRatio >= 70) {
    insights.push(`🎯 <strong>${productiveRatio}% productive time</strong> -- above the 60% benchmark. Well-balanced day.`);
  } else if (productiveRatio < 40 && totalMin > 60) {
    insights.push(`🎯 ${productiveRatio}% productive time today. Try starting tomorrow with your hardest task first -- the "eat the frog" approach works.`);
  }

  if (insights.length === 0) {
    insights.push('Keep tracking your activity to build personalized insights over time.');
  }

  return insights.map(insight => `
                                        <div style="padding: 12px 16px; margin-bottom: 8px; background-color: #1a1a1a; border-left: 3px solid #22c55e; border-radius: 0 6px 6px 0; color: #d4d4d4; font-size: 13px; line-height: 1.6;">
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
 * Dark-themed Telos template with charts, score bar, app bars, CTA, and insights
 */
function generateReportHTML(summary, userName = 'there', reportUrl = null) {
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

  const deepWork = summary.deep_work_sessions || [];
  const focusQuality = summary.focus_quality || {};
  const weeklyComp = summary.weekly_comparison || {};
  const peakHour = summary.peak_productivity_hour || 0;

  // Score
  const prodScore = Math.round(summary.productivity_score || 0);
  const scoreColor = prodScore >= 70 ? '#22c55e' : prodScore >= 45 ? '#f59e0b' : '#ef4444';
  const scoreBg = prodScore >= 70 ? '#0f2b1a' : prodScore >= 45 ? '#2b2410' : '#2b1010';
  const scoreVerdict = prodScore >= 80 ? 'Excellent day'
    : prodScore >= 65 ? 'Solid day'
    : prodScore >= 45 ? 'Mixed day'
    : prodScore >= 25 ? 'Light day'
    : 'Getting started';

  // Quick summary
  const topAppNames = apps.slice(0, 2).map(a => a.name).join(' and ');
  const peakFormatted = peakHour > 12 ? `${peakHour - 12} PM` : peakHour === 12 ? '12 PM' : peakHour === 0 ? '12 AM' : `${peakHour} AM`;
  let quickSummary = '';
  if (totalMin > 0) {
    quickSummary = `You tracked ${formatDuration(totalMin)}`;
    if (workMin > 0) quickSummary += `, worked ${formatDuration(workMin)}`;
    if (topAppNames) quickSummary += ` mostly in ${topAppNames}`;
    if (peakHour > 0 && workMin > 30) quickSummary += `. Peak focus: ${peakFormatted}`;
    quickSummary += '.';
  }

  // Distraction
  const distractionMin = entertainmentMin + (focusQuality.distraction_minutes || 0);
  const distractionDisplay = distractionMin > 0 ? formatDuration(distractionMin) : '0m';
  const distractionColor = distractionMin > 60 ? '#ef4444' : distractionMin > 30 ? '#f59e0b' : '#22c55e';

  // ===== STACKED TIME DISTRIBUTION BAR =====
  // Ensure minimum 1% width for non-zero categories so they're visible
  const safeWorkPct = workMin > 0 ? Math.max(1, workPct) : 0;
  const safeLearningPct = learningMin > 0 ? Math.max(1, learningPct) : 0;
  const safeBrowsePct = browsingMin > 0 ? Math.max(1, browsePct) : 0;
  const safeEntPct = entertainmentMin > 0 ? Math.max(1, entertainmentPct) : 0;
  // Normalize to 100
  const barTotal = safeWorkPct + safeLearningPct + safeBrowsePct + safeEntPct;
  const normWork = barTotal > 0 ? Math.round(safeWorkPct / barTotal * 100) : 25;
  const normLearn = barTotal > 0 ? Math.round(safeLearningPct / barTotal * 100) : 25;
  const normBrowse = barTotal > 0 ? Math.round(safeBrowsePct / barTotal * 100) : 25;
  const normEnt = 100 - normWork - normLearn - normBrowse; // remainder to avoid rounding errors

  // ===== QUICKCHART IMAGE URLS =====
  // QuickChart uses Chart.js v2 by default with chartjs-plugin-datalabels built-in.
  // We use v2 syntax for full compatibility. Dark backgrounds, light text throughout.

  // Filter out zero-value categories for cleaner donut
  const donutCategories = [
    { label: 'Work', value: workMin, color: '#3b82f6' },
    { label: 'Learning', value: learningMin, color: '#a855f7' },
    { label: 'Browsing', value: browsingMin, color: '#6b7280' },
    { label: 'Entertainment', value: entertainmentMin, color: '#f59e0b' }
  ].filter(c => c.value > 0);

  const donutConfig = {
    type: 'doughnut',
    data: {
      labels: donutCategories.map(c => `${c.label} ${formatDuration(c.value)}`),
      datasets: [{
        data: donutCategories.map(c => c.value),
        backgroundColor: donutCategories.map(c => c.color),
        borderColor: '#111111',
        borderWidth: 3
      }]
    },
    options: {
      legend: {
        position: 'bottom',
        labels: { fontColor: '#d4d4d4', fontSize: 11, padding: 12, usePointStyle: true, pointStyle: 'circle' }
      },
      cutoutPercentage: 60,
      layout: { padding: { top: 6, bottom: 2, left: 6, right: 6 } },
      plugins: {
        datalabels: {
          color: '#ffffff',
          font: { size: 11, weight: 'bold' },
          formatter: '__FN_DONUT__'
        }
      }
    }
  };
  // Use QuickChart's string-function support for the datalabels formatter
  const donutConfigStr = JSON.stringify(donutConfig)
    .replace('"formatter":"__FN_DONUT__"', 'formatter:(value,ctx)=>{let t=ctx.dataset.data.reduce((a,b)=>a+b,0);let p=Math.round(value/t*100);return p>=8?p+"%":""}');
  const donutChartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(donutConfigStr)}&w=320&h=280&bkg=%23111111&devicePixelRatio=2&f=png`;

  // Horizontal bar chart: top apps (v2 uses 'horizontalBar' type)
  const appChartApps = apps.slice(0, 6);
  const catColors = { work: '#3b82f6', learning: '#a855f7', browsing: '#6b7280', entertainment: '#f59e0b' };
  const appsConfig = {
    type: 'horizontalBar',
    data: {
      labels: appChartApps.map(a => a.name.length > 22 ? a.name.slice(0, 20) + '...' : a.name),
      datasets: [{
        data: appChartApps.map(a => a.minutes),
        backgroundColor: appChartApps.map(a => catColors[a.category] || '#6b7280'),
        borderWidth: 0,
        barPercentage: 0.65,
        categoryPercentage: 0.8
      }]
    },
    options: {
      legend: { display: false },
      scales: {
        xAxes: [{
          gridLines: { color: '#1f1f1f', zeroLineColor: '#1f1f1f', drawBorder: false },
          ticks: { fontColor: '#525252', fontSize: 9, beginAtZero: true, maxTicksLimit: 5 }
        }],
        yAxes: [{
          gridLines: { display: false, drawBorder: false },
          ticks: { fontColor: '#d4d4d4', fontSize: 10, padding: 4 }
        }]
      },
      layout: { padding: { top: 4, bottom: 4, left: 4, right: 30 } },
      plugins: {
        datalabels: {
          anchor: 'end',
          align: 'end',
          color: '#a3a3a3',
          font: { size: 10 },
          formatter: '__FN_APPS__'
        }
      }
    }
  };
  const appsConfigStr = JSON.stringify(appsConfig)
    .replace('"__FN_APPS__"', '(v)=>v+"m"');
  const appsChartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(appsConfigStr)}&w=380&h=220&bkg=%23111111&devicePixelRatio=2&f=png`;

  // ===== TOP APPS with proportional bars =====
  const maxAppMin = apps.length > 0 ? apps[0].minutes : 1;
  const topAppsHtml = apps.slice(0, 5).map((app, i) => {
    const icon = getAppIcon(app.name, app.category);
    const catColor = { 'work': '#3b82f6', 'learning': '#a855f7', 'browsing': '#6b7280', 'entertainment': '#f59e0b' }[app.category] || '#6b7280';
    const barWidth = Math.max(4, Math.round(app.minutes / maxAppMin * 100));
    const borderBottom = i < Math.min(apps.length, 5) - 1 ? 'border-bottom: 1px solid #1a1a1a;' : '';
    return `
                                <tr>
                                    <td style="padding: 10px 16px; ${borderBottom}" bgcolor="#111111">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="28" style="font-size: 15px; vertical-align: middle;" bgcolor="#111111">${icon}</td>
                                                <td style="padding-left: 8px; vertical-align: middle;" bgcolor="#111111">
                                                    <div style="color: #ededed; font-size: 13px; font-weight: 500; margin-bottom: 5px;">${app.name}</div>
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 0;">
                                                        <tr>
                                                            <td width="${barWidth}%" bgcolor="${catColor}" style="height: 4px; border-radius: 2px; line-height: 4px; font-size: 4px;">&nbsp;</td>
                                                            <td bgcolor="#111111" style="height: 4px; line-height: 4px; font-size: 4px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td width="48" style="text-align: right; font-family: monospace; font-size: 13px; font-weight: 600; color: ${catColor}; vertical-align: middle;" bgcolor="#111111">${app.minutes}m</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>`;
  }).join('');

  // ===== TIMELINE =====
  const timelineHtml = timeline
    .filter(item => item.duration_mins >= 1)
    .slice(0, 6)
    .map(item => {
      const catColor = { 'work': '#3b82f6', 'learning': '#a855f7', 'browsing': '#6b7280', 'entertainment': '#f59e0b' }[item.category] || '#6b7280';
      const icon = getAppIcon(item.app, item.category);
      const taskText = item.task || 'Activity';
      const durationDisplay = formatDuration(item.duration_mins);
      const startTime = item.start || '';

      return `
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 6px; background-color: #111111; border-left: 3px solid ${catColor}; border-radius: 0 8px 8px 0;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 10px 14px;" bgcolor="#111111">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="28" style="font-size: 16px; vertical-align: top;" bgcolor="#111111">${icon}</td>
                                                <td style="padding-left: 8px;" bgcolor="#111111">
                                                    <div style="font-weight: 600; color: #ededed; font-size: 13px;">${item.app}${startTime ? `<span style="font-weight: 400; color: #525252; font-size: 11px; margin-left: 6px;">${startTime}</span>` : ''}</div>
                                                    <div style="font-size: 12px; color: #737373; margin-top: 2px; line-height: 1.4;">${taskText.substring(0, 70)}${taskText.length > 70 ? '...' : ''}</div>
                                                </td>
                                                <td width="50" style="text-align: right; vertical-align: top;" bgcolor="#111111">
                                                    <div style="font-family: monospace; font-size: 13px; font-weight: 600; color: ${catColor};">${durationDisplay}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>`;
    }).join('');

  // ===== WEEKLY BAR COMPARISON =====
  let weeklyBarsHtml = '';
  if (weeklyComp && weeklyComp.has_history) {
    const maxWork = Math.max(weeklyComp.current_work, weeklyComp.avg_work, 1);
    const maxTotal = Math.max(weeklyComp.current_total, weeklyComp.avg_total, 1);
    const todayWorkW = Math.max(5, Math.round(weeklyComp.current_work / maxWork * 100));
    const avgWorkW = Math.max(5, Math.round(weeklyComp.avg_work / maxWork * 100));
    const todayTotalW = Math.max(5, Math.round(weeklyComp.current_total / maxTotal * 100));
    const avgTotalW = Math.max(5, Math.round(weeklyComp.avg_total / maxTotal * 100));

    weeklyBarsHtml = `
                    <tr>
                        <td style="padding: 0 16px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 14px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Weekly Trends
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 16px 18px; border-bottom: 1px solid #1a1a1a;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; text-transform: uppercase; margin-bottom: 10px;">Work Time</div>
                                        <!-- Today bar -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 6px;">
                                            <tr>
                                                <td width="46" style="font-size: 11px; color: #a3a3a3; vertical-align: middle;" bgcolor="#111111">Today</td>
                                                <td style="padding: 0 8px; vertical-align: middle;" bgcolor="#111111">
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                        <tr>
                                                            <td width="${todayWorkW}%" bgcolor="#3b82f6" style="height: 8px; border-radius: 4px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                            <td bgcolor="#111111" style="height: 8px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td width="42" style="font-family: monospace; font-size: 12px; font-weight: 600; color: #3b82f6; text-align: right; vertical-align: middle;" bgcolor="#111111">${formatDuration(weeklyComp.current_work)}</td>
                                            </tr>
                                        </table>
                                        <!-- Average bar -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="46" style="font-size: 11px; color: #525252; vertical-align: middle;" bgcolor="#111111">Avg</td>
                                                <td style="padding: 0 8px; vertical-align: middle;" bgcolor="#111111">
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                        <tr>
                                                            <td width="${avgWorkW}%" bgcolor="#1e3a5f" style="height: 8px; border-radius: 4px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                            <td bgcolor="#111111" style="height: 8px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td width="42" style="font-family: monospace; font-size: 12px; color: #525252; text-align: right; vertical-align: middle;" bgcolor="#111111">${formatDuration(weeklyComp.avg_work)}</td>
                                            </tr>
                                        </table>
                                        <div style="font-size: 11px; color: ${weeklyComp.work_diff >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 8px;">
                                            ${weeklyComp.work_diff >= 0 ? '&#9650;' : '&#9660;'} ${Math.abs(weeklyComp.work_diff)}m ${weeklyComp.work_diff >= 0 ? 'more' : 'less'} than ${weeklyComp.days_compared}-day avg
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 16px 18px;" bgcolor="#111111">
                                        <div style="font-size: 11px; color: #888888; text-transform: uppercase; margin-bottom: 10px;">Total Time</div>
                                        <!-- Today bar -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 6px;">
                                            <tr>
                                                <td width="46" style="font-size: 11px; color: #a3a3a3; vertical-align: middle;" bgcolor="#111111">Today</td>
                                                <td style="padding: 0 8px; vertical-align: middle;" bgcolor="#111111">
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                        <tr>
                                                            <td width="${todayTotalW}%" bgcolor="#22c55e" style="height: 8px; border-radius: 4px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                            <td bgcolor="#111111" style="height: 8px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td width="42" style="font-family: monospace; font-size: 12px; font-weight: 600; color: #22c55e; text-align: right; vertical-align: middle;" bgcolor="#111111">${formatDuration(weeklyComp.current_total)}</td>
                                            </tr>
                                        </table>
                                        <!-- Average bar -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="46" style="font-size: 11px; color: #525252; vertical-align: middle;" bgcolor="#111111">Avg</td>
                                                <td style="padding: 0 8px; vertical-align: middle;" bgcolor="#111111">
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                        <tr>
                                                            <td width="${avgTotalW}%" bgcolor="#0f3d1f" style="height: 8px; border-radius: 4px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                            <td bgcolor="#111111" style="height: 8px; line-height: 8px; font-size: 8px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td width="42" style="font-family: monospace; font-size: 12px; color: #525252; text-align: right; vertical-align: middle;" bgcolor="#111111">${formatDuration(weeklyComp.avg_total)}</td>
                                            </tr>
                                        </table>
                                        <div style="font-size: 11px; color: ${weeklyComp.total_diff >= 0 ? '#22c55e' : '#ef4444'}; margin-top: 8px;">
                                            ${weeklyComp.total_diff >= 0 ? '&#9650;' : '&#9660;'} ${Math.abs(weeklyComp.total_diff)}m ${weeklyComp.total_diff >= 0 ? 'more' : 'less'} than ${weeklyComp.days_compared}-day avg
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>`;
  }

  // Insights
  const insightsHtml = generateInsightsHTML(summary, workMin, totalMin, weeklyComp, focusQuality, deepWork);

  // ===== FULL TEMPLATE =====
  return `
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office" style="background:#0a0a0a;">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark only">
    <meta name="supported-color-schemes" content="dark only">
    <!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
    <title>Telos Daily Report</title>
</head>
<body style="margin:0;padding:0;word-spacing:normal;background:#0a0a0a;-webkit-text-size-adjust:none;" bgcolor="#0a0a0a">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="#0a0a0a" style="background:#0a0a0a;min-width:100%;width:100%;table-layout:fixed;">
        <tr>
            <td align="center" valign="top" bgcolor="#0a0a0a" style="background:#0a0a0a;padding:24px 10px;">
                
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px;width:100%;background:#0a0a0a;" bgcolor="#0a0a0a">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 0 20px 14px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 6px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.12em;">
                                ${dayName}, ${fullDate}
                            </p>
                            <h1 style="margin: 0; font-size: 22px; font-weight: 600; color: #ededed; line-height: 1.3;">
                                Here's your <span style="color: #22c55e;">${dayName}</span>, ${displayName}
                            </h1>
                        </td>
                    </tr>

                    <!-- Quick Summary -->
                    ${quickSummary ? `
                    <tr>
                        <td style="padding: 0 20px 18px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-size: 14px; color: #a3a3a3; line-height: 1.5;">
                                ${quickSummary}
                            </p>
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Day Score Hero with score bar -->
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: ${scoreBg}; border-radius: 12px; border: 1px solid #1a1a1a;" bgcolor="${scoreBg}">
                                <tr>
                                    <td style="padding: 22px 20px 18px;" bgcolor="${scoreBg}">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td width="90" style="text-align: center; vertical-align: top;" bgcolor="${scoreBg}">
                                                    <div style="font-family: monospace; font-size: 52px; font-weight: 800; color: ${scoreColor}; line-height: 1;">
                                                        ${prodScore}
                                                    </div>
                                                    <div style="font-size: 10px; color: #525252; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 6px;">
                                                        / 100
                                                    </div>
                                                    <!-- Score bar -->
                                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="70" align="center" style="margin-top: 10px;">
                                                        <tr>
                                                            <td width="${prodScore}%" bgcolor="${scoreColor}" style="height: 4px; border-radius: 2px; line-height: 4px; font-size: 4px;">&nbsp;</td>
                                                            <td bgcolor="#1a1a1a" style="height: 4px; border-radius: 0 2px 2px 0; line-height: 4px; font-size: 4px;">&nbsp;</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                                <td style="vertical-align: top; padding-left: 20px;" bgcolor="${scoreBg}">
                                                    <div style="font-size: 15px; font-weight: 600; color: ${scoreColor}; margin-bottom: 8px;">
                                                        ${scoreVerdict}
                                                    </div>
                                                    <div style="font-size: 13px; color: #a3a3a3; line-height: 1.55;">
                                                        ${narrative.substring(0, 180)}${narrative.length > 180 ? '...' : ''}
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Time Distribution Chart -->
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 16px 18px;" bgcolor="#111111">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom: 12px;">
                                            <tr>
                                                <td style="font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;" bgcolor="#111111">Time Breakdown</td>
                                                <td style="text-align: right; font-family: monospace; font-size: 13px; font-weight: 600; color: #ededed;" bgcolor="#111111">${formatDuration(totalMin)}</td>
                                            </tr>
                                        </table>
                                        <!-- Stacked bar -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-radius: 6px; overflow: hidden;">
                                            <tr>
                                                ${workMin > 0 ? `<td width="${normWork}%" bgcolor="#3b82f6" style="height: 14px; line-height: 14px; font-size: 14px;">&nbsp;</td>` : ''}
                                                ${learningMin > 0 ? `<td width="${normLearn}%" bgcolor="#a855f7" style="height: 14px; line-height: 14px; font-size: 14px;">&nbsp;</td>` : ''}
                                                ${browsingMin > 0 ? `<td width="${normBrowse}%" bgcolor="#6b7280" style="height: 14px; line-height: 14px; font-size: 14px;">&nbsp;</td>` : ''}
                                                ${entertainmentMin > 0 ? `<td width="${normEnt}%" bgcolor="#f59e0b" style="height: 14px; line-height: 14px; font-size: 14px;">&nbsp;</td>` : ''}
                                            </tr>
                                        </table>
                                        <!-- Legend -->
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top: 14px;">
                                            <tr>
                                                <td width="50%" style="font-size: 12px; color: #a3a3a3; padding-bottom: 8px;" bgcolor="#111111">
                                                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #3b82f6; border-radius: 2px; margin-right: 6px; vertical-align: middle;">&nbsp;</span>
                                                    Work <span style="color: #ededed; font-weight: 600;">${formatDuration(workMin)}</span> <span style="color: #525252;">${workPct}%</span>
                                                </td>
                                                <td width="50%" style="font-size: 12px; color: #a3a3a3; padding-bottom: 8px;" bgcolor="#111111">
                                                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #a855f7; border-radius: 2px; margin-right: 6px; vertical-align: middle;">&nbsp;</span>
                                                    Learning <span style="color: #ededed; font-weight: 600;">${formatDuration(learningMin)}</span> <span style="color: #525252;">${learningPct}%</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td width="50%" style="font-size: 12px; color: #a3a3a3;" bgcolor="#111111">
                                                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #6b7280; border-radius: 2px; margin-right: 6px; vertical-align: middle;">&nbsp;</span>
                                                    Browsing <span style="color: #ededed; font-weight: 600;">${formatDuration(browsingMin)}</span> <span style="color: #525252;">${browsePct}%</span>
                                                </td>
                                                <td width="50%" style="font-size: 12px; color: #a3a3a3;" bgcolor="#111111">
                                                    <span style="display: inline-block; width: 8px; height: 8px; background-color: #f59e0b; border-radius: 2px; margin-right: 6px; vertical-align: middle;">&nbsp;</span>
                                                    Distraction <span style="color: ${distractionColor}; font-weight: 600;">${distractionDisplay}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Interactive Charts (rendered via QuickChart.io) -->
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td width="46%" valign="top" bgcolor="#0a0a0a">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                            <tr>
                                                <td style="padding: 14px 12px 4px; font-family: monospace; font-size: 10px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;" bgcolor="#111111">Time Split</td>
                                            </tr>
                                            <tr>
                                                <td style="text-align: center; padding: 0 4px 10px;" bgcolor="#111111">
                                                    <img src="${donutChartUrl}" alt="Time distribution" width="260" style="max-width:100%;height:auto;border-radius:6px;" />
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <td width="8%" bgcolor="#0a0a0a">&nbsp;</td>
                                    <td width="46%" valign="top" bgcolor="#0a0a0a">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                            <tr>
                                                <td style="padding: 14px 12px 4px; font-family: monospace; font-size: 10px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;" bgcolor="#111111">Top Apps</td>
                                            </tr>
                                            <tr>
                                                <td style="text-align: center; padding: 0 4px 10px;" bgcolor="#111111">
                                                    <img src="${appsChartUrl}" alt="Top apps" width="320" style="max-width:100%;height:auto;border-radius:6px;" />
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Top Apps Section with bars -->
                    ${apps.length > 0 ? `
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 10px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                App Details
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
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 10px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Activity Timeline
                            </p>
                            ${timelineHtml}
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Insights Section -->
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 10px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Insights
                            </p>
                            ${insightsHtml}
                        </td>
                    </tr>

                    <!-- Focus Metrics -->
                    ${focusQuality && focusQuality.avg_session_length ? `
                    <tr>
                        <td style="padding: 0 20px 20px;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 10px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">
                                Focus Metrics
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td width="31%" style="padding: 14px 10px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 20px; font-weight: 700; color: #ededed;">${focusQuality.avg_session_length}m</div>
                                        <div style="font-size: 10px; color: #525252; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em;">Avg Session</div>
                                    </td>
                                    <td width="3.5%"></td>
                                    <td width="31%" style="padding: 14px 10px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 20px; font-weight: 700; color: ${summary.context_switches > 50 ? '#f59e0b' : '#22c55e'};">${summary.context_switches}</div>
                                        <div style="font-size: 10px; color: #525252; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em;">Switches</div>
                                    </td>
                                    <td width="3.5%"></td>
                                    <td width="31%" style="padding: 14px 10px; background-color: #111111; border-radius: 10px; text-align: center;" bgcolor="#111111">
                                        <div style="font-family: monospace; font-size: 20px; font-weight: 700; color: ${focusQuality.focus_quality_score >= 70 ? '#22c55e' : focusQuality.focus_quality_score >= 40 ? '#f59e0b' : '#ef4444'};">${focusQuality.focus_quality_score}</div>
                                        <div style="font-size: 10px; color: #525252; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em;">Focus Score</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    ` : ''}

                    <!-- Weekly Trends with bar comparison -->
                    ${weeklyBarsHtml}

                    <!-- CTA Button - links to local dashboard -->
                    <tr>
                        <td style="padding: 8px 20px 28px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 24px 20px; text-align: center;" bgcolor="#111111">
                                        <p style="margin: 0 0 14px 0; font-size: 14px; color: #a3a3a3; line-height: 1.5;">
                                            Explore your full timeline, interactive charts, and date range comparisons.
                                        </p>
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
                                            <tr>
                                                <td bgcolor="#22c55e" style="border-radius: 8px; mso-padding-alt: 0;">
                                                    <!--[if mso]><i style="letter-spacing:32px;mso-font-width:-100%;mso-text-raise:24pt" hidden>&nbsp;</i><![endif]-->
                                                    <a href="http://localhost:5555/dashboard?date=${summary.date}" target="_blank" style="display: inline-block; padding: 13px 36px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; font-weight: 600; color: #0a0a0a; text-decoration: none; letter-spacing: 0.02em;">
                                                        Explore Full Report &#8594;
                                                    </a>
                                                    <!--[if mso]><i style="letter-spacing:32px;mso-font-width:-100%" hidden>&nbsp;</i><![endif]-->
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="margin: 10px 0 0 0; font-size: 11px; color: #404040; line-height: 1.5;">
                                            Requires Telos to be running on your machine.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 0 20px 20px; text-align: center;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 12px; color: #333333;">
                                <span style="color: #22c55e; font-weight: 600;">telos</span> &middot; daily report
                            </p>
                            <p style="margin: 0 0 6px 0; font-size: 11px; color: #333333; line-height: 1.5;">
                                Your data is encrypted and stored under an anonymous identifier.
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #333333; line-height: 1.8;">
                                <a href="mailto:support@telos.dev?subject=Unsubscribe%20from%20daily%20reports" style="color: #404040; text-decoration: underline;">Unsubscribe</a>
                                &middot;
                                <a href="https://telos.app/privacy" style="color: #404040; text-decoration: underline;">Privacy</a>
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
Generated by Telos · Your data is encrypted and stored anonymously.
To change report timing or unsubscribe, open Telos > Settings.
Reply to this email for support.
  `.trim();
}

/**
 * Send daily report email with retry logic
 *
 * @param {string} userEmail - Recipient email
 * @param {object} summary - Daily summary data
 * @param {string} userName - User's display name
 * @param {number} maxRetries - Maximum retry attempts (default: 3)
 * @returns {object} Result with success status
 */
export async function sendDailyReport(userEmail, summary, userName = null, maxRetries = 3, reportUrl = null) {
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
    replyTo: 'anuragkurle27@gmail.com',
    subject: generateSubjectLine(summary),
    text: generatePlainText(summary),
    html: generateReportHTML(summary, userName, reportUrl),
    headers: {
      'List-Unsubscribe': `<mailto:support@telos.dev?subject=Unsubscribe%20${encodeURIComponent(userEmail)}>`,
      'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
    }
  };

  // Retry logic for transient failures
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await sgMail.send(msg);
      console.log(`[EMAIL] ✓ Report sent to ${userEmail} (attempt ${attempt})`);
      return { success: true, attempts: attempt };
    } catch (error) {
      console.error(`[EMAIL] Attempt ${attempt}/${maxRetries} failed for ${userEmail}:`, error.message);

      if (error.response) {
        const statusCode = error.response.statusCode || error.code;
        console.error(`[EMAIL] SendGrid error (${statusCode}):`, error.response.body);

        // Don't retry on permanent failures (4xx errors except rate limiting)
        if (statusCode >= 400 && statusCode < 500 && statusCode !== 429) {
          console.error(`[EMAIL] Permanent failure (${statusCode}), not retrying`);
          return { success: false, error: error.message, permanent: true };
        }
      }

      // Wait before retrying (exponential backoff: 2s, 4s, 8s)
      if (attempt < maxRetries) {
        const waitTime = Math.pow(2, attempt) * 1000;
        console.log(`[EMAIL] Retrying in ${waitTime / 1000}s...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  console.error(`[EMAIL] ✗ All ${maxRetries} attempts failed for ${userEmail}`);
  return { success: false, error: 'All retry attempts exhausted', attempts: maxRetries };
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
      const userEmail = user.email || userDoc.id;  // Use email field, fallback to doc ID for legacy
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
            .where('userId', '==', user.uid)
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

            // Encrypt sensitive fields before storing
            const encryptedGenerated = { ...generated };
            encryptFields(encryptedGenerated, SUMMARY_ENCRYPT_FIELDS);

            // Save generated summary to Firestore
            const newSummary = {
              userId: user.uid,
              userEmail: encrypt(userEmail),
              date: dateStr,
              uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
              emailSent: false,
              summary: encryptedGenerated
            };

            summaryRef = await db.collection('daily_summaries').add(newSummary);
            summaryData = generated; // Use unencrypted version for email sending

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
            // Decrypt sensitive fields if encrypted
            if (summaryData && typeof summaryData === 'object') {
              decryptFields(summaryData, SUMMARY_ENCRYPT_FIELDS, SUMMARY_JSON_FIELDS);
            }
            summaryRef = doc.ref;
          }

          // Check data freshness and warn user if data is old
          const dataAge = Math.floor((new Date(originalDateStr) - new Date(dateStr)) / (1000 * 60 * 60 * 24));
          if (dataAge > 0) {
            console.log(`[EMAIL] ⚠️  Data for ${userEmail} is ${dataAge} day(s) old (${dateStr} vs ${originalDateStr})`);
            // Add a warning to the summary
            summaryData.daily_narrative = `⚠️ Note: This report uses data from ${dateStr} (${dataAge} day${dataAge > 1 ? 's' : ''} old). Recent data not available.\n\n` + summaryData.daily_narrative;
          }

          // Generate web report URL for CTA button
          let reportUrl = null;
          try {
            const reportId = summaryRef.id;
            const token = await generateViewToken(reportId);
            const backendUrl = process.env.BACKEND_URL || `https://telos-backend-${process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718'}.run.app`;
            reportUrl = `${backendUrl}/r/${reportId}?t=${token}`;
          } catch (e) {
            console.warn(`[EMAIL] Could not generate report URL:`, e.message);
          }

          // Send email
          const result = await sendDailyReport(userEmail, summaryData, null, 3, reportUrl);

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
 * Check if we should send email to user based on timezone.
 *
 * Uses luxon for proper DST-aware timezone handling.
 * Converts preferred local time to UTC, then checks if current UTC time matches
 * within a 2-hour window. The emailSent flag in sendDailyReports prevents duplicates.
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

  // Use luxon for DST-aware timezone conversion
  let targetUTCHour;
  try {
    // Create a DateTime in the user's timezone at their preferred hour today
    const nowInTZ = DateTime.now().setZone(timezone);
    const preferredLocal = nowInTZ.set({ hour: preferredLocalHour, minute: preferredLocalMinute, second: 0 });
    // Convert to UTC and get the hour
    const preferredUTC = preferredLocal.toUTC();
    targetUTCHour = preferredUTC.hour + (preferredUTC.minute / 60);
  } catch (e) {
    // Fallback for invalid timezone: assume UTC
    console.warn(`[EMAIL] Invalid timezone "${timezone}", falling back to UTC`);
    targetUTCHour = preferredLocalHour;
  }

  // Create a 2-hour window to account for scheduler frequency (runs every 30 min)
  const targetUTCHourLower = Math.floor(targetUTCHour);
  const targetUTCHourUpper = Math.ceil(targetUTCHour) + 1; // +1 hour buffer

  // Check if current hour is within the target window
  let shouldSend = false;

  if (targetUTCHourLower <= targetUTCHourUpper) {
    shouldSend = currentUTCHour >= targetUTCHourLower && currentUTCHour <= targetUTCHourUpper;
  } else {
    // Edge case: window wraps around midnight (e.g., 23-1)
    shouldSend = currentUTCHour >= targetUTCHourLower || currentUTCHour <= targetUTCHourUpper;
  }

  // Logging for debugging
  console.log(`[EMAIL] Timezone: ${timezone}, Preferred: ${preferredLocalHour}:${preferredLocalMinute < 10 ? '0' : ''}${preferredLocalMinute} (${prefs.sendTime || preferredLocalHour})`);
  console.log(`[EMAIL]   Target UTC: ${targetUTCHour.toFixed(1)} (window: ${targetUTCHourLower}-${targetUTCHourUpper})`);
  console.log(`[EMAIL]   Current UTC: ${currentUTCHour}, Should send: ${shouldSend}`);

  return shouldSend;
}
