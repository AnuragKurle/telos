/**
 * Gemini API Service
 * 
 * Calls Google Gemini API for screenshot analysis.
 * Uses server-side API key to keep prompts private.
 * 
 * PORTKEY INTEGRATION: All calls are routed through Portkey for observability.
 * See https://app.portkey.ai for logs.
 */

import { Portkey } from 'portkey-ai';
import { getGeminiApiKey } from './secrets.js';
import { getScreenshotAnalysisPrompt } from './prompts.js';

/**
 * Portkey Configuration
 * Reads from environment variables for security.
 * Optional: If not configured, falls back to direct Gemini API calls.
 */
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY;
const PORTKEY_VIRTUAL_KEY = process.env.PORTKEY_VIRTUAL_KEY;
const PORTKEY_ENABLED = !!(PORTKEY_API_KEY && PORTKEY_VIRTUAL_KEY);

if (!PORTKEY_ENABLED) {
  console.warn('[GEMINI] Portkey not configured - using direct Gemini API (no observability)');
}

/**
 * Initialize Portkey client (singleton)
 */
let portkeyClient = null;
function getPortkeyClient(traceId = null, userId = null, contextMetadata = {}) {
  if (!PORTKEY_ENABLED) {
    throw new Error('Portkey is not configured. Please set PORTKEY_API_KEY and PORTKEY_VIRTUAL_KEY environment variables.');
  }
  
  // Create fresh client with metadata for each call
  return new Portkey({
    apiKey: PORTKEY_API_KEY,
    virtualKey: PORTKEY_VIRTUAL_KEY,
    user: userId || 'backend-service',  // Top-level user parameter for Portkey logs
    metadata: {
      call_type: 'screenshot_analysis',
      source: 'telos-backend',
      // Include window context in Portkey metadata for logging
      window_title: contextMetadata.window_title || 'unknown',
      app_name: contextMetadata.app_name || 'unknown',
      keystrokes: String(contextMetadata.keystrokes || 0),
      mouse_clicks: String(contextMetadata.mouse_clicks || 0),
      window_changes: String(contextMetadata.window_changes || 0),
    },
    traceId: traceId || `backend-${Date.now()}`,
  });
}

/**
 * Fallback metadata (used only if AI doesn't provide emoji/color)
 */
const FALLBACK_METADATA = {
  emoji: '❓',
  color: '#9CA3AF',
};

/**
 * In-memory cache for API key and Prompt to avoid hitting Firestore/SecretManager on every request.
 */
let cachedApiKey = null;
let cachedPromptData = null;
let cacheExpiry = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Call Gemini API to analyze a screenshot
 * 
 * @param {Buffer} imageBuffer - Screenshot image data
 * @param {string} mimeType - Image MIME type (e.g., "image/png")
 * @param {Array} previousCaptures - Previous captures for context
 * @param {string} userId - Optional user ID for logging
 * @param {Object} contextMetadata - System context (window title, app name, activity metrics)
 * @returns {Promise<object>} Analysis result matching API contract schema
 */
