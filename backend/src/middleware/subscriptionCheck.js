/**
 * Subscription Check Middleware
 * 
 * Verifies that the authenticated user has an active subscription (trial or pro)
 * before allowing access to protected routes like /analyze.
 * 
 * Must be used AFTER verifyFirebaseToken middleware (requires req.user).
 */

import admin from 'firebase-admin';

/**
 * Check if user has active access (trial or pro).
 * 
 * Returns 403 if:
 *   - User document not found
 *   - accessStatus is 'expired'
 *   - Trial has expired (by date check)
 * 
 * Allows through if:
 *   - accessStatus is 'pro'
 *   - accessStatus is 'trial' and trial hasn't expired
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

    // Explicitly expired users are blocked
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

    // Unknown status -- allow through with warning (fail open for safety during beta)
    console.warn(`[SUBSCRIPTION] Unknown accessStatus '${accessStatus}' for user ${uid}`);
    req.accessStatus = accessStatus || 'unknown';
    next();

  } catch (error) {
    // On error, log and allow through (fail open during beta to avoid blocking paying users)
    console.error('[SUBSCRIPTION] Check failed:', error.message);
    req.accessStatus = 'error';
    next();
  }
}

export default requireActiveSubscription;
