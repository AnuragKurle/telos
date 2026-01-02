# 🚀 Start Phase 1: Backend Development

**Start here when you're ready to build the Node.js backend!**

---

## ✅ What You've Already Completed

### Phase 0: Cloud Infrastructure ✅
- Google Cloud Project configured
- Firebase Auth enabled (Anonymous + Email/Password)
- Firestore database created
- Secret Manager configured with Gemini API key
- All APIs enabled
- Budget alerts set

**Your credentials:** See `docs/firebase-credentials.txt` (gitignored, on your computer only)

---

## 🎯 Phase 1 Overview

**What we're building:**
A Node.js Express backend that:
- Accepts screenshot uploads from Python client
- Verifies Firebase authentication tokens
- Calls Gemini API server-side (keeps prompts secret!)
- Returns analysis JSON to client
- Implements rate limiting (100/hour, 2000/day)
- Deploys to Google Cloud Run

**Time estimate:** 2-3 hours (with explanations)

---

## 📚 Documents You'll Need

### 1. **API Contract (Source of Truth)**
📄 `shared/api-contract.md`
- Complete endpoint specifications
- Request/response formats
- Error codes
- Authentication flow

### 2. **Backend Skeleton (Already Created!)**
📁 `backend/`
- `src/server.js` - Express app with health check ✅
- `package.json` - Dependencies defined ✅
- `Dockerfile` - Cloud Run deployment ready ✅
- `README.md` - Backend documentation ✅

### 3. **Build Plan**
📄 `.cursor/plans/telos_beta_build_(firebase+cloudrun)_c3e9f41c.plan.md`
- Complete Phase 1 tasks
- Dependencies between tasks
- Implementation order

### 4. **Firebase Credentials**
📄 `docs/firebase-credentials.txt` (on your computer, gitignored)
- Project ID
- Firebase Web API Key
- All other credentials

---

## 🛠️ Phase 1 Implementation Checklist

### Todo 1: Backend MVP Express ✅
**Status:** Skeleton ready! Health check works.

**What's done:**
- Express server created
- Health endpoint working
- Package.json with dependencies

**Next:** Add Firebase Admin SDK

---

### Todo 2: Client Version Check
**Status:** Pending

**What to build:**
- Middleware that checks `X-Client-Version` header
- Returns 426 error if client too old
- Configurable minimum version

**Files to modify:**
- `backend/src/middleware/versionCheck.js` (create)
- `backend/src/server.js` (add middleware)

---

### Todo 3: Firebase Token Verification
**Status:** Pending

**What to build:**
- Initialize Firebase Admin SDK
- Middleware to verify ID tokens
- Extract user UID from token
- Return 401 if invalid/expired

**Files to create:**
- `backend/src/middleware/auth.js`
- `backend/src/config/firebase.js`

**You'll need:**
- Firebase project ID from `firebase-credentials.txt`

---

### Todo 4: Rate Limiting
**Status:** Pending

**What to build:**
- Firestore-based rate limiter
- Track requests per UID (100/hour, 2000/day)
- Return 429 with retry_after if exceeded

**Files to create:**
- `backend/src/middleware/rateLimit.js`

---

### Todo 5: Gemini API Integration
**Status:** Pending

**What to build:**
- Fetch Gemini key from Secret Manager
- Load prompt from Firestore
- Call Gemini Vision API
- Return strict JSON schema

**Files to create:**
- `backend/src/services/gemini.js`
- `backend/src/services/secrets.js`
- `backend/src/services/prompts.js`

---

### Todo 6: Screenshot Upload Endpoint
**Status:** Pending