export async function analyzeScreenshot(imageBuffer, mimeType = 'image/png', previousCaptures = [], userId = null, contextMetadata = {}) {
  try {
    // Check cache or fetch in parallel
    const now = Date.now();
    if (!cachedApiKey || !cachedPromptData || now > cacheExpiry) {
      const [key, prompt] = await Promise.all([
        getGeminiApiKey(),
        getScreenshotAnalysisPrompt()
      ]);
      cachedApiKey = key;
      cachedPromptData = prompt;
      cacheExpiry = now + CACHE_TTL;
    }

    const promptData = cachedPromptData;

    // Build context string from previous captures (similar to client logic)
    const contextStr = buildPreviousContext(previousCaptures);

    // Build system context string from metadata
    const systemContextStr = buildSystemContext(contextMetadata);

    // Replace both placeholders in prompt
    let finalPrompt = promptData.content.replace('{previous_context}', contextStr);
    finalPrompt = finalPrompt.replace('{system_context}', systemContextStr);

    // Convert image to base64 for multimodal input
    const base64Image = imageBuffer.toString('base64');
    const imageUrl = `data:${mimeType};base64,${base64Image}`;

    // Get Portkey client with user metadata and context
    const portkey = getPortkeyClient(`screenshot-${Date.now()}`, userId, contextMetadata);

    // Use Portkey's OpenAI-compatible API
    // Portkey translates this to Gemini format automatically
    const model = "gemini-2.5-flash";

    const response = await portkey.chat.completions.create({
      model: model,
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: finalPrompt },
            { type: "image_url", image_url: { url: imageUrl } }
          ]
        }
      ],
      response_format: { type: "json_object" },
      max_tokens: 4096,
      temperature: 0.4,
    });

    // Extract the response text
    const textResponse = response.choices[0].message.content;

    // Parse JSON response
    let analysis;
    try {
      analysis = JSON.parse(textResponse);
    } catch (parseError) {
      console.error('Failed to parse Gemini JSON response:', textResponse);
      throw new Error('Invalid JSON response from Gemini API');
    }

    // Return standardized response matching API contract
    return {
      category: analysis.category || 'Unknown',
      simple_category: analysis.simple_category || 'idle',
      app: analysis.app || 'Unknown',
      task: analysis.task || 'Activity detected',
      confidence: typeof analysis.confidence === 'number' ? analysis.confidence : 0.5,
      detailed_context: analysis.detailed_context || {},
      category_emoji: analysis.category_emoji || FALLBACK_METADATA.emoji,
      category_color: analysis.category_color || FALLBACK_METADATA.color,
      analysis_version: promptData.version,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error('❌ Screenshot analysis failed:', error.message);
    throw error;
  }
}

/**
 * Helper to build context string from previous captures
 */
function buildPreviousContext(previousCaptures) {
  if (!previousCaptures || previousCaptures.length === 0) {
    return "No previous context available. This is the first capture.";
  }

  return previousCaptures.map((cap, i) => {
    const app = cap.app || cap.app_name || 'unknown';
    const task = cap.task || 'unknown';
    const cat = cap.category || 'unknown';
    return `${i + 1} capture(s) ago: [${cat}] ${app} - ${task}`;
  }).join('\n');
}

/**
 * Helper to build system context string from context metadata
 */
function buildSystemContext(contextMetadata) {
  if (!contextMetadata || Object.keys(contextMetadata).length === 0) {
    return "No system context available.";
  }

  const metrics = [];
  if ((contextMetadata.keystrokes || 0) > 10) {
    metrics.push("High Typing");
  } else if ((contextMetadata.keystrokes || 0) > 0) {
    metrics.push("Low Typing");
  }

  if ((contextMetadata.mouse_clicks || 0) > 2) {
    metrics.push("High Clicks");
  }

  if ((contextMetadata.mouse_distance || 0) > 500) {
    metrics.push("High Mouse Movement");
  }

  const inputDesc = metrics.length > 0 ? metrics.join(", ") : "No Input";

  let context = `Active Window: ${contextMetadata.window_title || 'Unknown'}\n`;
  context += `App Name: ${contextMetadata.app_name || 'Unknown'}\n`;
  context += `Input Activity (Last 30s): ${inputDesc}\n`;
  context += `(Raw: ${contextMetadata.keystrokes || 0} keys, ${contextMetadata.mouse_clicks || 0} clicks)`;

  // Include window changes if present
  if (contextMetadata.window_changes && contextMetadata.window_changes > 0) {
    context += `\nWindow Switches: ${contextMetadata.window_changes} changes in this interval`;
  }

  // Include window events if present
  if (contextMetadata.window_events && contextMetadata.window_events.length > 0) {
    context += `\nRecent Window Activity:`;
    contextMetadata.window_events.forEach(event => {
      context += `\n  - ${event.app_name}: ${event.window_title}`;
    });
  }

  return context;
}

