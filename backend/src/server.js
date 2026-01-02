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

// Load environment variables
dotenv.config();

// Initialize Firebase Admin SDK
initializeFirebase();

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
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

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Cannot ${req.method} ${req.path}`
  });
});

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
});

export default app;

