/**
 * Setup script to enable automated daily reports
 * - Upgrades account to pro
 * - Enables email reports with timezone preferences
 */

import admin from 'firebase-admin';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Initialize Firebase Admin
const projectId = process.env.FIREBASE_PROJECT_ID || 'telos-tracker';

if (!admin.apps.length) {
    admin.initializeApp({
        projectId: projectId,
    });
    console.log(`✅ Firebase initialized for project: ${projectId}`);
}

const db = admin.firestore();

async function setupUserReports() {
    const userEmail = 'anuragkurle27@gmail.com';
    const deliveryEmail = 'anurag@userology.co';

    console.log(`\n📧 Setting up automated reports for ${userEmail}`);
    console.log(`   Delivery to: ${deliveryEmail}\n`);

    try {
        const userRef = db.collection('users').doc(userEmail);
        const userDoc = await userRef.get();

        if (!userDoc.exists) {
            console.log('❌ User not found in database. Please sign in to the app first.');
            process.exit(1);
        }

        const userData = userDoc.data();
        console.log(`📊 Current status: ${userData.accessStatus || 'unknown'}`);

        // Upgrade to pro and enable email reports
        const updates = {
            accessStatus: 'pro',
            lastUpdated: admin.firestore.FieldValue.serverTimestamp(),
            'emailReports.enabled': true,
            'emailReports.deliveryEmail': deliveryEmail,
            'emailReports.timezone': 'Asia/Kolkata',  // IST timezone
            'emailReports.preferredHour': 21,  // 9 PM IST = 15:30 UTC (approximately)
        };

        await userRef.update(updates);

        console.log('\n✅ Account upgraded to PRO');
        console.log('✅ Email reports enabled');
        console.log(`✅ Reports will be sent to: ${deliveryEmail}`);
        console.log(`✅ Delivery time: ~9:00 PM IST (21:00) daily`);
        console.log('\n📝 Configuration saved:');
        console.log('   - Timezone: Asia/Kolkata (IST)');
        console.log('   - Preferred hour: 21 (9 PM local time)');
        console.log('\n⏰ Scheduler runs hourly, so your first email will arrive');
        console.log('   at the next scheduled run after activity data is available.\n');

    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    } finally {
        process.exit(0);
    }
}

setupUserReports();