/**
 * Validate that analysis result matches expected schema
 * 
 * @param {object} analysis - Analysis object to validate
 * @returns {boolean} True if valid
 */
export function validateAnalysisSchema(analysis) {
  const required = ['category', 'simple_category', 'app', 'task', 'confidence', 'detailed_context',
    'category_emoji', 'category_color', 'analysis_version', 'timestamp'];

  return required.every(field => field in analysis);
}

/**
 * Generate daily narrative from sessions and stats
 * Used by server-side summary generator when client hasn't uploaded a summary
 * 
 * @param {Array} sessions - Array of session objects
 * @param {Object} categoryTotals - Category totals in seconds
 * @param {string} userGoal - Optional user's analysis goal
 * @returns {Promise<Object>} {narrative, learnings, score}
 */
export async function generateDailyNarrative(sessions, categoryTotals, userGoal = null) {
  console.log('[GEMINI] Generating daily narrative from sessions');

  try {
    // Build prompt
    const prompt = buildNarrativePrompt(sessions, categoryTotals, userGoal);

    // Initialize Portkey client
    const client = getPortkeyClient('daily-narrative', 'system');

    // Call Gemini via Portkey
    const response = await client.chat.completions.create({
      model: 'gemini-2.5-flash',
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.7,
      response_format: { type: 'json_object' }
    });

    const resultText = response.choices[0].message.content;
    const result = JSON.parse(resultText);

    console.log('[GEMINI] Generated narrative successfully');

    return {
      narrative: result.daily_narrative || 'No narrative generated.',
      learnings: result.key_learnings || [],
      score: result.productivity_score || 50
    };

  } catch (error) {
    console.error('[GEMINI] Error generating narrative:', error);

    // Return fallback
    return {
      narrative: 'Summary generation temporarily unavailable.',
      learnings: [],
      score: calculateFallbackScore(categoryTotals)
    };
  }
}

/**
 * Build prompt for narrative generation
 */
function buildNarrativePrompt(sessions, categoryTotals, userGoal) {
  const totalMinutes = Object.values(categoryTotals).reduce((sum, val) => sum + val, 0) / 60;

  const sessionsText = sessions.map(s =>
    `- ${s.start_time ? new Date(s.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'N/A'}: ${s.app} - ${s.task} (${s.duration_mins}m, ${s.category})`
  ).join('\n');

  const goalText = userGoal ? `\n\nUSER'S GOAL: ${userGoal}\nPlease reference their progress toward this goal in the narrative.` : '';

  return `You are analyzing a user's daily activity and generating a personalized summary.

ACTIVITY DATA:
Total active time: ${Math.round(totalMinutes)} minutes
Work: ${Math.round(categoryTotals.work / 60)} minutes
Learning: ${Math.round(categoryTotals.learning / 60)} minutes
Browsing: ${Math.round(categoryTotals.browsing / 60)} minutes
Entertainment: ${Math.round(categoryTotals.entertainment / 60)} minutes

SESSIONS (chronological):
${sessionsText}${goalText}

Generate a JSON response with:
{
  "daily_narrative": "A 2-3 sentence personalized summary of their day, highlighting patterns and key activities. Be encouraging and specific.",
  "key_learnings": ["Learning 1", "Learning 2", "Learning 3"],  // Up to 3 specific things they worked on or learned
  "productivity_score": 75  // 0-100 score based on work/learning vs browsing/entertainment ratio
}

Make it personal, specific to their actual activities, and encouraging!`;
}

/**
 * Calculate fallback productivity score
 */
function calculateFallbackScore(categoryTotals) {
  const total = Object.values(categoryTotals).reduce((sum, val) => sum + val, 0);
  if (total === 0) return 0;

  const productive = categoryTotals.work + categoryTotals.learning;
  return Math.round((productive / total) * 100);
}

export default {
  analyzeScreenshot,
  validateAnalysisSchema,
  generateDailyNarrative
};
