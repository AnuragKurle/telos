/**
 * Admin Routes
 * 
 * Protected admin endpoints for managing the beta launch:
 * - Waitlist management (view, update statuses)
 * - Batch email campaigns (send invitations)
 * - Dashboard stats (signups, activations, referrals)
 * - User analytics (usage data)
 */

import express from 'express';
import { verifyFirebaseToken } from '../middleware/auth.js';
import {
  sendBatchEmailStartedNotification,
  sendBatchEmailCompletedNotification,
  sendIndividualEmailSentNotification,
  sendDailyBetaDigestNotification,
} from '../services/slack.js';
import {
  sendInvitationEmail, sendReminderEmail, sendReferralNudgeEmail,
  generateInvitationHTML, generateReminderHTML, generateReferralNudgeHTML,
} from '../services/inviteEmail.js';
import admin from 'firebase-admin';

const router = express.Router();

// ─── Admin Middleware ────────────────────────────────────────────────────────

/**
 * Verify the user is an admin (has flags.isAdmin === true in Firestore)
 */
async function requireAdmin(req, res, next) {
  try {
    const uid = req.user?.uid;
    if (!uid) {
      return res.status(401).json({ error: 'Not authenticated' });
    }

    const db = admin.firestore();
    const userDoc = await db.collection('users').doc(uid).get();

    if (!userDoc.exists || !userDoc.data()?.flags?.isAdmin) {
      return res.status(403).json({ error: 'Admin access required' });
    }

    req.adminUser = userDoc.data();
    next();
  } catch (error) {
    console.error('[ADMIN] Auth check failed:', error);
    return res.status(500).json({ error: 'Failed to verify admin access' });
  }
}

// Apply both auth middlewares to all admin routes
router.use(verifyFirebaseToken, requireAdmin);

// ─── Waitlist Management ─────────────────────────────────────────────────────

/**
 * GET /admin/waitlist
 * 
 * List all waitlist entries with optional filters.
 * Query params: status, batch, limit, offset
 */
router.get('/waitlist', async (req, res) => {
  try {
    const db = admin.firestore();
    const { status, batch, limit: queryLimit } = req.query;
    const resultLimit = Math.min(parseInt(queryLimit) || 200, 500);

    let query = db.collection('waitlist').orderBy('timestamp', 'desc');

    // Note: Firestore doesn't support multiple inequality filters,
    // so we filter in-memory for complex queries
    const snapshot = await query.limit(resultLimit).get();

    let entries = snapshot.docs.map(doc => {
      const data = doc.data();
      return {
        email: doc.id,
        status: data.status || (data.trialActivated ? 'activated' : 'pending'),
        batch: data.batch || null,
        source: data.source || null,
        invitedAt: data.invitedAt?.toDate?.()?.toISOString() || null,
        activatedAt: data.activatedAt?.toDate?.()?.toISOString() || null,
        lastActiveAt: data.lastActiveAt?.toDate?.()?.toISOString() || null,
        timestamp: data.timestamp?.toDate?.()?.toISOString() || null,
        uid: data.uid || null,
        notes: data.notes || null,
        trialActivated: data.trialActivated || false,
        emailMessageId: data.emailMessageId || null,
      };
    });

    // Client-side filtering
    if (status) {
      entries = entries.filter(e => e.status === status);
    }
    if (batch) {
      entries = entries.filter(e => e.batch === parseInt(batch));
    }

    // Compute summary stats
    const stats = {
      total: entries.length,
      pending: entries.filter(e => e.status === 'pending').length,
      invited: entries.filter(e => e.status === 'invited').length,
      activated: entries.filter(e => e.status === 'activated' || e.trialActivated).length,
      active: entries.filter(e => e.status === 'active').length,
      churned: entries.filter(e => e.status === 'churned').length,
    };

    return res.json({ entries, stats });

  } catch (error) {
    console.error('[ADMIN] Error fetching waitlist:', error);
    return res.status(500).json({ error: 'Failed to fetch waitlist' });
  }
});

/**
 * PUT /admin/waitlist/:email/status
 * 
 * Update a waitlist entry's status or notes.
 */
