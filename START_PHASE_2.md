# 🚀 Start Phase 2: Client Integration

**Start here after deploying your backend!**

---

## ✅ What You've Already Completed

### Phase 0: Cloud Infrastructure ✅
- Google Cloud Project configured
- Firebase Auth enabled
- Firestore database created
- Secret Manager with Gemini API key
- All APIs enabled

### Phase 1: Backend Development ✅
- Node.js Express backend complete
- Firebase token verification
- Rate limiting (100/hour, 2000/day)
- Gemini API integration (server-side)
- Screenshot upload endpoint
- Ready for Cloud Run deployment

**Backend Status:** ✅ All code complete, ready to deploy

---

## 📍 Phase 2 Overview

**What we're building:**
A Python client that:
- Authenticates with Firebase (anonymous sign-in)
- Uploads screenshots to your backend
- Receives AI analysis from Gemini
- Stores results in local SQLite
- Falls back to local Gemini if backend unavailable

**Time estimate:** 2-3 hours

---

## 🎯 Before You Start Phase 2

### 1. Deploy Your Backend

**Quick deploy:**
```bash
cd backend
./deploy.sh  # or .\deploy.ps1 on Windows
```

**Manual deploy:**
See `backend/DEPLOYMENT.md` for detailed instructions.

**After deployment, you'll get a URL like:**
```
https://telos-backend-xxxxx-uc.a.run.app
```

**Save this URL!** You'll need it for client configuration.

### 2. Test Backend Health

```bash
curl https://telos-backend-xxxxx-uc.a.run.app/health
```

Should return:
```json
{
  "status": "ok",
  "service": "telos-backend",
  "version": "0.1.0",
  "timestamp": "2025-01-02T..."
}
```

### 3. Set Up Firestore Prompts

```bash
cd backend
npm run setup
```

This populates Firestore with the default screenshot analysis prompt.

---

## 🛠️ Phase 2 Implementation Checklist

### Todo 1: Firebase Auth REST API (Python)
**Status:** Pending

**What to build:**
- Anonymous sign-in via Firebase REST API
- Token refresh logic
- Persist tokens to `~/.telos/auth.json`

**Files to create:**
- `client/core/firebase_auth.py`

**You'll need:**
- Firebase Web API Key (from `docs/firebase-credentials.txt`)

---

### Todo 2: Backend Client Module
**Status:** Pending

**What to build:**
- HTTP client for backend API
- Upload screenshot with Firebase token
- Handle rate limiting (429 responses)
- Handle token refresh (401 responses)
- Proper error handling

**Files to create:**
- `client/core/backend_client.py`

---

### Todo 3: Proxy Analysis Pipeline
**Status:** Pending

**What to build:**
- Modify capture pipeline to use backend
- Replace local Gemini calls
- Store backend analysis in SQLite
- Track upload success/failure

**Files to modify:**
- `client/core/analyzer.py`

---

### Todo 4: Fallback Mode
**Status:** Pending

**What to build:**
- Check backend health before upload
- Fall back to local Gemini if backend unavailable
- User preference: always local, always backend, or auto
- Configuration in `config.yaml`

**Files to create:**
- `client/core/fallback_handler.py`

**Files to modify:**
- `client/config.yaml`

---

### Todo 5: Onboarding Flow
**Status:** Pending

**What to build:**
- First-run setup wizard
- Privacy notice
- Goals/intention selection
- Explanation of cloud vs local analysis
- Optional: Skip for MVP

**Files to create:**
- `client/tui/screens/onboarding.py`

---

### Todo 6: Email Linking (Later)
**Status:** Future enhancement

**What to build:**
- Link anonymous account to email
- Store email in Firestore
- Allow email sign-in on other devices

**Files to create:**
- `client/core/email_linking.py`

---

## 📋 Phase 2 Tasks (Ordered)

### High Priority (MVP)
1. ✅ Deploy backend to Cloud Run
2. ✅ Test backend health endpoint
3. 📋 Implement Firebase Auth REST in Python
4. 📋 Create backend client module
5. 📋 Modify analyzer to use backend
6. 📋 Test end-to-end flow

### Medium Priority
7. 📋 Implement fallback mode
8. 📋 Add configuration options
9. 📋 Test offline behavior

### Low Priority (Post-MVP)
10. 📋 Onboarding flow
11. 📋 Email linking
12. 📋 Multi-device sync

---

## 🔧 Configuration Updates Needed

### `client/config.yaml`

