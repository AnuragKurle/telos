/**
 * Manually trigger email scheduler to test email delivery
 * Uses real data from Firestore
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { sendDailyReports } from './src/services/email.js';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718';

if (!admin.apps.length) {
    admin.initializeApp({
        projectId: projectId
    });
    console.log(`✓ Firebase initialized for project: ${projectId}`);
}

console.log('\n=== Testing Email Scheduler with Real Data ===\n');
console.log('This will:');
console.log('  1. Check for users with email enabled');
console.log('  2. Generate summary if missing');
console.log('  3. Send daily email report');
console.log('\nPress Ctrl+C to cancel...\n');

// Wait 2 seconds then run
setTimeout(async () => {
    try {
        await sendDailyReports();
        console.log('\n✅ Email scheduler test complete');
        console.log('Check your inbox at anurag@userology.co!');
        process.exit(0);
    } catch (error) {
        console.error('\n❌ Email scheduler test failed:', error);
        process.exit(1);
    }
}, 2000);
