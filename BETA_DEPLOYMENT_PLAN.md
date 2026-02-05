# Beta Deployment - Final Steps Plan

**Status:** 90% Ready | **Remaining Time:** ~40 minutes  
**Critical:** Payment system needs configuration

---

## ✅ What's Already Done

- Client v0.2.1 published to PyPI
- MCP server live and documented
- Website deployed with docs
- Backend API deployed to Cloud Run
- Firebase authentication working

## ❌ What Needs Completion

**Critical:** Dodo Payments configuration (required for Pro upgrades)  
**Optional:** Monitoring/alerts setup

---

## 🎯 Plan: Complete Beta Deployment

### Step 1: Dodo Payments Account Setup (15 min)

1. **Create Account**
   - Go to: https://app.dodopayments.com/signup
   - Sign up with your email
   - Verify email

2. **Get API Key**
   - Navigate to: https://app.dodopayments.com/settings/api
   - Click "Create API Key"
   - Copy the key (starts with `dodo_sk_live_` or `dodo_sk_test_`)
   - Save to notes

3. **Create Product**
   - Go to: https://app.dodopayments.com/products
   - Click "Add Product"
   - Fill in:
     - Name: `Telos Pro`
     - Type: `Subscription`
     - Billing Period: `Monthly`
     - Price: `$3.00 USD`
   - Click "Create"
   - Copy the Product ID (starts with `pdt_`)
   - Save to notes

4. **Configure Webhook**
   - Go to: https://app.dodopayments.com/settings/webhooks
   - Click "Add Webhook"
   - Webhook URL: `https://telos-backend-ae7k4avtpq-uc.a.run.app/v1/checkout/webhook`
   - Select events:
     - ✅ `checkout.completed`
     - ✅ `payment.succeeded`
     - ✅ `subscription.active`
     - ✅ `subscription.cancelled`
     - ✅ `payment.failed`
   - Click "Create"
   - Copy the Webhook Secret
   - Save to notes

**Result:** You now have 3 values:
- `DODO_PAYMENTS_API_KEY`
- `DODO_PRODUCT_ID_MONTHLY`
- `DODO_WEBHOOK_SECRET`

---

### Step 2: Add Secrets to Google Cloud (10 min)

Open terminal and run:

```bash
cd backend

# Find your service account email first
gcloud run services describe telos-backend --region=us-central1 --format="value(spec.template.spec.serviceAccountName)"
# Copy the output - you'll need it

# Create secrets (replace YOUR_VALUE with actual values from Step 1)
echo "YOUR_DODO_API_KEY" | gcloud secrets create DODO_PAYMENTS_API_KEY --data-file=-
echo "YOUR_PRODUCT_ID" | gcloud secrets create DODO_PRODUCT_ID_MONTHLY --data-file=-
echo "YOUR_WEBHOOK_SECRET" | gcloud secrets create DODO_WEBHOOK_SECRET --data-file=-
echo "https://gen-lang-client-0772617718.web.app" | gcloud secrets create FRONTEND_URL --data-file=-

# Grant access to service account (replace YOUR_SERVICE_ACCOUNT)
SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT_FROM_ABOVE"

gcloud secrets add-iam-policy-binding DODO_PAYMENTS_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding DODO_PRODUCT_ID_MONTHLY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding DODO_WEBHOOK_SECRET \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding FRONTEND_URL \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

**Verify:**
```bash
gcloud secrets list
# Should show all 4 secrets
```

---

### Step 3: Update Cloud Run Service (5 min)

```bash
cd backend

gcloud run services update telos-backend \
  --set-env-vars DODO_ENV=live_mode \
  --set-secrets DODO_PAYMENTS_API_KEY=DODO_PAYMENTS_API_KEY:latest,DODO_PRODUCT_ID_MONTHLY=DODO_PRODUCT_ID_MONTHLY:latest,DODO_WEBHOOK_SECRET=DODO_WEBHOOK_SECRET:latest,FRONTEND_URL=FRONTEND_URL:latest \
  --region=us-central1
```

**Wait for deployment to complete** (~2 minutes)

---

### Step 4: Test Payment Flow (5 min)

**Test 1: Products Endpoint**
```bash
curl https://telos-backend-ae7k4avtpq-uc.a.run.app/v1/checkout/products
```

Expected output:
```json
{
  "products": [
    {
      "plan": "monthly",
      "name": "Telos Pro",
      "priceDisplay": "$3/month",
      "available": true
    }
  ]
}
```

**Test 2: Try Upgrade in Client**
```bash
# Install/update client
pip install --upgrade telos-tracker

