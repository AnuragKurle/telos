# Phase 0: Firebase & GCP Setup Guide

## What We're Doing in This Phase

We're setting up the **foundation** of your cloud infrastructure:
- A Google Cloud Project (the container for everything)
- Firebase Authentication (for user accounts)
- Firestore Database (for storing prompts and user metadata)
- Secret Manager (for securely storing your Gemini API key)
- Budget alerts (so you don't get surprise bills!)

**Time estimate:** 20-30 minutes  
**Cost:** $0 during setup (free tier should cover beta usage)

---

## Prerequisites

- [ ] A Google account
- [ ] Your Gemini API key (from Google AI Studio)
- [ ] A credit card (required by GCP, but we'll set strict budget limits)

---

## Step 1: Create a Google Cloud Project

### What is a GCP Project?
Think of it as a **folder** that contains all your cloud resources (databases, servers, etc.). Everything for Telos will live here.

### Instructions:

1. Go to: https://console.cloud.google.com/
2. Click **"Select a project"** (top left, near the logo)
3. Click **"NEW PROJECT"** (top right of the modal)
4. Fill in:
   - **Project name:** `telos-beta` (or whatever you prefer)
   - **Organization:** Leave as "No organization" (unless you have a company)
   - **Location:** Leave as default
5. Click **"CREATE"**
6. Wait ~30 seconds for it to provision
7. **Make sure the new project is selected** (check the dropdown at the top)

### What Just Happened?
You now have an isolated environment in Google's cloud. Anything you create here won't interfere with other projects.

---

## Step 2: Enable Billing & Set Budget Alerts

### Why Billing?
Firebase/GCP require a billing account to use most services (even free tier). Don't worry - we'll set strict limits.

### Instructions:

1. Go to: https://console.cloud.google.com/billing
2. Click **"Link a billing account"** or **"Add billing account"**
3. Enter your credit card info
4. Select the billing account for your `telos-beta` project

### Set Budget Alerts (IMPORTANT!)

1. Go to: https://console.cloud.google.com/billing/budgets
2. Click **"CREATE BUDGET"**
3. Fill in:
   - **Name:** "Telos Beta Budget"
   - **Projects:** Select `telos-beta`
   - **Budget type:** Specified amount
   - **Target amount:** `$50` (adjust based on your comfort level)
   - **Set alert thresholds:** 50%, 75%, 90%, 100%
   - **Email notifications:** Your email
4. Click **"FINISH"**

### What Just Happened?
You'll now get email alerts if costs approach $50/month. For context:
- **Gemini API:** ~$0.00025 per image analysis (1.5c/minute at 1 screenshot per min)
- **Cloud Run:** Free tier = 2 million requests/month
- **Firestore:** Free tier = 50K reads/day, 20K writes/day

For 10 beta users, you should stay well under $50/month.

---

## Step 3: Enable Required APIs

### What are APIs?
These are Google's services. They're disabled by default to prevent accidental usage.

### Instructions:

1. Go to: https://console.cloud.google.com/apis/library
2. Search for and enable each of these (click "ENABLE" on each page):
   - **Firebase Authentication API**
   - **Cloud Firestore API**
   - **Secret Manager API**
   - **Cloud Run API**
   - **Cloud Build API** (needed for deploying to Cloud Run)
3. This takes ~1 minute per API

### What Just Happened?
Your project can now use these services. Without enabling them, API calls would fail with "API not enabled" errors.

---

## Step 4: Set Up Firebase

### What is Firebase?
Firebase is Google's app development platform. It sits on top of Google Cloud and makes common tasks (auth, databases) easier.

### Instructions:

1. Go to: https://console.firebase.google.com/
2. Click **"Add project"**
3. Select your existing `telos-beta` project (don't create a new one!)
4. **Google Analytics:** Toggle OFF (you don't need it for beta)
5. Click **"Continue"**
6. Wait ~30 seconds for Firebase to be added to your project

### What Just Happened?
Firebase is now connected to your GCP project. You get access to Firebase's easy-to-use console while still having full GCP power.

---

## Step 5: Enable Firebase Authentication

### What is Firebase Auth?
It handles user login/accounts. You don't have to write code for password hashing, sessions, etc.

### Instructions:

1. In Firebase Console, click **"Authentication"** in the left sidebar
2. Click **"Get started"**
3. Go to the **"Sign-in method"** tab
4. Enable **Anonymous**:
   - Click "Anonymous"
   - Toggle "Enable"
   - Click "Save"
5. Enable **Email/Password**:
   - Click "Email/Password"
   - Toggle "Enable" (leave "Email link" disabled)
   - Click "Save"

### What Just Happened?
- Users can now create anonymous accounts (instant, no signup)
- Later, they can upgrade those anonymous accounts to email/password accounts
- Firebase handles all the security and token management

---

## Step 6: Create Firestore Database

### What is Firestore?
A NoSQL database (like MongoDB). It stores JSON-like documents. Perfect for flexible data like prompts and user info.

### Instructions:

1. In Firebase Console, click **"Firestore Database"** in left sidebar
2. Click **"Create database"**
3. Choose **"Production mode"** (we'll set rules properly later)
4. Select location: **Choose the one closest to you**
   - `us-central1` (Iowa) - good default for North America
   - `europe-west1` (Belgium) - for Europe
   - `asia-northeast1` (Tokyo) - for Asia
   - ⚠️ **You can't change this later!**
5. Click **"Enable"**
6. Wait ~1 minute for provisioning

### What Just Happened?
You now have a cloud database. Your backend will store:
- AI prompts and their versions
- User metadata (email, joined date, etc.)
- Usage counters (for rate limiting)

---

## Step 7: Get Firebase Web API Key

### What is the Web API Key?
This key allows your Python client to talk to Firebase Auth via REST APIs. It's **safe to embed in the client** (it's not a secret - it's like a project identifier).

### Instructions:

1. In Firebase Console, click the **⚙️ gear icon** (top left) → **"Project settings"**
2. Scroll down to **"Your apps"** section
3. You might see "No apps in your project yet"
4. Click the **Web icon** (`</>`)
5. Fill in:
   - **App nickname:** `telos-client`
   - **Don't check** "Also set up Firebase Hosting"
6. Click **"Register app"**
7. You'll see a code snippet. Look for:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIza...",  // ← This is what you need!
     authDomain: "telos-beta.firebaseapp.com",
     projectId: "telos-beta",
     // ... more fields
   };
   ```
8. **Copy the `apiKey` value** and save it somewhere safe (we'll use it later)

### What Just Happened?
This key lets your Python app authenticate users. When a user signs in, your app will send requests to Firebase with this key.

---

## Step 8: Create Secret Manager Secret for Gemini API Key

### What is Secret Manager?
Secure storage for sensitive data (API keys, passwords, etc.). It's encrypted, access-controlled, and versioned.

### Why Not Just Put It in Code?
If you hardcode your Gemini key in your backend code:
- ❌ Anyone with access to your repo sees it
- ❌ Can't rotate it without redeploying
- ❌ It might leak in logs or error messages

Secret Manager solves all of this.

### Instructions:

1. Go to: https://console.cloud.google.com/security/secret-manager
2. Click **"CREATE SECRET"**
3. Fill in:
   - **Name:** `GEMINI_API_KEY`
   - **Secret value:** Paste your Gemini API key (from Google AI Studio)
   - **Regions:** Automatic (default is fine)
4. Click **"CREATE SECRET"**

### What Just Happened?
Your Gemini key is now stored encrypted in Google's infrastructure. Your backend will fetch it at runtime.

---

## Step 9: Set Up Firestore Security Rules (Temporary)

### What are Security Rules?
They control who can read/write data in Firestore. By default, everything is locked down.

### Instructions:

For now, we'll set very permissive rules (since you're the only one testing). We'll tighten them before public beta.

1. In Firebase Console, go to **"Firestore Database"** → **"Rules"** tab
2. Replace the rules with:
   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Allow the backend service account to read/write everything
       match /{document=**} {
         allow read, write: if true;
       }
     }
   }
   ```
3. Click **"Publish"**

⚠️ **Note:** These are temporary dev rules. Before public beta, we'll add proper authentication checks.

### What Just Happened?
Your backend can now read/write to Firestore without restrictions. This is fine for now since only you have access.

---

## Step 10: Record All the Important Info

Create a file to store the values you'll need for development:

### Instructions:

Create a file called `firebase-config.txt` (don't commit this to git!) with:

```
=== Firebase Config (for Phase 0) ===

GCP Project ID: telos-beta
Firebase Web API Key: AIza... (from Step 7)
Gemini API Key Location: Secret Manager → GEMINI_API_KEY

Firestore Location: us-central1 (or whatever you chose)
Firebase Auth Domain: telos-beta.firebaseapp.com

=== What's Next ===
- Phase 1: Build the Node.js backend
- Phase 2: Modify Python client to use Firebase Auth
```

---

## ✅ Phase 0 Complete!

You now have:
- ✅ Google Cloud Project (`telos-beta`)
- ✅ Budget alerts set up (no surprise bills!)
- ✅ Firebase Authentication (Anonymous + Email/Password enabled)
- ✅ Firestore Database (ready to store prompts and user data)
- ✅ Secret Manager secret (Gemini API key stored securely)
- ✅ Firebase Web API Key (for Python client to authenticate)
- ✅ All required APIs enabled

### Cost Check
Everything you've done so far: **$0**

Ongoing costs (estimated for 10 beta users):
- Firestore: ~$0 (well within free tier)
- Firebase Auth: ~$0 (free tier = 10K auths/month)
- Secret Manager: ~$0.06/month (6 cents for 1 secret)
- **Total before Cloud Run/Gemini:** ~$0.06/month

---

## Next: Phase 1 - Backend Development

We'll create a new Node.js backend that:
- Accepts screenshot uploads
- Verifies Firebase tokens
- Calls Gemini with your prompts
- Returns analysis JSON

Ready to move on? 🚀

