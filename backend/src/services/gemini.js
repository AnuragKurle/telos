/**
 * Gemini API Service
 * 
 * Calls Google Gemini API for screenshot analysis.
 * Uses server-side API key to keep prompts private.
 * 
 * Supports two modes:
 *  1. Direct Gemini API (default) - uses @google/generative-ai SDK
 *  2. Portkey (optional) - adds observability layer, enabled when PORTKEY_API_KEY is set
 */

import { GoogleGenerativeAI } from '@google/generative-ai';
import { getGeminiApiKey } from './secrets.js';
import { getScreenshotAnalysisPrompt } from './prompts.js';

/**
 * Portkey Configuration (optional)
 * When configured, routes calls through Portkey for observability.
 */
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY;
const PORTKEY_VIRTUAL_KEY = process.env.PORTKEY_VIRTUAL_KEY;
const PORTKEY_ENABLED = !!(PORTKEY_API_KEY && PORTKEY_VIRTUAL_KEY);

if (PORTKEY_ENABLED) {
  console.log('[GEMINI] Portkey enabled - calls routed through Portkey for observability');
} else {
  console.log('[GEMINI] Using direct Gemini API');
}

/**
 * Sanitize a string for use in HTTP headers (Portkey metadata).
 * Removes or replaces characters outside the ASCII byte range (0-255).
 */
function sanitizeForHeader(str) {
  if (!str) return 'unknown';
  // Replace non-ASCII characters with '?' to keep string readable
  return str.replace(/[^\x00-\xFF]/g, '?');
}

/**
 * Get Portkey client (only when Portkey is enabled)
 */
