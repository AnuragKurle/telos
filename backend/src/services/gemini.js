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
 * @returns {Promise<object>} Analysis result matching API contract schema
 */
export async function analyzeScreenshot(imageBuffer, mimeType = 'image/png') {
  try {
    // Get API key and prompt
    const apiKey = await getGeminiApiKey();
    const prompt = await getScreenshotAnalysisPrompt();

    // Convert image to base64
    const base64Image = imageBuffer.toString('base64');

    // Prepare request payload for Gemini API
    const requestBody = {
      contents: [
        {
          parts: [
            { text: prompt.content },
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
        maxOutputTokens: 1024,
        responseMimeType: 'application/json',
      },
    };

    // Call Gemini API (using gemini-2.0-flash-exp)
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${apiKey}`,
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

    // Use AI-generated values directly (AI autonomy!)
    // Only use fallbacks if AI didn't provide them
    const category = analysis.category || 'Unknown';
    const emoji = analysis.category_emoji || FALLBACK_METADATA.emoji;
    const color = analysis.category_color || FALLBACK_METADATA.color;
    const simpleCategory = analysis.simple_category || 'idle';

    // Return standardized response matching API contract
    return {
      category,
      simple_category: simpleCategory,
      app: analysis.app || 'Unknown',
      task: analysis.task || 'Activity detected',
      confidence: typeof analysis.confidence === 'number' ? analysis.confidence : 0.5,
      detailed_context: analysis.detailed_context || {},  // Now an object
      category_emoji: emoji,
      category_color: color,
      analysis_version: prompt.version,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error('❌ Screenshot analysis failed:', error.message);
    throw error;
  }
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

