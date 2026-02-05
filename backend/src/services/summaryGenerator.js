/**
 * Summary Generator Service
 * 
 * Generates daily summaries from Firestore usage data when client hasn't uploaded one.
 * Used by the email scheduler to ensure users always get their daily reports.
 */

import admin from 'firebase-admin';
import { generateDailyNarrative } from './gemini.js';
import { decrypt } from './encryption.js';

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

        // Decrypt sensitive capture fields if encrypted
        dayData.captures = dayData.captures.map(capture => ({
            ...capture,
            app_name: capture.app_name ? decrypt(capture.app_name) : capture.app_name,
            task: capture.task ? decrypt(capture.task) : capture.task,
        }));

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

        // Enhanced Analytics
        const deepWorkSessions = analyzeDeepWork(dayData.captures);
        const contextSwitches = countContextSwitches(dayData.captures);
        const hourlyActivity = analyzeHourlyActivity(dayData.captures);
        const focusQuality = analyzeFocusQuality(dayData.captures, sessions);
        const weeklyComparison = await getWeeklyComparison(usageData, dateStr, categoryTotals);

        // Get user's goal (if set) - look up by UID first, fallback to email for legacy
        let userGoal = null;
        const userDoc = await db.collection('users').doc(userId).get();
        if (userDoc.exists) {
            userGoal = userDoc.data().analysisGoal || null;
        }

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

        // Build timeline for email - sort chronologically by start time
        const timeline = sessions
            .sort((a, b) => {
                const timeA = new Date(a.start_time).getTime();
                const timeB = new Date(b.start_time).getTime();
                return timeA - timeB;  // Chronological order
            })
            .map(s => ({
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
            context_switches: contextSwitches,
            apps: apps,           // Top apps with usage
            timeline: timeline,    // Activity timeline

            // Enhanced analytics
            deep_work_sessions: deepWorkSessions,
            hourly_activity: hourlyActivity,
            focus_quality: focusQuality,
            weekly_comparison: weeklyComparison,
            total_captures: dayData.captures.length,
            peak_productivity_hour: hourlyActivity.peak_hour,
            distraction_time: focusQuality.distraction_minutes
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
 * Creates TWO types of aggregations:
 * 1. Aggregate sessions: Total time per app (for AI context)
 * 2. Detailed activities: Most significant individual activities with context
 *
 * @param {Array} captures - Array of capture objects
 * @returns {Array} Array of session objects for AI and email display
 */
function extractSessions(captures) {
    if (!captures || captures.length === 0) return [];

    // Sort by timestamp
    const sortedCaptures = [...captures].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeA - timeB;
    });

    // Phase 1: Create chronological sessions (consecutive captures with same app:task)
    const chronologicalSessions = [];
    let currentSession = null;

    sortedCaptures.forEach(capture => {
        const key = `${capture.app_name}:${capture.task || 'Unknown'}`;

        if (!currentSession || currentSession.key !== key) {
            // Save previous session if it exists
            if (currentSession) {
                chronologicalSessions.push(currentSession);
            }

            // Start new session
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

    // Don't forget the last session
    if (currentSession) {
        chronologicalSessions.push(currentSession);
    }

    // Phase 2: Aggregate by app across the entire day
    const appAggregates = {};

    chronologicalSessions.forEach(session => {
        const app = session.app;
        if (!appAggregates[app]) {
            appAggregates[app] = {
                app: app,
                category: session.category,
                totalCount: 0,
                activities: []
            };
        }
        appAggregates[app].totalCount += session.count;
        // Keep track of significant activities (>= 2 captures = 1 minute)
        if (session.count >= 2) {
            appAggregates[app].activities.push({
                task: session.task,
                count: session.count,
                start_time: session.start_time
            });
        }
    });

    // Phase 3: Create meaningful session objects for AI and email
    // Show top apps with their most significant activity
    const meaningfulSessions = Object.values(appAggregates)
        .sort((a, b) => b.totalCount - a.totalCount)
        .slice(0, 12)  // Top 12 apps
        .map(agg => {
            // Find the most significant activity for this app
            const topActivity = agg.activities.sort((a, b) => b.count - a.count)[0];

            return {
                app: agg.app,
                task: topActivity ? topActivity.task.substring(0, 100) : 'Various activities',
                category: agg.category,
                duration_mins: Math.floor(agg.totalCount * 30 / 60),
                start_time: topActivity ? topActivity.start_time : sortedCaptures[0].timestamp,
                // Add context about multiple activities
                activity_count: agg.activities.length
            };
        })
        .filter(s => s.duration_mins >= 1);  // Only show sessions >= 1 minute

    return meaningfulSessions;
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

/**
 * Analyze deep work sessions - sustained focus periods (>= 10 minutes on work/learning)
 */
function analyzeDeepWork(captures) {
    const sortedCaptures = [...captures].sort((a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const deepWorkSessions = [];
    let currentSession = null;

    sortedCaptures.forEach(capture => {
        const category = (capture.simple_category || capture.category || '').toLowerCase();
        const isProductive = category === 'work' || category === 'learning';

        if (!isProductive) {
            // End current session if it exists and meets threshold
            if (currentSession && currentSession.count >= 20) { // 20 captures = 10 mins
                deepWorkSessions.push(currentSession);
            }
            currentSession = null;
            return;
        }

        const app = capture.app_name;
        const timeDiff = currentSession
            ? (new Date(capture.timestamp).getTime() - new Date(currentSession.endTime).getTime()) / 1000
            : 0;

        // Continue session if same app and < 3 minutes gap
        if (currentSession && currentSession.app === app && timeDiff < 180) {
            currentSession.count++;
            currentSession.endTime = capture.timestamp;
        } else {
            // Save previous session if it meets threshold
            if (currentSession && currentSession.count >= 20) {
                deepWorkSessions.push(currentSession);
            }
            // Start new session
            currentSession = {
                app: app,
                category: category,
                startTime: capture.timestamp,
                endTime: capture.timestamp,
                count: 1
            };
        }
    });

    // Don't forget last session
    if (currentSession && currentSession.count >= 20) {
        deepWorkSessions.push(currentSession);
    }

    return deepWorkSessions.map(s => ({
        app: s.app,
        category: s.category,
        start: new Date(s.startTime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
        duration_mins: Math.floor(s.count * 30 / 60)
    }));
}

/**
 * Count context switches (app changes)
 */
function countContextSwitches(captures) {
    if (captures.length === 0) return 0;

    const sortedCaptures = [...captures].sort((a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    let switches = 0;
    let lastApp = sortedCaptures[0].app_name;

    for (let i = 1; i < sortedCaptures.length; i++) {
        const currentApp = sortedCaptures[i].app_name;
        if (currentApp !== lastApp) {
            switches++;
            lastApp = currentApp;
        }
    }

    return switches;
}

/**
 * Analyze activity by hour of day
 */
function analyzeHourlyActivity(captures) {
    const hourlyData = {};

    // Initialize all hours
    for (let h = 0; h < 24; h++) {
        hourlyData[h] = { work: 0, learning: 0, browsing: 0, entertainment: 0, total: 0 };
    }

    captures.forEach(capture => {
        const hour = new Date(capture.timestamp).getHours();
        const category = (capture.simple_category || capture.category || 'browsing').toLowerCase();

        if (hourlyData[hour][category] !== undefined) {
            hourlyData[hour][category] += 0.5; // 30 seconds = 0.5 minutes
        }
        hourlyData[hour].total += 0.5;
    });

    // Find peak productivity hour (most work + learning)
    let peakHour = 0;
    let peakProductiveTime = 0;

    Object.entries(hourlyData).forEach(([hour, data]) => {
        const productiveTime = data.work + data.learning;
        if (productiveTime > peakProductiveTime) {
            peakProductiveTime = productiveTime;
            peakHour = parseInt(hour);
        }
    });

    // Find peak activity hour (most total activity)
    let peakActivityHour = 0;
    let peakActivity = 0;

    Object.entries(hourlyData).forEach(([hour, data]) => {
        if (data.total > peakActivity) {
            peakActivity = data.total;
            peakActivityHour = parseInt(hour);
        }
    });

    // Convert to array for easy consumption
    const hourlyArray = Object.entries(hourlyData)
        .filter(([_, data]) => data.total > 0)
        .map(([hour, data]) => ({
            hour: parseInt(hour),
            ...data
        }));

    return {
        hourly_breakdown: hourlyArray,
        peak_hour: peakHour,
        peak_activity_hour: peakActivityHour
    };
}

/**
 * Analyze focus quality - fragmentation vs sustained focus
 */
function analyzeFocusQuality(captures, sessions) {
    // Calculate average session length
    const avgSessionLength = sessions.length > 0
        ? sessions.reduce((sum, s) => sum + s.duration_mins, 0) / sessions.length
        : 0;

    // Count short sessions (< 3 mins) - indicators of fragmentation
    const shortSessions = sessions.filter(s => s.duration_mins < 3).length;
    const fragmentationRatio = sessions.length > 0 ? shortSessions / sessions.length : 0;

    // Calculate distraction time (entertainment + non-work browsing)
    let distractionTime = 0;
    captures.forEach(capture => {
        const category = (capture.simple_category || capture.category || '').toLowerCase();
        if (category === 'entertainment' || (category === 'browsing' && !isProductiveBrowsing(capture))) {
            distractionTime += 0.5; // 30 seconds
        }
    });

    // Focus quality score (0-100)
    let qualityScore = 100;
    qualityScore -= fragmentationRatio * 30; // Penalty for fragmentation
    qualityScore -= Math.min(30, (distractionTime / 60) * 5); // Penalty for distractions
    if (avgSessionLength < 5) qualityScore -= 20; // Penalty for short average session

    return {
        avg_session_length: Math.round(avgSessionLength * 10) / 10,
        fragmentation_ratio: Math.round(fragmentationRatio * 100),
        short_sessions: shortSessions,
        distraction_minutes: Math.round(distractionTime),
        focus_quality_score: Math.max(0, Math.round(qualityScore))
    };
}

/**
 * Helper: Check if browsing activity is productive
 */
function isProductiveBrowsing(capture) {
    const task = (capture.task || '').toLowerCase();
    const app = (capture.app_name || '').toLowerCase();

    const productiveKeywords = ['documentation', 'stackoverflow', 'github', 'research', 'learning', 'tutorial', 'course'];
    const distractingKeywords = ['youtube', 'reddit', 'instagram', 'twitter', 'facebook', 'tiktok'];

    return productiveKeywords.some(kw => task.includes(kw) || app.includes(kw)) &&
           !distractingKeywords.some(kw => app.includes(kw));
}

/**
 * Get weekly comparison data
 */
async function getWeeklyComparison(usageData, currentDate, currentTotals) {
    const dayBucket = usageData.dayBucket || {};

    // Get last 7 days (excluding current)
    const currentDateTime = new Date(currentDate).getTime();
    const sevenDaysAgo = currentDateTime - (7 * 24 * 60 * 60 * 1000);

    const recentDays = Object.keys(dayBucket)
        .filter(date => {
            const dateTime = new Date(date).getTime();
            return dateTime >= sevenDaysAgo && dateTime < currentDateTime;
        })
        .sort();

    if (recentDays.length === 0) {
        return {
            has_history: false,
            avg_work: 0,
            avg_learning: 0,
            avg_total: 0
        };
    }

    // Calculate averages
    let totalWork = 0, totalLearning = 0, totalAll = 0;

    recentDays.forEach(date => {
        const dayData = dayBucket[date];
        if (dayData && dayData.captures) {
            dayData.captures.forEach(capture => {
                const category = (capture.simple_category || capture.category || '').toLowerCase();
                if (category === 'work') totalWork += 30;
                if (category === 'learning') totalLearning += 30;
                totalAll += 30;
            });
        }
    });

    const avgWork = Math.floor(totalWork / recentDays.length / 60);
    const avgLearning = Math.floor(totalLearning / recentDays.length / 60);
    const avgTotal = Math.floor(totalAll / recentDays.length / 60);

    const currentWork = Math.floor(currentTotals.work / 60);
    const currentLearning = Math.floor(currentTotals.learning / 60);
    const currentTotal = Math.floor((currentTotals.work + currentTotals.learning + currentTotals.browsing + currentTotals.entertainment) / 60);

    return {
        has_history: true,
        days_compared: recentDays.length,
        avg_work: avgWork,
        avg_learning: avgLearning,
        avg_total: avgTotal,
        current_work: currentWork,
        current_learning: currentLearning,
        current_total: currentTotal,
        work_diff: currentWork - avgWork,
        total_diff: currentTotal - avgTotal
    };
}

export default {
    generateSummaryFromUsage
};