router.put('/waitlist/:email/status', async (req, res) => {
  try {
    const { email } = req.params;
    const { status, notes, batch } = req.body;
    const db = admin.firestore();

    const safeEmail = decodeURIComponent(email).toLowerCase().trim();
    const waitlistRef = db.collection('waitlist').doc(safeEmail);
    const doc = await waitlistRef.get();

    if (!doc.exists) {
      return res.status(404).json({ error: 'Waitlist entry not found' });
    }

    const updates = {};
    if (status) updates.status = status;
    if (notes !== undefined) updates.notes = notes;
    if (batch !== undefined) updates.batch = batch;
    updates.updatedAt = admin.firestore.FieldValue.serverTimestamp();

    await waitlistRef.update(updates);

    return res.json({ success: true, email: safeEmail, updates });

  } catch (error) {
    console.error('[ADMIN] Error updating waitlist entry:', error);
    return res.status(500).json({ error: 'Failed to update waitlist entry' });
  }
});

// ─── Batch Email Campaigns ───────────────────────────────────────────────────

/**
 * POST /admin/email/send-batch
 * 
 * Send invitation emails to a list of waitlist emails.
 * Body: { emails: string[], template: 'invitation'|'reminder'|'referral_nudge', campaignName: string }
 */
router.post('/email/send-batch', async (req, res) => {
  try {
    const { emails, template = 'invitation', campaignName = 'Unnamed Campaign' } = req.body;

    if (!emails || !Array.isArray(emails) || emails.length === 0) {
      return res.status(400).json({ error: 'emails array is required' });
    }

    if (emails.length > 100) {
      return res.status(400).json({ error: 'Maximum 100 emails per batch' });
    }

    const db = admin.firestore();
    const adminEmail = req.adminUser.email || 'admin';

    // Create campaign record
    const campaignRef = await db.collection('email_campaigns').add({
      name: campaignName,
      status: 'sending',
      template,
      recipientCount: emails.length,
      sentCount: 0,
      failedCount: 0,
      recipients: emails,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      createdBy: adminEmail,
    });

    // Slack notification: campaign started
    sendBatchEmailStartedNotification(campaignName, emails.length, template, adminEmail).catch(console.error);

    const startTime = Date.now();
    let sentCount = 0;
    let failedCount = 0;
    const results = [];

    // Determine the next batch number
    const lastBatchSnapshot = await db.collection('waitlist')
      .orderBy('batch', 'desc')
      .limit(1)
      .get();
    const nextBatch = lastBatchSnapshot.empty
      ? 1
      : (lastBatchSnapshot.docs[0].data().batch || 0) + 1;

    // Send emails one by one with a delay
    for (const email of emails) {
      const safeEmail = email.toLowerCase().trim();

      try {
        let emailResult;

        if (template === 'invitation') {
          emailResult = await sendInvitationEmail(safeEmail);
        } else if (template === 'reminder') {
          // Get active user count for social proof
          const activeCount = await getActiveUserCount(db);
          emailResult = await sendReminderEmail(safeEmail, activeCount);
        } else if (template === 'referral_nudge') {
          // Look up user's referral code
          const userSnapshot = await db.collection('users')
            .where('email', '==', safeEmail)
            .limit(1)
            .get();
          const referralCode = userSnapshot.empty ? null : userSnapshot.docs[0].data()?.referral?.code;
          if (!referralCode) {
            results.push({ email: safeEmail, success: false, error: 'No referral code found' });
            failedCount++;
            continue;
          }
          emailResult = await sendReferralNudgeEmail(safeEmail, referralCode);
        } else {
          results.push({ email: safeEmail, success: false, error: `Unknown template: ${template}` });
          failedCount++;
          continue;
        }

        if (emailResult.success) {
          sentCount++;

          // Update waitlist entry
          const waitlistRef = db.collection('waitlist').doc(safeEmail);
          const waitlistDoc = await waitlistRef.get();
          if (waitlistDoc.exists) {
            const updateData = {
              updatedAt: admin.firestore.FieldValue.serverTimestamp(),
            };

            if (template === 'invitation') {
              updateData.status = 'invited';
              updateData.invitedAt = admin.firestore.FieldValue.serverTimestamp();
              updateData.batch = nextBatch;
              if (emailResult.messageId) {
                updateData.emailMessageId = emailResult.messageId;
              }
            }

            await waitlistRef.update(updateData);
          }

          results.push({ email: safeEmail, success: true, messageId: emailResult.messageId });

          // Slack: individual email sent
          sendIndividualEmailSentNotification(safeEmail, template, true, campaignName).catch(console.error);
        } else {
          failedCount++;
          results.push({ email: safeEmail, success: false, error: emailResult.error });

          // Slack: individual email failed
          sendIndividualEmailSentNotification(safeEmail, template, false, campaignName, emailResult.error).catch(console.error);
        }

        // 200ms delay between emails to avoid rate limits
        await new Promise(resolve => setTimeout(resolve, 200));

      } catch (error) {
        failedCount++;
        results.push({ email: safeEmail, success: false, error: error.message });
        console.error(`[ADMIN] Error sending to ${safeEmail}:`, error.message);

        // Slack: individual email exception
        sendIndividualEmailSentNotification(safeEmail, template, false, campaignName, error.message).catch(console.error);
      }
    }

    const durationMs = Date.now() - startTime;

    // Update campaign record
    await campaignRef.update({
      status: failedCount === emails.length ? 'failed' : 'sent',
      sentCount,
      failedCount,
      sentAt: admin.firestore.FieldValue.serverTimestamp(),
      durationMs,
    });

    // Slack notification: campaign completed
    sendBatchEmailCompletedNotification(campaignName, sentCount, failedCount, durationMs).catch(console.error);

    return res.json({
      success: true,
      campaignId: campaignRef.id,
      campaignName,
      batch: nextBatch,
      sentCount,
      failedCount,
      totalEmails: emails.length,
      durationMs,
      results,
    });

  } catch (error) {
    console.error('[ADMIN] Error sending batch emails:', error);
    return res.status(500).json({ error: 'Failed to send batch emails' });
  }
});

