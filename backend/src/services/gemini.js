/**
 * Gemini API Service
 * 
 * Calls Google Gemini API for screenshot analysis.
 * Uses server-side API key to keep prompts private.
 */

import { getGeminiApiKey } from './secrets.js';
import { getScreenshotAnalysisPrompt } from './prompts.js';

/**
 * Fallback metadata (used only if AI doesn't provide emoji/color)
 */
const FALLBACK_METADATA = {
  emoji: '❓',
  color: '#9CA3AF',
};

/**
 * Call Gemini API to analyze a screenshot
 * 
 * @param {Buffer} imageBuffer - Screenshot image data
 * @param {string} mimeType - Image MIME type (e.g., "image/png")
 * @param {Array} previousCaptures - Previous captures for context
 * @returns {Promise<object>} Analysis result matching API contract schema
 */
export async function analyzeScreenshot(imageBuffer, mimeType = 'image/png', previousCaptures = []) {
  try {
    // Get API key and prompt
    const apiKey = await getGeminiApiKey();
    const promptData = await getScreenshotAnalysisPrompt();

    // Build context string from previous captures (similar to client logic)
    const contextStr = buildPreviousContext(previousCaptures);
    const finalPrompt = promptData.content.replace('{previous_context}', contextStr);

    // Convert image to base64
    const base64Image = imageBuffer.toString('base64');

    // Define response schema to prevent "Unknown" fallbacks
    const responseSchema = {
      type: "object",
      properties: {
        simple_category: {
          type: "string",
          enum: ["work", "learning", "browsing", "entertainment", "idle"]
        },
        category: { type: "string" },
        category_emoji: { type: "string" },
        category_color: { type: "string" },
        app: { type: "string" },
        task: { type: "string" },
        confidence: { type: "number" },
        detailed_context: {
          type: "object",
          properties: {
            file_name: { type: "string" },
            cursor_position: { type: "string" },
            browser_url: { type: "string" },
            full_description: { type: "string" },
            progress_from_last: { type: "string" },
            ai_observations: { type: "string" }
          }
        }
      },
      required: ["simple_category", "category", "category_emoji", "category_color", "app", "task", "confidence"]
    };

    // Prepare request payload for Gemini API
    const requestBody = {
      contents: [
        {
          parts: [
            { text: finalPrompt },
            {
              inline_data: {
                mime_type: mimeType,
                data: base64Image,
              },
            },
          ],
        },
      ],
      generationConfig: {
        temperature: 0.4,
        maxOutputTokens: 4096,
        responseMimeType: 'application/json',
        responseSchema: responseSchema,
        // Enable thinking mode for gemini-2.5-flash
        // -1 = dynamic thinking budget (recommended)
        // 0 = disable thinking
        // >0 = specific token budget (e.g., 1024)
        thinkingConfig: {
          thinkingBudget: -1,
        },
      },
    };

    // Use the explicitly requested gemini-2.5-flash model
    const model = "gemini-2.5-flash";
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Gemini API error:', response.status, errorText);
      throw new Error(`Gemini API returned ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    // Extract the generated content
    if (!data.candidates || data.candidates.length === 0) {
      throw new Error('No candidates returned from Gemini API');
    }

    const candidate = data.candidates[0];
    if (!candidate.content || !candidate.content.parts || candidate.content.parts.length === 0) {
      throw new Error('No content parts in Gemini response');
    }

    const textResponse = candidate.content.parts[0].text;

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

