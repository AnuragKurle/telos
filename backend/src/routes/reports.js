/**
 * Reports routes - Daily summary upload and retrieval
 */

import express from 'express';
import { verifyFirebaseToken } from '../middleware/auth.js';
import admin from 'firebase-admin';
import sgMail from '@sendgrid/mail';
import { getSecret } from '../services/secrets.js';
import { encrypt, decrypt, encryptFields, decryptFields, encryptJSON, decryptJSON } from '../services/encryption.js';
import { DateTime } from 'luxon';

// Fields in daily_summaries that contain sensitive user activity data
const SUMMARY_ENCRYPT_FIELDS = ['daily_narrative', 'key_learnings_json', 'apps', 'timeline', 'deep_work_sessions', 'userEmail'];
const SUMMARY_JSON_FIELDS = ['apps', 'timeline', 'deep_work_sessions'];

const router = express.Router();

// SendGrid initialization
let sgInitialized = false;
async function initSendGrid() {
    if (sgInitialized) return;
    try {
        const apiKey = await getSecret(process.env.SENDGRID_API_KEY_SECRET_NAME || 'SENDGRID_API_KEY');
        sgMail.setApiKey(apiKey);
        sgInitialized = true;
        console.log('[REPORTS] SendGrid initialized');
    } catch (error) {
        console.error('[REPORTS] SendGrid init error:', error);
        throw error;
    }
}

/**
 * POST /v1/reports/send
 * Send HTML email report directly
 * Called by the Python batch sender script
 */
router.post('/send', async (req, res) => {
    try {
        const { to, subject, html, text, userName } = req.body;

        // Validate input
        if (!to || !html) {
            return res.status(400).json({ error: 'to and html are required' });
        }

        // Initialize SendGrid
        await initSendGrid();

        const msg = {
            to: to,
            from: {
                email: process.env.SENDGRID_FROM_EMAIL || 'reports@telos.dev',
                name: process.env.SENDGRID_FROM_NAME || 'Telos'
            },
            subject: subject || 'Your Daily Report',
            html: html,
            text: text || 'Please view this email in an HTML-capable email client.'
        };

        await sgMail.send(msg);
        console.log(`[REPORTS] Email sent to ${to}`);

        return res.json({ success: true });

    } catch (error) {
        console.error('[REPORTS] Send error:', error);
        if (error.response) {
            console.error('[REPORTS] SendGrid error:', error.response.body);
        }
        return res.status(500).json({
            error: 'Failed to send email',
            details: error.message
        });
    }
});

/**
 * POST /v1/reports/daily-summary
 * Upload daily summary from client
 */
router.post('/daily-summary', verifyFirebaseToken, async (req, res) => {
    try {
        const { date, summary } = req.body;
        const uid = req.user.uid;

        // Validate input
        if (!date || !summary) {
            return res.status(400).json({ error: 'Date and summary are required' });
        }

        // Get user email from Firestore
        const db = admin.firestore();
        const usersSnapshot = await db.collection('users')
            .where('uid', '==', uid)
            .limit(1)
            .get();

        if (usersSnapshot.empty) {
            return res.status(404).json({ error: 'User not found' });
        }

        const userEmail = usersSnapshot.docs[0].data().email || usersSnapshot.docs[0].id;

        // Encrypt sensitive fields before storing
        const encryptedSummary = typeof summary === 'object' ? { ...summary } : summary;
        if (typeof encryptedSummary === 'object') {
            encryptFields(encryptedSummary, SUMMARY_ENCRYPT_FIELDS);
        }

        // Store summary in Firestore
        const summaryRef = db.collection('daily_summaries').doc();
        await summaryRef.set({
            userId: uid,
            userEmail: encrypt(userEmail),
            date: date,
            uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
            emailSent: false,
            summary: encryptedSummary
        });

        console.log(`[REPORTS] Summary uploaded for ${userEmail} on ${date}`);

        return res.json({
            success: true,
            reportId: summaryRef.id
        });

    } catch (error) {
        console.error('[REPORTS] Error uploading summary:', error);
        return res.status(500).json({ error: 'Failed to upload summary' });
    }
});

/**
 * GET /v1/reports/daily-summary/:date
 * Retrieve daily summary for authenticated user
 */
