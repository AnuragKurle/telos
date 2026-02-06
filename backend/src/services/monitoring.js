/**
 * Monitoring Service with Slack Alerts
 *
 * Monitors application health, errors, and critical events.
 * Sends alerts to Slack for important issues.
 */

import axios from 'axios';
import { captureException, captureMessage } from './sentry.js';

// Rate limiting for alerts (prevent spam)
const alertCache = new Map();
const ALERT_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Alert severity levels
 */
export const AlertSeverity = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
};

/**
 * Alert categories
 */
export const AlertCategory = {
  ERROR: 'error',
  PERFORMANCE: 'performance',
  SECURITY: 'security',
  AVAILABILITY: 'availability',
  BUSINESS: 'business',
};

/**
 * Send alert to Slack
 *
 * @param {object} alert - Alert object
 * @returns {Promise<boolean>} Success status
 */
export async function sendSlackAlert(alert) {
  const webhookUrl = process.env.SLACK_ALERTS_WEBHOOK;

  if (!webhookUrl) {
    console.log('[MONITORING] Slack webhook not configured, skipping alert');
    return false;
  }

  // Check rate limiting
  const cacheKey = `${alert.category}:${alert.title}`;
  const lastSent = alertCache.get(cacheKey);
  const now = Date.now();

  if (lastSent && now - lastSent < ALERT_COOLDOWN_MS) {
    console.log(`[MONITORING] Alert rate limited: ${alert.title}`);
    return false;
  }

  // Determine color based on severity
  const colors = {
    [AlertSeverity.INFO]: '#36a64f',      // green
    [AlertSeverity.WARNING]: '#ff9800',   // orange
    [AlertSeverity.ERROR]: '#f44336',     // red
    [AlertSeverity.CRITICAL]: '#9c27b0',  // purple
  };

  const color = colors[alert.severity] || colors[AlertSeverity.INFO];

  // Determine emoji based on category
  const emojis = {
    [AlertCategory.ERROR]: '🚨',
    [AlertCategory.PERFORMANCE]: '⚡',
    [AlertCategory.SECURITY]: '🔒',
    [AlertCategory.AVAILABILITY]: '🔴',
    [AlertCategory.BUSINESS]: '💼',
  };

  const emoji = emojis[alert.category] || '📊';

  // Build Slack message
  const slackMessage = {
    username: 'Telos Monitoring',
    icon_emoji: ':robot_face:',
    attachments: [
      {
        color,
        fallback: `${alert.severity.toUpperCase()}: ${alert.title}`,
        pretext: `${emoji} *${alert.severity.toUpperCase()}* - ${alert.category.toUpperCase()}`,
        title: alert.title,
        text: alert.message,
        fields: [
          {
            title: 'Environment',
            value: process.env.NODE_ENV || 'development',
            short: true,
          },
          {
            title: 'Timestamp',
            value: new Date().toISOString(),
            short: true,
          },
          ...(alert.fields || []),
        ],
        footer: 'Telos Backend',
        footer_icon: 'https://platform.slack-edge.com/img/default_application_icon.png',
        ts: Math.floor(Date.now() / 1000),
      },
    ],
  };

  try {
    await axios.post(webhookUrl, slackMessage);
    alertCache.set(cacheKey, now);
    console.log(`[MONITORING] Alert sent to Slack: ${alert.title}`);
    return true;
  } catch (error) {
    console.error('[MONITORING] Failed to send Slack alert:', error.message);
    captureException(error, {
      tags: { component: 'monitoring', alert_category: alert.category },
      extra: { alert },
    });
    return false;
  }
}

/**
 * Monitor error rate and send alert if threshold exceeded
 *
 * @param {number} errorCount - Number of errors
 * @param {number} totalRequests - Total requests
 * @param {string} timeWindow - Time window (e.g., '1 minute', '5 minutes')
 */
export async function monitorErrorRate(errorCount, totalRequests, timeWindow = '1 minute') {
  const errorRate = totalRequests > 0 ? (errorCount / totalRequests) * 100 : 0;
  const threshold = 5; // 5% error rate threshold

  if (errorRate > threshold) {
    await sendSlackAlert({
      severity: AlertSeverity.ERROR,
      category: AlertCategory.ERROR,
      title: `High Error Rate Detected`,
      message: `Error rate is ${errorRate.toFixed(2)}% in the last ${timeWindow} (threshold: ${threshold}%)`,
      fields: [
        {
          title: 'Error Count',
          value: errorCount.toString(),
          short: true,
        },
        {
          title: 'Total Requests',
          value: totalRequests.toString(),
          short: true,
        },
      ],
    });

    captureMessage(
      `High error rate: ${errorRate.toFixed(2)}% (${errorCount}/${totalRequests})`,
      'warning',
      {
        tags: { alert_type: 'error_rate' },
        extra: { errorCount, totalRequests, errorRate, timeWindow },
      }
    );
  }
}

/**
 * Monitor critical business events
 *
 * @param {string} event - Event name
 * @param {object} data - Event data
 */
