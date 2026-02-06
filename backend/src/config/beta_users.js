/**
 * Beta Access Whitelist
 * 
 * Beta user whitelist is now managed via Firestore 'waitlist' collection
 * and the admin dashboard. This file is kept for backwards compatibility.
 * 
 * To add beta users, use the admin dashboard or add entries to the
 * 'waitlist' collection in Firestore directly.
 * 
 * For local development, set BETA_USERS env var as a comma-separated list.
 */
const envUsers = process.env.BETA_USERS
  ? process.env.BETA_USERS.split(',').map(e => e.trim().toLowerCase())
  : [];

export const betaUsers = [
    "test@example.com",
    ...envUsers,
];

export default betaUsers;