router.get('/daily-summary/:date', verifyFirebaseToken, async (req, res) => {
    try {
        const { date } = req.params;
        const uid = req.user.uid;

        const db = admin.firestore();
        const snapshot = await db.collection('daily_summaries')
            .where('userId', '==', uid)
            .where('date', '==', date)
            .limit(1)
            .get();

        if (snapshot.empty) {
            return res.status(404).json({ error: 'Summary not found' });
        }

        const doc = snapshot.docs[0];
        const data = doc.data();

        // Decrypt sensitive fields
        if (data.userEmail) data.userEmail = decrypt(data.userEmail);
        if (data.summary && typeof data.summary === 'object') {
            decryptFields(data.summary, SUMMARY_ENCRYPT_FIELDS, SUMMARY_JSON_FIELDS);
        }

        return res.json({
            reportId: doc.id,
            ...data
        });

    } catch (error) {
        console.error('[REPORTS] Error fetching summary:', error);
        return res.status(500).json({ error: 'Failed to fetch summary' });
    }
});

/**
 * PUT /v1/reports/email-preferences
 * Update email report preferences
 */
router.put('/email-preferences', verifyFirebaseToken, async (req, res) => {
    try {
        const { enabled, sendTime, timezone, frequency, preferredHour } = req.body;
        const uid = req.user.uid;

        const db = admin.firestore();
        const usersSnapshot = await db.collection('users')
            .where('uid', '==', uid)
            .limit(1)
            .get();

        if (usersSnapshot.empty) {
            return res.status(404).json({ error: 'User not found' });
        }

        const userRef = usersSnapshot.docs[0].ref;

        // Parse preferredHour from sendTime if not provided
        let hour = preferredHour;
        if (hour === undefined && sendTime) {
            const parts = sendTime.split(':');
            hour = parseInt(parts[0], 10);
        }

        const preferences = {
            emailReports: {
                enabled: enabled !== undefined ? enabled : true,
                sendTime: sendTime || '09:00',
                timezone: timezone || 'UTC',
                frequency: frequency || 'daily',
                preferredHour: hour !== undefined ? hour : 9,  // Store preferredHour for email timing
                updatedAt: admin.firestore.FieldValue.serverTimestamp()
            }
        };

        await userRef.update(preferences);

        console.log(`[REPORTS] Email preferences updated for ${uid}: time=${sendTime}, tz=${timezone}, hour=${hour}`);

        return res.json({
            success: true,
            preferences: preferences.emailReports
        });

    } catch (error) {
        console.error('[REPORTS] Error updating preferences:', error);
        return res.status(500).json({ error: 'Failed to update preferences' });
    }
});

/**
 * GET /v1/reports/email-preferences
 * Get email report preferences
 */
router.get('/email-preferences', verifyFirebaseToken, async (req, res) => {
    try {
        const uid = req.user.uid;

        const db = admin.firestore();
        const usersSnapshot = await db.collection('users')
            .where('uid', '==', uid)
            .limit(1)
            .get();

        if (usersSnapshot.empty) {
            return res.status(404).json({ error: 'User not found' });
        }

        const userData = usersSnapshot.docs[0].data();
        const preferences = userData.emailReports || {
            enabled: true,
            sendTime: '09:00',
            timezone: 'UTC',
            frequency: 'daily'
        };

        return res.json(preferences);

    } catch (error) {
        console.error('[REPORTS] Error fetching preferences:', error);
        return res.status(500).json({ error: 'Failed to fetch preferences' });
    }
});

/**
 * POST /v1/reports/trigger-daily-emails
 * Triggered by Cloud Scheduler hourly to send daily reports
 * No auth required - protected by Cloud Scheduler service account
 */