export async function monitorBusinessEvent(event, data) {
  const criticalEvents = ['trial_expired', 'payment_failed', 'high_churn'];

  if (criticalEvents.includes(event)) {
    await sendSlackAlert({
      severity: AlertSeverity.WARNING,
      category: AlertCategory.BUSINESS,
      title: `Business Event: ${event}`,
      message: JSON.stringify(data, null, 2),
      fields: Object.entries(data).map(([key, value]) => ({
        title: key,
        value: String(value),
        short: true,
      })),
    });
  }
}

/**
 * Monitor health check failures
 *
 * @param {string} service - Service name
 * @param {object} error - Error object
 */
export async function monitorHealthCheckFailure(service, error) {
  await sendSlackAlert({
    severity: AlertSeverity.CRITICAL,
    category: AlertCategory.AVAILABILITY,
    title: `Health Check Failed: ${service}`,
    message: error.message || 'Health check returned non-OK status',
    fields: [
      {
        title: 'Service',
        value: service,
        short: true,
      },
      {
        title: 'Error',
        value: error.message || 'Unknown',
        short: true,
      },
    ],
  });

  captureException(error, {
    tags: { component: 'health_check', service },
    extra: { service },
  });
}

/**
 * Monitor security events
 *
 * @param {string} event - Security event type
 * @param {object} details - Event details
 */
export async function monitorSecurityEvent(event, details) {
  await sendSlackAlert({
    severity: AlertSeverity.ERROR,
    category: AlertCategory.SECURITY,
    title: `Security Event: ${event}`,
    message: details.message || 'Security event detected',
    fields: [
      {
        title: 'Event Type',
        value: event,
        short: true,
      },
      {
        title: 'User',
        value: details.userId || 'unknown',
        short: true,
      },
      {
        title: 'IP Address',
        value: details.ipAddress || 'unknown',
        short: true,
      },
    ],
  });

  captureMessage(`Security event: ${event}`, 'error', {
    tags: { security_event: event },
    extra: details,
  });
}

/**
 * Monitor API quota usage
 *
 * @param {string} userId - User ID
 * @param {number} usage - Current usage
 * @param {number} limit - Usage limit
 */
export async function monitorQuotaUsage(userId, usage, limit) {
  const percentage = (usage / limit) * 100;
  const threshold = 90; // Alert at 90% usage

  if (percentage >= threshold) {
    await sendSlackAlert({
      severity: AlertSeverity.WARNING,
      category: AlertCategory.BUSINESS,
      title: `High Quota Usage`,
      message: `User ${userId} has used ${percentage.toFixed(1)}% of their quota`,
      fields: [
        {
          title: 'User ID',
          value: userId,
          short: true,
        },
        {
          title: 'Usage',
          value: `${usage}/${limit}`,
          short: true,
        },
      ],
    });
  }
}

/**
 * Send deployment notification
 *
 * @param {string} version - Deployment version
 * @param {string} environment - Environment name
 */
export async function notifyDeployment(version, environment) {
  await sendSlackAlert({
    severity: AlertSeverity.INFO,
    category: AlertCategory.BUSINESS,
    title: `Deployment Successful`,
    message: `Version ${version} deployed to ${environment}`,
    fields: [
      {
        title: 'Version',
        value: version,
        short: true,
      },
      {
        title: 'Environment',
        value: environment,
        short: true,
      },
    ],
  });
}

/**
 * Create middleware for monitoring request performance
 *
 * @returns {Function} Express middleware
 */
export function createPerformanceMonitoringMiddleware() {
  return (req, res, next) => {
    const start = Date.now();

    // Capture response when finished
    res.on('finish', () => {
      const duration = Date.now() - start;
      const endpoint = `${req.method} ${req.path}`;

      // Monitor error rates
      if (res.statusCode >= 500) {
        console.error(`[MONITORING] Server error: ${endpoint} returned ${res.statusCode}`);

        sendSlackAlert({
          severity: AlertSeverity.ERROR,
          category: AlertCategory.ERROR,
          title: `Server Error`,
          message: `${endpoint} returned ${res.statusCode}`,
          fields: [
            {
              title: 'Endpoint',
              value: endpoint,
              short: true,
            },
            {
              title: 'Status Code',
              value: res.statusCode.toString(),
              short: true,
            },
            {
              title: 'Duration',
              value: `${duration}ms`,
              short: true,
            },
          ],
        }).catch(console.error);
      }
    });

    next();
  };
}

/**
 * Clear alert cache (useful for testing)
 */
export function clearAlertCache() {
  alertCache.clear();
  console.log('[MONITORING] Alert cache cleared');
}

export default {
  sendSlackAlert,
  monitorErrorRate,
  monitorBusinessEvent,
  monitorHealthCheckFailure,
  monitorSecurityEvent,
  monitorQuotaUsage,
  notifyDeployment,
  createPerformanceMonitoringMiddleware,
  clearAlertCache,
  AlertSeverity,
  AlertCategory,
};
