const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const admin = require("firebase-admin");
const axios = require("axios");

admin.initializeApp();

/**
 * Triggered when a new document is added to the 'waitlist' collection.
 * Sends a notification to Slack channel C0A6L5K9Z0U.
 */
exports.notifySlackOnWaitlist = onDocumentCreated(
  {
    document: "waitlist/{email}",
    region: "asia-south1"
  },
  async (event) => {
    const data = event.data.data();
    const email = event.params.email;
    const source = data.source || "unknown";
    const channelId = "C0A6L5K9Z0U";

    // Access Slack config from environment variables
    // Set using: firebase functions:secrets:set SLACK_TOKEN
    const botToken = process.env.SLACK_TOKEN;
    const webhookUrl = process.env.SLACK_WEBHOOK;

    try {
      const message = {
        text: `🚀 *New Waitlist Sign-up!*\n*Email:* \`${email}\`\n*Source:* ${source}`
      };

      if (botToken) {
        // Option 1: Using Slack Bot Token (Web API) - Posts to specific channel
        await axios.post("https://slack.com/api/chat.postMessage", {
          channel: channelId,
          ...message
        }, {
          headers: { "Authorization": `Bearer ${botToken}` }
        });
        console.log(`✅ Slack alert sent via Bot API for ${email}`);
      } else if (webhookUrl) {
        // Option 2: Using Slack Webhook (Posts to channel configured in Slack)
        await axios.post(webhookUrl, message);
        console.log(`✅ Slack alert sent via Webhook for ${email}`);
      } else {
        console.error("❌ Slack alert failed: No SLACK_TOKEN or SLACK_WEBHOOK environment variable found.");
        console.error("Set it using: firebase functions:secrets:set SLACK_TOKEN");
      }
    } catch (error) {
      console.error("❌ Error sending Slack notification:", error.response?.data || error.message);
    }
  }
);
