/**
 * Test the email template with REAL Firestore data.
 *
 * Finds the most recent date with usage data for the user,
 * generates a real summary, saves it to Firestore,
 * generates a web report URL, and sends the email.
 *
 * Run: node test-new-email-template.js
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';
import { sendDailyReport } from './src/services/email.js';
import { initializeEncryption, encrypt, encryptFields } from './src/services/encryption.js';
import { generateViewToken } from './src/routes/webReport.js';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718';

if (!admin.apps.length) {
  admin.initializeApp({ projectId });
  console.log(`Firebase initialized for project: ${projectId}`);
}

const TARGET_EMAIL = 'anuragkurle27@gmail.com';

// Fields that need encryption before saving
const SUMMARY_ENCRYPT_FIELDS = ['daily_narrative', 'key_learnings_json', 'apps', 'timeline', 'deep_work_sessions'];

async function main() {
  // Initialize encryption (needed to decrypt captures and encrypt summary for storage)
  try {
    await initializeEncryption();
    console.log('Encryption initialized');
  } catch (e) {
    console.warn('Encryption init skipped:', e.message);
  }

  const db = admin.firestore();

  // 1. Find the user document
  console.log(`\nLooking up user: ${TARGET_EMAIL}`);

  let uid = null;
  let userEmail = TARGET_EMAIL;

  // Try doc ID = email first
  const docById = await db.collection('users').doc(TARGET_EMAIL).get();
  if (docById.exists) {
    uid = docById.data().uid;
    userEmail = docById.data().email || TARGET_EMAIL;
    console.log(`Found user by doc ID. UID: ${uid}`);
  } else {
    // Query by email field
    const q = await db.collection('users').where('email', '==', TARGET_EMAIL).limit(1).get();
    if (!q.empty) {
      uid = q.docs[0].data().uid;
      userEmail = q.docs[0].data().email || TARGET_EMAIL;
      console.log(`Found user by email query. UID: ${uid}`);
    }
  }

  if (!uid) {
    // Try anurag@userology.co as fallback
    const fallbackEmail = 'anurag@userology.co';
    console.log(`User not found with ${TARGET_EMAIL}. Trying fallback: ${fallbackEmail}`);
    const fallbackDoc = await db.collection('users').doc(fallbackEmail).get();
    if (fallbackDoc.exists) {
      uid = fallbackDoc.data().uid;
      userEmail = fallbackDoc.data().email || fallbackEmail;
      console.log(`Found via fallback. UID: ${uid}`);
    } else {
      const q2 = await db.collection('users').where('email', '==', fallbackEmail).limit(1).get();
      if (!q2.empty) {
        uid = q2.docs[0].data().uid;
        userEmail = q2.docs[0].data().email || fallbackEmail;
        console.log(`Found via fallback query. UID: ${uid}`);
      }
    }
  }

  if (!uid) {
    console.error('Could not find user in Firestore.');
    process.exit(1);
  }

  // 2. Find the most recent date with usage data
  //    The user may have data under a different UID (e.g. older account).
  //    Check both the found UID and fallback UIDs for actual capture data.
  console.log(`\nChecking usage data for UID: ${uid}`);
  let usageDoc = await db.collection('usage').doc(uid).get();

  // Check if this doc has valid captures (date keys should be YYYY-MM-DD format)
  let dayBucketRaw = usageDoc.exists ? usageDoc.data().dayBucket || {} : {};
  const hasValidDates = Object.keys(dayBucketRaw).some(k => /^\d{4}-\d{2}-\d{2}$/.test(k));
  
  if (!hasValidDates) {
    console.log(`No valid date-format captures under ${uid}. Checking alternate accounts...`);
    // Try the other known UID
    const altUid = 'DuysxZoYCsgnTd4B8H2bToTcSCG2';
    const altDoc = await db.collection('usage').doc(altUid).get();
    if (altDoc.exists) {
      const altBucket = altDoc.data().dayBucket || {};
      const altHasDates = Object.keys(altBucket).some(k => /^\d{4}-\d{2}-\d{2}$/.test(k));
      if (altHasDates) {
        console.log(`Found valid data under alternate UID: ${altUid}`);
        uid = altUid;
        usageDoc = altDoc;
      }
    }
  }

  if (!usageDoc.exists) {
    console.error('No usage document found for this user.');
    process.exit(1);
  }

  const dayBucket = usageDoc.data().dayBucket || {};
  // Only consider properly formatted dates (YYYY-MM-DD)
  const availableDates = Object.keys(dayBucket)
    .filter(k => /^\d{4}-\d{2}-\d{2}$/.test(k))
    .sort()
    .reverse();

  if (availableDates.length === 0) {
    console.error('No dates with usage data found.');
    process.exit(1);
  }

  // Pick the most recent date with captures
  let targetDate = null;
  for (const date of availableDates) {
    const captures = dayBucket[date]?.captures;
    if (captures && captures.length > 0) {
      targetDate = date;
      console.log(`Most recent date with data: ${date} (${captures.length} captures)`);
      break;
    }
  }

  if (!targetDate) {
    console.error('No dates with captures found.');
    process.exit(1);
  }

  console.log(`Available dates (last 5): ${availableDates.slice(0, 5).join(', ')}${availableDates.length > 5 ? '...' : ''}`);

  // 3. Generate summary from real data
  console.log(`\nGenerating summary for ${targetDate}...`);
  const summary = await generateSummaryFromUsage(userEmail, uid, targetDate);

  if (!summary) {
    console.error('Failed to generate summary from usage data.');
    process.exit(1);
  }

  console.log('\nGenerated summary:');
  console.log(`  Date: ${summary.date}`);
  console.log(`  Work: ${Math.floor(summary.work_seconds / 60)}m`);
  console.log(`  Learning: ${Math.floor(summary.learning_seconds / 60)}m`);
  console.log(`  Browsing: ${Math.floor(summary.browsing_seconds / 60)}m`);
  console.log(`  Entertainment: ${Math.floor(summary.entertainment_seconds / 60)}m`);
  console.log(`  Score: ${summary.productivity_score}`);
  console.log(`  Apps: ${(summary.apps || []).map(a => a.name).join(', ')}`);
  console.log(`  Deep work sessions: ${(summary.deep_work_sessions || []).length}`);
  console.log(`  Context switches: ${summary.context_switches}`);

  // 4. Save to Firestore so the web report URL actually works
  console.log(`\nSaving summary to Firestore for web report...`);
  const encryptedSummary = { ...summary };
  try {
    encryptFields(encryptedSummary, SUMMARY_ENCRYPT_FIELDS);
  } catch (e) {
    console.warn('Could not encrypt summary fields (continuing unencrypted):', e.message);
  }

  const summaryDoc = {
    userId: uid,
    userEmail: TARGET_EMAIL,
    date: targetDate,
    uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
    emailSent: false,
    summary: encryptedSummary,
    isTest: true  // Mark as test so we can clean up later
  };

  const docRef = await db.collection('daily_summaries').add(summaryDoc);
  const reportId = docRef.id;
  console.log(`Saved with ID: ${reportId}`);

  // 5. Generate web report URL
  let reportUrl = null;
  try {
    const token = await generateViewToken(reportId);
    // For local testing, use localhost. In production, this would be the Cloud Run URL.
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';
    reportUrl = `${backendUrl}/r/${reportId}?t=${token}`;
    console.log(`Web report URL: ${reportUrl}`);
  } catch (e) {
    console.warn('Could not generate report URL:', e.message);
  }

  // 6. Send the email with real data
  console.log(`\nSending email to ${TARGET_EMAIL}...`);
  const result = await sendDailyReport(TARGET_EMAIL, summary, 'Anurag', 3, reportUrl);

  if (result.success) {
    console.log(`\n✅ Email sent successfully! (attempt ${result.attempts})`);
    console.log(`📬 Check your inbox at ${TARGET_EMAIL}`);
    if (reportUrl) {
      console.log(`🌐 Web report: ${reportUrl}`);
    }
  } else {
    console.error(`\n❌ Failed: ${result.error}`);
  }

  process.exit(0);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