/**
 * GET /admin/email/campaigns
 * 
 * List all email campaigns.
 */
router.get('/email/campaigns', async (req, res) => {
  try {
    const db = admin.firestore();
    const snapshot = await db.collection('email_campaigns')
      .orderBy('createdAt', 'desc')
      .limit(50)
      .get();

    const campaigns = snapshot.docs.map(doc => {
      const data = doc.data();
      return {
        id: doc.id,
        name: data.name,
        status: data.status,
        template: data.template,
        recipientCount: data.recipientCount,
        sentCount: data.sentCount,
        failedCount: data.failedCount,
        createdAt: data.createdAt?.toDate?.()?.toISOString() || null,
        sentAt: data.sentAt?.toDate?.()?.toISOString() || null,
        createdBy: data.createdBy,
        durationMs: data.durationMs || null,
      };
    });

    return res.json({ campaigns });

  } catch (error) {
    console.error('[ADMIN] Error fetching campaigns:', error);
    return res.status(500).json({ error: 'Failed to fetch campaigns' });
  }
});

/**
 * GET /admin/email/preview/:template
 * 
 * Returns rendered HTML for a given email template.
 * Query params: email (sample recipient), referralCode (for referral templates)
 */
router.get('/email/preview/:template', async (req, res) => {
  try {
    const { template } = req.params;
    const sampleEmail = req.query.email || 'user@example.com';
    const sampleReferralCode = req.query.referralCode || 'TELOS-DEMO';

    let html;

    switch (template) {
      case 'invitation':
        html = generateInvitationHTML(sampleEmail);
        break;
      case 'reminder':
        html = generateReminderHTML(sampleEmail, 42);
        break;
      case 'referral_nudge':
        html = generateReferralNudgeHTML(sampleEmail, sampleReferralCode);
        break;
      default:
        return res.status(400).json({ error: `Unknown template: ${template}. Use invitation, reminder, or referral_nudge.` });
    }

    // Return raw HTML so it renders in a browser tab / iframe
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.send(html);

  } catch (error) {
    console.error('[ADMIN] Error generating email preview:', error);
    return res.status(500).json({ error: 'Failed to generate preview' });
  }
});

