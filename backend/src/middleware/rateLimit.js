/**
 * Rate Limiting Middleware (Firestore-based)
 *
 * Tracks and enforces rate limits per user (uid):
 * - 100 requests per hour
 * - 2000 requests per day
 *
 * Stores counters in Firestore for distributed rate limiting.
 */

import { getFirestore } from '../config/firebase.js';
import { monitorQuotaUsage } from '../services/monitoring.js';

/**
 * Get current hour and day timestamps for bucketing
 */
function getTimeBuckets() {
  const now = new Date();
  
  // Hour bucket: "2025-01-02T10" (truncate to hour)
  const hourBucket = now.toISOString().slice(0, 13);
  
  // Day bucket: "2025-01-02" (truncate to day)
  const dayBucket = now.toISOString().slice(0, 10);
  
  return { hourBucket, dayBucket };
}

/**
 * Get seconds until next hour
 */
function getSecondsUntilNextHour() {
  const now = new Date();
  const nextHour = new Date(now);
  nextHour.setHours(now.getHours() + 1, 0, 0, 0);
  return Math.floor((nextHour - now) / 1000);
}

/**
 * Get seconds until next day (midnight UTC)
 */
function getSecondsUntilNextDay() {
  const now = new Date();
  const nextDay = new Date(now);
  nextDay.setUTCDate(now.getUTCDate() + 1);
  nextDay.setUTCHours(0, 0, 0, 0);
  return Math.floor((nextDay - now) / 1000);
}

/**
 * Rate limiting middleware
 * 
 * Requires: req.user.uid (from auth middleware)
 * 
 * Checks both hourly and daily limits. Returns 429 if exceeded.
 */
export async function rateLimitMiddleware(req, res, next) {
  // Ensure user is authenticated (should be called after auth middleware)
  if (!req.user || !req.user.uid) {
    return res.status(401).json({
      error: 'AuthenticationError',
      message: 'User must be authenticated for rate limiting',
      code: 'AUTH_REQUIRED',
    });
  }

  const uid = req.user.uid;
  const { hourBucket, dayBucket } = getTimeBuckets();

  // Get rate limit config from env
  const hourlyLimit = parseInt(process.env.RATE_LIMIT_PER_HOUR || '100', 10);
  const dailyLimit = parseInt(process.env.RATE_LIMIT_PER_DAY || '2000', 10);

  try {
    const db = getFirestore();
    const usageRef = db.collection('usage').doc(uid);

    // Use transaction for atomic read-modify-write
    const result = await db.runTransaction(async (transaction) => {
      const usageDoc = await transaction.get(usageRef);
      
      let hourlyCount = 0;
      let dailyCount = 0;

      if (usageDoc.exists) {
        const data = usageDoc.data();
        
        // Get counts for current buckets (reset if bucket changed)
        if (data.hourBucket === hourBucket) {
          hourlyCount = data.hourlyCount || 0;
        }
        if (data.dayBucket === dayBucket) {
          dailyCount = data.dailyCount || 0;
        }
      }

      // Check limits BEFORE incrementing
      if (hourlyCount >= hourlyLimit) {
        return {
          limited: true,
          type: 'hourly',
          retryAfter: getSecondsUntilNextHour(),
        };
      }

      if (dailyCount >= dailyLimit) {
        return {
          limited: true,
          type: 'daily',
          retryAfter: getSecondsUntilNextDay(),
        };
      }

      // Increment counters
      const newData = {
        hourBucket,
        hourlyCount: hourlyCount + 1,
        dayBucket,
        dailyCount: dailyCount + 1,
        lastRequestAt: new Date(),
      };

      transaction.set(usageRef, newData, { merge: true });

      return {
        limited: false,
        hourlyCount: hourlyCount + 1,
        dailyCount: dailyCount + 1,
      };
    });

    // If rate limited, return 429
    if (result.limited) {
      const message = result.type === 'hourly'
        ? `Rate limit exceeded. Try again in ${result.retryAfter} seconds.`
        : `Daily rate limit exceeded. Try again in ${result.retryAfter} seconds.`;

      // Monitor rate limit hits (only for daily limit)
      if (result.type === 'daily') {
        monitorQuotaUsage(uid, dailyLimit, dailyLimit).catch(console.error);
      }

      return res.status(429).json({
        error: 'RateLimitError',
        message,
        retry_after: result.retryAfter,
        code: 'RATE_LIMIT_EXCEEDED',
      });
    }

    // Monitor users approaching their quota (at 80% and 90%)
    const dailyUsagePercent = (result.dailyCount / dailyLimit) * 100;
    if (dailyUsagePercent >= 80) {
      monitorQuotaUsage(uid, result.dailyCount, dailyLimit).catch(console.error);
    }

    // Add rate limit headers to response
    res.set({
      'X-RateLimit-Limit': hourlyLimit.toString(),
      'X-RateLimit-Remaining': (hourlyLimit - result.hourlyCount).toString(),
      'X-RateLimit-Reset': Math.floor(Date.now() / 1000 + getSecondsUntilNextHour()).toString(),
    });

    // Continue to next middleware
    next();
  } catch (error) {
    console.error('Rate limit check failed:', error);
    
    // On Firestore error, fail open (allow request) but log error
    // Better to allow one request through than block legitimate users
    console.warn(`⚠️  Rate limit check failed for user ${uid}, allowing request`);
    next();
  }
}

export default rateLimitMiddleware;


