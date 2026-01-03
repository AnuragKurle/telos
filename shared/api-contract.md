# Telos API Contract v1

**Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Status:** Draft (Phase 1 implementation)

This document defines the contract between the Telos Python client and the Node.js backend.

---

## Base URL

- **Local Development:** `http://localhost:8080`
- **Production (Beta):** `https://telos-backend-[hash].run.app` (will be set after Cloud Run deployment)

---

## Authentication

All endpoints (except `/health`) require Firebase Authentication.

### Headers

```
Authorization: Bearer <firebase-id-token>
```

### Getting a Token (Client Implementation)

1. Anonymous sign-in via Firebase REST API
2. Store `idToken` and `refreshToken` in `~/.telos/auth.json`
3. Include `idToken` in `Authorization` header
4. Refresh token when expired (1 hour lifetime)

---

## Endpoints

### 1. Health Check

```http
GET /health
```

**Purpose:** Verify backend is running (for client fallback logic)

**Response 200:**
```json
{
  "status": "ok",
  "service": "telos-backend",
  "version": "0.1.0",
  "timestamp": "2025-01-02T10:30:00.000Z"
}
```

**Client Usage:**
- Check before uploading screenshot
- If fails, fall back to local Gemini analysis

---

### 2. Analyze Screenshot

```http
POST /v1/analyze/screenshot
```

**Purpose:** Upload screenshot for AI analysis

**Headers:**
```
Authorization: Bearer <firebase-id-token>
Content-Type: multipart/form-data
X-Client-Version: 0.1.0
```

**Body:**
```
Form field: image (required)
  Type: File (PNG, JPEG, WebP)
  Max size: 10MB
  Dimensions: No limit (will be resized if needed)
```

**Response 200 (Success):**
```json
{
  "category": "Productive",
  "app": "Visual Studio Code",
  "task": "Editing Python file - implementing Firebase authentication",
  "confidence": 0.95,
  "detailed_context": "User is writing Python code to integrate Firebase Auth REST API. Multiple terminal windows visible with backend logs. Documentation open in browser tabs.",
  "category_emoji": "💼",
  "category_color": "#10B981",
  "analysis_version": "v1",
  "timestamp": "2025-01-02T10:30:15.123Z"
}
```

**Response 400 (Bad Request):**
```json
{
  "error": "ValidationError",
  "message": "Missing required field: image",
  "code": "MISSING_IMAGE"
}
```

**Response 401 (Unauthorized):**
```json
{
  "error": "AuthenticationError",
  "message": "Invalid or expired token",
  "code": "INVALID_TOKEN"
}
```

**Response 429 (Rate Limited):**
```json
{
  "error": "RateLimitError",
  "message": "Rate limit exceeded. Try again in 3600 seconds.",
  "retry_after": 3600,
  "code": "RATE_LIMIT_EXCEEDED"
}
```

**Response 426 (Upgrade Required):**
```json
{
  "error": "ClientVersionError",
  "message": "Client version 0.0.9 is too old. Minimum required: 0.1.0",
  "minimum_version": "0.1.0",
  "download_url": "https://github.com/yourrepo/telos/releases",
  "code": "CLIENT_TOO_OLD"
}
```

**Response 500 (Server Error):**
```json
{
  "error": "InternalError",
  "message": "Analysis failed. Please try again.",
  "code": "ANALYSIS_FAILED"
}
```

---

### 3. Submit Feedback

```http
POST /v1/feedback
```

**Purpose:** Submit user feedback on AI analysis quality

**Headers:**
```
Authorization: Bearer <firebase-id-token>
Content-Type: application/json
X-Client-Version: 0.1.0
```

**Body:**
```json
{
  "feedback_type": "summary",
  "feedback_text": "Category should be Learning, not Browsing",
  "context": {
    "summary_id": 123,
    "screen": "summary",
    "app": "Chrome",
    "task": "Reading documentation",
    "category": "Browsing"
  },
  "metadata": {
    "screen": "summary",
    "app_version": "0.1.0"
  }
}
```

**Fields:**
- `feedback_type` (required): One of `summary`, `session`, `capture`, `chat`, `general`
- `feedback_text` (required): User's feedback text
- `context` (optional): Contextual data about what's being corrected
- `metadata` (optional): Client metadata (screen, app version, etc.)