# Run client
telos

# In the app:
# 1. Press 'u' for Upgrade
# 2. Click the checkout link
# 3. Use test card: 4242 4242 4242 4242
# 4. Any future date + any CVC
# 5. Complete payment
# 6. Check if status updates to "Pro"
```

**Test 3: Webhook Delivery**
- Check Dodo dashboard: https://app.dodopayments.com/webhooks
- Should see webhook delivery logs after test payment
- Status should be "200 OK"

---

### Step 5: Optional - Monitoring Setup (10 min)

If you want error tracking and alerts:

**A. Sentry (Error Tracking)**
1. Sign up: https://sentry.io
2. Create project: "Node.js/Express"
3. Copy DSN
4. Add to Cloud Run:
```bash
echo "YOUR_SENTRY_DSN" | gcloud secrets create SENTRY_DSN --data-file=-
gcloud secrets add-iam-policy-binding SENTRY_DSN --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"

gcloud run services update telos-backend \
  --update-secrets SENTRY_DSN=SENTRY_DSN:latest,SENTRY_ENVIRONMENT=production \
  --region=us-central1
```

**B. Slack Alerts (Optional)**
1. Create webhook: https://api.slack.com/messaging/webhooks
2. Copy webhook URL
3. Add to Cloud Run:
```bash
echo "YOUR_SLACK_WEBHOOK_URL" | gcloud secrets create SLACK_ALERTS_WEBHOOK --data-file=-
gcloud secrets add-iam-policy-binding SLACK_ALERTS_WEBHOOK --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"

gcloud run services update telos-backend \
  --update-secrets SLACK_ALERTS_WEBHOOK=SLACK_ALERTS_WEBHOOK:latest \
  --region=us-central1
```

---

## 📋 Pre-Flight Checklist

Before starting tomorrow:

- [ ] Have Google Cloud SDK installed and authenticated
- [ ] Have access to Firebase project console
- [ ] Have credit card ready for Dodo Payments (if going live)
- [ ] Be on the `prod-monorepo` or `main-monorepo` branch
- [ ] Backend code is deployed (already done)

---

## 🎯 Success Criteria

After completing all steps, users should be able to:

1. ✅ Install client: `pip install telos-tracker`
2. ✅ Start 7-day trial automatically
3. ✅ Click "Upgrade to Pro" in the app
4. ✅ Complete payment via Dodo Payments
5. ✅ Automatically get Pro status in Firebase
6. ✅ Access Pro features immediately
7. ✅ Receive subscription renewals monthly

---

## 🚨 Troubleshooting

**If products endpoint returns empty:**
- Check secrets exist: `gcloud secrets list`
- Check service account permissions
- Check Cloud Run logs: `gcloud run services logs read telos-backend --region=us-central1`

**If payment doesn't upgrade status:**
- Check webhook logs in Dodo dashboard
- Check Firestore `users` collection for the user
- Check backend logs for webhook errors

**If webhook fails:**
- Verify webhook URL is exactly: `https://telos-backend-ae7k4avtpq-uc.a.run.app/v1/checkout/webhook`
- Check webhook secret matches in Dodo dashboard and Cloud Run
- Test webhook manually from Dodo dashboard

---

## 📁 Reference Documents

- **Dodo Setup Guide:** `backend/DODO_PAYMENTS_SETUP.md`
- **Environment Variables:** `backend/env.example`
- **Monitoring Setup:** `backend/MONITORING_SETUP.md`
- **Beta Launch Steps:** `BETA_LAUNCH_NEXT_STEPS.md`

---

## ⏱️ Time Estimate

- Dodo account + products: 15 min
- Google Cloud secrets: 10 min
- Cloud Run update: 5 min
- Testing: 5 min
- **Total: ~35 minutes**

Optional monitoring: +10 min

---

## 🎉 After Completion

Your beta will be **100% ready** with:
- ✅ Full payment processing
- ✅ Automatic Pro upgrades
- ✅ Webhook handling
- ✅ Trial-to-paid conversion
- ✅ Production-ready backend

Users can then:
1. Install from PyPI
2. Use free trial for 7 days
3. Upgrade to Pro for $3/month
4. Use MCP server with Claude/Cursor
5. Access all Pro features

---

**Next Session:** Follow this plan step-by-step. Estimated completion: 40 minutes.
