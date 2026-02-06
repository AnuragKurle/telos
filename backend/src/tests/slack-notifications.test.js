/**
 * Slack Notifications Smoke Test
 * 
 * Sends one test message for each new notification type to verify
 * they're wired up correctly and appearing in Slack.
 * 
 * All messages are prefixed with [TEST] so they're distinguishable.
 * 
 * Usage:
 *   1. Set up environment variables (or use .env file)
 *   2. Run: node backend/src/tests/slack-notifications.test.js
 *   3. Check your Slack channel for the test messages
 * 
 * Required env vars:
 *   - SLACK_SIGNUP_WEBHOOK or SLACK_WEBHOOK (from Google Secret Manager in prod)
 *   - For local testing: set directly in .env file
 */

import dotenv from 'dotenv';
dotenv.config();

// Import all notification functions
import {
  sendReferralCodeCopiedNotification,
  sendReferralLinkUsedNotification,
  sendReferralActivatedNotification,
  sendProCreditAppliedNotification,
  sendBatchEmailStartedNotification,
  sendBatchEmailCompletedNotification,
  sendDailyBetaDigestNotification,
} from '../services/slack.js';

const TEST_EMAIL = 'test@telos.dev';
const TEST_CODE = 'TELOS-TEST';

async function runSlackTests() {
  console.log('\n=== Slack Notification Smoke Tests ===\n');
  console.log('Sending test notifications to Slack...\n');

  const results = [];

  // 1. Referral Code Copied
  try {
    const result = await sendReferralCodeCopiedNotification(`[TEST] ${TEST_EMAIL}`, TEST_CODE);
    results.push({ name: 'Referral Code Copied', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Referral Code Copied`);
  } catch (error) {
    results.push({ name: 'Referral Code Copied', success: false, error: error.message });
    console.log(`  ✗ Referral Code Copied: ${error.message}`);
  }

  // 2. Referral Link Used
  try {
    const result = await sendReferralLinkUsedNotification(TEST_CODE, `[TEST] ${TEST_EMAIL}`, '[TEST] friend@example.com');
    results.push({ name: 'Referral Link Used', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Referral Link Used`);
  } catch (error) {
    results.push({ name: 'Referral Link Used', success: false, error: error.message });
    console.log(`  ✗ Referral Link Used: ${error.message}`);
  }

  // 3. Referral Activated
  try {
    const result = await sendReferralActivatedNotification(`[TEST] ${TEST_EMAIL}`, '[TEST] friend@example.com', TEST_CODE, 3);
    results.push({ name: 'Referral Activated', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Referral Activated`);
  } catch (error) {
    results.push({ name: 'Referral Activated', success: false, error: error.message });
    console.log(`  ✗ Referral Activated: ${error.message}`);
  }

  // 4. Pro Credit Applied
  try {
    const result = await sendProCreditAppliedNotification(`[TEST] ${TEST_EMAIL}`, 2);
    results.push({ name: 'Pro Credit Applied', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Pro Credit Applied`);
  } catch (error) {
    results.push({ name: 'Pro Credit Applied', success: false, error: error.message });
    console.log(`  ✗ Pro Credit Applied: ${error.message}`);
  }

  // 5. Batch Email Started
  try {
    const result = await sendBatchEmailStartedNotification('[TEST] Batch 1', 15, 'invitation', `[TEST] ${TEST_EMAIL}`);
    results.push({ name: 'Batch Email Started', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Batch Email Started`);
  } catch (error) {
    results.push({ name: 'Batch Email Started', success: false, error: error.message });
    console.log(`  ✗ Batch Email Started: ${error.message}`);
  }

  // 6. Batch Email Completed
  try {
    const result = await sendBatchEmailCompletedNotification('[TEST] Batch 1', 14, 1, 12000);
    results.push({ name: 'Batch Email Completed', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Batch Email Completed`);
  } catch (error) {
    results.push({ name: 'Batch Email Completed', success: false, error: error.message });
    console.log(`  ✗ Batch Email Completed: ${error.message}`);
  }

  // 7. Daily Beta Digest
  try {
    const result = await sendDailyBetaDigestNotification({
      newSignupsToday: 5,
      activeUsers24h: 12,
      referralCodesShared: 3,
      referralsActivated: 1,
      waitlistRemaining: 87,
      activationRate: 42,
      proCreditsAwardedToday: 1,
    });
    results.push({ name: 'Daily Beta Digest', ...result });
    console.log(`  ${result.success ? '✓' : '✗'} Daily Beta Digest`);
  } catch (error) {
    results.push({ name: 'Daily Beta Digest', success: false, error: error.message });
    console.log(`  ✗ Daily Beta Digest: ${error.message}`);
  }

  // Summary
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;

  console.log(`\n${'─'.repeat(50)}`);
  console.log(`Results: ${passed} passed, ${failed} failed out of ${results.length} tests`);

  if (failed > 0) {
    console.log('\nFailed tests:');
    results.filter(r => !r.success).forEach(r => {
      console.log(`  ✗ ${r.name}: ${r.error}`);
    });
  }

  if (passed === results.length) {
    console.log('\n✅ All Slack notifications working! Check your Slack channel.\n');
  } else if (passed === 0 && results.every(r => r.error === 'No webhook' || r.error === 'No credentials')) {
    console.log('\n⚠️  No Slack webhook configured. Set SLACK_SIGNUP_WEBHOOK or SLACK_WEBHOOK in .env');
    console.log('   This is expected for local development without Slack credentials.\n');
  } else {
    console.log('\n⚠️  Some notifications failed. Check the errors above.\n');
  }
}

runSlackTests().catch(console.error);
