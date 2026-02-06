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
 * @param {string} mode - User mode: 'cloud', 'byok', or 'unknown'
 */
export async function sendSignupNotification(user, mode = 'unknown') {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) {
      console.warn('Signup notification skipped: No signup webhook configured.');
      return { success: false, error: 'No webhook' };
    }

    const modeEmoji = mode === 'byok' ? '🔑' : mode === 'cloud' ? '☁️' : '❓';
    const modeLabel = mode === 'byok' ? 'BYOK (Local, Free)' : mode === 'cloud' ? 'Cloud (Trial)' : 'Unknown';

    const message = `🎉 *New User Signup*\n> *Email:* ${user.email}\n> *User ID:* ${user.uid}\n> *Mode:* ${modeEmoji} ${modeLabel}\n> *Created:* ${new Date(user.createdAt).toLocaleString()}`;

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

    console.log(`[SLACK] Signup notification sent for ${user.email} (mode: ${mode})`);
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
 * @param {string} mode - User mode: 'cloud', 'byok', or 'unknown'
 */
export async function sendTrialActivationNotification(email, trialStartDate, mode = 'cloud') {
  try {
    const webhookUrl = await getSlackSignupWebhook(); // Reuse signup webhook for now
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const modeEmoji = mode === 'byok' ? '🔑' : '☁️';
    const modeLabel = mode === 'byok' ? 'BYOK (Local)' : 'Cloud';

    const message = `🚀 *Trial Activated*\n> *User:* ${email}\n> *Mode:* ${modeEmoji} ${modeLabel}\n> *Started:* ${new Date(trialStartDate).toLocaleString()}`;

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

    console.log(`[SLACK] Trial activation notification sent for ${email} (mode: ${mode})`);
    return { success: true };
  } catch (error) {
    console.error('Error sending trial notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send Upgrade Notification (user upgraded to Pro)
 * 
 * @param {string} email - User email
 * @param {string} plan - Subscription plan (e.g., 'monthly')
 */
export async function sendUpgradeNotification(email, plan = 'monthly') {
  try {
    const webhookUrl = await getSlackSignupWebhook(); // Reuse signup webhook
    if (!webhookUrl) {
      console.warn('[SLACK] No signup webhook found for upgrade notification.');
      return { success: false, error: 'No webhook' };
    }

    const planLabel = plan === 'yearly' ? '$30/year' : '$3/month';

    const message = `\u{1F451} *New Pro Upgrade!*\n> *User:* ${email}\n> *Plan:* ${plan} (${planLabel})\n> *Time:* ${new Date().toLocaleString()}`;

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

    console.log(`[SLACK] Upgrade notification sent for ${email} (plan: ${plan})`);
    return { success: true };
  } catch (error) {
    console.error('Error sending upgrade notification:', error.message);
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

// ─── Referral & Beta Growth Notifications ────────────────────────────────────

/**
 * Send notification when a user views/copies their referral code
 * 
 * @param {string} email - User email
 * @param {string} referralCode - The referral code
 */
export async function sendReferralCodeCopiedNotification(email, referralCode) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const frontendUrl = (process.env.FRONTEND_URL || 'https://gen-lang-client-0772617718.web.app').replace(/\/$/, '');
    const message = `🔗 *Referral Code Copied*\n> *User:* ${email}\n> *Code:* ${referralCode}\n> *Link:* ${frontendUrl}/?ref=${referralCode}\n> *Time:* ${new Date().toLocaleString()}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Referral code copied notification sent for ${email}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending referral code copied notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification when a referral link is used during signup
 * 
 * @param {string} referralCode - The referral code used
 * @param {string} referrerEmail - Email of the person who shared the code
 * @param {string} refereeEmail - Email of the person who used the code
 */
export async function sendReferralLinkUsedNotification(referralCode, referrerEmail, refereeEmail) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `👀 *Referral Link Used*\n> *Referral Code:* ${referralCode}\n> *Referred By:* ${referrerEmail}\n> *New Signup Email:* ${refereeEmail}\n> *Time:* ${new Date().toLocaleString()}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Referral link used notification sent: ${referrerEmail} -> ${refereeEmail}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending referral link used notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification when a referral is fully activated (referee started trial)
 * 
 * @param {string} referrerEmail - Email of the referrer
 * @param {string} refereeEmail - Email of the referred user
 * @param {string} referralCode - The referral code
 * @param {number} totalCredits - Total Pro credits the referrer now has
 */
export async function sendReferralActivatedNotification(referrerEmail, refereeEmail, referralCode, totalCredits) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `🎉 *Referral Activated — Pro Credit Awarded!*\n> *Referrer:* ${referrerEmail}\n> *New User:* ${refereeEmail}\n> *Code:* ${referralCode}\n> *Pro Credits Earned:* 1 month (total: ${totalCredits} month${totalCredits !== 1 ? 's' : ''})\n> *Time:* ${new Date().toLocaleString()}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Referral activated notification sent: ${referrerEmail} earned credit from ${refereeEmail}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending referral activated notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification when Pro access is granted via referral credit
 * 
 * @param {string} email - User email
 * @param {number} creditsRemaining - Remaining Pro credits in months
 */
export async function sendProCreditAppliedNotification(email, creditsRemaining) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `🌟 *Pro Credit Used*\n> *User:* ${email}\n> *Access:* Pro (via referral credit)\n> *Credits Remaining:* ${creditsRemaining} month${creditsRemaining !== 1 ? 's' : ''}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Pro credit applied notification sent for ${email}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending pro credit applied notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification for each individual email sent within a batch campaign
 * 
 * @param {string} recipientEmail - Email address of the recipient
 * @param {string} template - Email template type (invitation, reminder, referral_nudge)
 * @param {boolean} success - Whether the email was sent successfully
 * @param {string} campaignName - Name of the parent campaign
 * @param {string|null} error - Error message if failed
 */
export async function sendIndividualEmailSentNotification(recipientEmail, template, success, campaignName, error = null) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const emoji = success ? '✅' : '❌';
    const status = success ? 'Sent' : 'Failed';
    let message = `${emoji} *Email ${status}*  \`${template}\`\n> *To:* ${recipientEmail}\n> *Campaign:* ${campaignName}`;
    if (!success && error) {
      message += `\n> *Error:* ${error}`;
    }

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Individual email ${status.toLowerCase()} notification: ${recipientEmail} (${template})`);
    return { success: true };
  } catch (err) {
    console.error('Error sending individual email notification:', err.message);
    return { success: false, error: err.message };
  }
}

/**
 * Send notification when a user changes their email report preferences
 * 
 * @param {string} email - User email
 * @param {object} preferences - The new preferences
 * @param {boolean} preferences.enabled - Whether email reports are enabled
 * @param {string} preferences.sendTime - Preferred send time (HH:MM)
 * @param {string} preferences.timezone - User timezone
 */
export async function sendEmailPreferencesChangedNotification(email, preferences) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const statusEmoji = preferences.enabled ? '🔔' : '🔕';
    const statusLabel = preferences.enabled ? 'Enabled' : 'Disabled';

    const message = `⚙️ *Email Preferences Updated*\n> *User:* ${email}\n> *Reports:* ${statusEmoji} ${statusLabel}\n> *Send Time:* ${preferences.sendTime || '09:00'} (${preferences.timezone || 'UTC'})\n> *Time:* ${new Date().toLocaleString()}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Email preferences changed notification sent for ${email}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending email preferences notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification when a batch email campaign starts
 * 
 * @param {string} campaignName - Campaign name
 * @param {number} recipientCount - Number of recipients
 * @param {string} template - Email template type
 * @param {string} adminEmail - Admin who triggered it
 */
export async function sendBatchEmailStartedNotification(campaignName, recipientCount, template, adminEmail) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `📧 *Batch Email Campaign Started*\n> *Campaign:* ${campaignName}\n> *Recipients:* ${recipientCount}\n> *Template:* ${template}\n> *Started By:* ${adminEmail}`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Batch email started notification sent: ${campaignName}`);
    return { success: true };
  } catch (error) {
    console.error('Error sending batch email started notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send notification when a batch email campaign completes
 * 
 * @param {string} campaignName - Campaign name
 * @param {number} sentCount - Emails successfully sent
 * @param {number} failedCount - Emails that failed
 * @param {number} durationMs - Duration in milliseconds
 */
export async function sendBatchEmailCompletedNotification(campaignName, sentCount, failedCount, durationMs) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const durationSec = Math.round(durationMs / 1000);
    const totalCount = sentCount + failedCount;
    const emoji = failedCount > 0 ? '⚠️' : '✅';

    const message = `${emoji} *Batch Email Campaign Completed*\n> *Campaign:* ${campaignName}\n> *Sent:* ${sentCount}/${totalCount}${failedCount > 0 ? ` (${failedCount} failed)` : ''}\n> *Duration:* ${durationSec}s`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Batch email completed notification sent: ${campaignName} (${sentCount}/${totalCount})`);
    return { success: true };
  } catch (error) {
    console.error('Error sending batch email completed notification:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send daily beta digest with key metrics
 * 
 * @param {object} stats - Beta metrics
 * @param {number} stats.newSignupsToday - New signups in last 24h
 * @param {number} stats.activeUsers24h - Users active in last 24h
 * @param {number} stats.referralCodesShared - Referral codes viewed today
 * @param {number} stats.referralsActivated - Referrals activated today
 * @param {number} stats.waitlistRemaining - Pending waitlist entries
 * @param {number} stats.activationRate - Overall activation rate percentage
 * @param {number} stats.proCreditsAwardedToday - Pro credits awarded today
 */
export async function sendDailyBetaDigestNotification(stats) {
  try {
    const webhookUrl = await getSlackSignupWebhook();
    if (!webhookUrl) return { success: false, error: 'No webhook' };

    const message = `📊 *Daily Beta Digest*\n> *New Signups Today:* ${stats.newSignupsToday || 0}\n> *Active Users (24h):* ${stats.activeUsers24h || 0}\n> *Referral Codes Shared:* ${stats.referralCodesShared || 0}\n> *Referrals Activated:* ${stats.referralsActivated || 0}\n> *Waitlist Remaining:* ${stats.waitlistRemaining || 0}\n> *Total Activation Rate:* ${stats.activationRate || 0}%\n> *Pro Credits Awarded Today:* ${stats.proCreditsAwardedToday || 0} month(s)`;

    await axios.post(webhookUrl, {
      text: message,
      blocks: [{ type: 'section', text: { type: 'mrkdwn', text: message } }]
    });

    console.log(`[SLACK] Daily beta digest sent`);
    return { success: true };
  } catch (error) {
    console.error('Error sending daily beta digest:', error.message);
    return { success: false, error: error.message };
  }
}
