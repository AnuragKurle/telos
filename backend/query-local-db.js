/**
 * Quick script to query the local SQLite database for today's capture data.
 */
import Database from 'better-sqlite3';
import { homedir } from 'os';
import { join } from 'path';

const dbPath = join(homedir(), '.telos', 'tracker.db');
console.log('DB path:', dbPath);

const db = new Database(dbPath, { readonly: true });

// List tables
const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
console.log('Tables:', tables.map(t => t.name).join(', '));

// Check captures for today
const today = '2026-02-06';
const captureCount = db.prepare("SELECT COUNT(*) as cnt FROM captures WHERE timestamp LIKE ?").get(today + '%');
console.log('\nCaptures today:', captureCount.cnt);

// Get latest captures
const samples = db.prepare(`
  SELECT timestamp, app_name, task, category 
  FROM captures 
  WHERE timestamp LIKE ? 
  ORDER BY timestamp DESC 
  LIMIT 10
`).all(today + '%');

console.log('\nLatest captures today:');
for (const s of samples) {
  console.log(`  ${s.timestamp} | ${s.app_name} | ${s.category} | ${(s.task || '').substring(0, 60)}`);
}

// Also check earliest capture today
const earliest = db.prepare(`
  SELECT timestamp, app_name, task, category 
  FROM captures 
  WHERE timestamp LIKE ? 
  ORDER BY timestamp ASC 
  LIMIT 3
`).all(today + '%');

console.log('\nEarliest captures today:');
for (const s of earliest) {
  console.log(`  ${s.timestamp} | ${s.app_name} | ${s.category} | ${(s.task || '').substring(0, 60)}`);
}

// Check sessions
const sessionCount = db.prepare("SELECT COUNT(*) as cnt FROM sessions WHERE start_time LIKE ?").get(today + '%');
console.log('\nSessions today:', sessionCount.cnt);

const sessionSamples = db.prepare(`
  SELECT id, start_time, end_time, category, primary_task 
  FROM sessions 
  WHERE start_time LIKE ? 
  ORDER BY start_time DESC 
  LIMIT 5
`).all(today + '%');

if (sessionSamples.length > 0) {
  console.log('\nRecent sessions:');
  for (const s of sessionSamples) {
    console.log(`  ${s.start_time} - ${s.end_time || 'ongoing'} | ${s.category} | ${(s.primary_task || '').substring(0, 60)}`);
  }
}

// Daily summaries
const summaries = db.prepare("SELECT date, work_seconds, learning_seconds, browsing_seconds, entertainment_seconds, productivity_score FROM daily_summaries ORDER BY date DESC LIMIT 5").all();
console.log('\nRecent daily_summaries:');
for (const s of summaries) {
  console.log(`  ${s.date} | work: ${Math.floor(s.work_seconds/60)}m | learn: ${Math.floor(s.learning_seconds/60)}m | browse: ${Math.floor(s.browsing_seconds/60)}m | ent: ${Math.floor(s.entertainment_seconds/60)}m | score: ${s.productivity_score}`);
}

// Category breakdown for today
const categories = db.prepare(`
  SELECT category, COUNT(*) as cnt 
  FROM captures 
  WHERE timestamp LIKE ? 
  GROUP BY category 
  ORDER BY cnt DESC
`).all(today + '%');

console.log('\nToday category breakdown:');
for (const c of categories) {
  const minutes = Math.round(c.cnt * 30 / 60);
  console.log(`  ${c.category}: ${c.cnt} captures (~${minutes}m)`);
}

db.close();
