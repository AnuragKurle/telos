import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { initializeFirebase } from './src/config/firebase.js';
import { generateSummaryFromUsage } from './src/services/summaryGenerator.js';

dotenv.config();

async function testAggregation() {
    if (!admin.apps.length) {
        initializeFirebase();
    }

    const summary = await generateSummaryFromUsage('anurag@userology.co', 'DuysxZoYCsgnTd4B8H2bToTcSCG2', '2026-01-10');

    if (!summary) {
        console.error('Failed to generate summary');
        process.exit(1);
    }

    console.log('\n=== TOP APPS (from summary.apps) ===');
    summary.apps.forEach((a, i) => {
        console.log(`  ${i+1}. ${a.name}: ${a.minutes}m [${a.category}]`);
    });

    console.log('\n=== TIMELINE/YOUR DAY (from summary.timeline) ===');
    summary.timeline.forEach((t, i) => {
        console.log(`  ${i+1}. ${t.app}: ${t.duration_mins}m at ${t.start}`);
        console.log(`      Task: ${t.task?.substring(0, 60)}`);
    });

    console.log('\n=== ANALYSIS ===');
    console.log(`Timeline has ${summary.timeline.length} entries`);

    // Check for duplicates
    const appCounts = {};
    summary.timeline.forEach(t => {
        appCounts[t.app] = (appCounts[t.app] || 0) + 1;
    });

    console.log('\nApps appearing multiple times in timeline:');
    Object.entries(appCounts).forEach(([app, count]) => {
        if (count > 1) {
            console.log(`  - ${app}: ${count} times`);
        }
    });

    process.exit(0);
}

testAggregation().catch(e => {
    console.error('Error:', e);
    process.exit(1);
});
