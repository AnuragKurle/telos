/**
 * Force send a daily email report for testing
 * Bypasses timezone check and sends immediately
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { sendDailyReport } from './src/services/email.js';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718';

if (!admin.apps.length) {
    admin.initializeApp({
        projectId: projectId
    });
}

async function forceSendEmail() {
    console.log('\n=== Force Sending Daily Email Report ===\n');

    const userEmail = 'anurag@userology.co';
    const userId = 'DuysxZoYCsgnTd4B8H2bToTcSCG2';

    // Get yesterday's date
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];

    console.log(`User: ${userEmail}`);
    console.log(`Date: ${dateStr}\n`);

    console.log('Step 1: Generating summary from Firestore...');
    const summary = await generateSummaryFromUsage(userEmail, userId, dateStr);

    if (!summary) {
        console.error('❌ Could not generate summary');
        process.exit(1);
    }

    console.log('✅ Summary generated\n');

    console.log('Step 2: Sending email...');
    const result = await sendDailyReport(userEmail, summary, 'Anurag');

    if (result.success) {
        console.log('\n✅ EMAIL SENT SUCCESSFULLY!');
        console.log(`\n📬 Check your inbox at ${userEmail}`);
        console.log('\nSummary details:');
        console.log(`  - Work: ${Math.floor(summary.work_seconds / 60)}m`);
        console.log(`  - Learning: ${Math.floor(summary.learning_seconds / 60)}m`);
        console.log(`  - Score: ${summary.productivity_score}/100`);
        console.log(`  - Narrative: "${summary.daily_narrative.substring(0, 80)}..."`);

        // Save to Firestore
        const db = admin.firestore();
        await db.collection('daily_summaries').add({
            userId: userId,
            userEmail: userEmail,
            date: dateStr,
            uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
            emailSent: true,
            emailSentAt: admin.firestore.FieldValue.serverTimestamp(),
            summary: summary
        });

        console.log('\n✅ Summary saved to Firestore');
        process.exit(0);
    } else {
        console.error('\n❌ EMAIL FAILED:', result.error);
        process.exit(1);
    }
}

forceSendEmail().catch(err => {
    console.error('❌ Error:', err);
    process.exit(1);
});
