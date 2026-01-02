/**
 * Authentication routes for user management
 */

import express from 'express';
import { verifyFirebaseToken } from '../middleware/auth.js';
import { sendSignupNotification } from '../services/slack.js';
import admin from 'firebase-admin';

const router = express.Router();

/**
 * POST /auth/link-email
 * 
 * Convert anonymous account to email-based account
 * 
 * Request body:
 * {
 *   "email": "user@example.com",
 *   "password": "securepassword"
 * }
 * 
 * Response:
 * {
 *   "success": true,
 *   "user": {
 *     "uid": "firebase-uid",
 *     "email": "user@example.com",
 *     "emailVerified": false,
 *     "isAnonymous": false
 *   }
 * }
 */
router.post('/link-email', verifyFirebaseToken, async (req, res) => {
  try {
    const { email, password } = req.body;
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
      
      // Send Slack notification (non-blocking)
      sendSignupNotification({
        uid: updatedUser.uid,
        email: updatedUser.email,
        createdAt: updatedUser.metadata.creationTime
      }).catch(err => console.error('[SLACK] Failed to send signup notification:', err));
      
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
 * 
 * Response:
 * {
 *   "uid": "firebase-uid",
 *   "email": "user@example.com" | null,
 *   "isAnonymous": true | false,
 *   "emailVerified": true | false,
 *   "createdAt": "2025-01-02T...",
 *   "lastSignIn": "2025-01-02T..."
 * }
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

export default router;

