# Firebase Concepts Cheat Sheet

Quick reference for Firebase/GCP concepts as you build Telos Beta.

---

## 🔑 Authentication Concepts

### Firebase ID Token
- **What:** A JWT (JSON Web Token) that proves a user's identity
- **Lifetime:** 1 hour
- **Purpose:** Sent with every API request to your backend
- **Format:** `Authorization: Bearer eyJhbGc...`
- **Security:** Backend verifies this with Firebase Admin SDK

### Refresh Token
- **What:** A long-lived token to get new ID tokens
- **Lifetime:** ~30 days (configurable)
- **Purpose:** When ID token expires, client uses this to get a new one
- **Storage:** `~/.telos/auth.json` (on user's machine)

### Anonymous Authentication
- **What:** Temporary account with no email/password
- **UID:** Each anonymous user gets a unique ID
- **Why:** Zero-friction onboarding - user tries app immediately
- **Later:** Can be "upgraded" to email/password (keeps same UID!)

### Email/Password Authentication
- **What:** Traditional account with email + password
- **Linking:** Anonymous → Email means same user, same data
- **Security:** Firebase handles password hashing/salting

---

## 💾 Firestore Concepts

### Document
- **What:** A single record (like a JSON object)
- **Example:** `{ email: "user@example.com", createdAt: "2024-01-01" }`
- **ID:** Each document has a unique ID (auto-generated or custom)

### Collection
- **What:** A folder of documents (like a table in SQL)
- **Example:** `users` collection contains user documents

### Path Structure
```
users/{uid}/sessions/{sessionId}
└──┬──┘ └┬┘ └───┬───┘ └────┬────┘
 colln  doc   colln      doc
```

### Your Schema (from the plan)
```
prompts/
  {promptName}/          # e.g. "screenshot_analysis"
    activeVersion: "v1"
    updatedAt: timestamp

prompt_versions/
  {promptName}/
    versions/
      {version}/         # e.g. "v1", "v2"
        content: "Analyze this screenshot..."
        createdAt: timestamp

users/
  {uid}/
    email: "user@example.com"  # null until linked
    createdAt: timestamp
    lastSeenAt: timestamp
    betaFlags: {}

usage/
  {uid}/
    dailyCount: 150
    lastRequest: timestamp
```

---

## 🔒 Secret Manager

### Secret vs Environment Variable
| | Secret Manager | Env Var |
|---|---|---|
| Security | Encrypted, access-controlled | Plain text, easy to leak |
| Rotation | Easy (versioned) | Requires redeployment |
| Auditing | Full access logs | No tracking |
| Cost | $0.06/secret/month | Free |

### Best Practices
- ✅ **Use for:** API keys, database passwords, JWT secrets
- ❌ **Don't use for:** Non-sensitive config (ports, feature flags)

---

## ☁️ Cloud Run Concepts

### What is Cloud Run?
- **Serverless containers:** You give Google a Docker image, they run it
- **Auto-scaling:** 0 to 1000 instances automatically
- **Pay-per-use:** Billed by request, not uptime

### Request Lifecycle
```
User uploads screenshot
    ↓
Cloud Run spins up container (if needed) ⚡ cold start ~1-2s
    ↓
Your Express app handles request
    ↓
Cloud Run keeps container warm for ~15 min
    ↓
No requests for 15 min → container shuts down (saves money!)
```

### Cold Start
- **What:** Delay when starting a new container
- **Duration:** 1-3 seconds (Node.js is fast)
- **When:** First request, or after idle period
- **Mitigation:** Keep 1 instance always warm (costs more)

---

## 🔐 Firebase Admin SDK vs REST API

### REST API (for Python client)
- **Language:** Any (HTTP requests)
- **Use case:** Client apps
- **Example:** Anonymous sign-in, refresh token
- **Auth:** Uses Firebase Web API Key

### Admin SDK (for Node backend)
- **Language:** Node, Python, Java, Go, etc.
- **Use case:** Server/backend apps
- **Powers:** Verify ID tokens, manage users, bypass security rules
- **Auth:** Uses service account credentials

---

## 📊 Rate Limiting Strategies

### Per-UID (User)
- **Track:** Requests per user ID
- **Storage:** Firestore `usage/{uid}` document
- **Granularity:** Per hour, per day
- **Bypass:** Can't - tied to user identity

### Per-IP Address
- **Track:** Requests per IP
- **Storage:** In-memory (Redis/Memcached) or Firestore
- **Granularity:** Per minute
- **Bypass:** Easy (VPN, proxy) - less reliable

### Best Practice: Use Both
- Per-UID for logged-in users (primary)
- Per-IP for anonymous/unauthenticated endpoints (fallback)

---

## 🎨 JSON Schema for Analysis Response

Your backend will return this structure (same as current local version):

```json
{
  "category": "Productive",
  "app": "Visual Studio Code",
  "task": "Editing Python file - function implementation",
  "confidence": 0.95,
  "detailed_context": "Writing a FastAPI endpoint handler...",
  "category_emoji": "💼",
  "category_color": "#10B981"
}
```

**Validation:** Backend should enforce this schema before returning (use Joi or Zod in Node.js).

---

## 🚨 Common Gotchas

### 1. Firestore Region is Permanent
Once you choose `us-central1`, you **cannot** change it. Choose wisely based on your target users.

### 2. Firebase Web API Key is NOT Secret
It's safe to embed in client code. It identifies your project but doesn't grant admin access.

### 3. ID Tokens Expire (1 hour)
Your Python client must refresh tokens proactively or handle 401 errors gracefully.

### 4. Anonymous Accounts Can Be Lost
If user clears `~/.telos/auth.json`, their anonymous account is gone. That's why email linking is important.

### 5. Firestore Reads Cost Money
Every document read counts toward your quota. Cache aggressively (e.g., load prompts once at backend startup).

---

## 📚 Useful Links

- **Firebase Auth REST API:** https://firebase.google.com/docs/reference/rest/auth
- **Firestore Python Client:** https://firebase.google.com/docs/firestore/quickstart
- **Cloud Run Docs:** https://cloud.google.com/run/docs
- **Secret Manager API:** https://cloud.google.com/secret-manager/docs
- **Firebase Admin Node.js:** https://firebase.google.com/docs/admin/setup

---

## 💡 Quick Debugging Tips

### "Permission Denied" in Firestore
- Check security rules
- Verify user is authenticated
- Confirm service account has Firestore permissions

### "Invalid ID Token"
- Token might be expired (refresh it)
- Token might be for wrong project (check API key)
- Backend clock might be skewed (rare)

### "API not enabled"
- Go to GCP Console → APIs & Services → Enable the API
- Wait ~1 minute for propagation

### Backend Logs Not Showing
- Go to Cloud Run → Your Service → LOGS tab
- Or use `gcloud run logs tail <service-name>`

---

**Keep this handy as we build!** 📌

