/**
 * Scheduler Service
 * 
 * Runs periodic background jobs for user lifecycle management.
 * - Checks for expired trials
 * - Sends expiration nudges
 */

import admin from 'firebase-admin';
import { sendSlackNotification } from './slack.js';
import { sendDailyReports } from './email.js';

/**
 * Run Daily Jobs
 * Should be called once per day (e.g. via Cloud Scheduler or simple interval)
 */
export async function runDailyJobs() {
    console.log('[SCHEDULER] Running daily jobs...');
    await checkExpiredTrials();
    await sendDailyReports();  // Send email reports
}

/**
 * Check for trials that have ended and update status
 */
async function checkExpiredTrials() {
    const db = admin.firestore();
    const now = admin.firestore.Timestamp.now();

    try {
        // Query: active trial users where current date > trial end date
        const snapshot = await db.collection('users')
            .where('accessStatus', '==', 'trial')
            .where('trial.endDate', '<', now)
            .get();

        if (snapshot.empty) {
            console.log('[SCHEDULER] No expired trials found.');
            return;
        }

        console.log(`[SCHEDULER] Found ${snapshot.size} expired trials.`);

        const batch = db.batch();
        const updates = [];

        snapshot.forEach(doc => {
            const user = doc.data();
            updates.push(user.email);

            // Set status to expired
            batch.update(doc.ref, {
                accessStatus: 'expired',
                'trial.isActive': false,
                lastUpdated: admin.firestore.FieldValue.serverTimestamp()
            });
        });

        await batch.commit();

        // Notify Slack about expirations
        if (updates.length > 0) {
            await sendSlackNotification(
                null,
                `🚫 *Trials Expired*\n${updates.map(e => `> ${e}`).join('\n')}`
            );
        }

    } catch (error) {
        console.error('[SCHEDULER] Error processing expired trials:', error);
    }
}

// Simple interval runner for local dev / MVP
// In production, use Cloud Scheduler -> HTTP triggering
let intervalId = null;

export function startScheduler() {
    if (intervalId) return;

    // Run immediately on startup for testing/safety
    runDailyJobs();

    // Run every hour to check for emails to send (timezone-aware)
    const HOUR_MS = 60 * 60 * 1000;
    intervalId = setInterval(runDailyJobs, HOUR_MS);

    console.log('[SCHEDULER] Started hourly job runner');
}
