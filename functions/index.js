const functions = require("firebase-functions");
const axios = require("axios");

// You should store this in Firebase environment config, not hardcoded.
// For now, we'll assume it's passed via environment or hardcoded if necessary (but risky).
// Better: Use `firebase functions:config:set slack.webhook="YOUR_WEBHOOK_URL"`
// For this task, I will use a placeholder or ask the user for the webhook URL, 
// but the user only gave me the Channel ID: C0A6L5K9Z0U.
// Sending to a channel ID requires a Bot Token, not just a webhook if we want to be specific.
// A simpler way is an Incoming Webhook which is tied to a channel.
// If the user wants to use the Channel ID specifically, I need a Slack Bot Token.

// Assumption: The user wants me to SET UP the alert mechanism. 
// Since I don't have the Bot Token, I will write the code to use a process.env variable.

exports.notifySlackOnWaitlist = functions.firestore
  .document("waitlist/{email}")
  .onCreate(async (snap, context) => {
    const data = snap.data();
    const email = context.params.email;
    const source = data.source || "unknown";

    const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL; 
    // OR if using a bot token:
    const slackBotToken = process.env.SLACK_BOT_TOKEN;
    const channelId = "C0A6L5K9Z0U";

    try {
        if (slackBotToken) {
            // Using Bot API
            await axios.post("https://slack.com/api/chat.postMessage", {
                channel: channelId,
                text: `🚀 *New Waitlist Sign-up!*\nEmail: \`${email}\`\nSource: ${source}`
            }, {
                headers: { "Authorization": `Bearer ${slackBotToken}` }
            });
        } else if (slackWebhookUrl) {
             // Using Webhook (tied to specific channel usually)
             await axios.post(slackWebhookUrl, {
                text: `🚀 *New Waitlist Sign-up!*\nEmail: \`${email}\`\nSource: ${source}`
             });
        } else {
            console.warn("No Slack configuration found (SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL).");
        }
    } catch (error) {
      console.error("Error sending Slack notification:", error);
    }
  });

