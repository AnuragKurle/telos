/**
 * Firebase Admin SDK Configuration
 * 
 * Initializes Firebase Admin for token verification and Firestore access.
 * Uses Application Default Credentials in production (Cloud Run) or
 * local credentials file in development.
 */

import admin from 'firebase-admin';

let firebaseApp;
let firestoreDb;

/**
 * Initialize Firebase Admin SDK
 * 
 * @returns {admin.app.App} Initialized Firebase app instance
 */
export function initializeFirebase() {
  if (firebaseApp) {
    return firebaseApp;
  }

  const projectId = process.env.FIREBASE_PROJECT_ID;

  if (!projectId) {
    throw new Error('FIREBASE_PROJECT_ID environment variable is required');
  }

  try {
    firebaseApp = admin.initializeApp({
      projectId: projectId,
      // In Cloud Run, this uses Application Default Credentials automatically
      // In local dev, set GOOGLE_APPLICATION_CREDENTIALS env var if needed
    });

    console.log(`✅ Firebase Admin initialized for project: ${projectId}`);
    return firebaseApp;
  } catch (error) {
    console.error('❌ Failed to initialize Firebase Admin:', error.message);
    throw error;
  }
}

/**
 * Get Firebase Admin app instance
 * 
 * @returns {admin.app.App} Firebase app instance
 */
export function getFirebaseApp() {
  if (!firebaseApp) {
    return initializeFirebase();
  }
  return firebaseApp;
}

/**
 * Get Firestore database instance
 * 
 * @returns {admin.firestore.Firestore} Firestore instance
 */
export function getFirestore() {
  if (!firestoreDb) {
    const app = getFirebaseApp();
    firestoreDb = admin.firestore(app);
  }
  return firestoreDb;
}

/**
 * Get Firebase Auth instance
 * 
 * @returns {admin.auth.Auth} Auth instance
 */
export function getAuth() {
  const app = getFirebaseApp();
  return admin.auth(app);
}

export default {
  initializeFirebase,
  getFirebaseApp,
  getFirestore,
  getAuth,
};

