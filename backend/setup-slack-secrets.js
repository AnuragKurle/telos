#!/usr/bin/env node

/**
 * Setup Slack Secrets in GCP Secret Manager
 * 
 * This script helps you configure Slack webhooks in GCP Secret Manager
 * so they're not stored in the GitHub repo.
 * 
 * Usage:
 *   node setup-slack-secrets.js check
 *   node setup-slack-secrets.js setup
 */

import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import { getSlackWebhook, getSlackBotToken } from './src/services/secrets.js';
import readline from 'readline';

const PROJECT_ID = process.env.GCP_PROJECT_ID || 'gen-lang-client-0772617718';
const client = new SecretManagerServiceClient();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

/**
 * Check if a secret exists and is accessible
 */
async function checkSecret(secretName) {
  try {
    const name = `projects/${PROJECT_ID}/secrets/${secretName}/versions/latest`;
    const [response] = await client.accessSecretVersion({ name });
    const value = response.payload.data.toString('utf8');
    return { exists: true, value: value.substring(0, 20) + '...' };
  } catch (error) {
    if (error.code === 5) {
      return { exists: false, error: 'Secret not found' };
    }
    return { exists: false, error: error.message };
  }
}

/**
 * Create or update a secret
 */
async function createOrUpdateSecret(secretName, secretValue) {
  try {
    const parent = `projects/${PROJECT_ID}`;
    
    // Try to create the secret first
    try {
      await client.createSecret({
        parent,
        secretId: secretName,
        secret: {
          replication: {
            automatic: {},
          },
        },
      });
      console.log(`✓ Created secret: ${secretName}`);
    } catch (error) {
      if (error.code === 6) {
        // Secret already exists, that's fine
        console.log(`ℹ Secret ${secretName} already exists`);
      } else {
        throw error;
      }
    }

    // Add the secret version
    const secretPath = `projects/${PROJECT_ID}/secrets/${secretName}`;
    await client.addSecretVersion({
      parent: secretPath,
      payload: {
        data: Buffer.from(secretValue, 'utf8'),
      },
    });

    console.log(`✓ Added new version to ${secretName}`);
    return true;
  } catch (error) {
    console.error(`✗ Failed to create/update ${secretName}:`, error.message);
    return false;
  }
}

/**
 * Check current status of Slack secrets
 */
async function checkStatus() {
  console.log('\n🔍 Checking Slack secrets configuration...\n');
  
  // Check SLACK_WEBHOOK
  console.log('1. Checking SLACK_WEBHOOK...');
  const webhookCheck = await checkSecret('SLACK_WEBHOOK');
  if (webhookCheck.exists) {
    console.log(`   ✓ SLACK_WEBHOOK exists: ${webhookCheck.value}`);
  } else {
    console.log(`   ✗ SLACK_WEBHOOK not found: ${webhookCheck.error}`);
  }

  // Check SLACK_BOT_TOKEN
  console.log('\n2. Checking SLACK_BOT_TOKEN...');
  const botTokenCheck = await checkSecret('SLACK_BOT_TOKEN');
  if (botTokenCheck.exists) {
    console.log(`   ✓ SLACK_BOT_TOKEN exists: ${botTokenCheck.value}`);
  } else {
    console.log(`   ✗ SLACK_BOT_TOKEN not found: ${botTokenCheck.error}`);
  }

  // Check SLACK_SIGNUP_WEBHOOK
  console.log('\n3. Checking SLACK_SIGNUP_WEBHOOK...');
  const signupWebhookCheck = await checkSecret('SLACK_SIGNUP_WEBHOOK');
  if (signupWebhookCheck.exists) {
    console.log(`   ✓ SLACK_SIGNUP_WEBHOOK exists: ${signupWebhookCheck.value}`);
  } else {
    console.log(`   ✗ SLACK_SIGNUP_WEBHOOK not found: ${signupWebhookCheck.error}`);
  }

  // Test if backend can access them
  console.log('\n4. Testing backend access...');
  try {
    const webhook = await getSlackWebhook();
    const botToken = await getSlackBotToken();
    
    if (webhook) {
      console.log(`   ✓ Backend can access SLACK_WEBHOOK`);
    } else if (botToken) {
      console.log(`   ✓ Backend can access SLACK_BOT_TOKEN`);
    } else {
      console.log(`   ⚠️ Backend cannot access any Slack credentials`);
    }
  } catch (error) {
    console.log(`   ✗ Backend access failed: ${error.message}`);
  }

  // Summary
  console.log('\n📊 Summary:');
  const hasWebhook = webhookCheck.exists;
  const hasBotToken = botTokenCheck.exists;
  const hasSignupWebhook = signupWebhookCheck.exists;

  if (hasWebhook || hasBotToken) {
    console.log('   ✅ Slack integration is configured');
    console.log('   ✅ Feedback notifications will work');
  } else {
    console.log('   ❌ No Slack credentials found');
    console.log('   ❌ Feedback notifications will fail');
    console.log('\n   Run: node setup-slack-secrets.js setup');
  }

  if (!hasSignupWebhook) {
    console.log('   ⚠️ Signup webhook not configured (optional)');
  }

  console.log('');
}

