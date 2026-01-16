import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { initializeFirebase } from './src/config/firebase.js';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';

dotenv.config();

async function debugTimeline() {
    if (!admin.apps.length) {
        initializeFirebase();
    }

    const summary = await generateSummaryFromUsage('anurag@userology.co', 'DuysxZoYCsgnTd4B8H2bToTcSCG2', '2026-01-10');

    if (!summary) {
        console.error('Failed to generate summary');
        process.exit(1);
    }

    console.log('\n=== YOUR DAY TIMELINE (as sent in email) ===\n');

    // Group by app to check for duplicates
    const appCounts = {};
    summary.timeline.forEach((item, i) => {
        console.log(`${i + 1}. ${item.app}`);
        console.log(`   Time: ${item.start}, Duration: ${item.duration_mins}m`);
        console.log(`   Task: ${item.task.substring(0, 60)}`);
        console.log('');

        if (!appCounts[item.app]) {
            appCounts[item.app] = [];
        }
        appCounts[item.app].push(item.duration_mins);
    });

    console.log('\n=== DUPLICATE CHECK ===\n');
    Object.entries(appCounts).forEach(([app, durations]) => {
        if (durations.length > 1) {
            console.log(`❌ ${app}: appears ${durations.length} times with durations: ${durations.join(', ')}m`);
        } else {
            console.log(`✅ ${app}: appears once with ${durations[0]}m`);
        }
    });

    process.exit(0);
}

debugTimeline().catch(e => {
    console.error('Error:', e);
    process.exit(1);
});
