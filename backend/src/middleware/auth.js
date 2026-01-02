/**
 * Authentication Middleware
 * 
 * Verifies Firebase ID tokens and attaches user info to request.
 */

import { getAuth } from '../config/firebase.js';

/**
 * Middleware to verify Firebase ID token from Authorization header
 * 
 * Expects: Authorization: Bearer <firebase-id-token>
 * 
 * On success: Attaches req.user = { uid, email, ... }
 * On failure: Returns 401 with proper error code
 */
export async function verifyFirebaseToken(req, res, next) {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Missing Authorization header',
        code: 'MISSING_TOKEN',
      });
    }

    // Check Bearer format
    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Authorization header must be in format: Bearer <token>',
        code: 'INVALID_AUTH_FORMAT',
      });
    }

    const idToken = parts[1];

    if (!idToken) {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Token is empty',
        code: 'MISSING_TOKEN',
      });
    }

    // Verify token with Firebase Admin
    const auth = getAuth();
    const decodedToken = await auth.verifyIdToken(idToken);

    // Attach user info to request
    req.user = {
      uid: decodedToken.uid,
      email: decodedToken.email || null,
      emailVerified: decodedToken.email_verified || false,
      isAnonymous: decodedToken.firebase?.sign_in_provider === 'anonymous',
      authTime: decodedToken.auth_time,
      iat: decodedToken.iat,
      exp: decodedToken.exp,
    };

    // Continue to next middleware
    next();
  } catch (error) {
    // Handle specific Firebase errors
    if (error.code === 'auth/id-token-expired') {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Token has expired',
        code: 'TOKEN_EXPIRED',
      });
    }

    if (error.code === 'auth/id-token-revoked') {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Token has been revoked',
        code: 'TOKEN_REVOKED',
      });
    }

    if (error.code === 'auth/argument-error') {
      return res.status(401).json({
        error: 'AuthenticationError',
        message: 'Invalid token format',
        code: 'INVALID_TOKEN',
      });
    }

    // Generic token verification failure
    console.error('Token verification failed:', error.message);
    return res.status(401).json({
      error: 'AuthenticationError',
      message: 'Invalid or expired token',
      code: 'INVALID_TOKEN',
    });
  }
}

export default verifyFirebaseToken;

