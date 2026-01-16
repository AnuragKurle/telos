import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { initializeFirebase } from './src/config/firebase.js';

dotenv.config();

async function debugData() {
    if (!admin.apps.length) {
        initializeFirebase();
    }

    const db = admin.firestore();
    const userEmail = 'anurag@userology.co';
    const dateStr = '2026-01-10';

    const userDoc = await db.collection('users').doc(userEmail).get();
    const uid = userDoc.data().uid;

    const usageDoc = await db.collection('usage').doc(uid).get();
    const dayData = usageDoc.data().dayBucket[dateStr];

    console.log(`Total captures: ${dayData.captures.length}`);

    // Sample first 5 and last 5 captures
    console.log('\nFirst 5 captures:');
    dayData.captures.slice(0, 5).forEach((c, i) => {
        console.log(`  ${i+1}. ${c.timestamp} - ${c.app_name} - ${c.task?.substring(0, 50)} [${c.simple_category}]`);
    });

    console.log('\nLast 5 captures:');
    dayData.captures.slice(-5).forEach((c, i) => {
        console.log(`  ${i+1}. ${c.timestamp} - ${c.app_name} - ${c.task?.substring(0, 50)} [${c.simple_category}]`);
    });

    // Check timestamps to see total span
    const timestamps = dayData.captures.map(c => new Date(c.timestamp).getTime()).sort((a, b) => a - b);
    const firstTime = new Date(timestamps[0]);
    const lastTime = new Date(timestamps[timestamps.length - 1]);
    const spanMinutes = (lastTime - firstTime) / 1000 / 60;

    console.log(`\nTime span: ${firstTime.toLocaleTimeString()} to ${lastTime.toLocaleTimeString()} (${Math.round(spanMinutes)} minutes)`);
    console.log(`Capture density: ${dayData.captures.length} captures over ${Math.round(spanMinutes)} minutes = ${Math.round(dayData.captures.length / (spanMinutes / 30))}x expected`);

    // Group by app
    const byApp = {};
    dayData.captures.forEach(c => {
        const app = c.app_name;
        if (!byApp[app]) byApp[app] = 0;
        byApp[app]++;
    });

    console.log('\nTop apps by capture count:');
    Object.entries(byApp)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .forEach(([app, count]) => {
            console.log(`  ${app}: ${count} captures (${Math.round(count * 30 / 60)} mins)`);
        });

    process.exit(0);
}

debugData();
