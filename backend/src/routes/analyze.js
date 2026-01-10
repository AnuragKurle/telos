/**
 * Analysis Routes
 * 
 * Handles screenshot upload and analysis endpoints.
 */

import express from 'express';
import { checkClientVersion } from '../middleware/versionCheck.js';
import { verifyFirebaseToken } from '../middleware/auth.js';
import { rateLimitMiddleware } from '../middleware/rateLimit.js';
import { uploadImage, handleUploadErrors, validateImageUploaded } from '../middleware/upload.js';
import { analyzeScreenshot } from '../services/gemini.js';

const router = express.Router();

/**
 * POST /v1/analyze/screenshot
 * 
 * Upload a screenshot for AI analysis
 * 
 * Headers:
 *   - Authorization: Bearer <firebase-id-token>
 *   - X-Client-Version: <version>
 * 
 * Body (multipart/form-data):
 *   - image: Screenshot file (PNG/JPEG/WebP, max 10MB)
 * 
 * Response: Analysis JSON matching API contract schema
 */
router.post(
  '/screenshot',
  // Middleware chain (order matters!)
  checkClientVersion,           // 1. Check client version
  verifyFirebaseToken,          // 2. Verify Firebase token
  rateLimitMiddleware,          // 3. Check rate limits
  uploadImage,                  // 4. Handle file upload
  handleUploadErrors,           // 5. Handle upload errors
  validateImageUploaded,        // 6. Validate file exists
  async (req, res) => {         // 7. Process request
    try {
      // Log request (without logging image data)
      console.log(`[Analysis] User: ${req.user.uid}, File: ${req.file.originalname}, Size: ${req.file.size} bytes`);

      // Parse previous context if provided
      let previousCaptures = [];
      if (req.body.previous_context) {
        try {
          previousCaptures = JSON.parse(req.body.previous_context);
        } catch (e) {
          console.warn('[Analysis] Failed to parse previous_context:', e.message);
        }
      }

      // Parse context metadata if provided (window info, activity metrics)
      let contextMetadata = {};
      if (req.body.context_metadata) {
        try {
          contextMetadata = JSON.parse(req.body.context_metadata);
        } catch (e) {
          console.warn('[Analysis] Failed to parse context_metadata:', e.message);
        }
      }

      // Pass user identifier for Portkey logging (email preferred, fallback to UID)
      const userIdentifier = req.user.email || req.user.uid;
      const analysis = await analyzeScreenshot(req.file.buffer, req.file.mimetype, previousCaptures, userIdentifier, contextMetadata);

      // Return analysis result
      res.status(200).json(analysis);

      // Log success
      console.log(`[Analysis] Success: ${analysis.category} - ${analysis.app}`);
    } catch (error) {
      console.error('[Analysis] Error:', error.message);

      // Check if it's a Gemini API error
      if (error.message.includes('Gemini API')) {
        return res.status(500).json({
          error: 'InternalError',
          message: 'Analysis failed. Please try again.',
          code: 'ANALYSIS_FAILED',
        });
      }

      // Generic server error
      res.status(500).json({
        error: 'InternalError',
        message: 'An unexpected error occurred',
        code: 'INTERNAL_ERROR',
      });
    }
  }
);

/**
 * Health check for analysis service
 * (optional - could be useful for debugging)
 */
router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'analysis',
    timestamp: new Date().toISOString(),
  });
});

export default router;

