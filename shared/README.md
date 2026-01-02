# Shared Resources

This directory contains resources shared between the Telos client and backend.

## Purpose

In a monorepo, shared resources ensure consistency between frontend and backend:
- **API contracts** - Single source of truth for endpoints
- **Type definitions** - Shared data structures
- **Constants** - Shared enums and values
- **Documentation** - Architecture docs

## Contents

### `api-contract.md`
Complete API specification for client-backend communication.
- Endpoint definitions
- Request/response formats
- Error codes
- Authentication flow
- Rate limits

**⚠️ This is the source of truth!** Update this file when making API changes, then update both client and backend to match.

### `types.json`
JSON Schema definitions for shared data structures.
- Analysis result schema
- User object schema
- Error response schema

Can be used by both Python (with `jsonschema`) and Node.js (with `ajv`) for validation.

### `constants.json`
Shared constants and configuration values.
- Categories and their metadata (emoji, colors)
- Supported file types
- Size limits
- Timeout values

## Usage

### In Backend (Node.js)

```javascript
import { categories } from '../shared/constants.json' assert { type: 'json' };
```

### In Client (Python)

```python
import json
from pathlib import Path

shared_dir = Path(__file__).parent.parent / 'shared'
with open(shared_dir / 'constants.json') as f:
    constants = json.load(f)
```

## Workflow

When making changes that affect both client and backend:

1. **Update API contract** (`api-contract.md`) first
2. **Update types/constants** if needed
3. **Implement in backend** following the contract
4. **Implement in client** following the contract
5. **Test** both together locally
6. **Commit** changes to both client and backend together

## Versioning

The API contract includes version numbers. When making breaking changes:
1. Increment version in `api-contract.md`
2. Update `MIN_CLIENT_VERSION` in backend
3. Update client to check version compatibility
4. Consider backward compatibility period

## Why Not Just Duplicate?

You might ask: "Why not just document this in both repos?"

**Problems with duplication:**
- ❌ Docs drift out of sync
- ❌ Hard to see what changed
- ❌ Unclear which is correct
- ❌ More maintenance burden

**Benefits of shared docs:**
- ✅ Single source of truth
- ✅ Changes are atomic (one commit updates both)
- ✅ Git history shows evolution
- ✅ Easier for new developers

---

**When we split to separate repos:** These files can be published as an npm package / Python package, or kept as git submodule.

