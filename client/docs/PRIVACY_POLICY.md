# Telos Privacy Policy

**Last Updated: January 2, 2026**

## Our Commitment to Privacy

Telos is built with privacy as a core principle, not an afterthought. We believe your data is yours, and yours alone.

## What Data We Collect

### Screenshots (Temporary)
- **Captured**: Every 30 seconds when you're active
- **Analyzed**: By AI to understand your activity
- **Deleted**: Within 5 seconds of capture
- **Never stored**: Screenshots are never saved to disk or sent to any server

### Analysis Metadata (Local)
- **What**: Category, app name, task description, confidence scores
- **Where**: Stored locally in SQLite database on your device
- **Access**: Only you can access this data
- **Control**: You can export or delete anytime

### Backend Communication (Optional)
If you enable backend integration:
- **Sent**: Only analysis metadata (no images)
- **Purpose**: To use our AI analysis service
- **Storage**: Metadata temporarily processed, not permanently stored
- **Authentication**: Anonymous Firebase tokens (no personal info required)

## What We DON'T Collect

- ❌ Screenshots (deleted immediately)
- ❌ Personal information (unless you provide email for reports)
- ❌ Browsing history (only app names and categories)
- ❌ Telemetry or analytics
- ❌ Crash reports (unless you opt-in)
- ❌ Usage statistics

## How We Use Your Data

### Local Processing
- Analyze your work patterns
- Build intelligent sessions
- Generate daily summaries
- Power AI chat queries

### Backend Processing (Optional)
- Provide AI analysis without requiring your own API key
- Keep proprietary prompts secure
- Enable future cloud features

## Your Rights

You have complete control over your data:

1. **Export**: Export all data in CSV/JSON format anytime
2. **Delete**: Delete all data with one command
3. **Disable**: Turn off tracking anytime
4. **Opt-out**: Use local-only mode (no backend)

## Email Reports (Optional)

If you enable email reports:
- **What we need**: Your Gmail address and app password
- **Stored where**: Locally in your config file
- **Used for**: Sending daily summaries via Gmail SMTP
- **Never shared**: Your credentials stay on your device

## Data Security

### Local Storage
- SQLite database stored in `~/.telos/`
- Only accessible by you (OS-level permissions)
- No encryption by default (it's on your device)

### Network Communication
- HTTPS only for all backend communication
- Firebase authentication tokens (short-lived)
- No sensitive data in transit

## Third-Party Services

### Google Gemini API
- **Purpose**: AI-powered screenshot analysis
- **Data sent**: Screenshots (immediately deleted) or analysis requests
- **Privacy policy**: https://ai.google.dev/terms

### Firebase (Optional)
- **Purpose**: Authentication for backend access
- **Data sent**: Anonymous authentication tokens
- **Privacy policy**: https://firebase.google.com/support/privacy

### Gmail SMTP (Optional)
- **Purpose**: Sending email reports
- **Data sent**: Daily summary emails
- **Privacy policy**: https://policies.google.com/privacy

## Children's Privacy

Telos is not intended for users under 13 years old. We do not knowingly collect data from children.

## Changes to This Policy

We may update this policy occasionally. Changes will be noted in:
- This document (with updated date)
- Release notes
- In-app notification (for major changes)

## Open Source

Telos is open source. You can:
- Review the code: github.com/your-repo/telos
- Verify our privacy claims
- Contribute improvements
- Fork and self-host

## Contact

Questions about privacy?
- Email: privacy@telos.app
- GitHub: github.com/your-repo/telos/issues
- Discord: discord.gg/telos

## Your Trust Matters

We built Telos because we wanted a productivity tool that respects privacy. If we ever violate these principles, we've failed our mission.

---

**TL;DR**: Screenshots deleted in 5 seconds. Data stays local. No tracking. You're in control.

