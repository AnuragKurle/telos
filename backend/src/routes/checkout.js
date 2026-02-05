/**
 * Dodo Payments Checkout routes for subscription handling
 * 
 * Dodo Payments is an India-friendly payment processor
 * that supports subscriptions and global payments.
 */

import express from 'express';
import { verifyFirebaseToken } from '../middleware/auth.js';
import admin from 'firebase-admin';
import DodoPayments from 'dodopayments';

const router = express.Router();

// Lazy-initialize Dodo Payments client (created on first use)
let dodoClient = null;

function getDodoClient() {
    if (!dodoClient) {
        const apiKey = process.env.DODO_PAYMENTS_API_KEY;
        if (!apiKey) {
            throw new Error('DODO_PAYMENTS_API_KEY not configured');
        }
        dodoClient = new DodoPayments({
            bearerToken: apiKey,
            environment: process.env.DODO_ENV || (process.env.NODE_ENV === 'production' ? 'live_mode' : 'test_mode')
        });
    }
    return dodoClient;
}

// Product IDs from Dodo Payments Dashboard
// These are created in the Dodo dashboard, not via API
const PRODUCTS = {
    monthly: {
        productId: process.env.DODO_PRODUCT_ID_MONTHLY,  // e.g., 'pdt_xxxxx'
        name: 'Telos Pro',
        priceDisplay: '$3/month',
    }
};

/**
 * POST /checkout/create-session
 * 
 * Create a Dodo Payments Checkout session for subscription purchase
 */
