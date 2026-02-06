# Changelog

All notable changes to this project will be documented in this file.
## [0.2.2] - 2026-02-06

### Fixed
- Fix Portkey ByteString crash on non-ASCII window titles (screenshot analysis 500 errors)

### Changed
- Migrate all sensitive keys to Google Cloud Secret Manager
- Switch Dodo Payments to live mode for real payment processing
- Enable Slack monitoring alerts for errors and slow requests

### Added
- Splash screen with animated branding
- Getting started guide for new users
- Sample preview screen showing tracking in action
- Email setup screen for report configuration
- Centralized theme system for consistent styling
- Feedback mixin for user feedback collection

### Improved
- Dashboard, summary, timeline, settings, and chat screens polished
- Welcome carousel and onboarding flow refined
- Trial manager with better expiry handling
- Website pricing component and Firebase functions

## [0.2.1] - 2026-02-06

Added MCP server for Claude Desktop and Cursor integration. 7 new tools for AI assistants to query activity data.


## [0.2.0] - 2026-02-06

Beta launch polish: $3/month pricing, AES-256 encryption for all stored data, anonymous user IDs, professional onboarding UX with clear trial messaging, improved email service with proper timezone handling

### Breaking Changes
- User documents migrated from email-based to UID-based identifiers in Firestore

### Added
- AES-256-GCM encryption for all sensitive data stored in Firestore
- Professional email template with unsubscribe links and privacy information
- 7-day free trial messaging throughout onboarding flow
- Encryption and anonymity information in privacy notices

### Changed
- Pricing updated from $9/month to $3/month (removed yearly tier)
- Setup mode renamed from "SaaS/Local" to "Just get it running/Bring your own API key"
- Email service now uses luxon for proper DST-aware timezone handling
- Privacy notices now accurately describe data handling (screenshots analyzed and discarded, data encrypted)
- User documents now keyed by Firebase UID instead of email for anonymity

### Improved
- Email onboarding explains reports are enabled by default
- Zen complete screen shows trial pricing and encryption information
- Privacy policy on website updated with honest transparency about data handling

