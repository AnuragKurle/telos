/**
 * Summary Generator Service
 * 
 * Generates daily summaries from Firestore usage data when client hasn't uploaded one.
 * Used by the email scheduler to ensure users always get their daily reports.
 */

import admin from 'firebase-admin';
import { generateDailyNarrative } from './gemini.js';

/**
 * Generate a daily summary from Firestore usage data
 * 
 * @param {string} userEmail - User's email address
 * @param {string} userId - User's Firebase UID
 * @param {string} dateStr - Date in YYYY-MM-DD format
 * @returns {Promise<Object|null>} Summary object or null if no data
 */
export async function generateSummaryFromUsage(userEmail, userId, dateStr) {
    console.log(`[SUMMARY_GEN] Generating summary for ${userEmail} on ${dateStr}`);

    const db = admin.firestore();

    try {
        // Get user's usage document
        const usageDoc = await db.collection('usage').doc(userId).get();

        if (!usageDoc.exists) {
            console.log(`[SUMMARY_GEN] No usage document found for user ${userId}`);
            return null;
        }

        const usageData = usageDoc.data();

        // Extract data for target date from dayBucket
        const dayData = usageData.dayBucket?.[dateStr];

        if (!dayData || !dayData.captures || dayData.captures.length === 0) {
            console.log(`[SUMMARY_GEN] No captures found for ${dateStr}`);
            return null;
        }

        console.log(`[SUMMARY_GEN] Found ${dayData.captures.length} captures for ${dateStr}`);

        // Aggregate by category
        const categoryTotals = {
            work: 0,
            learning: 0,
            browsing: 0,
            entertainment: 0,
            idle: 0
        };

        // Each capture represents ~30 seconds
        const CAPTURE_DURATION_SECONDS = 30;

        dayData.captures.forEach(capture => {
            const category = (capture.simple_category || capture.category || 'browsing').toLowerCase();
            if (categoryTotals.hasOwnProperty(category)) {
                categoryTotals[category] += CAPTURE_DURATION_SECONDS;
            } else {
                categoryTotals.browsing += CAPTURE_DURATION_SECONDS;
            }
        });

        // Build timeline/sessions for AI context
        const sessions = extractSessions(dayData.captures);

        console.log(`[SUMMARY_GEN] Extracted ${sessions.length} sessions`);
        console.log(`[SUMMARY_GEN] Category totals:`, {
            work: `${Math.floor(categoryTotals.work / 60)}m`,
            learning: `${Math.floor(categoryTotals.learning / 60)}m`,
            browsing: `${Math.floor(categoryTotals.browsing / 60)}m`,
            entertainment: `${Math.floor(categoryTotals.entertainment / 60)}m`
        });

        // Get user's goal (if set)
        const userDoc = await db.collection('users').doc(userEmail).get();
        const userGoal = userDoc.exists ? userDoc.data().analysisGoal : null;

        // Generate narrative using Gemini
        const aiResult = await generateDailyNarrative(sessions, categoryTotals, userGoal);

        // Calculate productivity score
        const productivityScore = calculateProductivityScore(categoryTotals);

        // Build apps list from captures
        const appUsage = {};
        dayData.captures.forEach(capture => {
            const appName = capture.app_name || 'Unknown';
            const category = capture.simple_category || capture.category || 'browsing';
            if (!appUsage[appName]) {
                appUsage[appName] = { name: appName, category: category, count: 0 };
            }
            appUsage[appName].count++;
        });

        const apps = Object.values(appUsage)
            .sort((a, b) => b.count - a.count)
            .slice(0, 8)
            .map(app => ({
                name: app.name,
                category: app.category,
                minutes: Math.floor(app.count * 30 / 60) // ~30 sec per capture
            }));

        // Build timeline for email
        const timeline = sessions.map(s => ({
            app: s.app,
            task: s.task,
            category: s.category,
            start: s.start_time ? new Date(s.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }) : 'N/A',
            duration_mins: s.duration_mins
        }));

        // Build summary object with all data needed for email
        const summary = {
            date: dateStr,  // Required by email template
            work_seconds: categoryTotals.work,
            learning_seconds: categoryTotals.learning,
            browsing_seconds: categoryTotals.browsing,
            entertainment_seconds: categoryTotals.entertainment,
            productivity_score: aiResult.score || productivityScore,
            daily_narrative: aiResult.narrative,
            key_learnings_json: JSON.stringify(aiResult.learnings || []),
            context_switches: sessions.length,
            apps: apps,           // Top apps with usage
            timeline: timeline    // Activity timeline
        };

        console.log(`[SUMMARY_GEN] Generated summary with score: ${summary.productivity_score}`);

        return summary;

    } catch (error) {
        console.error(`[SUMMARY_GEN] Error generating summary:`, error);
        return null;
    }
}

/**
 * Extract sessions from captures
 * Groups consecutive captures by app/task into sessions
 * 
 * @param {Array} captures - Array of capture objects
 * @returns {Array} Array of session objects
 */
function extractSessions(captures) {
    if (!captures || captures.length === 0) return [];

    const sessions = [];
    let currentSession = null;

    // Sort by timestamp
    const sortedCaptures = [...captures].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeA - timeB;
    });

    sortedCaptures.forEach(capture => {
        const key = `${capture.app_name}:${capture.task || 'Unknown'}`;

        if (!currentSession || currentSession.key !== key) {
            // Start new session
            if (currentSession && currentSession.count >= 2) {
                sessions.push(currentSession);
            }

            currentSession = {
                key: key,
                app: capture.app_name,
                task: capture.task || 'Unknown',
                category: capture.simple_category || capture.category || 'browsing',
                start_time: capture.timestamp,
                end_time: capture.timestamp,
                count: 1
            };
        } else {
            // Continue current session
            currentSession.end_time = capture.timestamp;
            currentSession.count++;
        }
    });

    // Add last session
    if (currentSession && currentSession.count >= 2) {
        sessions.push(currentSession);
    }

    // Return top sessions by duration (limit to 12)
    return sessions
        .sort((a, b) => b.count - a.count)
        .slice(0, 12)
        .map(s => ({
            app: s.app,
            task: s.task.substring(0, 80), // Truncate long tasks
            category: s.category,
            duration_mins: Math.floor(s.count * 30 / 60), // ~30 sec per capture
            start_time: s.start_time,
            end_time: s.end_time
        }));
}

/**
 * Calculate productivity score (0-100) based on category totals
 * Heuristic: More work/learning = higher score
 * 
 * @param {Object} categoryTotals - Category totals in seconds
 * @returns {number} Score from 0-100
 */
function calculateProductivityScore(categoryTotals) {
    const total = categoryTotals.work + categoryTotals.learning +
        categoryTotals.browsing + categoryTotals.entertainment;

    if (total === 0) return 0;

    const productiveTime = categoryTotals.work + categoryTotals.learning;
    const productiveRatio = productiveTime / total;

    // Base score from productive ratio (0-80)
    let score = Math.round(productiveRatio * 80);

    // Bonus for absolute productive time (up to 20 points)
    const productiveHours = productiveTime / 3600;
    const bonus = Math.min(20, Math.floor(productiveHours / 2) * 5);

    score = Math.min(100, score + bonus);

    return score;
}

export default {
    generateSummaryFromUsage
};
