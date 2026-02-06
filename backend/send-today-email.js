/**
 * Send today's email using REAL data from the local SQLite database.
 * 
 * Reads the daily summary + captures from ~/.telos/tracker.db,
 * enriches them into the format the email template expects,
 * saves to Firestore for the web report, and sends.
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import Database from 'better-sqlite3';
import { homedir } from 'os';
import { join } from 'path';
import { sendDailyReport } from './src/services/email.js';
import { initializeEncryption, encrypt, encryptFields } from './src/services/encryption.js';
import { generateViewToken } from './src/routes/webReport.js';
import { generateDailyNarrative } from './src/services/gemini.js';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718';
if (!admin.apps.length) {
  admin.initializeApp({ projectId });
}

const TARGET_EMAIL = 'anurag@userology.co';
// Note: using userology.co because sending from/to same gmail gets hidden
const USER_NAME = 'Anurag';
const UID = 'UQgcLrVEb5bQl7d1aBhSSGzXNCD2';

async function main() {
  try { await initializeEncryption(); } catch (e) { console.warn('Encryption init:', e.message); }

  const dbPath = join(homedir(), '.telos', 'tracker.db');
  console.log('Reading local DB:', dbPath);
  const localDb = new Database(dbPath, { readonly: true });

  const today = new Date().toISOString().slice(0, 10); // 2026-02-06
  console.log('Target date:', today);

  // 1. Get the local daily summary
  const localSummary = localDb.prepare(
    "SELECT * FROM daily_summaries WHERE date LIKE ? ORDER BY date DESC LIMIT 1"
  ).get(today + '%');

  if (!localSummary) {
    console.error('No daily summary found for today in local DB.');
    process.exit(1);
  }

  console.log(`\nLocal summary found:`);
  console.log(`  Work: ${Math.floor(localSummary.work_seconds / 60)}m`);
  console.log(`  Learning: ${Math.floor(localSummary.learning_seconds / 60)}m`);
  console.log(`  Browsing: ${Math.floor(localSummary.browsing_seconds / 60)}m`);
  console.log(`  Entertainment: ${Math.floor(localSummary.entertainment_seconds / 60)}m`);
  console.log(`  Score: ${localSummary.productivity_score}`);
  console.log(`  Narrative: ${(localSummary.daily_narrative || '').substring(0, 100)}...`);

  // 2. Get all captures for today with app aggregation
  const captures = localDb.prepare(`
    SELECT app_name, task, category, timestamp
    FROM captures 
    WHERE timestamp LIKE ? 
    ORDER BY timestamp ASC
  `).all(today + '%');

  console.log(`\nTotal captures today: ${captures.length}`);

  // 3. Build app usage data (aggregate by app_name)
  const appMap = {};
  for (const cap of captures) {
    const name = cap.app_name || 'Unknown';
    if (!appMap[name]) {
      appMap[name] = { name, minutes: 0, category: 'browsing', captures: 0 };
    }
    appMap[name].minutes += 0.5; // Each capture = ~30 seconds = 0.5 min
    appMap[name].captures++;
    // Use most common category
    appMap[name].category = mapCategory(cap.category);
  }

  const apps = Object.values(appMap)
    .map(a => ({ ...a, minutes: Math.round(a.minutes) }))
    .filter(a => a.minutes >= 1)
    .sort((a, b) => b.minutes - a.minutes)
    .slice(0, 12); // Top 12 apps

  console.log('\nTop apps:');
  for (const app of apps.slice(0, 8)) {
    console.log(`  ${app.name}: ${app.minutes}m (${app.category})`);
  }

  // 4. Build timeline from sessions
  const sessions = localDb.prepare(`
    SELECT id, start_time, end_time, category, primary_task
    FROM sessions 
    WHERE start_time LIKE ? 
    ORDER BY start_time ASC
  `).all(today + '%');

  const timeline = sessions
    .filter(s => s.end_time) // Only finished sessions
    .map(s => {
      const startTime = new Date(s.start_time);
      const endTime = new Date(s.end_time);
      const durationMins = Math.round((endTime - startTime) / 60000);
      const startStr = startTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
      
      // Get the most used app in this session
      const sessionCaptures = localDb.prepare(`
        SELECT app_name, COUNT(*) as cnt 
        FROM captures 
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY app_name 
        ORDER BY cnt DESC 
        LIMIT 1
      `).get(s.start_time, s.end_time);

      return {
        app: sessionCaptures?.app_name || s.category,
        task: s.primary_task || s.category,
        category: mapCategory(s.category),
        duration_mins: durationMins,
        start: startStr
      };
    })
    .filter(t => t.duration_mins >= 2); // Only show sessions >= 2 min

  console.log(`\nTimeline entries: ${timeline.length}`);

  // 5. Calculate deep work sessions (sessions >= 15 min of work/learning)
  const deepWorkSessions = sessions
    .filter(s => {
      if (!s.end_time) return false;
      const dur = (new Date(s.end_time) - new Date(s.start_time)) / 60000;
      const cat = mapCategory(s.category);
      return dur >= 15 && (cat === 'work' || cat === 'learning');
    })
    .map(s => ({
      start: new Date(s.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
      duration_mins: Math.round((new Date(s.end_time) - new Date(s.start_time)) / 60000),
      app: s.primary_task || s.category
    }));

  // 6. Calculate focus quality
  const totalSessions = sessions.filter(s => s.end_time).length;
  const avgSessionLen = totalSessions > 0
    ? Math.round(sessions.filter(s => s.end_time).reduce((acc, s) => acc + (new Date(s.end_time) - new Date(s.start_time)) / 60000, 0) / totalSessions)
    : 0;

  const focusQuality = {
    avg_session_length: avgSessionLen,
    focus_quality_score: Math.round(localSummary.productivity_score * 100)
  };

  // 7. Find peak productivity hour
  const hourCounts = {};
  for (const cap of captures) {
    const cat = mapCategory(cap.category);
    if (cat === 'work' || cat === 'learning') {
      const hr = new Date(cap.timestamp).getHours();
      hourCounts[hr] = (hourCounts[hr] || 0) + 1;
    }
  }
  const peakHour = Object.entries(hourCounts).sort((a, b) => b[1] - a[1])[0];
  const peakHourStr = peakHour ? formatHour(parseInt(peakHour[0])) : null;

  // 8. Get weekly comparison from older summaries
  const olderSummaries = localDb.prepare(`
    SELECT work_seconds, learning_seconds, browsing_seconds, entertainment_seconds
    FROM daily_summaries 
    WHERE date < ? 
    ORDER BY date DESC 
    LIMIT 7
  `).all(today);

  let weeklyComparison = { has_history: false };
  if (olderSummaries.length >= 2) {
    const avgWork = Math.round(olderSummaries.reduce((a, s) => a + s.work_seconds / 60, 0) / olderSummaries.length);
    const avgTotal = Math.round(olderSummaries.reduce((a, s) => a + (s.work_seconds + s.learning_seconds + s.browsing_seconds + s.entertainment_seconds) / 60, 0) / olderSummaries.length);
    const currentWork = Math.floor(localSummary.work_seconds / 60);
    const currentTotal = Math.floor((localSummary.work_seconds + localSummary.learning_seconds + localSummary.browsing_seconds + localSummary.entertainment_seconds) / 60);

    weeklyComparison = {
      has_history: true,
      days_compared: olderSummaries.length,
      current_work: currentWork,
      avg_work: avgWork,
      work_diff: currentWork - avgWork,
      current_total: currentTotal,
      avg_total: avgTotal,
      total_diff: currentTotal - avgTotal
    };
  }

  // 9. Regenerate daily narrative with new prompt
  console.log('\n🤖 Generating fresh narrative with improved prompt...');
  let freshNarrative = localSummary.daily_narrative || 'No narrative generated.';
  let freshScore = Math.round(localSummary.productivity_score * 100);
  
  try {
    // Prepare sessions format for Gemini
    const narrativeSessions = sessions
      .filter(s => s.end_time) // Only finished sessions
      .map(s => ({
        start_time: s.start_time,
        app: s.primary_task || 'Unknown',
        task: s.primary_task || s.category,
        duration_mins: Math.round((new Date(s.end_time) - new Date(s.start_time)) / 60000),
        category: mapCategory(s.category)
      }))
      .filter(s => s.duration_mins >= 1); // At least 1 minute

    // Prepare category totals in seconds
    const categoryTotals = {
      work: localSummary.work_seconds,
      learning: localSummary.learning_seconds,
      browsing: localSummary.browsing_seconds,
      entertainment: localSummary.entertainment_seconds
    };
    
    const result = await generateDailyNarrative(narrativeSessions, categoryTotals, null);
    freshNarrative = result.narrative;
    freshScore = result.score;
    console.log('✅ New narrative generated:', freshNarrative.substring(0, 100) + '...');
    console.log('✅ AI-computed score:', freshScore);
  } catch (e) {
    console.warn('⚠️  Failed to generate narrative, using cached:', e.message);
  }

  // 10. Assemble the full summary object
  const summary = {
    date: today,
    work_seconds: localSummary.work_seconds,
    learning_seconds: localSummary.learning_seconds,
    browsing_seconds: localSummary.browsing_seconds,
    entertainment_seconds: localSummary.entertainment_seconds,
    idle_seconds: localSummary.idle_seconds || 0,
    productivity_score: freshScore,
    daily_narrative: freshNarrative,
    key_learnings_json: localSummary.key_learnings_json || '[]',
    context_switches: sessions.length,
    apps,
    timeline,
    deep_work_sessions: deepWorkSessions,
    focus_quality: focusQuality,
    weekly_comparison: weeklyComparison,
    peak_hour: peakHourStr
  };

  console.log('\n=== Final Summary ===');
  console.log(`  Score: ${summary.productivity_score}/100`);
  console.log(`  Peak hour: ${summary.peak_hour}`);
  console.log(`  Deep work sessions: ${deepWorkSessions.length}`);
  console.log(`  Context switches: ${summary.context_switches}`);
  console.log(`  Weekly comparison: ${weeklyComparison.has_history ? `work ${weeklyComparison.work_diff >= 0 ? '+' : ''}${weeklyComparison.work_diff}m vs avg` : 'not enough history'}`);

  // 11. Save to Firestore for web report
  const firestoreDb = admin.firestore();
  console.log('\nSaving to Firestore...');

  const encryptedSummary = { ...summary };
  try {
    encryptFields(encryptedSummary, ['daily_narrative', 'key_learnings_json', 'apps', 'timeline', 'deep_work_sessions']);
  } catch (e) {
    console.warn('Encryption skipped:', e.message);
  }

  const docRef = await firestoreDb.collection('daily_summaries').add({
    userId: UID,
    userEmail: TARGET_EMAIL,
    date: today,
    uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
    emailSent: false,
    summary: encryptedSummary,
    isTest: true
  });

  const reportId = docRef.id;
  console.log('Saved with ID:', reportId);

  // 12. Generate web report URL
  let reportUrl = null;
  try {
    const token = await generateViewToken(reportId);
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';
    reportUrl = `${backendUrl}/r/${reportId}?t=${token}`;
    console.log('Web report URL:', reportUrl);
  } catch (e) {
    console.warn('Could not generate URL:', e.message);
  }

  // 13. Send the email
  console.log(`\nSending email to ${TARGET_EMAIL}...`);
  const result = await sendDailyReport(TARGET_EMAIL, summary, USER_NAME, 3, reportUrl);

  if (result.success) {
    console.log(`\n✅ Email sent successfully!`);
    console.log(`📬 Check your inbox at ${TARGET_EMAIL}`);
  } else {
    console.error(`\n❌ Failed: ${result.error}`);
  }

  localDb.close();
  process.exit(0);
}

/**
 * Map the detailed client-side categories to the 4 email categories
 */
