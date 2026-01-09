/**
 * Simple script to check what collections exist and help locate your account
 */

console.log(`
📋 Firebase Collections Overview
================================

Based on code analysis, your Firebase should have:

1. **users** collection (keyed by email)
   - Example: anuragkurle27@gmail.com
   - Contains: accessStatus, emailReports, trial info, etc.
   - This is WHERE email prefs should be set

2. **usage** collection (keyed by UID)
   - Example: DuysxZoYCsgnTd4B8H2bToTcSCG2
   - Contains: dailyCount, dayBucket, hourBucket, hourlyCount

3. **waitlist** collection (for website signups)
   - Contains emails from landing page

4. **daily_summaries** collection
   - Contains generated reports ready to email

================================

🔍 Finding Your Account:

Option 1 - Check if 'users' collection exists:
1. Go to Firebase Console Firestore
2. Look for 'users' collection in left sidebar
3. If it exists, find document: anuragkurle27@gmail.com
4. If you DON'T see 'users' collection, it means you haven't completed onboarding yet

Option 2 - Check your client code:
1. The client should call POST /auth/verify-access with your email
2. This creates the user document in the 'users' collection
3. Check if you've run this step in the app

================================

📸 Next Step:
Take a screenshot showing:
1. All collections in your Firebase (left sidebar)
2. If 'users' exists, click it and show the documents inside

Then I can give you exact instructions for your setup.
`);
