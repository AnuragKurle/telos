# Shared

Resources shared between the client and backend to keep them in sync.

## Contents

| File | Purpose |
|------|---------|
| `api-contract.md` | API specification -- endpoints, auth, rate limits, error codes. **Source of truth.** |
| `types.json` | JSON Schema definitions for API types (AnalysisResult, ErrorResponse, etc.) |
| `constants.json` | Shared constants -- categories, rate limits, upload limits, timeouts |

## Workflow

When making changes that affect both client and backend:

1. Update `api-contract.md` first
2. Update `types.json` / `constants.json` if needed
3. Implement in backend, then client
4. Test both together locally
5. Commit changes together
