import express from 'express';
import { getFirestore } from '../config/firebase.js';
import { verifyFirebaseToken } from '../middleware/auth.js';
import { sendSlackNotification } from '../services/slack.js';

const router = express.Router();

/**
 * POST /v1/feedback
 * Submit user feedback, save to Firestore, and alert Slack.
 */
router.post('/', verifyFirebaseToken, async (req, res) => {
  try {
    const { feedback_type, feedback_text, context, metadata } = req.body;
    const { uid, email } = req.user;

    if (!feedback_text) {
      return res.status(400).json({ error: 'Feedback text is required' });
    }

    const firestore = getFirestore();
    const feedbackRef = firestore.collection('feedback').doc();

    const feedbackData = {
      id: feedbackRef.id,
      uid,
      email: email || 'anonymous',
      feedback_type: feedback_type || 'general',
      feedback_text,
      context: context || {},
      metadata: metadata || {},
      created_at: new Date(),
      status: 'pending'
    };

    // 1. Save to Firestore
    await feedbackRef.set(feedbackData);

    // 2. Send Slack Notification (non-critical)
    const channelId = process.env.SLACK_FEEDBACK_CHANNEL_ID || 'C0A6VF5PBUH';
    const screen = context?.screen || 'unknown';
    
    let slackMessage = `📝 *New Feedback Received* (from ${screen} screen)\n`;
    slackMessage += `> *Type:* ${feedbackData.feedback_type}\n`;
    slackMessage += `> *User:* ${feedbackData.email} (${uid})\n`;
    slackMessage += `> *Feedback:* ${feedback_text}`;

    const blocks = [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: slackMessage
        }
      }
    ];

    // Add context details if available
    if (context && Object.keys(context).length > 0) {
      let contextStr = '';
      if (context.app) contextStr += `*App:* ${context.app}  `;
      if (context.task) contextStr += `*Task:* ${context.task}  `;
      if (context.category) contextStr += `*Category:* ${context.category}  `;
      if (context.summary_id) contextStr += `*Summary ID:* ${context.summary_id}  `;
      
      if (contextStr) {
        blocks.push({
          type: 'context',
          elements: [
            {
              type: 'mrkdwn',
              text: contextStr.trim()
            }
          ]
        });
      }
    }

    // Send to Slack and track the result
    const slackResult = await sendSlackNotification(channelId, slackMessage, blocks);
    
    // Update Firestore with Slack delivery status
    await feedbackRef.update({
      slack_notification: {
        sent: slackResult.success,
        method: slackResult.method || null,
        error: slackResult.error || null,
        timestamp: new Date()
      }
    });

    // Log if Slack failed (but still return success to user since feedback is saved)
    if (!slackResult.success) {
      console.error(`⚠️ Feedback ${feedbackRef.id} saved but Slack notification failed:`, slackResult.error);
    }

    return res.status(201).json({
      success: true,
      message: 'Feedback submitted successfully',
      feedback_id: feedbackRef.id,
      slack_notified: slackResult.success  // Let client know if Slack worked
    });
  } catch (error) {
    console.error('Error submitting feedback:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
