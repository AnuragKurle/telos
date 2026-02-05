# Changelog

All notable changes to this project will be documented in this file.
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

