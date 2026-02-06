/**
 * Authentication routes for user management
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import { verifyFirebaseToken } from '../middleware/auth.js';
import {
  sendSignupNotification,
  sendTrialActivationNotification,
  sendPaymentIntentNotification,
  sendReferralLinkUsedNotification,
  sendReferralActivatedNotification,
} from '../services/slack.js';
import admin from 'firebase-admin';
import betaUsers from '../config/beta_users.js';
import { MAX_REFERRAL_CREDITS } from './referral.js';

const router = express.Router();

// IP-based rate limiter for auth endpoints (stricter than API rate limit)
const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 30, // 30 requests per 15 minutes per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    error: 'RateLimitError',
    message: 'Too many requests from this IP. Please try again later.',
    code: 'IP_RATE_LIMIT_EXCEEDED',
  },
});

// Apply rate limiter to all auth routes
router.use(authRateLimiter);

/**
 * POST /auth/link-email
 * ... (existing endpoints unchanged)
 */
// (I will keep the existing endpoints and append mine)

// ... [Previous code for link-email and status]

// RE-IMPLEMENTING FULL FILE with new routes appended for clarity and correctness

/**
 * POST /auth/link-email
 * 
 * Convert anonymous account to email-based account
 */
router.post('/link-email', verifyFirebaseToken, async (req, res) => {
  try {
    const { email, password, mode } = req.body;
    const uid = req.user.uid;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({
        error: 'Email and password are required'
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        error: 'Invalid email format'
      });
    }

    // Validate password strength
    if (password.length < 8) {
      return res.status(400).json({
        error: 'Password must be at least 8 characters'
      });
    }

    // Check if user is anonymous
    const userRecord = await admin.auth().getUser(uid);

    if (!userRecord.providerData || userRecord.providerData.length === 0) {
      // User is anonymous, proceed with linking

      // Update user with email and password
      const updatedUser = await admin.auth().updateUser(uid, {
        email: email,
        password: password,
        emailVerified: false
      });

      // Log the conversion
      console.log(`[AUTH] Anonymous user ${uid} linked to email: ${email}`);

      // Send Slack notification (non-blocking) — includes user mode
      sendSignupNotification({
        uid: updatedUser.uid,
        email: updatedUser.email,
        createdAt: updatedUser.metadata.creationTime
      }, mode || 'unknown').catch(err => console.error('[SLACK] Failed to send signup notification:', err));

      // Return updated user info
      return res.json({
        success: true,
        user: {
          uid: updatedUser.uid,
          email: updatedUser.email,
          emailVerified: updatedUser.emailVerified,
          isAnonymous: false,
          createdAt: updatedUser.metadata.creationTime,
          lastSignIn: updatedUser.metadata.lastSignInTime
        }
      });

    } else {
      // User already has providers (not anonymous)
      return res.status(400).json({
        error: 'User account is not anonymous or already has email linked'
      });
    }

  } catch (error) {
    console.error('[AUTH] Error linking email:', error);

    // Handle specific Firebase errors
    if (error.code === 'auth/email-already-exists') {
      return res.status(409).json({
        error: 'Email already in use by another account'
      });
    }

    if (error.code === 'auth/invalid-email') {
      return res.status(400).json({
        error: 'Invalid email address'
      });
    }

    if (error.code === 'auth/weak-password') {
      return res.status(400).json({
        error: 'Password is too weak'
      });
    }

    // Generic error
    return res.status(500).json({
      error: 'Failed to link email to account',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * GET /auth/status
 * 
 * Get current user authentication status
 */
router.get('/status', verifyFirebaseToken, async (req, res) => {
  try {
    const uid = req.user.uid;
    const userRecord = await admin.auth().getUser(uid);

    const isAnonymous = !userRecord.providerData || userRecord.providerData.length === 0;

    return res.json({
      uid: userRecord.uid,
      email: userRecord.email || null,
      isAnonymous: isAnonymous,
      emailVerified: userRecord.emailVerified || false,
      createdAt: userRecord.metadata.creationTime,
      lastSignIn: userRecord.metadata.lastSignInTime
    });

  } catch (error) {
    console.error('[AUTH] Error getting user status:', error);
    return res.status(500).json({
      error: 'Failed to get user status'
    });
  }
});

/**
 * POST /auth/verify-access
 * 
 * Verify if email is in whitelist and start trial.
 * 
 * Request: { email: "user@example.com" }
 */
router.post('/verify-access', verifyFirebaseToken, async (req, res) => {
  try {
    const { email, mode, referralCode } = req.body;
    const uid = req.user.uid;
    const userMode = mode || 'unknown';

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    const safeEmail = email.toLowerCase().trim();

    // Beta access: Allow all signups (whitelist removed for launch)
    console.log(`[AUTH] Processing trial activation for: ${safeEmail}${referralCode ? ` (referral: ${referralCode})` : ''}`);

    // 2. Fetch or Create User Document (keyed by UID for anonymity)
    const db = admin.firestore();
    const userRef = db.collection('users').doc(uid);
    const userDoc = await userRef.get();

    let accessStatus = 'trial'; // Default for new users
    let trialStartDate = new Date();

    // Determine trial duration: 14 days for waitlist/referral users, 7 for others
    const waitlistRef = db.collection('waitlist').doc(safeEmail);
    const waitlistDoc = await waitlistRef.get();
    const isWaitlistUser = waitlistDoc.exists;
    const hasReferral = referralCode && referralCode.startsWith('TELOS-');
    const trialDays = (isWaitlistUser || hasReferral) ? 14 : 7;

    let trialEndDate = new Date();
    trialEndDate.setDate(trialEndDate.getDate() + trialDays);

    if (userDoc.exists) {
      const userData = userDoc.data();
      accessStatus = userData.accessStatus;

      // If already expired, don't restart trial
      if (accessStatus === 'expired') {
        return res.status(403).json({
          error: 'Trial Expired',
          message: 'Your trial period has ended. Please upgrade to continue.',
          accessStatus: 'expired'
        });
      }

      // If exists but no trial info (legacy), backfill
      if (!userData.trial) {
        await userRef.update({
          accessStatus: 'trial',
          trial: {
            activatedAt: admin.firestore.FieldValue.serverTimestamp(),
            startDate: admin.firestore.Timestamp.fromDate(trialStartDate),
            endDate: admin.firestore.Timestamp.fromDate(trialEndDate),
            isActive: true,
            extendedTrial: trialDays === 14,
          }
        });
        // Send Slack Notification for Backfill/New Activation
        sendTrialActivationNotification(safeEmail, trialStartDate);
      } else {
        // Return existing trial info
        trialEndDate = userData.trial.endDate.toDate();
        trialStartDate = userData.trial.startDate.toDate();
      }

    } else {
      // New User - Create Record (includes mode for analytics)
      const newUserData = {
        email: safeEmail,
        uid: uid,
        accessStatus: 'trial',
        mode: userMode,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastActiveAt: admin.firestore.FieldValue.serverTimestamp(),
        trial: {
          activatedAt: admin.firestore.FieldValue.serverTimestamp(),
          startDate: admin.firestore.Timestamp.fromDate(trialStartDate),
          endDate: admin.firestore.Timestamp.fromDate(trialEndDate),
          isActive: true,
          extendedTrial: trialDays === 14,
        },
        paymentIntent: {
          hasRequestedUpgrade: false,
          requestCount: 0
        },
        referral: {
          referredBy: null,
          code: null,
          referralCount: 0,
          proCreditsEarned: 0,
          proCreditsUsed: 0,
        },
      };

      // Handle referral code if provided
      if (hasReferral) {
        const referrerSnapshot = await db.collection('users')
          .where('referral.code', '==', referralCode.toUpperCase())
          .limit(1)
          .get();

        if (!referrerSnapshot.empty) {
          const referrerDoc = referrerSnapshot.docs[0];
          const referrerData = referrerDoc.data();
          const referrerUid = referrerDoc.id;
          const referrerEmail = referrerData.email || 'unknown';

          // Set referredBy on new user
          newUserData.referral.referredBy = referralCode.toUpperCase();

          // Create referral record
          await db.collection('referrals').add({
            referrerUid,
            referrerEmail,
            refereeUid: uid,
            refereeEmail: safeEmail,
            referralCode: referralCode.toUpperCase(),
            status: 'trial_active',
            proCreditAwarded: false,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
          });

          // Award Pro credit to referrer (if under cap)
          const currentCredits = referrerData.referral?.proCreditsEarned || 0;
          if (currentCredits < MAX_REFERRAL_CREDITS) {
            const newCredits = currentCredits + 1;
            await db.collection('users').doc(referrerUid).update({
              'referral.referralCount': admin.firestore.FieldValue.increment(1),
              'referral.proCreditsEarned': admin.firestore.FieldValue.increment(1),
            });

            // Mark the referral as credit-awarded
            const referralDocs = await db.collection('referrals')
              .where('referrerUid', '==', referrerUid)
              .where('refereeUid', '==', uid)
              .limit(1)
              .get();
            if (!referralDocs.empty) {
              await referralDocs.docs[0].ref.update({ proCreditAwarded: true });
            }

            // Slack: referral activated with credit
            sendReferralActivatedNotification(referrerEmail, safeEmail, referralCode.toUpperCase(), newCredits).catch(console.error);
          } else {
            // Just count the referral but don't award credit (cap reached)
            await db.collection('users').doc(referrerUid).update({
              'referral.referralCount': admin.firestore.FieldValue.increment(1),
            });

            // Slack: referral used, but notify about cap
            sendReferralLinkUsedNotification(referralCode.toUpperCase(), referrerEmail, safeEmail).catch(console.error);
          }
        } else {
          console.warn(`[AUTH] Referral code ${referralCode} not found, ignoring`);
        }
      }

      await userRef.set(newUserData);

      // Update Waitlist Entry if it exists
      if (isWaitlistUser) {
        await waitlistRef.update({
          trialActivated: true,
          status: 'activated',
          activatedAt: admin.firestore.FieldValue.serverTimestamp(),
          uid: uid,
          trialStartDate: admin.firestore.FieldValue.serverTimestamp(),
        });
      }

      // Send Slack Notification with mode
      sendTrialActivationNotification(safeEmail, trialStartDate, userMode);
    }

    return res.json({
      access: true,
      accessStatus: accessStatus,
      trialStartDate: trialStartDate.toISOString(),
      trialEndDate: trialEndDate.toISOString(),
      trialDays,
      extendedTrial: trialDays === 14,
    });

  } catch (error) {
    console.error('[AUTH] Error verifying access:', error);
    return res.status(500).json({ error: 'Failed to verify access' });
  }
});

/**
 * POST /auth/record-payment-intent
 * 
 * Log that user wants to upgrade to Pro.
 */
router.post('/record-payment-intent', verifyFirebaseToken, async (req, res) => {
  try {
    const uid = req.user.uid;
    // We need email, but we can look it up from UID or pass it in.
    // Better to look up to rely on trusted source.
    // But for speed, let's assume client passes it or we get it from auth token.
    // Wait, anonymous auth doesn't have email in token usually.
    // We will pass email in body for now, trusting the client context.
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email required' });
    }

    const db = admin.firestore();
    const userRef = db.collection('users').doc(uid);

    // Use set with merge to create if missing (though they should be in trial)
    await userRef.set({
      email: email.toLowerCase().trim(),
      paymentIntent: {
        hasRequestedUpgrade: true,
        requestedAt: admin.firestore.FieldValue.serverTimestamp(),
        requestCount: admin.firestore.FieldValue.increment(1)
      }
    }, { merge: true });

    // Notification
    console.log(`[AUTH] Attempting Slack notification for payment intent: ${email}`);
    const slackResult = await sendPaymentIntentNotification(email);
    console.log(`[AUTH] Slack notification result:`, slackResult);

    return res.json({
      success: true,
      message: 'Intent recorded',
      slack_notified: slackResult.success
    });

  } catch (error) {
    console.error('[AUTH] Error recording payment intent:', error);
    return res.status(500).json({ error: 'Failed to record intent' });
  }
});

export default router;
