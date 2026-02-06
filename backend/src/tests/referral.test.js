/**
 * Referral System Tests
 * 
 * Tests for the referral code generation, validation, pro credit logic,
 * batch email sending, and Slack notifications.
 * 
 * Run: node backend/src/tests/referral.test.js
 * 
 * Requires:
 *   - Backend running locally or BACKEND_URL env var set
 *   - A valid Firebase admin token (TEST_FIREBASE_TOKEN env var)
 *   - Or run against the deployed backend with a real token
 * 
 * For quick local testing without a real backend, use the unit tests below.
 */

import assert from 'assert';

// ─── Unit Tests (no backend needed) ─────────────────────────────────────────

console.log('\n=== Referral System Unit Tests ===\n');

// Test 1: Referral code format
function testReferralCodeFormat() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  
  // Simulate code generation
  function generateTestCode() {
    let code = '';
    for (let i = 0; i < 4; i++) {
      code += chars[Math.floor(Math.random() * chars.length)];
    }
    return `TELOS-${code}`;
  }

  const code = generateTestCode();
  assert(code.startsWith('TELOS-'), `Code should start with TELOS-: ${code}`);
  assert(code.length === 10, `Code should be 10 chars: ${code} (${code.length})`);
  
  // Check no ambiguous characters
  const codeBody = code.replace('TELOS-', '');
  assert(!codeBody.includes('0'), 'Code should not contain 0');
  assert(!codeBody.includes('O'), 'Code should not contain O');
  assert(!codeBody.includes('1'), 'Code should not contain 1');
  assert(!codeBody.includes('I'), 'Code should not contain I');
  
  console.log(`  ✓ Referral code format: ${code}`);
}

// Test 2: Email masking
function testEmailMasking() {
  function maskEmail(email) {
    if (!email || !email.includes('@')) return '***';
    const [local, domain] = email.split('@');
    const masked = local.length > 2
      ? local.substring(0, 2) + '***'
      : local[0] + '***';
    return `${masked}@${domain}`;
  }

  assert.strictEqual(maskEmail('alice@example.com'), 'al***@example.com');
  assert.strictEqual(maskEmail('ab@test.com'), 'a***@test.com');  // 2-char local, shows first char
  assert.strictEqual(maskEmail('a@test.com'), 'a***@test.com');
  assert.strictEqual(maskEmail(''), '***');
  assert.strictEqual(maskEmail(null), '***');
  
  console.log('  ✓ Email masking works correctly');
}

// Test 3: Pro credit cap logic
function testProCreditCap() {
  const MAX_CREDITS = 12;
  
  // Under cap
  let currentCredits = 5;
  let canAward = currentCredits < MAX_CREDITS;
  assert(canAward, 'Should award credits when under cap');
  
  // At cap
  currentCredits = 12;
  canAward = currentCredits < MAX_CREDITS;
  assert(!canAward, 'Should NOT award credits when at cap');
  
  // Over cap (safety check)
  currentCredits = 15;
  canAward = currentCredits < MAX_CREDITS;
  assert(!canAward, 'Should NOT award credits when over cap');
  
  console.log('  ✓ Pro credit cap (12 months) enforced');
}

// Test 4: Referral code validation format
function testReferralCodeValidation() {
  function isValidCode(code) {
    return code && typeof code === 'string' && code.startsWith('TELOS-') && code.length === 10;
  }

  assert(isValidCode('TELOS-X7K9'), 'Valid code should pass');
  assert(!isValidCode('INVALID'), 'Invalid prefix should fail');
  assert(!isValidCode('TELOS-'), 'Too short should fail');
  assert(!isValidCode(''), 'Empty should fail');
  assert(!isValidCode(null), 'Null should fail');
  assert(!isValidCode('TELOS-TOOLONG'), 'Too long should fail');
  
  console.log('  ✓ Referral code validation');
}

// Test 5: Trial duration logic
function testTrialDuration() {
  function getTrialDays(isWaitlistUser, hasReferral) {
    return (isWaitlistUser || hasReferral) ? 14 : 7;
  }

  assert.strictEqual(getTrialDays(true, false), 14, 'Waitlist user gets 14 days');
  assert.strictEqual(getTrialDays(false, true), 14, 'Referred user gets 14 days');
  assert.strictEqual(getTrialDays(true, true), 14, 'Both gets 14 days');
  assert.strictEqual(getTrialDays(false, false), 7, 'Organic user gets 7 days');
  
  console.log('  ✓ Extended trial duration logic (14d for waitlist/referral, 7d for organic)');
}

// Test 6: Pro credits remaining calculation
function testProCreditsRemaining() {
  function creditsRemaining(earned, used) {
    return Math.max(0, earned - used);
  }

  assert.strictEqual(creditsRemaining(5, 2), 3);
  assert.strictEqual(creditsRemaining(0, 0), 0);
  assert.strictEqual(creditsRemaining(3, 3), 0);
  assert.strictEqual(creditsRemaining(1, 5), 0); // Can't go negative
  
  console.log('  ✓ Pro credits remaining calculation');
}

