/**
 * Telos Backend - Main Server Entry Point
 * 
 * This is the Express.js server that handles screenshot analysis requests.
 * It verifies Firebase tokens, calls Gemini API, and returns analysis results.
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { initializeFirebase } from './config/firebase.js';
import analyzeRoutes from './routes/analyze.js';
import authRoutes from './routes/auth.js';
import feedbackRoutes from './routes/feedback.js';
import reportsRoutes from './routes/reports.js';
import checkoutRoutes from './routes/checkout.js';
import referralRoutes from './routes/referral.js';
import adminRoutes from './routes/admin.js';
import webReportRoutes from './routes/webReport.js';
import { startScheduler } from './services/scheduler.js';
import { initializeEncryption } from './services/encryption.js';
import { initializeSendGrid } from './services/email.js';
import {
  initializeSentry,
  getRequestHandler,
  getTracingHandler,
  getErrorHandler
} from './services/sentry.js';
import { createPerformanceMonitoringMiddleware, notifyDeployment } from './services/monitoring.js';

// Load environment variables
dotenv.config();

// Initialize Firebase Admin SDK
initializeFirebase();

// Initialize encryption (loads key from Secret Manager)
initializeEncryption().catch(err => {
  console.warn('[STARTUP] Encryption initialization deferred:', err.message);
});

// Initialize SendGrid email service
initializeSendGrid().then(() => {
  console.log('[STARTUP] SendGrid ready');
}).catch(err => {
  console.error('[STARTUP] *** SENDGRID INITIALIZATION FAILED ***');
  console.error('[STARTUP] Email reports will NOT work until this is fixed.');
  console.error('[STARTUP] Error:', err.message);
  console.error('[STARTUP] Ensure SENDGRID_API_KEY secret exists in GCP Secret Manager');
});

// Start Background Scheduler
startScheduler();

const app = express();
const PORT = process.env.PORT || 8080;

// Trust proxy for Cloud Run (required for rate limiting and IP detection)
// Cloud Run sits behind Google's load balancer, so we need to trust the X-Forwarded-* headers
app.set('trust proxy', true);

// Initialize Sentry (must be first)
initializeSentry(app);

// Sentry request handler (must be the first middleware)
app.use(getRequestHandler());

// Sentry tracing handler (must be after request handler)
app.use(getTracingHandler());

// Performance monitoring middleware (tracks slow requests and errors)
app.use(createPerformanceMonitoringMiddleware());

// Security headers
app.use(helmet());

// CORS - restrict to known origins
const allowedOrigins = [
  'https://telos.dev',
  'https://www.telos.dev',
  'https://telos.app',
  'https://www.telos.app',
  'https://gen-lang-client-0772617718.web.app',
  'https://gen-lang-client-0772617718.firebaseapp.com',
  ...(process.env.NODE_ENV === 'development' ? ['http://localhost:3000', 'http://localhost:8080'] : []),
];

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (server-to-server, curl, mobile clients, desktop clients)
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('Not allowed by CORS'));
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Client-Version'],
  credentials: true,
}));

// Dodo Payments webhook needs raw body, so handle it before JSON parser
app.use('/v1/checkout/webhook', express.raw({ type: 'application/json' }));

// JSON parser for all other routes (with size limit to prevent abuse)
app.use(express.json({ limit: '1mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'telos-backend',
    version: '0.1.0',
    timestamp: new Date().toISOString()
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Telos Backend API',
    version: '0.1.0',
    docs: 'See /api/docs for API documentation',
    health: '/health'
  });
});

// API routes
app.use('/v1/analyze', analyzeRoutes);
app.use('/v1/auth', authRoutes);
app.use('/v1/feedback', feedbackRoutes);
app.use('/v1/reports', reportsRoutes);
app.use('/v1/checkout', checkoutRoutes);
app.use('/v1/referral', referralRoutes);
app.use('/v1/admin', adminRoutes);
app.use('/r', webReportRoutes);  // Web report viewer (no auth, token-based access from email)

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Cannot ${req.method} ${req.path}`
  });
});

// Sentry error handler (must be after all routes, before other error handlers)
app.use(getErrorHandler());

// Error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Telos Backend running on port ${PORT}`);
  console.log(`📍 Health check: http://localhost:${PORT}/health`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);

  // Notify deployment in production (only on actual deployments, not instance restarts)
  // Cloud Run sets K_REVISION env var that changes with each deployment
  // We'll only notify once per revision to avoid spam
  if (process.env.NODE_ENV === 'production' && process.env.K_REVISION) {
    // Skip deployment notifications - they were causing spam
    // Actual deployments should be tracked via Cloud Build notifications instead
    console.log(`[STARTUP] Revision: ${process.env.K_REVISION}`);
  }
});

export default app;