/**
 * Interactive setup wizard
 */
async function setupWizard() {
  console.log('\n🔧 Slack Secrets Setup Wizard\n');
  console.log('This will configure Slack webhooks in GCP Secret Manager.');
  console.log('You need at least ONE of the following:\n');
  console.log('  1. Slack Webhook URL (recommended, easier to set up)');
  console.log('  2. Slack Bot Token (advanced, more features)\n');
  
  const proceed = await question('Do you want to continue? (y/n): ');
  if (proceed.toLowerCase() !== 'y') {
    console.log('Setup cancelled.');
    return;
  }

  // Setup SLACK_WEBHOOK
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('1. Slack Webhook URL Setup');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('To get a Slack Webhook URL:');
  console.log('  1. Go to https://api.slack.com/apps');
  console.log('  2. Select your app (or create one)');
  console.log('  3. Go to "Incoming Webhooks"');
  console.log('  4. Enable webhooks and add to channel');
  console.log('  5. Copy the webhook URL\n');

  const webhookUrl = await question('Enter Slack Webhook URL (or press Enter to skip): ');
  
  if (webhookUrl && webhookUrl.trim()) {
    if (webhookUrl.startsWith('https://hooks.slack.com/')) {
      const success = await createOrUpdateSecret('SLACK_WEBHOOK', webhookUrl.trim());
      if (success) {
        console.log('✅ SLACK_WEBHOOK configured successfully!\n');
      }
    } else {
      console.log('⚠️ Warning: URL doesn\'t look like a Slack webhook. Saving anyway...');
      await createOrUpdateSecret('SLACK_WEBHOOK', webhookUrl.trim());
    }
  } else {
    console.log('Skipped SLACK_WEBHOOK.\n');
  }

  // Setup SLACK_BOT_TOKEN (optional)
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('2. Slack Bot Token Setup (Optional)');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('If you prefer using a bot token instead of webhook:');
  console.log('  1. Go to https://api.slack.com/apps');
  console.log('  2. Select your app');
  console.log('  3. Go to "OAuth & Permissions"');
  console.log('  4. Copy the "Bot User OAuth Token"\n');

  const botToken = await question('Enter Slack Bot Token (or press Enter to skip): ');
  
  if (botToken && botToken.trim()) {
    if (botToken.startsWith('xoxb-')) {
      const success = await createOrUpdateSecret('SLACK_BOT_TOKEN', botToken.trim());
      if (success) {
        console.log('✅ SLACK_BOT_TOKEN configured successfully!\n');
      }
    } else {
      console.log('⚠️ Warning: Token doesn\'t look like a bot token (should start with xoxb-). Saving anyway...');
      await createOrUpdateSecret('SLACK_BOT_TOKEN', botToken.trim());
    }
  } else {
    console.log('Skipped SLACK_BOT_TOKEN.\n');
  }

  // Setup SLACK_SIGNUP_WEBHOOK (optional)
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('3. Signup Webhook Setup (Optional)');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('Separate webhook for user signup notifications (optional).\n');

  const signupWebhook = await question('Enter Signup Webhook URL (or press Enter to skip): ');
  
  if (signupWebhook && signupWebhook.trim()) {
    await createOrUpdateSecret('SLACK_SIGNUP_WEBHOOK', signupWebhook.trim());
    console.log('✅ SLACK_SIGNUP_WEBHOOK configured!\n');
  } else {
    console.log('Skipped SLACK_SIGNUP_WEBHOOK.\n');
  }

  // Grant Cloud Run access
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('4. Granting Cloud Run Access');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log('Run these commands to grant Cloud Run access to secrets:\n');
  
  const serviceAccount = `${PROJECT_ID}@appspot.gserviceaccount.com`;
  
  if (webhookUrl && webhookUrl.trim()) {
    console.log(`gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \\`);
    console.log(`  --member="serviceAccount:${serviceAccount}" \\`);
    console.log(`  --role="roles/secretmanager.secretAccessor"\n`);
  }
  
  if (botToken && botToken.trim()) {
    console.log(`gcloud secrets add-iam-policy-binding SLACK_BOT_TOKEN \\`);
    console.log(`  --member="serviceAccount:${serviceAccount}" \\`);
    console.log(`  --role="roles/secretmanager.secretAccessor"\n`);
  }

  if (signupWebhook && signupWebhook.trim()) {
    console.log(`gcloud secrets add-iam-policy-binding SLACK_SIGNUP_WEBHOOK \\`);
    console.log(`  --member="serviceAccount:${serviceAccount}" \\`);
    console.log(`  --role="roles/secretmanager.secretAccessor"\n`);
  }

  console.log('✅ Setup complete!');
  console.log('\nNext steps:');
  console.log('  1. Run the commands above to grant Cloud Run access');
  console.log('  2. Deploy backend: .\\deploy-anywhere.ps1');
  console.log('  3. Test feedback: node setup-slack-secrets.js test\n');
}

