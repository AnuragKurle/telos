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
 */
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY || 'AapMbWHuS0fvPfOSF9z4iOBuEYTm';
const PORTKEY_VIRTUAL_KEY = process.env.PORTKEY_VIRTUAL_KEY || 'google-virtual-881dd3';

/**
 * Initialize Portkey client (singleton)
 */
let portkeyClient = null;
function getPortkeyClient(traceId = null, userId = null) {
  // Create fresh client with metadata for each call
  return new Portkey({
    apiKey: PORTKEY_API_KEY,
    virtualKey: PORTKEY_VIRTUAL_KEY,
    metadata: {
      _user: userId || 'backend-service',
      call_type: 'screenshot_analysis',
      source: 'telos-backend',
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
 * @returns {Promise<object>} Analysis result matching API contract schema
 */
export async function analyzeScreenshot(imageBuffer, mimeType = 'image/png', previousCaptures = [], userId = null) {
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
    const finalPrompt = promptData.content.replace('{previous_context}', contextStr);

    // Convert image to base64 for multimodal input
    const base64Image = imageBuffer.toString('base64');
    const imageUrl = `data:${mimeType};base64,${base64Image}`;

    // Get Portkey client with user metadata
    const portkey = getPortkeyClient(`screenshot-${Date.now()}`, userId);

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

export default {
  analyzeScreenshot,
  validateAnalysisSchema,
};