async function getPortkeyClient(traceId = null, userId = null, contextMetadata = {}) {
  if (!PORTKEY_ENABLED) return null;

  // Dynamic import to avoid crash when portkey-ai is not installed
  const { Portkey } = await import('portkey-ai');
  return new Portkey({
    apiKey: PORTKEY_API_KEY,
    virtualKey: PORTKEY_VIRTUAL_KEY,
    user: userId || 'backend-service',
    metadata: {
      call_type: 'screenshot_analysis',
      source: 'telos-backend',
      window_title: sanitizeForHeader(contextMetadata.window_title),
      app_name: sanitizeForHeader(contextMetadata.app_name),
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

const MODEL_NAME = 'gemini-2.5-flash';

/**
 * Refresh the cached API key and prompt data if stale.
 */
async function refreshCache() {
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
  return { apiKey: cachedApiKey, promptData: cachedPromptData };
}

/**
 * Call Gemini via Portkey's OpenAI-compatible API
 */
async function callViaPortkey(finalPrompt, imageUrl, userId, contextMetadata) {
  const portkey = await getPortkeyClient(`screenshot-${Date.now()}`, userId, contextMetadata);

  const response = await portkey.chat.completions.create({
    model: MODEL_NAME,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: finalPrompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    response_format: { type: 'json_object' },
    max_tokens: 4096,
    temperature: 0.4,
  });

  return response.choices[0].message.content;
}

/**
 * Call Gemini directly using the Google Generative AI SDK
 */
async function callDirectGemini(apiKey, finalPrompt, imageBuffer, mimeType) {
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({
    model: MODEL_NAME,
    generationConfig: {
      temperature: 0.4,
      maxOutputTokens: 4096,
      responseMimeType: 'application/json',
    },
  });

  const imagePart = {
    inlineData: {
      data: imageBuffer.toString('base64'),
      mimeType: mimeType,
    },
  };

  const result = await model.generateContent([finalPrompt, imagePart]);
  return result.response.text();
}

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
    const { apiKey, promptData } = await refreshCache();

    // Build context string from previous captures (similar to client logic)
    const contextStr = buildPreviousContext(previousCaptures);

    // Build system context string from metadata
    const systemContextStr = buildSystemContext(contextMetadata);

    // Replace both placeholders in prompt
    let finalPrompt = promptData.content.replace('{previous_context}', contextStr);
    finalPrompt = finalPrompt.replace('{system_context}', systemContextStr);

    // Call Gemini (via Portkey if configured, otherwise direct)
    let textResponse;
    if (PORTKEY_ENABLED) {
      const base64Image = imageBuffer.toString('base64');
      const imageUrl = `data:${mimeType};base64,${base64Image}`;
      textResponse = await callViaPortkey(finalPrompt, imageUrl, userId, contextMetadata);
    } else {
      textResponse = await callDirectGemini(apiKey, finalPrompt, imageBuffer, mimeType);
    }

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
    const prompt = buildNarrativePrompt(sessions, categoryTotals, userGoal);

    let resultText;

    if (PORTKEY_ENABLED) {
      const client = await getPortkeyClient('daily-narrative', 'system');
      const response = await client.chat.completions.create({
        model: MODEL_NAME,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
        response_format: { type: 'json_object' }
      });
      resultText = response.choices[0].message.content;
    } else {
      // Direct Gemini call for text-only request
      const { apiKey } = await refreshCache();
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({
        model: MODEL_NAME,
        generationConfig: {
          temperature: 0.7,
          responseMimeType: 'application/json',
        },
      });
      const result = await model.generateContent(prompt);
      resultText = result.response.text();
    }

    const parsed = JSON.parse(resultText);

    console.log('[GEMINI] Generated narrative successfully');

    return {
      narrative: parsed.daily_narrative || 'No narrative generated.',
      learnings: parsed.key_learnings || [],
      score: parsed.productivity_score || 50
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
  const workMin = Math.round(categoryTotals.work / 60);
  const learnMin = Math.round(categoryTotals.learning / 60);
  const browseMin = Math.round(categoryTotals.browsing / 60);
  const entMin = Math.round(categoryTotals.entertainment / 60);
  const productiveMin = workMin + learnMin;
  const productivePct = totalMinutes > 0 ? Math.round(productiveMin / Math.round(totalMinutes) * 100) : 0;

  const sessionsText = sessions.map(s =>
    `- ${s.start_time ? new Date(s.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'N/A'}: ${s.app} - ${s.task} (${s.duration_mins}m, ${s.category})`
  ).join('\n');

  // Find longest work session
  const workSessions = sessions.filter(s => s.category === 'work' || s.category === 'learning');
  const longestWork = workSessions.sort((a, b) => (b.duration_mins || 0) - (a.duration_mins || 0))[0];

  // Find most-used apps
  const appTime = {};
  sessions.forEach(s => { appTime[s.app] = (appTime[s.app] || 0) + (s.duration_mins || 0); });
  const topApps = Object.entries(appTime).sort((a, b) => b[1] - a[1]).slice(0, 3).map(a => `${a[0]} (${a[1]}m)`).join(', ');

  const goalText = userGoal ? `\nUSER'S CURRENT GOAL: "${userGoal}"\nYou MUST reference their progress toward this goal specifically.` : '';

  return `You are a sharp, direct productivity analyst writing a daily email summary. Your job is to tell the user something they DON'T already know about their day — patterns, blind spots, and honest observations.

HARD RULES:
- Do NOT start with "The user started the day..." or any variation of that.
- Do NOT be generic. No filler phrases like "a productive day" or "showing dedication."
- Reference SPECIFIC apps and tasks by name.
- Call out patterns: context switching, distraction spirals, deep work streaks.
- Be honest. If they spent 30% of their time on social media, say so directly.
- Write in second person ("you", "your") — this is a personal email to them.
- Keep it punchy: 3-4 sentences max. Every sentence must contain a concrete observation.

ACTIVITY DATA:
Total tracked time: ${Math.round(totalMinutes)} minutes
Work: ${workMin}m | Learning: ${learnMin}m | Browsing: ${browseMin}m | Entertainment: ${entMin}m
Productive time: ${productiveMin}m (${productivePct}% of total)
Number of sessions: ${sessions.length}
Top apps: ${topApps}${longestWork ? `\nLongest focused block: ${longestWork.app} — ${longestWork.task} (${longestWork.duration_mins}m)` : ''}

FULL SESSION TIMELINE (chronological):
${sessionsText}${goalText}

Generate a JSON response:
{
  "daily_narrative": "3-4 punchy sentences. Specific app names, times, patterns. No generic filler. Honest.",
  "key_learnings": [
    "A specific behavioral pattern you noticed (e.g., 'You context-switched 8 times between 2-3 PM — your focus fragmented after lunch')",
    "A concrete suggestion tied to their data (e.g., 'Your deepest work happened before 10 AM — consider protecting that window')",
    "An honest observation about time allocation (e.g., '45 minutes on YouTube between work blocks — that's almost as much as your longest focus session')"
  ],
  "productivity_score": 65
}

The productivity_score should be 0-100 based on:
- Ratio of work+learning to total (base)
- Penalize heavy context switching
- Reward long uninterrupted work blocks
- Penalize if entertainment > 20% of total

Be the analyst they'd pay for, not a generic AI cheerleader.`;
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