/**
 * Test Slack integration
 */
async function testIntegration() {
  console.log('\n🧪 Testing Slack Integration...\n');

  try {
    // Import after checking we have the module
    const { sendSlackNotification } = await import('./src/services/slack.js');

    const channelId = process.env.SLACK_FEEDBACK_CHANNEL_ID || 'C0A6VF5PBUH';
    const message = '🧪 *Test Message from Telos Backend Setup*\n> This is a test to verify Slack integration is working.';
    
    const blocks = [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: message
        }
      },
      {
        type: 'context',
        elements: [
          {
            type: 'mrkdwn',
            text: `Sent from: setup-slack-secrets.js`
          }
        ]
      }
    ];

    console.log('Sending test message to Slack...');
    const result = await sendSlackNotification(channelId, message, blocks);

    if (result.success) {
      console.log(`\n✅ Success! Test message sent via ${result.method}`);
      console.log('   Check your Slack channel for the message.');
    } else {
      console.log(`\n✗ Failed to send test message: ${result.error}`);
      console.log('\nTroubleshooting:');
      console.log('  1. Check that secrets are created: node setup-slack-secrets.js check');
      console.log('  2. Verify Cloud Run has access to secrets');
      console.log('  3. Check webhook URL or bot token is valid');
    }
  } catch (error) {
    console.error('\n✗ Test failed:', error.message);
  }

  console.log('');
}

/**
 * Main function
 */
async function main() {
  const command = process.argv[2] || 'check';

  console.log(`
╔═══════════════════════════════════════════════════╗
║   Telos Slack Secrets Setup                       ║
║   Project: ${PROJECT_ID.padEnd(32)} ║
╚═══════════════════════════════════════════════════╝
  `);

  try {
    switch (command) {
      case 'check':
        await checkStatus();
        break;
      case 'setup':
        await setupWizard();
        break;
      case 'test':
        await testIntegration();
        break;
      default:
        console.log('Usage:');
        console.log('  node setup-slack-secrets.js check    - Check current status');
        console.log('  node setup-slack-secrets.js setup    - Interactive setup wizard');
        console.log('  node setup-slack-secrets.js test     - Test Slack integration');
        console.log('');
    }
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error('\nMake sure you have:');
    console.error('  1. GCP_PROJECT_ID environment variable set');
    console.error('  2. gcloud CLI authenticated');
    console.error('  3. Secret Manager API enabled');
    process.exit(1);
  } finally {
    rl.close();
  }
}

main();