**Response 201 (Success):**
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback_id": "abc123def456",
  "slack_notified": true
}
```

**Fields:**
- `slack_notified`: Whether Slack notification succeeded (added in v1.1.0)
  - `true` - Feedback sent to Slack successfully
  - `false` - Feedback saved to Firestore but Slack failed (dev will check)

**Response 400 (Bad Request):**
```json
{
  "error": "Feedback text is required"
}
```

**Response 401 (Unauthorized):**
```json
{
  "error": "Invalid or expired token"
}
```

**Client Usage:**
- Show warning if `slack_notified` is `false`
- Feedback is always saved to Firestore even if Slack fails

---

## Response Schema

### Analysis Result Object

All successful analysis responses follow this schema:

```typescript
{
  category: string;           // One of: Productive, Communication, Research, 
                              // Entertainment, Distraction, System, Uncategorized
  
  app: string;                // Detected application name (e.g., "Chrome", "Slack")
  
  task: string;               // Brief description of user activity 
                              // (e.g., "Reading documentation")
  
  confidence: number;         // 0.0 to 1.0 - how confident the AI is
  
  detailed_context: string;   // Extended description (2-3 sentences)
  
  category_emoji: string;     // Unicode emoji representing category
  
  category_color: string;     // Hex color for UI (e.g., "#10B981")
  
  analysis_version: string;   // Prompt version used (e.g., "v1")
  
  timestamp: string;          // ISO 8601 timestamp of analysis
}
```

### Categories & Colors Reference

| Category | Emoji | Color |
|----------|-------|-------|
| Productive | 💼 | #10B981 (green) |
| Communication | 💬 | #3B82F6 (blue) |
| Research | 📚 | #8B5CF6 (purple) |
| Entertainment | 🎬 | #F59E0B (amber) |
| Distraction | 🎮 | #EF4444 (red) |
| System | ⚙️ | #6B7280 (gray) |
| Uncategorized | ❓ | #9CA3AF (light gray) |

---

## Rate Limits (Beta)

Per user (`uid`):
- **100 requests per hour**
- **2,000 requests per day**

Headers in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1704196200
```

---

## Error Codes Reference

| Code | HTTP Status | Meaning | Client Action |
|------|-------------|---------|---------------|
| `MISSING_IMAGE` | 400 | No image in request | Fix client bug |
| `INVALID_TOKEN` | 401 | Token expired/invalid | Refresh token |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait and retry |
| `CLIENT_TOO_OLD` | 426 | Client outdated | Prompt user to update |
| `ANALYSIS_FAILED` | 500 | Gemini API error | Retry or fall back to local |

---

## Client Implementation Notes

### Error Handling Flow

```python
try:
    response = upload_screenshot(image, token)
    if response.status == 200:
        return response.json()
    elif response.status == 401:
        # Refresh token and retry once
        new_token = refresh_firebase_token()
        return upload_screenshot(image, new_token)
    elif response.status == 429:
        # Respect rate limit
        sleep(response.json()['retry_after'])
    elif response.status == 426:
        # Show update prompt to user
        show_update_required_dialog()
    elif response.status >= 500:
        # Fall back to local analysis
        return local_gemini_analysis(image)
except NetworkError:
    # Backend unreachable - use local fallback
    return local_gemini_analysis(image)
```

### Token Refresh

ID tokens expire after 1 hour. Client should:
1. Store token expiry time (from Firebase response)
2. Refresh proactively before expiry
3. Or handle 401 and refresh on-demand

---

## Versioning Strategy

### API Version in URL

`/v1/analyze/screenshot` - Version is in the path

**Breaking changes** → Bump API version (`/v2/...`)  
**Non-breaking changes** → Keep same version, add optional fields

### Client Version Header

Backend checks `X-Client-Version` header and rejects if too old.

**Current minimum:** `0.1.0`

---

## Development & Testing

### Local Testing with cURL

```bash
# Get Firebase token first (using your auth implementation)
TOKEN="your-firebase-id-token"

# Test health
curl http://localhost:8080/health

# Test analysis
curl -X POST http://localhost:8080/v1/analyze/screenshot \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Client-Version: 0.1.0" \
  -F "image=@screenshot.png"
```

### Mock Responses for Testing

During development, backend can return mock responses:

```bash
# Set environment variable
MOCK_ANALYSIS=true npm run dev
```

---

## Future Extensions (Post-Beta)

These endpoints are planned but not yet implemented:

- `GET /v1/user/profile` - Get user profile
- `POST /v1/user/link-email` - Link anonymous to email
- `GET /v1/user/usage` - Get usage stats

---

## Changelog

### v1.1.0 (2026-01-03)
- **Added** `/v1/feedback` endpoint for submitting user feedback
- **Fixed** Feedback now awaits Slack notification instead of fire-and-forget
- **Added** `slack_notified` field in feedback response
- **Added** Slack delivery status logged to Firestore for monitoring

### v1.0.0 (2025-01-02)
- Initial API contract
- `/health` endpoint
- `/v1/analyze/screenshot` endpoint
- Firebase authentication
- Rate limiting specification

---

**Questions or Issues?**  
This contract evolves during development. Update both copies when making changes:
- `shared/api-contract.md` (source of truth)
- Backend: `backend/README.md` (reference)
- Client: Document in code comments

