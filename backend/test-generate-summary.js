/**
 * Test script to verify server-side summary generation
 * Tests generating a daily summary from Firestore usage data
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID;

if (!admin.apps.length) {
    admin.initializeApp({
        projectId: projectId
    });
    console.log(`✓ Firebase initialized for project: ${projectId}`);
}

async function testSummaryGeneration() {
    console.log('\n=== Testing Server-Side Summary Generation ===\n');

    const userEmail = 'anurag@userology.co';

    // Get user to find their UID
    const db = admin.firestore();
    const userDoc = await db.collection('users').doc(userEmail).get();

    if (!userDoc.exists) {
        console.error('❌ User document not found!');
        process.exit(1);
    }

    const userId = userDoc.data().uid;
    console.log(`Testing for user: ${userEmail}`);
    console.log(`User ID: ${userId}\n`);

    // Test with yesterday's date
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];

    console.log(`Generating summary for: ${dateStr}\n`);
    console.log('='.repeat(60));

    try {
        const summary = await generateSummaryFromUsage(userEmail, userId, dateStr);

        if (!summary) {
            console.log('\n❌ Summary generation returned null');
            console.log('This could mean:');
            console.log('  - No usage data exists for this date');
            console.log('  - User has no captures in Firestore');
            process.exit(1);
        }

        console.log('\n✅ Summary Generated Successfully!\n');
        console.log('='.repeat(60));
        console.log('SUMMARY DETAILS:');
        console.log('='.repeat(60));

        console.log(`\n📊 Activity Breakdown:`);
        console.log(`  Work: ${Math.floor(summary.work_seconds / 60)} minutes`);
        console.log(`  Learning: ${Math.floor(summary.learning_seconds / 60)} minutes`);
        console.log(`  Browsing: ${Math.floor(summary.browsing_seconds / 60)} minutes`);
        console.log(`  Entertainment: ${Math.floor(summary.entertainment_seconds / 60)} minutes`);

        console.log(`\n🎯 Productivity Score: ${summary.productivity_score}/100`);

        console.log(`\n📝 Daily Narrative:`);
        console.log(`  "${summary.daily_narrative}"`);

        try {
            const learnings = JSON.parse(summary.key_learnings_json);
            if (learnings && learnings.length > 0) {
                console.log(`\n🎓 Key Learnings:`);
                learnings.forEach((l, i) => {
                    console.log(`  ${i + 1}. ${l}`);
                });
            }
        } catch (e) {
            console.log('\n(No key learnings parsed)');
        }

        console.log(`\n🔄 Context Switches: ${summary.context_switches}`);

        console.log('\n' + '='.repeat(60));
        console.log('✅ TEST PASSED - Summary generation working!');
        console.log('='.repeat(60));
        console.log('\nNext step: Deploy backend and test full email flow');

        process.exit(0);

    } catch (error) {
        console.error('\n❌ TEST FAILED');
        console.error('Error:', error.message);
        console.error('\nStack trace:', error.stack);
        process.exit(1);
    }
}

testSummaryGeneration();
