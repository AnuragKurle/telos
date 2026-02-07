# Deployment Guide

How to deploy the backend to Cloud Run and build desktop executables.

## Backend Deployment (Cloud Run)

### Prerequisites

- Google Cloud SDK installed and authenticated
- Firebase project configured
- Gemini API key in Secret Manager

### Quick Deploy

```bash
cd backend

# Windows
.\deploy-anywhere.ps1

# Linux/Mac
./deploy.sh
```

### Manual Deploy

**1. Build and push container:**

```bash
gcloud builds submit --tag gcr.io/gen-lang-client-0772617718/telos-backend
```

**2. Deploy to Cloud Run:**

```bash
gcloud run deploy telos-backend \
  --image gcr.io/gen-lang-client-0772617718/telos-backend \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_PROJECT_ID=gen-lang-client-0772617718,GCP_PROJECT_ID=gen-lang-client-0772617718,GEMINI_SECRET_NAME=GEMINI_API_KEY,MIN_CLIENT_VERSION=0.1.0,NODE_ENV=production \
  --memory 512Mi \
  --timeout 60
```

**3. Note the service URL:**

```
Service URL: https://telos-backend-xxxxx-el.a.run.app
```

### Verify Deployment

```bash
curl https://telos-backend-ae7k4avtpq-el.a.run.app/health
```

### View Logs

```bash
gcloud run services logs tail telos-backend --region asia-south1
```

## Building Desktop Apps

### Windows Executable

```bash
cd client

# Install PyInstaller
pip install pyinstaller

# Build
python build_installer.py
```

**Output:** `dist/Telos.exe` and `Telos-v0.1.0-beta-Windows.zip`

### macOS App Bundle

```bash
cd client

# Build
python build_macos.py
```

**Output:** `dist/Telos.app` and DMG installer

**macOS Notes:**
- Users need to grant Screen Recording and Accessibility permissions
- First launch: Right-click → Open (to bypass Gatekeeper)

## GitHub Actions CI/CD

Automated builds are configured in `.github/workflows/`:

**Triggers:**
- Push to `prod-monorepo` branch
- Manual workflow dispatch
- Version tags (`v*`)

**What it builds:**
- Windows `.exe` (~5-7 min)
- macOS `.app` + `.dmg` (~8-10 min)

**Access builds:**
1. Go to Actions tab on GitHub
2. Select latest workflow run
3. Download artifacts

### Creating a Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will:
1. Build both platforms
2. Create a Release
3. Attach installers

## Credentials Management

### Secret Manager (Backend)

Gemini API key stored in Secret Manager:

```bash
# View secrets
gcloud secrets list

# Create/update secret
echo -n "YOUR_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

### Firebase Credentials

Local credentials stored in `docs/firebase-credentials.txt` (gitignored).

**Never commit:**
- `.env` files
- `firebase-credentials.txt`
- Service account JSON files
- API keys

## Git Workflow

| Branch | Purpose | Deploy |
|--------|---------|--------|
| `main-monorepo` | Development | Manual testing |
| `prod-monorepo` | Production | Auto-deploy |

**Promoting to production:**

```bash
git checkout prod-monorepo
git cherry-pick <commit-hash>
git push origin prod-monorepo
```

## Monitoring & Costs

### Cloud Run Metrics

Go to Cloud Console → Cloud Run → telos-backend → Metrics

### Estimated Costs (Beta)

| Service | Free Tier | Estimated Use |
|---------|-----------|---------------|
| Cloud Run | 2M requests/month | ~30K/month |
| Firestore | 50K reads/day | ~5K/day |
| Secret Manager | 6 free secrets | 1 secret |
| Gemini API | 1500/day | ~60-100/day |

**Total estimated: $2-5/month** (mostly Gemini if exceeding free tier)

## Rollback

If something breaks:

```bash
# List revisions
gcloud run revisions list --service telos-backend --region asia-south1

# Rollback to previous
gcloud run services update-traffic telos-backend \
  --to-revisions PREVIOUS_REVISION=100 \
  --region asia-south1
```

## Checklist

Before deploying:

- [ ] Test locally with `npm run dev`
- [ ] Verify health endpoint works
- [ ] Check `.env` has correct values
- [ ] Confirm Secret Manager has API key
- [ ] Test with curl after deploy

