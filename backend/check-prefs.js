import admin from 'firebase-admin';

admin.initializeApp({
    projectId: process.env.FIREBASE_PROJECT_ID || 'gen-lang-client-0772617718'
});

const db = admin.firestore();

async function checkUserPreferences() {
    const email = 'anurag@userology.co';
    console.log(`Checking preferences for ${email}...`);

    const usersSnapshot = await db.collection('users')
        .where('email', '==', email)
        .limit(1)
        .get();

    if (usersSnapshot.empty) {
        console.log('User not found!');
        return;
    }

    const userDoc = usersSnapshot.docs[0];
    const userData = userDoc.data();
    const prefs = userData.emailReports || {};

    console.log('Current Email Preferences:');
    console.log(JSON.stringify(prefs, null, 2));

    // Check if we need to update
    if (prefs.sendTime !== '21:00' || prefs.timezone !== 'Asia/Kolkata' || !prefs.enabled) {
        console.log('\nUpdating to 21:00 IST...');

        await userDoc.ref.update({
            'emailReports.sendTime': '21:00',
            'emailReports.timezone': 'Asia/Kolkata',
            'emailReports.enabled': true,
            'emailReports.frequency': 'daily'
        });
        console.log('✅ Updated successfully');
    } else {
        console.log('\n✅ Already configured correctly for 9 PM IST');
    }
}

checkUserPreferences().catch(console.error);
