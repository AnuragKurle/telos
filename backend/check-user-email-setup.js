import dotenv from 'dotenv';
import admin from 'firebase-admin';

dotenv.config();

const projectId = process.env.FIREBASE_PROJECT_ID;

if (!admin.apps.length) {
    admin.initializeApp({
        projectId: projectId
    });
}

const db = admin.firestore();

async function checkUserEmailSetup() {
    const userEmail = 'anurag@userology.co'; // Your email

    console.log('\n🔍 Checking Email Report Setup for:', userEmail);
    console.log('='.repeat(60));

    // 1. Check user document
    console.log('\n1. Checking user document...');
    const userDoc = await db.collection('users').doc(userEmail).get();

    if (!userDoc.exists) {
        console.log('❌ User document NOT found in Firestore!');
        console.log('\n💡 Solution: You need to create a user document first.');
        console.log('   Run: node create-user-document.js');
        return;
    }

    const userData = userDoc.data();
    console.log('✅ User document exists');
    console.log('   Email Reports Config:', JSON.stringify(userData.emailReports, null, 2));

    // 2. Check daily summaries
    console.log('\n2. Checking daily summaries...');
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];

    const summariesSnapshot = await db.collection('daily_summaries')
        .where('userEmail', '==', userEmail)
        .orderBy('date', 'desc')
        .limit(5)
        .get();

    if (summariesSnapshot.empty) {
        console.log('❌ No daily summaries found!');
        console.log('\n💡 Solution: The client needs to upload daily summaries.');
        console.log('   - Run the desktop app and let it generate a daily summary');
        console.log('   - Or manually upload using: node send-real-report.js');
    } else {
        console.log(`✅ Found ${summariesSnapshot.size} daily summaries:`);
        summariesSnapshot.forEach(doc => {
            const data = doc.data();
            console.log(`   - ${data.date}: emailSent=${data.emailSent || false}`);
        });

        // Check for yesterday's summary
        const yesterdaySnapshot = await db.collection('daily_summaries')
            .where('userEmail', '==', userEmail)
            .where('date', '==', dateStr)
            .limit(1)
            .get();

        if (yesterdaySnapshot.empty) {
            console.log(`\n⚠️  No summary for yesterday (${dateStr})`);
            console.log('   This is why you didn\'t get an email!');
        } else {
            const yesterdayData = yesterdaySnapshot.docs[0].data();
            console.log(`\n📊 Yesterday's summary (${dateStr}):`);
            console.log('   Email sent:', yesterdayData.emailSent || false);
            if (yesterdayData.emailSentAt) {
                console.log('   Sent at:', yesterdayData.emailSentAt.toDate());
            }
        }
    }

    // 3. Check scheduler logs
    console.log('\n3. Scheduler Status:');
    console.log('   The scheduler runs hourly on Cloud Run');
    console.log('   Last check showed NO scheduler logs - this means:');
    console.log('   - Scheduler might not be running');
    console.log('   - OR no users were ready for email at the last hour');

    console.log('\n' + '='.repeat(60));
    console.log('✅ Diagnosis complete!');

    process.exit(0);
}

checkUserEmailSetup().catch(err => {
    console.error('❌ Error:', err);
    process.exit(1);
});