router.post('/trigger-daily-emails', async (req, res) => {
    try {
        console.log('[SCHEDULER] Daily email trigger received');

        // Import email service
        const { sendDailyReports } = await import('../services/email.js');

        // Run the daily reports job
        // Allow forcing via request body (for manual recovery)
        const { force } = req.body;
        if (force) console.log('[SCHEDULER] Forcing email delivery (bypassing time checks)');

        await sendDailyReports(force);

        console.log('[SCHEDULER] Daily email job completed');

        return res.json({
            success: true,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('[SCHEDULER] Error in daily email job:', error);
        return res.status(500).json({
            error: 'Failed to send daily reports',
            details: error.message
        });
    }
});

/**
 * GET /v1/reports/email-diagnostics
 * Get diagnostic information for email system
 * Helps debug why emails might not be sent
 */
router.get('/email-diagnostics', verifyFirebaseToken, async (req, res) => {
    try {
        const uid = req.user.uid;
        const db = admin.firestore();

        // Get user info
        const usersSnapshot = await db.collection('users')
            .where('uid', '==', uid)
            .limit(1)
            .get();

        if (usersSnapshot.empty) {
            return res.status(404).json({ error: 'User not found' });
        }

        const userData = usersSnapshot.docs[0].data();
        const userEmail = userData.email || usersSnapshot.docs[0].id;
        const emailPrefs = userData.emailReports || {};

        // Get recent summaries
        const summariesSnapshot = await db.collection('daily_summaries')
            .where('userEmail', '==', userEmail)
            .orderBy('date', 'desc')
            .limit(7)
            .get();

        const recentSummaries = summariesSnapshot.docs.map(doc => ({
            id: doc.id,
            date: doc.data().date,
            emailSent: doc.data().emailSent || false,
            emailSentAt: doc.data().emailSentAt?.toDate?.() || null,
            uploadedAt: doc.data().uploadedAt?.toDate?.() || null
        }));

        // Get usage data status
        const usageDoc = await db.collection('usage').doc(uid).get();
        let usageStatus = { exists: false, dates: [] };

        if (usageDoc.exists) {
            const dayBucket = usageDoc.data().dayBucket || {};
            const dates = Object.keys(dayBucket).sort().reverse().slice(0, 7);
            usageStatus = {
                exists: true,
                dates: dates,
                latestDate: dates[0] || null,
                captureCountByDate: dates.reduce((acc, date) => {
                    acc[date] = dayBucket[date]?.captures?.length || 0;
                    return acc;
                }, {})
            };
        }

        // Calculate what would happen now
        const now = new Date();
        const currentUTCHour = now.getUTCHours();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];

        // Calculate target time using luxon for proper DST handling
        const timezone = emailPrefs.timezone || 'UTC';
        const preferredHour = emailPrefs.preferredHour || 9;
        let targetUTCHour;
        try {
            const nowInTZ = DateTime.now().setZone(timezone);
            const preferredLocal = nowInTZ.set({ hour: preferredHour, minute: 0, second: 0 });
            const preferredUTC = preferredLocal.toUTC();
            targetUTCHour = preferredUTC.hour;
        } catch (e) {
            targetUTCHour = preferredHour; // Fallback for invalid timezone
        }

        const diagnostics = {
            timestamp: now.toISOString(),
            currentUTCHour,
            user: {
                uid,
                email: userEmail
            },
            emailPreferences: {
                enabled: emailPrefs.enabled || false,
                sendTime: emailPrefs.sendTime || '09:00',
                timezone: emailPrefs.timezone || 'UTC',
                preferredHour: emailPrefs.preferredHour || 9,
                targetUTCHour: targetUTCHour,
                wouldSendNow: emailPrefs.enabled && (
                    currentUTCHour >= Math.floor(targetUTCHour) &&
                    currentUTCHour <= Math.ceil(targetUTCHour) + 1
                )
            },
            firestoreData: usageStatus,
            recentSummaries,
            recommendations: []
        };

        // Add recommendations based on diagnostics
        if (!emailPrefs.enabled) {
            diagnostics.recommendations.push('Email reports are disabled. Enable them in settings.');
        }
        if (!usageStatus.exists || usageStatus.dates.length === 0) {
            diagnostics.recommendations.push('No usage data in Firestore. The client app needs to sync data.');
        } else if (!usageStatus.dates.includes(yesterdayStr)) {
            diagnostics.recommendations.push(`No data for yesterday (${yesterdayStr}). Check if client sync is working.`);
        }
        if (recentSummaries.length > 0 && recentSummaries[0].emailSent) {
            diagnostics.recommendations.push('Most recent summary was already sent. Check spam folder.');
        }

        return res.json(diagnostics);

    } catch (error) {
        console.error('[REPORTS] Error in diagnostics:', error);
        return res.status(500).json({ error: 'Failed to get diagnostics', details: error.message });
    }
});

export default router;
