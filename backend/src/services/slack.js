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
