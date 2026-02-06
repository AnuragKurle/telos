/**
 * Referral System Routes
 * 
 * Handles referral code generation, validation, and stats.
 * Each user gets a unique TELOS-XXXX code they can share.
 * Successful referrals earn 1 month of free Pro access.
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import { verifyFirebaseToken } from '../middleware/auth.js';
import { sendReferralCodeCopiedNotification } from '../services/slack.js';
import admin from 'firebase-admin';
import crypto from 'crypto';

const router = express.Router();

// Frontend URL for referral share links (reads from FRONTEND_URL secret mounted in Cloud Run)
const FRONTEND_BASE_URL = (process.env.FRONTEND_URL || 'https://gen-lang-client-0772617718.web.app').replace(/\/$/, '');

// Strict rate limiter for the public referral validation endpoint (prevents brute-force)
const referralValidationLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20, // 20 attempts per 15 minutes per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    error: 'RateLimitError',
    message: 'Too many referral validation attempts. Please try again later.',
    code: 'IP_RATE_LIMIT_EXCEEDED',
  },
});

// Max referral credits a user can earn (12 months)
const MAX_REFERRAL_CREDITS = 12;

/**
 * Generate a unique referral code in format TELOS-XXXX
 */
function generateReferralCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Removed ambiguous chars (0, O, 1, I)
  let code = '';
  const bytes = crypto.randomBytes(4);
  for (let i = 0; i < 4; i++) {
    code += chars[bytes[i] % chars.length];
  }
  return `TELOS-${code}`;
}

/**
 * GET /referral/code
 * 
 * Get or generate the authenticated user's referral code.
 * Returns the code and a shareable link.
 * Also fires a Slack notification for observability.
 */
router.get('/code', verifyFirebaseToken, async (req, res) => {
  try {
    const uid = req.user.uid;
    const db = admin.firestore();
    const userRef = db.collection('users').doc(uid);
    const userDoc = await userRef.get();

    if (!userDoc.exists) {
      return res.status(404).json({ error: 'User not found. Please activate your trial first.' });
    }

    const userData = userDoc.data();
    let referralCode = userData.referral?.code;

    // Generate code if user doesn't have one yet
    if (!referralCode) {
      // Generate and check uniqueness
      let attempts = 0;
      let isUnique = false;

      while (!isUnique && attempts < 10) {
        referralCode = generateReferralCode();
        // Check if code exists
        const existing = await db.collection('users')
          .where('referral.code', '==', referralCode)
          .limit(1)
          .get();
        isUnique = existing.empty;
        attempts++;
      }

      if (!isUnique) {
        return res.status(500).json({ error: 'Failed to generate unique referral code. Try again.' });
      }

      // Save the code
      await userRef.update({
        'referral.code': referralCode,
        'referral.referralCount': userData.referral?.referralCount || 0,
        'referral.proCreditsEarned': userData.referral?.proCreditsEarned || 0,
        'referral.proCreditsUsed': userData.referral?.proCreditsUsed || 0,
      });
    }

    const shareLink = `${FRONTEND_BASE_URL}/?ref=${referralCode}`;

    // Slack notification (non-blocking)
    const userEmail = userData.email || 'unknown';
    sendReferralCodeCopiedNotification(userEmail, referralCode).catch(err =>
      console.error('[SLACK] Failed to send referral code copied notification:', err)
    );

    return res.json({
      referralCode,
      shareLink,
      stats: {
        referralCount: userData.referral?.referralCount || 0,
        proCreditsEarned: userData.referral?.proCreditsEarned || 0,
        proCreditsUsed: userData.referral?.proCreditsUsed || 0,
        proCreditsRemaining: Math.max(0, (userData.referral?.proCreditsEarned || 0) - (userData.referral?.proCreditsUsed || 0)),
        maxCredits: MAX_REFERRAL_CREDITS,
      }
    });

  } catch (error) {
    console.error('[REFERRAL] Error getting referral code:', error);
    return res.status(500).json({ error: 'Failed to get referral code' });
  }
});

/**
 * GET /referral/stats
 * 
 * Get referral statistics for the authenticated user.
 */
router.get('/stats', verifyFirebaseToken, async (req, res) => {
  try {
    const uid = req.user.uid;
    const db = admin.firestore();
    const userDoc = await db.collection('users').doc(uid).get();

    if (!userDoc.exists) {
      return res.status(404).json({ error: 'User not found' });
    }

    const userData = userDoc.data();
    const referral = userData.referral || {};

    // Get individual referral records
    const referralsSnapshot = await db.collection('referrals')
      .where('referrerUid', '==', uid)
      .orderBy('createdAt', 'desc')
      .limit(50)
      .get();

    const referrals = referralsSnapshot.docs.map(doc => {
      const data = doc.data();
      return {
        id: doc.id,
        refereeEmail: data.refereeEmail ? maskEmail(data.refereeEmail) : 'unknown',
        status: data.status,
        proCreditAwarded: data.proCreditAwarded || false,
        createdAt: data.createdAt?.toDate?.()?.toISOString() || null,
      };
    });

    return res.json({
      referralCode: referral.code || null,
      shareLink: referral.code ? `${FRONTEND_BASE_URL}/?ref=${referral.code}` : null,
      referredBy: referral.referredBy || null,
      stats: {
        referralCount: referral.referralCount || 0,
        proCreditsEarned: referral.proCreditsEarned || 0,
        proCreditsUsed: referral.proCreditsUsed || 0,
        proCreditsRemaining: Math.max(0, (referral.proCreditsEarned || 0) - (referral.proCreditsUsed || 0)),
        maxCredits: MAX_REFERRAL_CREDITS,
      },
      referrals,
    });

  } catch (error) {
    console.error('[REFERRAL] Error getting referral stats:', error);
    return res.status(500).json({ error: 'Failed to get referral stats' });
  }
});

/**
 * POST /referral/validate/:code
 * 
 * Validate a referral code exists and return info.
 * Called during signup when a user arrives via referral link.
 * No auth required (user hasn't signed up yet).
 * Rate-limited to prevent brute-force enumeration of codes.
 */
router.post('/validate/:code', referralValidationLimiter, async (req, res) => {
  try {
    const { code } = req.params;

    if (!code || !code.startsWith('TELOS-')) {
      return res.status(400).json({ error: 'Invalid referral code format' });
    }

    const db = admin.firestore();
    const usersSnapshot = await db.collection('users')
      .where('referral.code', '==', code.toUpperCase())
      .limit(1)
      .get();

    if (usersSnapshot.empty) {
      return res.status(404).json({ error: 'Referral code not found', valid: false });
    }

    const referrerData = usersSnapshot.docs[0].data();

    return res.json({
      valid: true,
      referralCode: code.toUpperCase(),
      referrerHint: referrerData.email ? maskEmail(referrerData.email) : 'a Telos user',
    });

  } catch (error) {
    console.error('[REFERRAL] Error validating referral code:', error);
    return res.status(500).json({ error: 'Failed to validate referral code' });
  }
});

/**
 * Mask an email for privacy (e.g., "alice@example.com" -> "al***@example.com")
 */
function maskEmail(email) {
  if (!email || !email.includes('@')) return '***';
  const [local, domain] = email.split('@');
  const masked = local.length > 2
    ? local.substring(0, 2) + '***'
    : local[0] + '***';
  return `${masked}@${domain}`;
}

export { MAX_REFERRAL_CREDITS };
export default router;