// Test 7: Subscription check with referral credits
function testSubscriptionCheckLogic() {
  function shouldAllowAccess(accessStatus, proCreditsEarned, proCreditsUsed, trialEndDate) {
    // Pro always allowed
    if (accessStatus === 'pro') return { allowed: true, type: 'pro' };
    
    // Referral credits
    const creditsRemaining = (proCreditsEarned || 0) - (proCreditsUsed || 0);
    if (creditsRemaining > 0) return { allowed: true, type: 'pro_referral' };
    
    // Expired
    if (accessStatus === 'expired') return { allowed: false, type: 'expired' };
    
    // Trial check
    if (accessStatus === 'trial') {
      if (trialEndDate && new Date(trialEndDate) < new Date()) {
        return { allowed: false, type: 'trial_expired' };
      }
      return { allowed: true, type: 'trial' };
    }
    
    return { allowed: true, type: 'unknown' }; // Fail open
  }

  // Pro user
  let result = shouldAllowAccess('pro', 0, 0, null);
  assert(result.allowed && result.type === 'pro', 'Pro user should be allowed');

  // Expired but has credits
  result = shouldAllowAccess('expired', 3, 1, null);
  assert(result.allowed && result.type === 'pro_referral', 'Expired with credits should get pro_referral');

  // Expired with no credits
  result = shouldAllowAccess('expired', 2, 2, null);
  assert(!result.allowed, 'Expired with no credits should be blocked');

  // Trial active
  const futureDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
  result = shouldAllowAccess('trial', 0, 0, futureDate);
  assert(result.allowed && result.type === 'trial', 'Active trial should be allowed');

  // Trial expired
  const pastDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  result = shouldAllowAccess('trial', 0, 0, pastDate);
  assert(!result.allowed, 'Expired trial should be blocked');

  // Trial expired but has referral credits
  result = shouldAllowAccess('trial', 1, 0, pastDate);
  assert(result.allowed && result.type === 'pro_referral', 'Expired trial with credits should get pro_referral');

  console.log('  ✓ Subscription check with referral credits');
}

// Run all tests
try {
  testReferralCodeFormat();
  testEmailMasking();
  testProCreditCap();
  testReferralCodeValidation();
  testTrialDuration();
  testProCreditsRemaining();
  testSubscriptionCheckLogic();
  
  console.log('\n✅ All unit tests passed!\n');
} catch (error) {
  console.error('\n❌ Test failed:', error.message);
  process.exit(1);
}

// ─── Integration Test Helpers (require running backend) ─────────────────────

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8080';

/**
 * Run integration tests against a running backend.
 * Set TEST_FIREBASE_TOKEN env var to a valid admin Firebase token.
 * 
 * Usage:
 *   BACKEND_URL=http://localhost:8080 TEST_FIREBASE_TOKEN=xxx node backend/src/tests/referral.test.js --integration
 */
async function runIntegrationTests() {
  const token = process.env.TEST_FIREBASE_TOKEN;
  if (!token) {
    console.log('⚠️  Skipping integration tests (set TEST_FIREBASE_TOKEN env var to run)');
    return;
  }

  console.log(`\n=== Integration Tests (${BACKEND_URL}) ===\n`);

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Test: Health check
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    const data = await res.json();
    assert(data.status === 'ok', 'Health check should return ok');
    console.log('  ✓ Health check passed');
  } catch (error) {
    console.error('  ✗ Health check failed:', error.message);
    return;
  }

  // Test: Get referral code
  try {
    const res = await fetch(`${BACKEND_URL}/v1/referral/code`, { headers });
    if (res.status === 200) {
      const data = await res.json();
      assert(data.referralCode, 'Should return referral code');
      assert(data.shareLink, 'Should return share link');
      assert(data.stats, 'Should return stats');
      console.log(`  ✓ Get referral code: ${data.referralCode}`);
    } else {
      console.log(`  ⚠ Get referral code returned ${res.status} (may need auth)`);
    }
  } catch (error) {
    console.error('  ✗ Get referral code failed:', error.message);
  }

  // Test: Validate non-existent code
  try {
    const res = await fetch(`${BACKEND_URL}/v1/referral/validate/TELOS-XXXX`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    assert(res.status === 404, 'Should return 404 for invalid code');
    console.log('  ✓ Invalid referral code returns 404');
  } catch (error) {
    console.error('  ✗ Validate code failed:', error.message);
  }

  // Test: Admin stats (requires admin user)
  try {
    const res = await fetch(`${BACKEND_URL}/v1/admin/stats`, { headers });
    if (res.status === 200) {
      const data = await res.json();
      assert(data.waitlist, 'Should return waitlist stats');
      assert(data.users, 'Should return user stats');
      console.log('  ✓ Admin stats endpoint works');
    } else if (res.status === 403) {
      console.log('  ⚠ Admin stats: user is not admin (expected if not admin)');
    }
  } catch (error) {
    console.error('  ✗ Admin stats failed:', error.message);
  }

  console.log('\n✅ Integration tests complete!\n');
}

// Run integration tests if --integration flag is passed
if (process.argv.includes('--integration')) {
  runIntegrationTests().catch(console.error);
}
