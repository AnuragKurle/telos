import dotenv from 'dotenv';
import admin from 'firebase-admin';
import { initializeFirebase } from './src/config/firebase.js';

dotenv.config();

async function getUid() {
    if (!admin.apps.length) {
        initializeFirebase();
    }

    const db = admin.firestore();
    const userDoc = await db.collection('users').doc('anurag@userology.co').get();

    if (!userDoc.exists) {
        console.log('User not found!');
        process.exit(1);
    }

    const userData = userDoc.data();
    console.log('UID:', userData.uid);

    // Check if usage doc exists
    const usageDoc = await db.collection('usage').doc(userData.uid).get();
    console.log('Usage doc exists:', usageDoc.exists);

    if (usageDoc.exists) {
        const dates = Object.keys(usageDoc.data().dayBucket || {});
        console.log('Available dates:', dates.sort().slice(-5));
    }

    process.exit(0);
}

getUid();
