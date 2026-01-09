import dotenv from 'dotenv';
import { initializeFirebase } from './src/config/firebase.js';
import { sendDailyReport } from './src/services/email.js';

dotenv.config();
initializeFirebase();

const testSummary = {
    date: '2026-01-08',
    work_seconds: 5400,
    learning_seconds: 360,
    browsing_seconds: 3600,
    entertainment_seconds: 1800,
    productivity_score: 75,
    daily_narrative: 'You had a productive day with balanced work and learning time. Most of your day was spent on focused work tasks, with good breaks for learning new skills.',
    key_learnings_json: '["Successfully integrated SendGrid email service", "Configured timezone-aware email scheduling", "Set up secure API key storage in GCP Secret Manager"]',
    context_switches: 5
};

console.log('Sending test email...');
sendDailyReport('anuragkurle@gmail.com', testSummary)
    .then(result => {
        console.log('✅ Test result:', result);
        if (result.success) {
            console.log('\n🎉 SUCCESS! Check your inbox at anuragkurle@gmail.com');
        } else {
            console.log('\n❌ FAILED:', result.error);
        }
        process.exit(result.success ? 0 : 1);
    })
    .catch(err => {
        console.error('❌ Test failed:', err);
        process.exit(1);
    });
