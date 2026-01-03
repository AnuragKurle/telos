const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const {defineSecret} = require("firebase-functions/params");
const admin = require("firebase-admin");
const axios = require("axios");

admin.initializeApp();

// Define secrets
const slackWebhook = defineSecret("SLACK_WEBHOOK");

/**
 * Triggered when a new document is added to the 'waitlist' collection.
 * Sends a notification to Slack channel C0A6L5K9Z0U.
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
    const channelId = "C0A6L5K9Z0U";

    // Access Slack webhook from secret
    const webhookUrl = slackWebhook.value();

    try {
      const message = {
        text: `🚀 *New Waitlist Sign-up!*\n*Email:* \`${email}\`\n*Source:* ${source}`
      };

      if (webhookUrl) {
        // Send notification via Slack Webhook
        await axios.post(webhookUrl, message);
        console.log(`✅ Slack alert sent via Webhook for ${email}`);
      } else {
        console.error("❌ Slack alert failed: No SLACK_WEBHOOK secret found.");
        console.error("Set it using: firebase functions:secrets:set SLACK_WEBHOOK");
      }
    } catch (error) {
      console.error("❌ Error sending Slack notification:", error.response?.data || error.message);
    }
  }
);
