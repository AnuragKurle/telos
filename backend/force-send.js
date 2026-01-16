
import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';
import { sendDailyReport } from './src/services/email.js';

dotenv.config();

// Initialize Firebase
if (!admin.apps.length) {
    admin.initializeApp({
        projectId: process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718'
    });
}

const TARGET_EMAIL = 'anurag@userology.co';

async function forceSend() {
    console.log(`[FORCE-SEND] Starting manual send for ${TARGET_EMAIL}...`);

    try {
        const db = admin.firestore();

        // 1. Get User
        const usersSnapshot = await db.collection('users').doc(TARGET_EMAIL).get();
        if (!usersSnapshot.exists) {
            // Try valid query if doc id is not email
            const q = await db.collection('users').where('email', '==', TARGET_EMAIL).get();
            if (q.empty) throw new Error('User not found');
            // Proceed with first match
        }

        const uid = usersSnapshot.exists ? usersSnapshot.data().uid : (await db.collection('users').where('email', '==', TARGET_EMAIL).get()).docs[0].data().uid;

        // 2. Determine Date (Use most recent available data)
        const now = new Date();
        let dateStr = '2026-01-10'; // Use a date we know has data
        console.log(`[FORCE-SEND] Using date with known data: ${dateStr}`);

        console.log(`[FORCE-SEND] Processing for date: ${dateStr}`);

        // 3. Generate Summary
        console.log('[FORCE-SEND] Generating summary...');
        const summary = await generateSummaryFromUsage(TARGET_EMAIL, uid, dateStr);

        if (!summary) {
            console.error('[FORCE-SEND] Could not generate summary (no data?)');
            return;
        }

        // 4. Send Email
        console.log('[FORCE-SEND] Sending email...');
        const result = await sendDailyReport(TARGET_EMAIL, summary, 'Anurag');

        if (result.success) {
            console.log('\n✅ SUCCESS: Email sent successfully!');
        } else {
            console.error('\n❌ FAILED: ' + result.error);
        }

    } catch (error) {
        console.error('[FORCE-SEND] Error:', error);
    }
}

forceSend();
