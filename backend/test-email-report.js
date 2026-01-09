/**
 * Test script to verify email report sending
 * Run: node test-email-report.js
 */

import dotenv from 'dotenv';
import admin from 'firebase-admin';
import sgMail from '@sendgrid/mail';
import { getSecret } from './src/services/secrets.js';

dotenv.config();

// Initialize Firebase using the same approach as the server
const projectId = process.env.FIREBASE_PROJECT_ID;

if (!projectId) {
  console.error('❌ FIREBASE_PROJECT_ID environment variable is required');
  process.exit(1);
}

if (!admin.apps.length) {
  admin.initializeApp({
    projectId: projectId
  });
  console.log(`✓ Firebase initialized for project: ${projectId}`);
}

async function testEmailReport() {
  const db = admin.firestore();
  const userEmail = 'anurag@userology.co';

  console.log('\n=== Testing Email Report ===\n');

  // 1. Check user document
  console.log('1. Checking user document...');
  const userDoc = await db.collection('users').doc(userEmail).get();

  if (!userDoc.exists) {
    console.error('❌ User document not found!');
    process.exit(1);
  }

  const userData = userDoc.data();
  console.log('✓ User found:', {
    email: userData.email,
    status: userData.status,
    plan: userData.plan,
    emailReports: userData.emailReports
  });

  // 2. Check if email reports are enabled
  if (!userData.emailReports?.enabled) {
    console.error('❌ Email reports not enabled for this user');
    process.exit(1);
  }
  console.log('✓ Email reports enabled');

  // 3. Create test summary data
  console.log('\n2. Creating test summary data...');
  const testSummary = {
    date: new Date().toISOString().split('T')[0],
    work_seconds: 4 * 3600,        // 4 hours
    learning_seconds: 1.5 * 3600,  // 1.5 hours
    browsing_seconds: 0.5 * 3600,  // 30 mins
    entertainment_seconds: 0.25 * 3600, // 15 mins
    productivity_score: 78,
    daily_narrative: "Today was a productive day! You spent most of your time on focused work, with some time dedicated to learning new skills. Your entertainment consumption was minimal, showing excellent self-discipline.",
    key_learnings_json: JSON.stringify([
      "Learned about Firebase Admin SDK integration",
      "Explored SendGrid email templates",
      "Studied timezone handling in JavaScript"
    ]),
    context_switches: 12
  };
  console.log('✓ Test summary created');

  // 4. Initialize SendGrid
  console.log('\n3. Initializing SendGrid...');
  try {
    const apiKey = await getSecret(process.env.SENDGRID_API_KEY_SECRET_NAME || 'SENDGRID_API_KEY');
    sgMail.setApiKey(apiKey);
    console.log('✓ SendGrid initialized');
  } catch (error) {
    console.error('❌ Failed to initialize SendGrid:', error.message);
    process.exit(1);
  }

  // 5. Generate email content
  const date = new Date(testSummary.date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const workMin = Math.floor(testSummary.work_seconds / 60);
  const learningMin = Math.floor(testSummary.learning_seconds / 60);
  const browsingMin = Math.floor(testSummary.browsing_seconds / 60);
  const entertainmentMin = Math.floor(testSummary.entertainment_seconds / 60);
  const totalMin = workMin + learningMin + browsingMin + entertainmentMin;

  const score = Math.round(testSummary.productivity_score || 0);
  let scoreColor = '#e74c3c';
  let scoreEmoji = '📊';
  if (score >= 75) { scoreColor = '#27ae60'; scoreEmoji = '🌟'; }
  else if (score >= 50) { scoreColor = '#f39c12'; scoreEmoji = '⭐'; }

  let keyLearnings = JSON.parse(testSummary.key_learnings_json || '[]');
  const learningsHTML = keyLearnings.length > 0 ? `
    <div style="margin: 25px 0;">
      <h2 style="color: #2c3e50; margin-bottom: 15px;">🎓 Key Learnings</h2>
      <ul style="color: #34495e; line-height: 1.6;">
        ${keyLearnings.map(l => `<li style="margin: 8px 0;">${l}</li>`).join('')}
      </ul>
    </div>
  ` : '';

  const progressBars = [
    { label: 'Work', minutes: workMin, color: '#3498db' },
    { label: 'Learning', minutes: learningMin, color: '#9b59b6' },
    { label: 'Browsing', minutes: browsingMin, color: '#95a5a6' },
    { label: 'Entertainment', minutes: entertainmentMin, color: '#e67e22' }
  ].map(({ label, minutes, color }) => {
    const percentage = totalMin > 0 ? Math.round((minutes / totalMin) * 100) : 0;
    return `
      <div style="margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
          <span style="color: #2c3e50; font-weight: 500;">${label}</span>
          <span style="color: #7f8c8d;">${minutes}m (${percentage}%)</span>
        </div>
        <div style="background: #ecf0f1; height: 24px; border-radius: 12px; overflow: hidden;">
          <div style="background: ${color}; height: 100%; width: ${percentage}%;"></div>
        </div>
      </div>
    `;
  }).join('');

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
      <h1 style="color: white; margin: 0; font-size: 28px;">📊 Daily Activity Report</h1>
      <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">${date}</p>
    </div>
    
    <!-- Productivity Score -->
    <div style="text-align: center; padding: 30px 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
      <div style="font-size: 48px; margin-bottom: 10px;">${scoreEmoji}</div>
      <div style="font-size: 42px; font-weight: bold; color: ${scoreColor}; margin-bottom: 5px;">
        ${score}/100
      </div>
      <div style="color: #6c757d; font-size: 16px;">Productivity Score</div>
    </div>
    
    <!-- Content -->
    <div style="padding: 30px;">
      
      <!-- Daily Narrative -->
      <div style="margin-bottom: 25px;">
        <h2 style="color: #2c3e50; margin-bottom: 15px;">📝 Daily Summary</h2>
        <p style="color: #34495e; line-height: 1.7; font-size: 15px; background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
          ${testSummary.daily_narrative}
        </p>
      </div>
      
      <!-- Time Breakdown -->
      <div style="margin: 25px 0;">
        <h2 style="color: #2c3e50; margin-bottom: 15px;">⏱️ Time Breakdown</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
          <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #dee2e6;">
            <span style="font-size: 32px; font-weight: bold; color: #2c3e50;">${totalMin}</span>
            <span style="color: #7f8c8d; font-size: 16px; margin-left: 5px;">minutes</span>
            <div style="color: #6c757d; font-size: 14px; margin-top: 5px;">Total Active Time</div>
          </div>
          ${progressBars}
        </div>
      </div>
      
      ${learningsHTML}
      
      <!-- Stats Footer -->
      <div style="margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">
        <div style="color: #6c757d; font-size: 14px;">
          <strong style="color: #2c3e50;">${testSummary.context_switches || 0}</strong> context switches
        </div>
      </div>
      
    </div>
    
    <!-- Footer -->
    <div style="background: #2c3e50; padding: 20px; text-align: center;">
      <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px;">
        Generated by Telos Screen Tracker
      </p>
      <p style="color: rgba(255,255,255,0.5); margin: 5px 0 0 0; font-size: 12px;">
        AI-powered activity insights
      </p>
    </div>
    
  </div>
</body>
</html>
  `;

  // 6. Send test email
  console.log('\n4. Sending test email...');
  const msg = {
    to: userEmail,
    from: {
      email: process.env.SENDGRID_FROM_EMAIL || 'anuragkurle27@gmail.com',
      name: process.env.SENDGRID_FROM_NAME || 'Telos'
    },
    subject: `📊 Daily Activity Report - ${date} (TEST)`,
    text: `Test report for ${date}. Productivity Score: ${score}/100`,
    html: html
  };

  try {
    await sgMail.send(msg);
    console.log('\n✅ SUCCESS! Email sent to', userEmail);
    console.log('\nCheck your inbox for the daily report!');
  } catch (error) {
    console.error('\n❌ FAILED:', error.message);
    if (error.response) {
      console.error('Details:', error.response.body);
    }
  }

  process.exit(0);
}

testEmailReport().catch(console.error);
