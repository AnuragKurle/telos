# Website

Next.js static site deployed to Firebase Hosting. Serves the marketing pages and admin dashboard.

## What It Does

**Public pages:**
- Landing page with features, pricing, how-it-works
- Privacy policy
- MCP server documentation
- Waitlist signup (writes to Firestore)

**Admin dashboard (`/admin`):**
- Overview stats (signups, active users, trials)
- Waitlist management
- User management
- Email campaign management (batch invitations)
- Referral tracking

**Firebase Functions:**
- `notifySlackOnWaitlist` -- Slack notification when someone joins the waitlist
- `notifyOnNewUser` -- Slack notification when a Firebase Auth user is created

## Project Structure

```
website/
├── app/
│   ├── page.tsx               # Landing page
│   ├── layout.tsx             # Root layout
│   ├── globals.css            # Tailwind theme
│   ├── privacy/page.tsx       # Privacy policy
│   ├── mcp/page.tsx           # MCP documentation
│   └── admin/
│       ├── layout.tsx         # Admin layout with auth
│       ├── page.tsx           # Admin dashboard
│       ├── waitlist/page.tsx  # Waitlist management
│       ├── users/page.tsx     # User management
│       ├── campaigns/page.tsx # Email campaigns
│       └── referrals/page.tsx # Referral tracking
├── components/
│   ├── Hero.tsx               # Hero section with email signup
│   ├── Features.tsx           # Features section
│   ├── HowItWorks.tsx         # How it works section
│   ├── Pricing.tsx            # Pricing section
│   ├── WaitlistCTA.tsx        # Waitlist call-to-action
│   ├── Vision.tsx             # Vision section
│   ├── FeatureCard.tsx        # Feature card component
│   ├── TerminalFrame.tsx      # Terminal frame component
│   └── TypewriterEffect.tsx   # Typewriter animation
├── functions/
│   ├── index.js               # Firebase Cloud Functions
│   ├── slack-app-manifest.json
│   └── package.json
├── firebase.json              # Firebase hosting + functions config
├── firestore.rules            # Firestore security rules
├── env.example                # Environment variable template
├── next.config.ts
├── tsconfig.json
└── package.json
```

## Local Development

```bash
cp env.example .env.local      # Edit with your Firebase config
npm install
npm run dev                    # http://localhost:3000
```

## Deploy

```bash
npm run build
npx firebase deploy --only hosting

# Deploy functions separately
cd functions && npm install
npx firebase deploy --only functions
```

## Environment Variables

Create `.env.local` from `env.example`:

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Web API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase project ID |
| `NEXT_PUBLIC_BACKEND_URL` | Backend Cloud Run URL |