Add these fields:
```yaml
# Backend Configuration
backend:
  enabled: true
  url: "https://telos-backend-xxxxx-uc.a.run.app"
  fallback_to_local: true
  timeout: 30

# Firebase Configuration (from firebase-credentials.txt)
firebase:
  api_key: "AIza..."
  project_id: "gen-lang-client-0772617718"
  auth_domain: "gen-lang-client-0772617718.firebaseapp.com"

# Client Version (must match MIN_CLIENT_VERSION in backend)
version: "0.1.0"
```

---

## 🧪 Testing Strategy

### 1. Unit Tests (Optional)
```python
# Test Firebase auth
python -m pytest tests/test_firebase_auth.py

# Test backend client
python -m pytest tests/test_backend_client.py
```

### 2. Integration Tests
```bash
# Test full flow
python -c "
from core.backend_client import BackendClient
client = BackendClient()
result = client.analyze_screenshot('test.png')
print(result)
"
```

### 3. Manual Testing
- Take screenshot
- Verify upload to backend
- Check Cloud Run logs
- Verify data in SQLite
- Test rate limiting (100+ requests)
- Test token refresh after 1 hour
- Test fallback when backend down

---

## 📊 Success Criteria for Phase 2

By the end, you'll have:
- ✅ Python client authenticates with Firebase
- ✅ Screenshots upload to backend
- ✅ Analysis stored in local SQLite
- ✅ Fallback to local Gemini works
- ✅ Token refresh automatic
- ✅ Rate limiting handled gracefully
- ✅ End-to-end flow tested

---

## 🚀 Quick Start (When You Resume)

### 1. Verify Backend is Deployed
```bash
curl https://your-backend-url.run.app/health
```

### 2. Start Phase 2 Implementation
```bash
cd client
# Start with Firebase Auth implementation
```

### 3. Tell the AI You're Ready
Say something like:
> "Backend is deployed at [URL]. Ready to start Phase 2! Let's implement Firebase Auth REST in Python."

---

## 📖 Helpful References

### Firebase REST API
https://firebase.google.com/docs/reference/rest/auth

Key endpoints:
- `accounts:signUp` - Anonymous sign-in
- `securetoken.googleapis.com/v1/token` - Refresh token

### Python Requests Library
```python
import requests

response = requests.post(
    url,
    headers={'Authorization': f'Bearer {token}'},
    files={'image': open('screenshot.png', 'rb')}
)
```

---

## 💡 Tips for Phase 2

### 1. Start Small
- Get Firebase auth working first
- Then test backend upload
- Finally integrate into capture loop

### 2. Test Incrementally
```bash
# Test auth
python -c "from core.firebase_auth import get_token; print(get_token())"

# Test upload
python -c "from core.backend_client import upload; upload('test.png')"
```

### 3. Handle Errors Gracefully
- Network timeouts
- Token expiration
- Rate limiting
- Backend unavailable

### 4. Log Everything (During Development)
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎯 Where You Are Now

```
Phase 0: Cloud Setup          ✅ COMPLETE
Phase 1: Backend Dev          ✅ COMPLETE
├─ Backend code               ✅ DONE
└─ Ready to deploy            ✅ READY

Phase 2: Client Integration   📍 START HERE
├─ Deploy backend             📋 TODO (5 min)
├─ Firebase Auth REST         📋 TODO
├─ Backend client             📋 TODO
├─ Proxy analysis             📋 TODO
├─ Fallback mode              📋 TODO
└─ Testing                    📋 TODO

Phase 3: Beta Launch          ⏳ AFTER PHASE 2
```

---

## ❓ Common Questions

### "Do I need to change the local SQLite schema?"
No! The backend returns the same JSON format that your local Gemini analysis uses. No schema changes needed.

### "What if the backend is slow?"
The client should have a timeout (30 seconds). If exceeded, fall back to local analysis.

### "How do I test rate limiting?"
Write a script to upload 101 screenshots rapidly. The 101st should return 429.

### "Can users opt out of cloud analysis?"
Yes! Add a config option: `backend.enabled: false` to always use local Gemini.

---

## 🔥 Next Steps

1. **Deploy backend** (if not done yet)
   ```bash
   cd backend
   ./deploy.sh
   ```

2. **Save the Cloud Run URL**

3. **Open Phase 2 checklist** (this file)

4. **Tell the AI you're ready:**
   > "Backend deployed at [URL]. Let's start Phase 2!"

---

**See you in Phase 2! 🚀**

