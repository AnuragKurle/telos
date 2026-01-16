/**
 * Secret Manager Service
 * 
 * Fetches secrets from Google Cloud Secret Manager.
 * Caches secrets in memory to avoid repeated API calls.
 */

import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

// Cache for secrets (in-memory)
const secretCache = new Map();

// Initialize Secret Manager client
const client = new SecretManagerServiceClient();

/**
 * Get a secret from Secret Manager
 * 
 * @param {string} secretName - Name of the secret (e.g., "GEMINI_API_KEY")
 * @param {string} version - Version of the secret (default: "latest")
 * @returns {Promise<string>} Secret value
 */
export async function getSecret(secretName, version = 'latest') {
  const cacheKey = `${secretName}:${version}`;

  // 1. Try environment variable first (priority for local dev)
  if (process.env[secretName]) {
    console.log(`[SECRETS] Using environment variable for ${secretName}`);
    return process.env[secretName];
  }

  // Return cached value if available
  if (secretCache.has(cacheKey)) {
    return secretCache.get(cacheKey);
  }

  const projectId = process.env.GCP_PROJECT_ID;

  if (!projectId) {
    throw new Error('GCP_PROJECT_ID environment variable is required');
  }

  try {
    // Build the resource name
    const name = `projects/${projectId}/secrets/${secretName}/versions/${version}`;

    // Access the secret
    const [response] = await client.accessSecretVersion({ name });

    // Extract the payload
    const secretValue = response.payload.data.toString('utf8').trim();

    // Cache the secret
    secretCache.set(cacheKey, secretValue);

    console.log(`✅ Retrieved secret: ${secretName}`);
    return secretValue;
  } catch (error) {
    console.error(`❌ Failed to retrieve secret ${secretName}:`, error.message);
    throw new Error(`Failed to retrieve secret ${secretName}: ${error.message}`);
  }
}

/**
 * Get Gemini API key from Secret Manager
 * 
 * @returns {Promise<string>} Gemini API key
 */
export async function getGeminiApiKey() {
  const secretName = process.env.GEMINI_SECRET_NAME || 'GEMINI_API_KEY';
  return await getSecret(secretName);
}

/**
 * Get Slack Bot Token from Secret Manager or environment
 * 
 * @returns {Promise<string|null>} Slack Bot Token or null if not found
 */
export async function getSlackBotToken() {
  // Try Secret Manager first
  try {
    const secretName = process.env.SLACK_BOT_TOKEN_SECRET_NAME || 'SLACK_BOT_TOKEN';
    return await getSecret(secretName);
  } catch (error) {
    // Fallback to environment variable
    if (process.env.SLACK_BOT_TOKEN) {
      return process.env.SLACK_BOT_TOKEN;
    }
    return null;
  }
}

/**
 * Get Slack Webhook URL from Secret Manager or environment
 * 
 * @returns {Promise<string|null>} Slack Webhook URL or null if not found
 */
export async function getSlackWebhook() {
  // Try Secret Manager first
  try {
    const secretName = process.env.SLACK_WEBHOOK_SECRET_NAME || 'SLACK_WEBHOOK';
    return await getSecret(secretName);
  } catch (error) {
    // Fallback to environment variable
    if (process.env.SLACK_WEBHOOK) {
      return process.env.SLACK_WEBHOOK;
    }
    return null;
  }
}

/**
 * Get Slack Signup Webhook URL from Secret Manager or environment
 * 
 * @returns {Promise<string|null>} Slack Signup Webhook URL or null if not found
 */
export async function getSlackSignupWebhook() {
  // Try Secret Manager first
  try {
    const secretName = process.env.SLACK_SIGNUP_WEBHOOK_SECRET_NAME || 'SLACK_SIGNUP_WEBHOOK';
    return await getSecret(secretName);
  } catch (error) {
    // Fallback to environment variable
    if (process.env.SLACK_SIGNUP_WEBHOOK) {
      return process.env.SLACK_SIGNUP_WEBHOOK;
    }
    return null;
  }
}

/**
 * Clear the secret cache (useful for testing or forced refresh)
 */
export function clearSecretCache() {
  secretCache.clear();
  console.log('🔄 Secret cache cleared');
}

export default {
  getSecret,
  getGeminiApiKey,
  getSlackBotToken,
  getSlackWebhook,
  getSlackSignupWebhook,
  clearSecretCache,
};