// ─── Dashboard Stats ─────────────────────────────────────────────────────────

/**
 * GET /admin/stats
 * 
 * Get dashboard overview stats.
 */
router.get('/stats', async (req, res) => {
  try {
    const db = admin.firestore();

    // Waitlist stats
    const waitlistSnapshot = await db.collection('waitlist').get();
    const waitlistEntries = waitlistSnapshot.docs.map(doc => doc.data());

    const waitlistStats = {
      total: waitlistEntries.length,
      pending: waitlistEntries.filter(e => !e.status || e.status === 'pending').length,
      invited: waitlistEntries.filter(e => e.status === 'invited').length,
      activated: waitlistEntries.filter(e => e.status === 'activated' || e.trialActivated).length,
    };

    // User stats
    const usersSnapshot = await db.collection('users').get();
    const users = usersSnapshot.docs.map(doc => doc.data());

    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const userStats = {
      total: users.length,
      trial: users.filter(u => u.accessStatus === 'trial').length,
      pro: users.filter(u => u.accessStatus === 'pro').length,
      expired: users.filter(u => u.accessStatus === 'expired').length,
      activeToday: users.filter(u => {
        const lastActive = u.lastActiveAt?.toDate?.();
        return lastActive && lastActive > oneDayAgo;
      }).length,
    };

    // Referral stats
    const referralsSnapshot = await db.collection('referrals').get();
    const referrals = referralsSnapshot.docs.map(doc => doc.data());

    const referralStats = {
      totalReferrals: referrals.length,
      activatedReferrals: referrals.filter(r => r.status === 'trial_active').length,
      proCreditsAwarded: referrals.filter(r => r.proCreditAwarded).length,
    };

    // Activation rate
    const activationRate = waitlistStats.invited > 0
      ? Math.round((waitlistStats.activated / (waitlistStats.invited + waitlistStats.activated)) * 100)
      : 0;

    // Campaign stats
    const campaignsSnapshot = await db.collection('email_campaigns')
      .orderBy('createdAt', 'desc')
      .limit(5)
      .get();
    const recentCampaigns = campaignsSnapshot.docs.map(doc => ({
      id: doc.id,
      name: doc.data().name,
      sentCount: doc.data().sentCount,
      createdAt: doc.data().createdAt?.toDate?.()?.toISOString(),
    }));

    return res.json({
      waitlist: waitlistStats,
      users: userStats,
      referrals: referralStats,
      activationRate,
      recentCampaigns,
    });

  } catch (error) {
    console.error('[ADMIN] Error fetching stats:', error);
    return res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

/**
 * GET /admin/users
 * 
 * List users with usage data.
 */
router.get('/users', async (req, res) => {
  try {
    const db = admin.firestore();
    const { limit: queryLimit, status: statusFilter } = req.query;
    const resultLimit = Math.min(parseInt(queryLimit) || 100, 200);

    let query = db.collection('users').orderBy('createdAt', 'desc');
    const snapshot = await query.limit(resultLimit).get();

    let users = snapshot.docs.map(doc => {
      const data = doc.data();
      return {
        uid: doc.id,
        email: data.email || null,
        accessStatus: data.accessStatus,
        mode: data.mode || 'unknown',
        createdAt: data.createdAt?.toDate?.()?.toISOString() || null,
        lastActiveAt: data.lastActiveAt?.toDate?.()?.toISOString() || null,
        trialEndDate: data.trial?.endDate?.toDate?.()?.toISOString() || null,
        referralCode: data.referral?.code || null,
        referralCount: data.referral?.referralCount || 0,
        proCreditsEarned: data.referral?.proCreditsEarned || 0,
        emailReportsEnabled: data.emailReports?.enabled || false,
        hasFlags: data.flags ? {
          isAdmin: data.flags.isAdmin || false,
          isBeta: data.flags.isBeta || false,
        } : null,
      };
    });

    if (statusFilter) {
      users = users.filter(u => u.accessStatus === statusFilter);
    }

    return res.json({ users, total: users.length });

  } catch (error) {
    console.error('[ADMIN] Error fetching users:', error);
    return res.status(500).json({ error: 'Failed to fetch users' });
  }
});

/**
 * GET /admin/referrals
 * 
 * List all referrals with details.
 */
router.get('/referrals', async (req, res) => {
  try {
    const db = admin.firestore();

    const snapshot = await db.collection('referrals')
      .orderBy('createdAt', 'desc')
      .limit(100)
      .get();

    const referrals = snapshot.docs.map(doc => {
      const data = doc.data();
      return {
        id: doc.id,
        referrerEmail: data.referrerEmail || null,
        refereeEmail: data.refereeEmail || null,
        referralCode: data.referralCode,
        status: data.status,
        proCreditAwarded: data.proCreditAwarded || false,
        createdAt: data.createdAt?.toDate?.()?.toISOString() || null,
      };
    });

    // Top referrers
    const referrerCounts = {};
    referrals.forEach(r => {
      if (r.referrerEmail) {
        referrerCounts[r.referrerEmail] = (referrerCounts[r.referrerEmail] || 0) + 1;
      }
    });
    const topReferrers = Object.entries(referrerCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([email, count]) => ({ email, count }));

    return res.json({
      referrals,
      topReferrers,
      totalReferrals: referrals.length,
      activatedReferrals: referrals.filter(r => r.status === 'trial_active').length,
      creditsAwarded: referrals.filter(r => r.proCreditAwarded).length,
    });

  } catch (error) {
    console.error('[ADMIN] Error fetching referrals:', error);
    return res.status(500).json({ error: 'Failed to fetch referrals' });
  }
});

/**
 * POST /admin/digest
 * 
 * Manually trigger the daily beta digest Slack notification.
 */
router.post('/digest', async (req, res) => {
  try {
    const db = admin.firestore();

    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    // Gather stats
    const usersSnapshot = await db.collection('users').get();
    const users = usersSnapshot.docs.map(doc => doc.data());

    const waitlistSnapshot = await db.collection('waitlist').get();
    const waitlistEntries = waitlistSnapshot.docs.map(doc => doc.data());

    const referralsSnapshot = await db.collection('referrals').get();
    const referrals = referralsSnapshot.docs.map(doc => doc.data());

    // Calculate metrics
    const newSignupsToday = users.filter(u => {
      const created = u.createdAt?.toDate?.();
      return created && created > oneDayAgo;
    }).length;

    const activeUsers24h = users.filter(u => {
      const lastActive = u.lastActiveAt?.toDate?.();
      return lastActive && lastActive > oneDayAgo;
    }).length;

    const waitlistRemaining = waitlistEntries.filter(e =>
      !e.status || e.status === 'pending'
    ).length;

    const totalInvited = waitlistEntries.filter(e =>
      e.status === 'invited' || e.status === 'activated' || e.status === 'active'
    ).length;
    const totalActivated = waitlistEntries.filter(e =>
      e.status === 'activated' || e.status === 'active' || e.trialActivated
    ).length;
    const activationRate = totalInvited > 0
      ? Math.round((totalActivated / totalInvited) * 100)
      : 0;

    const referralsToday = referrals.filter(r => {
      const created = r.createdAt?.toDate?.();
      return created && created > oneDayAgo;
    });

    const stats = {
      newSignupsToday,
      activeUsers24h,
      referralCodesShared: 0, // Would need tracking; approximate for now
      referralsActivated: referralsToday.filter(r => r.status === 'trial_active').length,
      waitlistRemaining,
      activationRate,
      proCreditsAwardedToday: referralsToday.filter(r => r.proCreditAwarded).length,
    };

    await sendDailyBetaDigestNotification(stats);

    return res.json({ success: true, stats });

  } catch (error) {
    console.error('[ADMIN] Error sending digest:', error);
    return res.status(500).json({ error: 'Failed to send digest' });
  }
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function getActiveUserCount(db) {
  try {
    const snapshot = await db.collection('users')
      .where('accessStatus', 'in', ['trial', 'pro'])
      .get();
    return snapshot.size;
  } catch {
    return 0;
  }
}

export default router;
