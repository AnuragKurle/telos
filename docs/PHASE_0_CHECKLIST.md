# Phase 0 Setup Checklist

Use this to track your progress through Phase 0.

## ☐ Step 1: Create Google Cloud Project
- [ ] Go to https://console.cloud.google.com/
- [ ] Create new project named `telos-beta`
- [ ] Verify project is selected in top dropdown
- [ ] Record Project ID: _________________

## ☐ Step 2: Enable Billing & Set Budget
- [ ] Link billing account
- [ ] Create budget alert for $50/month
- [ ] Set alert thresholds: 50%, 75%, 90%, 100%
- [ ] Verify you receive test email

## ☐ Step 3: Enable APIs
- [ ] Firebase Authentication API
- [ ] Cloud Firestore API
- [ ] Secret Manager API
- [ ] Cloud Run API
- [ ] Cloud Build API

## ☐ Step 4: Add Firebase to Project
- [ ] Go to https://console.firebase.google.com/
- [ ] Add Firebase to existing `telos-beta` project
- [ ] Disable Google Analytics
- [ ] Wait for provisioning to complete

## ☐ Step 5: Enable Authentication Providers
- [ ] Go to Authentication → Get Started
- [ ] Enable Anonymous authentication
- [ ] Enable Email/Password authentication
- [ ] Both providers show "Enabled" status

## ☐ Step 6: Create Firestore Database
- [ ] Go to Firestore Database
- [ ] Create database in Production mode
- [ ] Choose region: _________________
- [ ] Wait for provisioning (~1 min)

## ☐ Step 7: Get Firebase Web API Key
- [ ] Go to Project Settings → General
- [ ] Register Web App named `telos-client`
- [ ] Copy `apiKey` value: _________________
- [ ] Save to FIREBASE_CONFIG_TEMPLATE.txt

## ☐ Step 8: Store Gemini API Key
- [ ] Go to Secret Manager
- [ ] Create secret named `GEMINI_API_KEY`
- [ ] Paste your Gemini API key as value
- [ ] Verify secret shows as "Active"

## ☐ Step 9: Set Firestore Security Rules
- [ ] Go to Firestore Database → Rules tab
- [ ] Set temporary permissive rules (from guide)
- [ ] Publish rules
- [ ] Verify no errors

## ☐ Step 10: Document Everything
- [ ] Fill out FIREBASE_CONFIG_TEMPLATE.txt
- [ ] Save all important URLs/values
- [ ] Take a screenshot of Firebase Console (optional)

---

## ✅ Phase 0 Complete!

Once all boxes are checked, you're ready for Phase 1: Backend Development.

**Estimated time:** 20-30 minutes  
**Actual time:** _______ minutes

**Issues encountered:**
- (Note any problems here for future reference)

---

**Ready for Phase 1?** Let me know and we'll start building the Node.js backend! 🚀

