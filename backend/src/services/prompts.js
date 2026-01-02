/**
 * Prompt Management Service
 * 
 * Loads AI prompts from Firestore and caches them in memory.
 * Prompts are stored in Firestore for easy updates without redeployment.
 */

import { getFirestore } from '../config/firebase.js';

// In-memory cache with TTL
const promptCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Get a prompt from Firestore (with caching)
 * 
 * @param {string} promptName - Name of the prompt (e.g., "screenshot-analysis")
 * @returns {Promise<object>} Prompt data { content, version, metadata }
 */
export async function getPrompt(promptName) {
  const now = Date.now();

  // Check cache
  if (promptCache.has(promptName)) {
    const cached = promptCache.get(promptName);
    if (now - cached.timestamp < CACHE_TTL) {
      return cached.data;
    }
  }

  try {
    const db = getFirestore();

    // Get active version for this prompt
    const promptDoc = await db.collection('prompts').doc(promptName).get();

    if (!promptDoc.exists) {
      throw new Error(`Prompt "${promptName}" not found in Firestore`);
    }

    const promptData = promptDoc.data();
    const activeVersion = promptData.activeVersion || 'v1';

    // Get the specific version content
    const versionDoc = await db
      .collection('prompts')
      .doc(promptName)
      .collection('versions')
      .doc(activeVersion)
      .get();

    if (!versionDoc.exists) {
      throw new Error(`Version "${activeVersion}" not found for prompt "${promptName}"`);
    }

    const versionData = versionDoc.data();

    const result = {
      content: versionData.content,
      version: activeVersion,
      metadata: {
        createdAt: versionData.createdAt?.toDate(),
        updatedAt: promptData.updatedAt?.toDate(),
        ...versionData.metadata,
      },
    };

    // Cache the result
    promptCache.set(promptName, {
      data: result,
      timestamp: now,
    });

    console.log(`✅ Loaded prompt "${promptName}" version ${activeVersion}`);
    return result;
  } catch (error) {
    console.error(`❌ Failed to load prompt "${promptName}":`, error.message);
    
    // Fall back to default prompt if Firestore fails
    console.warn(`⚠️  Using fallback prompt for "${promptName}"`);
    return getDefaultPrompt(promptName);
  }
}

/**
 * Get screenshot analysis prompt
 * 
 * @returns {Promise<object>} Screenshot analysis prompt
 */
export async function getScreenshotAnalysisPrompt() {
  return await getPrompt('screenshot-analysis');
}

/**
 * Get session enrichment prompt
 * 
 * @returns {Promise<object>} Session enrichment prompt
 */
export async function getSessionEnrichmentPrompt() {
  return await getPrompt('session-enrichment');
}

/**
 * Get daily summary prompt
 * 
 * @returns {Promise<object>} Daily summary prompt
 */
export async function getDailySummaryPrompt() {
  return await getPrompt('daily-summary');
}

/**
 * Get AI chat system prompt
 * 
 * @returns {Promise<object>} AI chat system prompt
 */
export async function getAiChatSystemPrompt() {
  return await getPrompt('ai-chat-system');
}

/**
 * Default fallback prompts (used if Firestore is unavailable)
 * 
 * @param {string} promptName - Name of the prompt
 * @returns {object} Default prompt data
 */
function getDefaultPrompt(promptName) {
  const defaults = {
    'screenshot-analysis': {
      content: `You are an AI assistant that analyzes screenshots of user activity.

Analyze the provided screenshot and return a JSON object with the following fields:
- simple_category: One of [work, learning, browsing, entertainment, idle]
- category: Specific category name (e.g., "Coding", "Meeting", "Research")
- category_emoji: Emoji character representing the activity
- category_color: Hex color code (e.g., "#3498db")
- app: The primary application being used (e.g., "Chrome", "VS Code", "Slack")
- task: Brief description of what the user is doing (max 80 chars)
- confidence: Your confidence level (0.0 to 1.0)
- detailed_context: Object with rich details (file_name, browser_url, full_description, etc.)

Respond ONLY with valid JSON, no other text.`,
      version: 'fallback',
      metadata: {
        isFallback: true,
      },
    },
    'session-enrichment': {
      content: `Analyze this work session and provide insights.

Return JSON with:
- summary: 2-3 sentences describing what was accomplished
- learnings: Key insights or patterns (or empty string if none)
- focus_score: 0.0 to 1.0 (1.0 = deep focus, <0.5 = fragmented)

Respond ONLY with valid JSON.`,
      version: 'fallback',
      metadata: {
        isFallback: true,
      },
    },
    'daily-summary': {
      content: `Generate a daily summary.

Return JSON with:
- daily_narrative: 3-4 sentence summary of the day
- key_learnings: Array of 2-5 strings (or empty array)

Respond ONLY with valid JSON.`,
      version: 'fallback',
      metadata: {
        isFallback: true,
      },
    },
    'ai-chat-system': {
      content: `You are an AI assistant that helps users understand their computer activity data.

Be concise, helpful, and specific. Reference actual timestamps, file names, and tasks.
When generating content (posts, tweets), make it polished and ready to use.`,
      version: 'fallback',
      metadata: {
        isFallback: true,
      },
    },
  };

  return defaults[promptName] || {
    content: 'Analyze this data.',
    version: 'fallback',
    metadata: { isFallback: true },
  };
}

/**
 * Clear the prompt cache (useful for testing or forced refresh)
 */
export function clearPromptCache() {
  promptCache.clear();
  console.log('🔄 Prompt cache cleared');
}

/**
 * Preload prompts on startup (optional optimization)
 */
export async function preloadPrompts() {
  try {
    await Promise.all([
      getScreenshotAnalysisPrompt(),
      getSessionEnrichmentPrompt(),
      getDailySummaryPrompt(),
      getAiChatSystemPrompt(),
    ]);
    console.log('✅ All prompts preloaded');
  } catch (error) {
    console.warn('⚠️  Failed to preload prompts:', error.message);
  }
}

export default {
  getPrompt,
  getScreenshotAnalysisPrompt,
  getSessionEnrichmentPrompt,
  getDailySummaryPrompt,
  getAiChatSystemPrompt,
  clearPromptCache,
  preloadPrompts,
};

