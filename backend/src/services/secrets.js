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
    const secretValue = response.payload.data.toString('utf8');

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
 * Clear the secret cache (useful for testing or forced refresh)
 */
export function clearSecretCache() {
  secretCache.clear();
  console.log('🔄 Secret cache cleared');
}

export default {
  getSecret,
  getGeminiApiKey,
  clearSecretCache,
};

