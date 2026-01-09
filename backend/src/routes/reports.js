/**
 * Reports routes - Daily summary upload and retrieval
 */

import express from 'express';
import { verifyFirebaseToken } from '../middleware/auth.js';
import admin from 'firebase-admin';
import sgMail from '@sendgrid/mail';
import { getSecret } from '../services/secrets.js';

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

        const userEmail = usersSnapshot.docs[0].id;

        // Store summary in Firestore
        const summaryRef = db.collection('daily_summaries').doc();
        await summaryRef.set({
            userId: uid,
            userEmail: userEmail,
            date: date,
            uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
            emailSent: false,
            summary: summary
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
        return res.json({
            reportId: doc.id,
            ...doc.data()
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
        const { enabled, sendTime, timezone, frequency } = req.body;
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

        const preferences = {
            emailReports: {
                enabled: enabled !== undefined ? enabled : true,
                sendTime: sendTime || '09:00',
                timezone: timezone || 'UTC',
                frequency: frequency || 'daily',
                updatedAt: admin.firestore.FieldValue.serverTimestamp()
            }
        };

        await userRef.update(preferences);

        console.log(`[REPORTS] Email preferences updated for ${uid}`);

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

export default router;
