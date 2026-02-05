/**
 * Telos Backend - Main Server Entry Point
 * 
 * This is the Express.js server that handles screenshot analysis requests.
 * It verifies Firebase tokens, calls Gemini API, and returns analysis results.
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { initializeFirebase } from './config/firebase.js';
import analyzeRoutes from './routes/analyze.js';
import authRoutes from './routes/auth.js';
import feedbackRoutes from './routes/feedback.js';
import reportsRoutes from './routes/reports.js';
import checkoutRoutes from './routes/checkout.js';
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
  console.warn('[STARTUP] SendGrid initialization deferred:', err.message);
});

// Start Background Scheduler
startScheduler();

const app = express();
const PORT = process.env.PORT || 8080;

// Initialize Sentry (must be first)
initializeSentry(app);

// Sentry request handler (must be the first middleware)
app.use(getRequestHandler());

// Sentry tracing handler (must be after request handler)
app.use(getTracingHandler());

// Performance monitoring middleware (tracks slow requests and errors)
app.use(createPerformanceMonitoringMiddleware());

// Middleware
app.use(cors());

// Stripe webhook needs raw body, so handle it before JSON parser
app.use('/v1/checkout/webhook', express.raw({ type: 'application/json' }));

// JSON parser forall other routes
app.use(express.json());

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

  // Notify deployment in production
  if (process.env.NODE_ENV === 'production') {
    notifyDeployment('0.1.0', 'production').catch(console.error);
  }
});

export default app;

