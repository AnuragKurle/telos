import axios from 'axios';
import { getSlackBotToken, getSlackWebhook, getSlackSignupWebhook } from './secrets.js';

/**
 * Send a notification to Slack
 * 
 * Supports both Bot Token (for channel ID) and Webhook URL.
 * 
 * @param {string} channelId - Slack channel ID (e.g., C0A6VF5PBUH)
 * @param {string} message - Plain text message/fallback
 * @param {Array} blocks - Rich Slack blocks (optional)
 * @param {string} webhookOverride - Optional webhook URL to use instead of default
 */
export async function sendSlackNotification(channelId, message, blocks = [], webhookOverride = null) {
  try {
    // 1. Try sending via Webhook if configured (simplest)
    const webhookUrl = webhookOverride || await getSlackWebhook();
    if (webhookUrl) {
      await axios.post(webhookUrl, {
        text: message,
        blocks: blocks.length > 0 ? blocks : undefined,
        channel: channelId // Some webhooks allow overriding channel
      });
      return { success: true, method: 'webhook' };
    }

    // 2. Try sending via Bot Token if configured
    const botToken = await getSlackBotToken();
    if (botToken) {
      await axios.post('https://slack.com/api/chat.postMessage', {
        channel: channelId,
        text: message,
        blocks: blocks.length > 0 ? blocks : undefined
      }, {
        headers: {
          'Authorization': `Bearer ${botToken}`,
          'Content-Type': 'application/json'
        }
      });
      return { success: true, method: 'bot_token' };
    }

    console.warn('Slack notification skipped: No webhook or bot token found in secrets.');
    return { success: false, error: 'No credentials' };
  } catch (error) {
    console.error('Error sending Slack notification:', error.response?.data || error.message);
    // Don't throw - feedback should still be saved even if Slack fails
    return { success: false, error: error.message };
  }
}

/**
 * Send a user signup notification to Slack
 * 
 * @param {Object} user - User object with uid, email, createdAt
 */
export async function sendSignupNotification(user) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) {
      console.warn('Signup notification skipped: No signup webhook configured.');
      return { success: false, error: 'No webhook' };
    }

    const message = `🎉 *New User Signup*\n> *Email:* ${user.email}\n> *User ID:* ${user.uid}\n> *Created:* ${new Date(user.createdAt).toLocaleString()}`;

    const blocks = [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: message
        }
      }
    ];

    await axios.post(webhookUrl, {
      text: message,
      blocks: blocks
    });

    console.log(`[SLACK] Signup notification sent for ${user.email}`);
    return { success: true, method: 'webhook' };
  } catch (error) {
    console.error('Error sending signup notification:', error.response?.data || error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send Trial Activation Notification
 * 
 * @param {string} email - User email
 * @param {Date} trialStartDate - When the trial started
 */
export async function sendTrialActivationNotification(email, trialStartDate) {
  try {
    const webhookUrl = await getSlackSignupWebhook(); // Reuse signup webhook for now
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `🚀 *Trial Activated*\n> *User:* ${email}\n> *Started:* ${new Date(trialStartDate).toLocaleString()}`;

    const blocks = [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: message
        }
      }
    ];

    await axios.post(webhookUrl, {
      text: message,
      blocks: blocks
    });

    console.log(`[SLACK] Trial activation notification sent for ${email}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending trial notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send Payment Intent Notification
 * 
 * @param {string} email - User email
 */
export async function sendPaymentIntentNotification(email) {
  try {
    const webhookUrl = await getSlackSignupWebhook(); // Reuse signup webhook
    if (!webhookUrl) {
      console.warn('[SLACK] No signup webhook found for payment intent.');
      return { success: false, error: 'No webhook' };
    }

    const message = `💰 *PAYMENT INTENT DETECTED*\n> *User:* ${email}\n> *Action:* Clicked 'Upgrade to Pro'`;

    const blocks = [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: message
        }
      }
    ];

    await axios.post(webhookUrl, {
      text: message,
      blocks: blocks
    });

    console.log(`[SLACK] Payment intent notification sent for ${email}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending payment intent notification:', error.message);
    return { success: false, error: error.message };
  }
}