**What to build:**
- `POST /v1/analyze/screenshot` endpoint
- Multer middleware for multipart/form-data
- Validate image format/size
- Process in-memory (don't save to disk)
- Return analysis JSON

**Files to create:**
- `backend/src/routes/analyze.js`
- `backend/src/middleware/upload.js`

---

### Todo 7: Cloud Run Deployment
**Status:** Pending (do last)

**What to do:**
- Build Docker container
- Deploy to Cloud Run
- Configure environment variables
- Test production endpoint

**Commands:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/telos-backend
gcloud run deploy telos-backend --image gcr.io/PROJECT_ID/telos-backend
```

---

## 🚀 How to Resume (Step-by-Step)

### 1. Open Your IDE
```bash
cd D:\Experiments\screentracker
```

### 2. Verify You're on the Right Branch
```bash
git branch
# Should show: * main-monorepo
```

### 3. Open Key Files
- `START_PHASE_1.md` (this file!)
- `shared/api-contract.md` (API spec)
- `backend/src/server.js` (backend entry point)
- `docs/firebase-credentials.txt` (your credentials)

### 4. Tell the AI You're Ready
Say something like:
> "Ready to start Phase 1! Let's build the backend. Start with Firebase Admin SDK integration."

Or:
> "Let's implement Phase 1, todo by todo. Start with backend-auth-verify."

---

## 💡 Tips for Phase 1

### 1. We'll Build Incrementally
Each todo = working code you can test immediately

### 2. Test as We Go
```bash
# Terminal 1: Run backend
cd backend
npm install
npm run dev

# Terminal 2: Test endpoints
curl http://localhost:8080/health
```

### 3. Commit Often
After each major todo, commit:
```bash
git add backend/
git commit -m "feat: implement Firebase token verification"
```

### 4. Ask Questions!
If anything is unclear:
- How does Firebase Admin work?
- Why are we using Firestore for rate limiting?
- What's the difference between service account and API key?

I'll explain everything!

---

## 📖 Helpful References

### Firebase Admin SDK (Node.js)
https://firebase.google.com/docs/admin/setup

We'll use this to verify tokens sent by your Python client.

### Gemini API (Node.js)
https://ai.google.dev/gemini-api/docs/get-started/node

We'll call this server-side to keep prompts secret.

### Cloud Run Docs
https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-nodejs-service

We'll deploy here at the end.

---

## 🎯 Success Criteria for Phase 1

By the end, you'll have:
- ✅ Backend running locally (`npm run dev`)
- ✅ Health check endpoint working
- ✅ Screenshot analysis endpoint working
- ✅ Firebase token verification
- ✅ Rate limiting enforced
- ✅ Gemini integration (server-side)
- ✅ Deployed to Cloud Run
- ✅ Python client can call it (we'll update client in Phase 2)

---

## 📊 Where You Are Now

```
Phase 0: Cloud Setup          ✅ COMPLETE
├─ Firebase Auth              ✅
├─ Firestore                  ✅
├─ Secret Manager             ✅
└─ Budget Alerts              ✅

Phase 1: Backend Dev          📍 START HERE
├─ Express skeleton           ✅ READY
├─ Firebase Admin SDK         📋 TODO
├─ Token verification         📋 TODO
├─ Rate limiting              📋 TODO
├─ Gemini integration         📋 TODO
├─ Upload endpoint            📋 TODO
└─ Cloud Run deployment       📋 TODO

Phase 2: Client Integration   ⏳ AFTER PHASE 1
Phase 3: Beta Launch          ⏳ AFTER PHASE 2
```

---

## 🔥 Quick Start Commands (When You Resume)

```bash
# 1. Navigate to project
cd D:\Experiments\screentracker

# 2. Check branch
git status

# 3. Open backend
cd backend

# 4. Install dependencies (if not done yet)
npm install

# 5. Start development server
npm run dev

# Should see: 🚀 Telos Backend running on port 8080
```

---

## ❓ Common Questions When Resuming

### "What environment variables do I need?"
Create `backend/.env` with:
```env
PORT=8080
NODE_ENV=development
FIREBASE_PROJECT_ID=gen-lang-client-0772617718
GCP_PROJECT_ID=gen-lang-client-0772617718
GEMINI_SECRET_NAME=GEMINI_API_KEY
```

Copy from `backend/env.example` and fill in values from `docs/firebase-credentials.txt`.

### "Where are my credentials?"
`docs/firebase-credentials.txt` (on your computer, not in git)

### "What's the first thing to implement?"
Firebase Admin SDK integration for token verification. This is the foundation - everything else builds on it.

### "Can I test without the client?"
Yes! We'll use `curl` or Postman to test each endpoint as we build.

---

## 🎉 You're All Set!

When you're ready to continue:
1. Open this file (`START_PHASE_1.md`)
2. Review the checklist above
3. Tell me you're ready to start
4. We'll build todo by todo, with full explanations!

**Estimated time:** 2-3 hours for Phase 1 (with breaks)

---

**See you soon! 🚀**

