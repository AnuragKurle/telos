
import admin from 'firebase-admin';
import dotenv from 'dotenv';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';
import { initializeFirebase } from './src/config/firebase.js';

dotenv.config();

// Helpers copied from email.js because they are not exported
function testShouldSendEmail(prefs, currentUTCHour) {
    const timezone = prefs.timezone || 'UTC';
    let sendHour;
    if (typeof prefs.preferredHour === 'number') {
        sendHour = prefs.preferredHour;
    } else if (prefs.sendTime) {
        sendHour = parseInt(prefs.sendTime.split(':')[0], 10);
    } else {
        sendHour = 9;
    }

    const timezoneOffsets = {
        'UTC': 0,
        'America/New_York': -5,
        'America/Los_Angeles': -8,
        'Europe/London': 0,
        'Europe/Paris': 1,
        'Asia/Kolkata': 5.5,
        'Asia/Tokyo': 9,
        'Australia/Sydney': 11,
    };

    const offset = timezoneOffsets[timezone] || 0;
    const targetUTCHour = (sendHour - offset + 24) % 24;
    const targetHourRounded = Math.round(targetUTCHour);
    const hourMatches = targetHourRounded === currentUTCHour;

    console.log(`[DEBUG] Timezone: ${timezone}, SendHour: ${sendHour}, Offset: ${offset}`);
    console.log(`[DEBUG] TargetUTC: ${targetUTCHour}, Rounded: ${targetHourRounded}, CurrentUTC: ${currentUTCHour}`);
    console.log(`[DEBUG] Match: ${hourMatches}`);
    return hourMatches;
}

async function runDebug() {
    console.log("Starting Debug Script...");

    // Initialize
    if (!admin.apps.length) {
        initializeFirebase();
    }
    const db = admin.firestore();
    const userEmail = 'anurag@userology.co';

    console.log(`Checking user: ${userEmail}`);
    const docRef = db.collection('users').doc(userEmail);
    const doc = await docRef.get();

    if (!doc.exists) {
        console.error("User not found!");
        return;
    }

    const userData = doc.data();
    console.log("User Data (Email Prefs):", userData.emailReports);

    // 1. Check Schedule Logic
    console.log("\n--- Checking Schedule Logic ---");
    const now = new Date();
    const currentUTCHour = now.getUTCHours();
    console.log(`Current Server Time: ${now.toISOString()} (UTC Hour: ${currentUTCHour})`);

    // Test for matches in a 24h cycle
    console.log("Searching for matching hours...");
    for (let h = 0; h < 24; h++) {
        if (testShouldSendEmail(userData.emailReports || {}, h)) {
            console.log(`!!! MATCH FOUND AT UTC HOUR ${h} !!!`);
        }
    }

    // 2. Check Data Availability
    console.log("\n--- Checking Data Availability ---");
    // Check for yesterday
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];
    console.log(`Target Date: ${dateStr}`);

    const summaries = await db.collection('daily_summaries')
        .where('userEmail', '==', userEmail)
        .where('date', '==', dateStr)
        .get();

    if (!summaries.empty) {
        console.log(`Found existing summary for ${dateStr}. ID: ${summaries.docs[0].id}`);
        console.log(`Email Sent Status: ${summaries.docs[0].data().emailSent}`);
    } else {
        console.log(`No existing summary for ${dateStr}. Testing generation...`);
        const summary = await generateSummaryFromUsage(userEmail, userData.uid, dateStr);
        if (summary) {
            console.log("SUCCESS: Summary generated successfully.");
            console.log(`Productivity Score: ${summary.productivity_score}`);
            console.log(`App Count: ${summary.apps.length}`);
        } else {
            console.error("FAILURE: Could not generate summary. Likely missing usage data.");

            // Check usage doc specifically
            const usageDoc = await db.collection('usage').doc(userData.uid).get();
            if (usageDoc.exists) {
                const dayBucket = usageDoc.data().dayBucket || {};
                const dayData = dayBucket[dateStr];
                if (!dayData) {
                    console.log(`No entry in dayBucket for ${dateStr}`);
                    console.log("Available dates:", Object.keys(dayBucket).sort().slice(-5));
                } else {
                    console.log(`Entry exists for ${dateStr}, captures length: ${dayData.captures?.length}`);
                }
            } else {
                console.log("Usage document does not exist.");
            }
        }
    }
}

runDebug().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
