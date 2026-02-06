# Beta Deployment Checklist

**Follow:** `BETA_DEPLOYMENT_PLAN.md` for detailed instructions

---

## Quick Checklist

### 1. Dodo Payments Setup (15 min)
- [x] Create account at https://app.dodopayments.com/signup
- [x] Get API key from Settings > API
- [x] Create "Telos Pro" product ($3/month subscription)
- [x] Configure webhook endpoint
- [x] Save these 3 values:
  - [x] `DODO_PAYMENTS_API_KEY`
  - [x] `DODO_PRODUCT_ID_MONTHLY`
  - [x] `DODO_WEBHOOK_SECRET`

### 2. Google Cloud Secrets (10 min)
- [ ] Get service account email
- [ ] Create 4 secrets:
  - [ ] `DODO_PAYMENTS_API_KEY`
  - [ ] `DODO_PRODUCT_ID_MONTHLY`
  - [ ] `DODO_WEBHOOK_SECRET`
  - [ ] `FRONTEND_URL`
- [ ] Grant access to service account (all 4 secrets)

### 3. Cloud Run Update (5 min)
- [ ] Update service with new secrets
- [ ] Wait for deployment to complete
- [ ] Verify service is running

### 4. Testing (5 min)
- [ ] Test products endpoint (should return Telos Pro)
- [ ] Test upgrade flow in client
- [ ] Test payment with test card: 4242 4242 4242 4242
- [ ] Verify Pro status updates in Firebase
- [ ] Check webhook delivery in Dodo dashboard

### 5. Optional: Monitoring (10 min)
- [ ] Set up Sentry (error tracking)
- [ ] Set up Slack (alerts)
- [ ] Deploy with monitoring secrets

---

## Success Criteria

- [ ] Products endpoint returns `{"products":[...]}`
- [ ] Clicking "Upgrade" opens Dodo checkout
- [ ] Test payment completes successfully
- [ ] User status changes to "Pro" in Firebase
- [ ] Webhook shows "200 OK" in Dodo dashboard
- [ ] Client app shows "Pro" status after refresh

---

**Total Time:** ~40 minutes  
**Status:** Ready for beta once complete ✅
