/**
 * Setup script to enable automated daily reports via API
 * Uses the existing backend server instead of direct Firebase access
 */

const userEmail = 'anuragkurle27@gmail.com';
const deliveryEmail = 'anurag@userology.co';

console.log('\n📧 Setting up automated reports for', userEmail);
console.log('   Delivery to:', deliveryEmail);
console.log('\n🔧 To complete setup, run these commands:\n');

console.log('1. Update user account status to "pro":');
console.log('   Use Firebase Console or send API request to update user document\n');

console.log('2. Enable email reports:');
console.log('   Update the user document with these fields:');
console.log('   {');
console.log('     "accessStatus": "pro",');
console.log('     "emailReports": {');
console.log('       "enabled": true,');
console.log('       "deliveryEmail": "anurag@userology.co",');
console.log('       "timezone": "Asia/Kolkata",');
console.log('       "preferredHour": 21  // 9 PM IST');
console.log('     }');
console.log('   }\n');

console.log('3. Verify scheduler is running:');
console.log('   The backend scheduler runs every hour');
console.log('   Check logs to confirm it\'s calling sendDailyReports()\n');

console.log('📝 Alternative: Use Firebase Console directly:');
console.log('   1. Go to https://console.firebase.google.com/project/telos-tracker/firestore');
console.log('   2. Navigate to users collection → anuragkurle27@gmail.com');
console.log('   3. Add/update the fields shown above\n');

console.log('✅ Once configured, you\'ll receive daily reports at ~9 PM IST');
console.log('   based on activity tracked throughout the day.\n');
