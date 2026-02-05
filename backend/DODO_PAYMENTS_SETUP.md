# Dodo Payments Setup Instructions

Dodo Payments is an India-friendly payment processor that supports global payments and subscriptions.

## Prerequisites
1. Create a Dodo Payments account at https://app.dodopayments.com/signup
2. Get your API key from the dashboard

## Setup Steps

### 1. Get API Key
1. Go to https://app.dodopayments.com/settings/api
2. Copy your **API Key** (starts with `dodo_sk_`)
3. Add to `.env`:
   ```
   DODO_PAYMENTS_API_KEY=dodo_sk_test_xxxxx
   ```

### 2. Create Products
1. Go to https://app.dodopayments.com/products
2. Click "Add Product"

**Telos Pro:**
- Type: Subscription
- Name: "Telos Pro"
- Price: $3.00 USD / month
- Copy the Product ID (starts with `pdt_`)
- Add to `.env`:
  ```
  DODO_PRODUCT_ID_MONTHLY=pdt_xxxxx
  ```

### 3. Configure Webhook
1. Go to https://app.dodopayments.com/settings/webhooks
2. Add webhook endpoint:
   - URL: `https://your-backend-url.com/v1/checkout/webhook`
   - Events to subscribe:
     - `checkout.completed`
     - `payment.succeeded`
     - `subscription.active`
     - `subscription.cancelled`
     - `payment.failed`
3. Copy the Webhook Secret
4. Add to `.env`:
   ```
   DODO_WEBHOOK_SECRET=your_webhook_secret
   ```

### 4. Install SDK
```bash
cd backend
npm install dodopayments
```

### 5. Test Mode
- In development, set `NODE_ENV=development` to use test mode
- In production, set `NODE_ENV=production` for live payments

## Testing

### Test Cards
Dodo Payments uses standard test cards in test mode:
- **Success**: `4242 4242 4242 4242`
- **Requires 3DS**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 9995`

Use any future expiry date and any CVC (e.g., 12/34, 123)

## Environment Variables Summary

```env
# Required
DODO_PAYMENTS_API_KEY=dodo_sk_test_xxxxx

# Product IDs (create in dashboard)
DODO_PRODUCT_ID_MONTHLY=pdt_xxxxx
DODO_PRODUCT_ID_YEARLY=pdt_xxxxx

# Webhook secret (from webhook configuration)
DODO_WEBHOOK_SECRET=xxxxx

# Frontend URL for redirects
FRONTEND_URL=https://telos.app
```

## API Endpoints

After setup, these endpoints are available:

### Create Checkout Session
```
POST /v1/checkout/create-session
Authorization: Bearer <firebase_token>
Body: { "plan": "monthly", "email": "user@example.com" }
Response: { "sessionId": "...", "url": "https://checkout.dodopayments.com/..." }
```

### Webhook (configured in Dodo dashboard)
```
POST /v1/checkout/webhook
```

### List Products
```
GET /v1/checkout/products
Response: { "products": [...] }
```

## Support
- Dodo Payments Docs: https://docs.dodopayments.com
- Dashboard: https://app.dodopayments.com