router.post('/create-session', verifyFirebaseToken, async (req, res) => {
    try {
        const { plan, email } = req.body;  // plan: 'monthly' or 'yearly'
        const uid = req.user.uid;

        if (!plan || !email) {
            return res.status(400).json({ error: 'Plan and email are required' });
        }

        if (!PRODUCTS[plan]) {
            return res.status(400).json({ error: 'Invalid plan selected' });
        }

        const productId = PRODUCTS[plan].productId;

        if (!productId) {
            return res.status(500).json({
                error: 'Product not configured',
                message: 'Please configure DODO_PRODUCT_ID_MONTHLY and DODO_PRODUCT_ID_YEARLY in .env'
            });
        }

        // Create Checkout Session using Dodo Payments SDK
        const dodo = getDodoClient();
        const checkoutSession = await dodo.checkoutSessions.create({
            product_cart: [
                {
                    product_id: productId,
                    quantity: 1
                }
            ],
            // Customer information
            customer: {
                email: email,
                name: email.split('@')[0],  // Use email prefix as name
            },
            // Metadata for webhook processing
            metadata: {
                uid: uid,
                email: email,
                plan: plan
            },
            // Redirect URLs
            success_url: `${process.env.FRONTEND_URL || 'https://telos.app'}/success`,
            cancel_url: `${process.env.FRONTEND_URL || 'https://telos.app'}/cancel`,
        });

        console.log(`[CHECKOUT] Created Dodo session: ${JSON.stringify(checkoutSession)}`);

        if (!checkoutSession || !checkoutSession.payment_link) {
            console.error('[CHECKOUT] Session created but missing payment_link/url');
        }

        const responseData = {
            sessionId: checkoutSession.session_id,
            // Check all possible fields: payment_link (v1), url (stripe-like), checkout_url (docs)
            url: checkoutSession.payment_link || checkoutSession.checkout_url || checkoutSession.url
        };

        console.log('[CHECKOUT] Sending response:', responseData);

        return res.json(responseData);

    } catch (error) {
        console.error('[CHECKOUT] Error creating session:', error);
        return res.status(500).json({
            error: 'Failed to create checkout session',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

/**
 * POST /checkout/webhook
 * 
 * Handle Dodo Payments webhooks (payment completion, subscription events, etc.)
 * 
 * Configure this webhook endpoint in Dodo Dashboard: Settings > Webhooks
 */
router.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
    const webhookSecret = process.env.DODO_WEBHOOK_SECRET;

    // Get the signature from headers
    const signature = req.headers['x-dodo-signature'] || req.headers['dodo-signature'];

    if (!signature) {
        console.warn('[WEBHOOK] Missing signature header');
        return res.status(400).json({ error: 'Missing signature' });
    }

    let event;

    try {
        // Parse the webhook payload
        const payload = typeof req.body === 'string' ? req.body : req.body.toString();
        event = JSON.parse(payload);

        // TODO: Verify webhook signature when Dodo provides verification method
        // For now, we trust the payload from the configured endpoint

    } catch (err) {
        console.error(`[WEBHOOK] Error parsing payload: ${err.message}`);
        return res.status(400).json({ error: 'Invalid payload' });
    }

    // Handle the event
    try {
        const eventType = event.type || event.event_type;

        console.log(`[WEBHOOK] Received event: ${eventType}`);

        switch (eventType) {
            case 'payment.succeeded':
            case 'checkout.completed':
            case 'subscription.active':
                {
                    const data = event.data || event;
                    const metadata = data.metadata || {};
                    const customerEmail = metadata.email || data.customer?.email;
                    const plan = metadata.plan || 'yearly';

                    if (!customerEmail) {
                        console.warn('[WEBHOOK] No customer email found in event');
                        break;
                    }

                    console.log(`[WEBHOOK] Payment successful for ${customerEmail}, plan: ${plan}`);

                    // Update user to Pro status in Firestore (look up by email field)
                    const db = admin.firestore();
                    const usersSnapshot = await db.collection('users')
                        .where('email', '==', customerEmail.toLowerCase())
                        .limit(1)
                        .get();

                    if (!usersSnapshot.empty) {
                        const userRef = usersSnapshot.docs[0].ref;
                        await userRef.set({
                            accessStatus: 'pro',
                            subscription: {
                                plan: plan,
                                provider: 'dodo_payments',
                                subscriptionId: data.subscription_id || data.id,
                                customerId: data.customer_id || data.customer?.id,
                                activatedAt: admin.firestore.FieldValue.serverTimestamp(),
                                status: 'active'
                            },
                            upgradedAt: admin.firestore.FieldValue.serverTimestamp()
                        }, { merge: true });
                    } else {
                        console.warn(`[WEBHOOK] User not found for email: ${customerEmail}`);
                    }

                    console.log(`[WEBHOOK] User ${customerEmail} upgraded to Pro`);

                    // Send Slack notification
                    try {
                        const { sendUpgradeNotification } = await import('../services/slack.js');
                        await sendUpgradeNotification(customerEmail, plan);
                    } catch (slackErr) {
                        console.warn('[WEBHOOK] Failed to send Slack notification:', slackErr.message);
                    }
                }
                break;

            case 'subscription.cancelled':
            case 'subscription.canceled':
                {
                    const data = event.data || event;
                    const customerEmail = data.metadata?.email || data.customer?.email;

                    if (customerEmail) {
                        const db = admin.firestore();
                        const cancelSnapshot = await db.collection('users')
                            .where('email', '==', customerEmail.toLowerCase())
                            .limit(1)
                            .get();

                        if (!cancelSnapshot.empty) {
                            await cancelSnapshot.docs[0].ref.update({
                                accessStatus: 'expired',
                                'subscription.status': 'canceled',
                                'subscription.canceledAt': admin.firestore.FieldValue.serverTimestamp()
                            });
                        }

                        console.log(`[WEBHOOK] Subscription canceled for ${customerEmail}`);
                    }
                }
                break;

            case 'payment.failed':
                {
                    const data = event.data || event;
                    const customerEmail = data.metadata?.email || data.customer?.email;
                    console.log(`[WEBHOOK] Payment failed for ${customerEmail || 'unknown'}`);
                    // Could update subscription.status to 'past_due' here
                }
                break;

            default:
                console.log(`[WEBHOOK] Unhandled event type: ${eventType}`);
        }

        // Return success to acknowledge receipt
        res.json({ received: true });

    } catch (error) {
        console.error(`[WEBHOOK] Error processing event:`, error);
        return res.status(500).json({ error: 'Webhook processing failed' });
    }
});

/**
 * GET /checkout/products
 * 
 * Return available products for display in client
 */
router.get('/products', (req, res) => {
    res.json({
        products: Object.entries(PRODUCTS).map(([key, value]) => ({
            plan: key,
            name: value.name,
            priceDisplay: value.priceDisplay,
            available: !!value.productId
        }))
    });
});

export default router;
