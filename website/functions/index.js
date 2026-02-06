const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const {defineSecret} = require("firebase-functions/params");
const functionsV1 = require("firebase-functions/v1");
const admin = require("firebase-admin");
const axios = require("axios");

admin.initializeApp();

// Define secrets
const slackWebhook = defineSecret("SLACK_WEBHOOK");

// ============================================================================
// Helper: Send Slack notification
// ============================================================================

/**
 * Sends a Slack message via webhook.
 * @param {string} webhookUrl - Slack webhook URL
 * @param {string} text - Message text (supports Slack markdown)
 * @returns {Promise<boolean>} - true if sent successfully
 */
async function sendSlackNotification(webhookUrl, text) {
  if (!webhookUrl) {
    console.error("No SLACK_WEBHOOK secret found. Set it using: firebase functions:secrets:set SLACK_WEBHOOK");
    return false;
  }

  try {
    await axios.post(webhookUrl, { text });
    return true;
  } catch (error) {
    console.error("Error sending Slack notification:", error.response?.data || error.message);
    return false;
  }
}

// ============================================================================
// Trigger: New waitlist sign-up
// ============================================================================

/**
 * Triggered when a new document is added to the 'waitlist' collection.
 * Sends a notification to Slack.
 */
exports.notifySlackOnWaitlist = onDocumentCreated(
  {
    document: "waitlist/{email}",
    region: "asia-south1",
    secrets: [slackWebhook]
  },
  async (event) => {
    const data = event.data.data();
    const email = event.params.email;
    const source = data.source || "unknown";

    const webhookUrl = slackWebhook.value();
    const message = `🚀 *New Waitlist Sign-up!*\n*Email:* \`${email}\`\n*Source:* ${source}`;

    const sent = await sendSlackNotification(webhookUrl, message);
    if (sent) {
      console.log(`Slack alert sent for waitlist: ${email}`);
    }
  }
);

// ============================================================================
// Trigger: New user sign-up (Firebase Auth)
// ============================================================================

/**
 * Triggered when a new user is created in Firebase Auth.
 * This fires when someone completes onboarding in the Telos client
 * (i.e., after `pip install telos-tracker` → `telos setup` → account creation).
 *
 * Sends a Slack notification with user details and platform info.
 */
exports.notifyOnNewUser = functionsV1
  .region("asia-south1")
  .runWith({ secrets: ["SLACK_WEBHOOK"] })
  .auth.user()
  .onCreate(async (user) => {
    const email = user.email || "anonymous";
    const uid = user.uid;
    const provider = user.providerData?.[0]?.providerId || "password";
    const createdAt = user.metadata?.creationTime || new Date().toISOString();

    const webhookUrl = process.env.SLACK_WEBHOOK;

    const message = [
      `🎉 *New Telos User!*`,
      `*Email:* \`${email}\``,
      `*UID:* \`${uid}\``,
      `*Provider:* ${provider}`,
      `*Created:* ${createdAt}`,
    ].join("\n");

    const sent = await sendSlackNotification(webhookUrl, message);
    if (sent) {
      console.log(`Slack alert sent for new user: ${email} (${uid})`);
    }
  });
