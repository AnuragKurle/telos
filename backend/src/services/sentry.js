/**
 * Sentry Error Tracking Service
 *
 * Initializes Sentry for error tracking and performance monitoring.
 * Integrates with Express for automatic error capture.
 */

import * as Sentry from '@sentry/node';
import { ProfilingIntegration } from '@sentry/profiling-node';

let sentryInitialized = false;

/**
 * Initialize Sentry
 *
 * @param {object} app - Express app instance
 */
export function initializeSentry(app) {
  const dsn = process.env.SENTRY_DSN;

  // Skip initialization if DSN not provided (local dev)
  if (!dsn) {
    console.log('[SENTRY] DSN not provided, skipping initialization');
    return;
  }

  try {
    Sentry.init({
      dsn,
      environment: process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV || 'development',
      integrations: [
        // Enable HTTP calls tracing
        new Sentry.Integrations.Http({ tracing: true }),
        // Enable Express.js middleware tracing
        new Sentry.Integrations.Express({ app }),
        // Capture Breadcrumbs (console logs, network requests)
        new Sentry.Integrations.Console(),
        // Performance Profiling
        new ProfilingIntegration(),
      ],
      // Performance Monitoring
      tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0, // 10% in prod, 100% in dev
      // Profiling
      profilesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
      // Release tracking
      release: `telos-backend@${process.env.npm_package_version || '0.1.0'}`,
      // Before sending events, you can filter or modify them
      beforeSend(event, hint) {
        // Don't send events in development unless explicitly enabled
        if (process.env.NODE_ENV === 'development' && !process.env.SENTRY_SEND_IN_DEV) {
          return null;
        }

        // Filter out sensitive data
        if (event.request) {
          delete event.request.cookies;
          // Redact authorization headers
          if (event.request.headers && event.request.headers.authorization) {
            event.request.headers.authorization = '[Filtered]';
          }
        }

        return event;
      },
    });

    sentryInitialized = true;
    console.log('✅ Sentry initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize Sentry:', error.message);
  }
}

/**
 * Get Sentry request handler (must be first middleware)
 */
export function getRequestHandler() {
  return Sentry.Handlers.requestHandler();
}

/**
 * Get Sentry tracing handler (must be after request handler)
 */
export function getTracingHandler() {
  return Sentry.Handlers.tracingHandler();
}

/**
 * Get Sentry error handler (must be after all routes, before other error handlers)
 */
export function getErrorHandler() {
  return Sentry.Handlers.errorHandler({
    shouldHandleError(error) {
      // Capture all errors with status >= 500
      if (error.status && error.status >= 500) {
        return true;
      }
      // Also capture specific error types
      if (error.name === 'UnhandledPromiseRejection') {
        return true;
      }
      return false;
    }
  });
}

/**
 * Capture an exception manually
 *
 * @param {Error} error - Error to capture
 * @param {object} context - Additional context
 */
export function captureException(error, context = {}) {
  if (!sentryInitialized) {
    console.error('[SENTRY] Not initialized, cannot capture exception:', error);
    return;
  }

  Sentry.captureException(error, {
    tags: context.tags || {},
    extra: context.extra || {},
    user: context.user || null,
  });
}

/**
 * Capture a message manually
 *
 * @param {string} message - Message to capture
 * @param {string} level - Severity level (info, warning, error)
 * @param {object} context - Additional context
 */
export function captureMessage(message, level = 'info', context = {}) {
  if (!sentryInitialized) {
    return;
  }

  Sentry.captureMessage(message, {
    level,
    tags: context.tags || {},
    extra: context.extra || {},
  });
}

/**
 * Set user context for subsequent errors
 *
 * @param {object} user - User data
 */
export function setUser(user) {
  if (!sentryInitialized) {
    return;
  }

  Sentry.setUser({
    id: user.uid || user.id,
    email: user.email,
    username: user.username || user.displayName,
  });
}

/**
 * Add breadcrumb (for debugging)
 *
 * @param {string} message - Breadcrumb message
 * @param {object} data - Additional data
 * @param {string} category - Category (e.g., 'auth', 'api', 'db')
 */
export function addBreadcrumb(message, data = {}, category = 'default') {
  if (!sentryInitialized) {
    return;
  }

  Sentry.addBreadcrumb({
    message,
    data,
    category,
    level: 'info',
  });
}

/**
 * Check if Sentry is initialized
 */
export function isInitialized() {
  return sentryInitialized;
}

export default {
  initializeSentry,
  getRequestHandler,
  getTracingHandler,
  getErrorHandler,
  captureException,
  captureMessage,
  setUser,
  addBreadcrumb,
  isInitialized,
};
