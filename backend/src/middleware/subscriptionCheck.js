/**
 * Subscription Check Middleware
 * 
 * Verifies that the authenticated user has an active subscription (trial or pro)
 * before allowing access to protected routes like /analyze.
 * 
 * Now also checks referral Pro credits: if a user has unused credits,
 * they get Pro access even if their trial has expired.
 * 
 * Must be used AFTER verifyFirebaseToken middleware (requires req.user).
 */

import admin from 'firebase-admin';
import { sendProCreditAppliedNotification } from '../services/slack.js';

/**
 * Check if user has active access (trial, pro, or referral credits).
 * 
 * Returns 403 if:
 *   - User document not found
 *   - accessStatus is 'expired' AND no referral credits remaining
 *   - Trial has expired AND no referral credits remaining
 * 
 * Allows through if:
 *   - accessStatus is 'pro'
 *   - accessStatus is 'trial' and trial hasn't expired
 *   - User has unused referral Pro credits (proCreditsEarned > proCreditsUsed)
 */
export async function requireActiveSubscription(req, res, next) {
  try {
    const uid = req.user?.uid;
    
    if (!uid) {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'User not authenticated',
        code: 'NOT_AUTHENTICATED',
      });
    }

    const db = admin.firestore();
    const userRef = db.collection('users').doc(uid);
    const userDoc = await userRef.get();

    if (!userDoc.exists) {
      // No user document -- they haven't activated yet
      return res.status(403).json({
        error: 'SubscriptionError',
        message: 'No active subscription. Please activate your trial.',
        code: 'NO_SUBSCRIPTION',
        accessStatus: 'none',
      });
    }

    const userData = userDoc.data();
    const accessStatus = userData.accessStatus;

    // Pro users always pass through
    if (accessStatus === 'pro') {
      req.accessStatus = 'pro';
      return next();
    }

    // Check for referral Pro credits (works for any status including expired)
    const referral = userData.referral || {};
    const creditsEarned = referral.proCreditsEarned || 0;
    const creditsUsed = referral.proCreditsUsed || 0;
    const creditsRemaining = creditsEarned - creditsUsed;

    if (creditsRemaining > 0) {
      // User has referral credits — grant Pro access
      req.accessStatus = 'pro_referral';

      // Slack notification (non-blocking, rate-limited by caller)
      const userEmail = userData.email || 'unknown';
      sendProCreditAppliedNotification(userEmail, creditsRemaining).catch(err =>
        console.error('[SLACK] Failed to send pro credit applied notification:', err)
      );

      return next();
    }

    // Explicitly expired users are blocked (no credits left)
    if (accessStatus === 'expired') {
      return res.status(403).json({
        error: 'SubscriptionError',
        message: 'Trial expired. Upgrade to Pro to continue.',
        code: 'TRIAL_EXPIRED',
        accessStatus: 'expired',
      });
    }

    // For trial users, verify the trial hasn't expired by date
    if (accessStatus === 'trial') {
      const trial = userData.trial;
      if (trial && trial.endDate) {
        const endDate = trial.endDate.toDate ? trial.endDate.toDate() : new Date(trial.endDate);
        if (endDate < new Date()) {
          // Trial expired -- update status in Firestore and reject
          await userRef.update({
            accessStatus: 'expired',
            'trial.isActive': false,
          });

          return res.status(403).json({
            error: 'SubscriptionError',
            message: 'Trial expired. Upgrade to Pro to continue.',
            code: 'TRIAL_EXPIRED',
            accessStatus: 'expired',
          });
        }
      }

      // Trial is still active
      req.accessStatus = 'trial';
      return next();
    }

    // Unknown status -- block by default (fail closed)
    console.warn(`[SUBSCRIPTION] Unknown accessStatus '${accessStatus}' for user ${uid}, blocking request`);
    return res.status(403).json({
      error: 'SubscriptionError',
      message: 'Unable to verify subscription status. Please contact support.',
      code: 'UNKNOWN_STATUS',
      accessStatus: accessStatus || 'unknown',
    });

  } catch (error) {
    // Fail closed: block the request when we can't verify subscription
    console.error('[SUBSCRIPTION] Check failed:', error.message);
    return res.status(503).json({
      error: 'ServiceError',
      message: 'Unable to verify subscription status. Please try again shortly.',
      code: 'SUBSCRIPTION_CHECK_FAILED',
    });
  }
}

export default requireActiveSubscription;