function mapCategory(category) {
  if (!category) return 'browsing';
  const cat = category.toLowerCase();
  
  // Work categories
  if (cat.includes('debug') || cat.includes('development') || cat.includes('coding') || 
      cat.includes('deploy') || cat.includes('devops') || cat.includes('feature') ||
      cat.includes('planning') || cat.includes('project') || cat.includes('review') ||
      cat.includes('audit') || cat.includes('admin') || cat.includes('management') ||
      cat.includes('documentation') || cat.includes('meeting') || cat.includes('team') ||
      cat.includes('professional comm') || cat.includes('work comm') ||
      cat.includes('security') || cat.includes('setup') || cat.includes('config') ||
      cat.includes('api') || cat.includes('bot') || cat.includes('agent') ||
      cat.includes('refactor') || cat.includes('code') || cat.includes('issue') ||
      cat.includes('release') || cat.includes('bug') || cat.includes('testing') ||
      cat.includes('monitor') || cat.includes('product') || cat.includes('strategy') ||
      cat.includes('waitlist') || cat.includes('email') && !cat.includes('email -') ||
      cat.includes('beta') || cat.includes('webhook') || cat.includes('scheduling') ||
      cat.includes('root cause') || cat.includes('technical') || cat.includes('cloud') ||
      cat.includes('system') || cat.includes('version control') || cat.includes('software') ||
      cat.includes('ui/ux') || cat.includes('frontend') || cat.includes('backend') ||
      cat.includes('database') || cat.includes('dependency') || cat.includes('application') ||
      cat.includes('onboarding') || cat.includes('integration') ||
      cat.includes('ai-assisted') || cat.includes('ai assisted') || cat.includes('ai agent') ||
      cat.includes('ai tool') || cat.includes('ai ') && cat.includes('develop'))
    return 'work';
  
  // Learning categories
  if (cat.includes('learning') || cat.includes('philosophy') || cat.includes('research') ||
      cat.includes('educational') || cat.includes('career') || cat.includes('resume') ||
      cat.includes('self-improvement') || cat.includes('coaching') || cat.includes('lecture') ||
      cat.includes('reading') || cat.includes('tech & science'))
    return 'learning';
  
  // Entertainment categories
  if (cat.includes('entertainment') || cat.includes('gaming') || cat.includes('game') ||
      cat.includes('video streaming') || cat.includes('comedy') || cat.includes('music') ||
      cat.includes('playing') || cat.includes('casual') || cat.includes('youtube') ||
      cat.includes('creative platform'))
    return 'entertainment';
  
  // Browsing / social
  if (cat.includes('social media') || cat.includes('instagram') || cat.includes('linkedin') ||
      cat.includes('browsing') || cat.includes('messaging') || cat.includes('chatting') ||
      cat.includes('chat') || cat.includes('whatsapp') || cat.includes('personal') ||
      cat.includes('shopping') || cat.includes('local') || cat.includes('content') ||
      cat.includes('conceptual'))
    return 'browsing';
  
  return 'browsing';
}

function formatHour(hour) {
  if (hour === 0) return '12 AM';
  if (hour === 12) return '12 PM';
  return hour > 12 ? `${hour - 12} PM` : `${hour} AM`;
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
