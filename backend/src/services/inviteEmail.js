/**
 * Invite Email Service
 * 
 * Handles sending invitation, reminder, and referral nudge emails
 * to waitlist users during the beta launch.
 */

import sgMail from '@sendgrid/mail';
import { initializeSendGrid } from './email.js';

/**
 * Generate invitation email HTML
 * Dark-themed, matching the Telos brand.
 * 
 * Positioning: understand where your time goes. Positive, aspirational framing.
 * Not "you forgot your day" but "now you can see it clearly."
 */
function generateInvitationHTML(email) {
  return `
<!DOCTYPE html>
<html lang="en" style="background-color: #0a0a0a; background: #0a0a0a;">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark only">
    <meta name="supported-color-schemes" content="dark only">
    <title>Your Telos access is ready</title>
    <style>
        :root { color-scheme: dark only; supported-color-schemes: dark only; }
        body, html { background-color: #0a0a0a !important; }
        .dark-bg { background-color: #0a0a0a !important; }
        u + .body { background-color: #0a0a0a !important; }
        @media (prefers-color-scheme: dark) {
            body, html, .dark-bg { background-color: #0a0a0a !important; }
        }
    </style>
</head>
<body class="body dark-bg" style="margin: 0; padding: 0; background-color: #0a0a0a; background: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; -webkit-text-size-adjust: none;" bgcolor="#0a0a0a">
    <div class="dark-bg" style="background-color: #0a0a0a; background: #0a0a0a; width: 100%; table-layout: fixed; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0a0a0a; background: #0a0a0a;" bgcolor="#0a0a0a" class="dark-bg">
        <tr>
            <td align="center" style="padding: 20px 10px;" bgcolor="#0a0a0a">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; background-color: #0a0a0a;" bgcolor="#0a0a0a">

                    <!-- Header -->
                    <tr>
                        <td style="padding: 24px 24px 12px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 20px; font-weight: 700; color: #22c55e;">telos</p>
                        </td>
                    </tr>

                    <!-- ─── Opening ─── -->
                    <tr>
                        <td style="padding: 12px 24px 24px;" bgcolor="#0a0a0a">
                            <h1 style="margin: 0 0 20px 0; font-size: 26px; font-weight: 700; color: #ededed; line-height: 1.35;">
                                Your access is ready.
                            </h1>
                            <p style="margin: 0 0 14px 0; font-size: 15px; color: #d4d4d4; line-height: 1.7;">
                                You signed up for Telos, and we're ready for you.
                            </p>
                            <p style="margin: 0 0 14px 0; font-size: 15px; color: #d4d4d4; line-height: 1.7;">
                                <strong style="color: #ededed;">Telos maps your screen time, automatically.</strong> It runs quietly in the background, uses AI to understand what you're working on, and turns your day into a clear, searchable timeline. No manual logging. No browser extensions. Just clarity about where your hours actually go.
                            </p>
                            <p style="margin: 0; font-size: 15px; color: #d4d4d4; line-height: 1.7;">
                                Your screenshots are analyzed in real-time and immediately deleted&nbsp;&mdash;&nbsp;only the insights stay, encrypted and anonymous.
                            </p>
                        </td>
                    </tr>

                    <!-- ─── What it gives you ─── -->
                    <tr>
                        <td style="padding: 0 24px 24px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 20px;" bgcolor="#111111">
                                        <p style="margin: 0 0 14px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">What you'll see</p>
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #d4d4d4; line-height: 1.65;">
                                            <strong style="color: #ededed;">Your real patterns</strong>&nbsp;&mdash;&nbsp;how much time is deep work vs. meetings vs. browsing, broken down by app and activity, every single day.
                                        </p>
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #d4d4d4; line-height: 1.65;">
                                            <strong style="color: #ededed;">Where your time drifts</strong>&nbsp;&mdash;&nbsp;the context switches you didn't notice, the rabbit holes, the apps that quietly ate an hour.
                                        </p>
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #d4d4d4; line-height: 1.65;">
                                            <strong style="color: #ededed;">Answers on demand</strong>&nbsp;&mdash;&nbsp;ask things like <em style="color: #a3a3a3;">"How much time did I spend coding today?"</em> or <em style="color: #a3a3a3;">"What happened between 2 and 4pm?"</em> in plain English.
                                        </p>
                                        <p style="margin: 0; font-size: 14px; color: #d4d4d4; line-height: 1.65;">
                                            <strong style="color: #ededed;">A daily summary in your inbox</strong>&nbsp;&mdash;&nbsp;a productivity report every morning with time breakdowns, focus scores, and personalized insights.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ─── Install ─── -->
                    <tr>
                        <td style="padding: 0 24px 6px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">Get started</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 24px 8px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 20px;" bgcolor="#111111">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 12px 16px; background-color: #1a1a1a; border-radius: 6px; font-family: monospace; font-size: 14px; color: #22c55e;" bgcolor="#1a1a1a">
                                                    $ pip install telos-tracker<br/>
                                                    $ telos setup
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="margin: 12px 0 0 0; font-size: 13px; color: #a3a3a3; line-height: 1.5;">
                                            That's it. Works on <strong style="color: #d4d4d4;">Windows</strong> and <strong style="color: #d4d4d4;">macOS</strong>.
                                        </p>
                                        <p style="margin: 6px 0 0 0; font-size: 12px; color: #737373; line-height: 1.5;">
                                            Don't have Python or pip? <a href="https://www.python.org/downloads/" style="color: #22c55e; text-decoration: underline;">Install Python</a> (pip is included). Or use <span style="font-family: monospace; color: #a3a3a3;">pipx install telos-tracker</span> if you prefer.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ─── 14 Days of Pro ─── -->
                    <tr>
                        <td style="padding: 16px 24px 6px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">Your early access perk</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 24px 8px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px; border-left: 3px solid #22c55e;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 20px;" bgcolor="#111111">
                                        <p style="margin: 0 0 10px 0; font-size: 15px; font-weight: 600; color: #ededed; line-height: 1.4;">
                                            14 days of Telos Pro, on us.
                                        </p>
                                        <p style="margin: 0 0 14px 0; font-size: 13px; color: #d4d4d4; line-height: 1.6;">
                                            Because you signed up early, you get the full Pro experience&nbsp;&mdash;&nbsp;no credit card needed:
                                        </p>
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 12px 16px; background-color: #1a1a1a; border-radius: 8px;" bgcolor="#1a1a1a">
                                                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #d4d4d4;">&#10003;&nbsp; AI-powered activity tracking &amp; timeline</p>
                                                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #d4d4d4;">&#10003;&nbsp; Ask questions about your day in plain English</p>
                                                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #d4d4d4;">&#10003;&nbsp; Daily email reports delivered to your inbox</p>
                                                    <p style="margin: 0 0 5px 0; font-size: 13px; color: #d4d4d4;">&#10003;&nbsp; Data export (CSV &amp; JSON)</p>
                                                    <p style="margin: 0; font-size: 13px; color: #d4d4d4;">&#10003;&nbsp; Unlimited history retention</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ─── Pricing honesty + BYOK ─── -->
                    <tr>
                        <td style="padding: 16px 24px 6px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase; letter-spacing: 0.1em;">A note about pricing</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 24px 8px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 20px;" bgcolor="#111111">
                                        <p style="margin: 0 0 12px 0; font-size: 14px; color: #d4d4d4; line-height: 1.65;">
                                            Every screen analysis is an AI call that costs money to run&nbsp;&mdash;&nbsp;on top of servers, encryption, and storage. To keep building Telos, Pro is <strong style="color: #ededed;">$3/month</strong> after your 14 days.
                                        </p>
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #1a1a1a; border-radius: 8px; border-left: 3px solid #a855f7;" bgcolor="#1a1a1a">
                                            <tr>
                                                <td style="padding: 16px;" bgcolor="#1a1a1a">
                                                    <p style="margin: 0 0 6px 0; font-size: 13px; font-weight: 600; color: #a855f7;">
                                                        But you don't have to pay at all.
                                                    </p>
                                                    <p style="margin: 0 0 10px 0; font-size: 13px; color: #d4d4d4; line-height: 1.6;">
                                                        Bring your own Gemini API key (free from Google) and Telos runs entirely on your machine, forever. All the core features&nbsp;&mdash;&nbsp;tracking, AI chat, timeline, summaries&nbsp;&mdash;&nbsp;stay free. The only thing you'll miss is the daily email reports, which need our cloud.
                                                    </p>
                                                    <p style="margin: 0; font-size: 12px; color: #737373;">
                                                        Get your free Gemini key&nbsp;&rarr;&nbsp;<a href="https://aistudio.google.com/app/apikey" style="color: #a855f7; text-decoration: underline;">aistudio.google.com</a>
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        <p style="margin: 12px 0 0 0; font-size: 13px; color: #737373; line-height: 1.6;">
                                            After 14&nbsp;days: keep Pro for $3/mo, switch to the free BYOK mode, or just stop. No card on file, no pressure.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ─── Referral tease ─── -->
                    <tr>
                        <td style="padding: 16px 24px 8px;" bgcolor="#0a0a0a">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px; border-left: 3px solid #f59e0b;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 16px 20px;" bgcolor="#111111">
                                        <p style="margin: 0; font-size: 13px; color: #d4d4d4; line-height: 1.6;">
                                            <strong style="color: #f59e0b;">Want Pro without paying?</strong>&nbsp;&nbsp;Once you're set up, you'll find a referral link in Settings. Share it with friends&nbsp;&mdash;&nbsp;every friend who signs up gets you <strong style="color: #ededed;">1 month of Pro free</strong> (up to 12 months).
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ─── Footer ─── -->
                    <tr>
                        <td style="padding: 28px 24px 16px; border-top: 1px solid #1a1a1a; text-align: center;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 13px; color: #525252;">
                                <span style="color: #22c55e; font-weight: 600;">telos</span> &middot; know where your time goes
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #404040; line-height: 1.8;">
                                You're receiving this because you signed up at telos.dev.
                                <br/>
                                <a href="mailto:support@telos.dev?subject=Unsubscribe%20from%20invitations" style="color: #525252; text-decoration: underline;">Unsubscribe</a>
                                &middot;
                                <a href="https://telos.dev/privacy" style="color: #525252; text-decoration: underline;">Privacy Policy</a>
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
    </div>
</body>
</html>`;
}

/**
 * Generate reminder email HTML for invited but not activated users
 */
function generateReminderHTML(email, activeUserCount = 0) {
  return `
<!DOCTYPE html>
<html lang="en" style="background-color: #0a0a0a; background: #0a0a0a;">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark only">
    <meta name="supported-color-schemes" content="dark only">
    <title>Still want to try Telos?</title>
    <style>
        :root { color-scheme: dark only; supported-color-schemes: dark only; }
        body, html { background-color: #0a0a0a !important; }
        .dark-bg { background-color: #0a0a0a !important; }
        u + .body { background-color: #0a0a0a !important; }
    </style>
</head>
<body class="body dark-bg" style="margin: 0; padding: 0; background-color: #0a0a0a; background: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; -webkit-text-size-adjust: none;" bgcolor="#0a0a0a">
    <div class="dark-bg" style="background-color: #0a0a0a; background: #0a0a0a; width: 100%; table-layout: fixed;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0a0a0a; background: #0a0a0a;" bgcolor="#0a0a0a" class="dark-bg">
        <tr>
            <td align="center" style="padding: 20px 10px;" bgcolor="#0a0a0a">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px;" bgcolor="#0a0a0a">
                    <tr>
                        <td style="padding: 20px 16px 10px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 20px; font-weight: 700; color: #22c55e;">telos</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px 20px;" bgcolor="#0a0a0a">
                            <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 700; color: #ededed;">
                                Your invite is still waiting 👋
                            </h1>
                            <p style="margin: 0 0 16px 0; font-size: 15px; color: #d4d4d4; line-height: 1.6;">
                                We sent you an invite to Telos a few days ago. Just wanted to make sure it didn't get lost in your inbox.
                            </p>
                            ${activeUserCount > 0 ? `<p style="margin: 0 0 16px 0; font-size: 14px; color: #a3a3a3; line-height: 1.5;">
                                ${activeUserCount} people are already tracking their screen time with Telos.
                            </p>` : ''}
                            <p style="margin: 0 0 20px 0; font-size: 15px; color: #d4d4d4; line-height: 1.6;">
                                It takes 30 seconds to install:
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td style="padding: 12px 16px; background-color: #111111; border-radius: 6px; font-family: monospace; font-size: 14px; color: #22c55e;" bgcolor="#111111">
                                        $ pip install telos-tracker
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 16px 0 0 0; font-size: 13px; color: #737373;">
                                Your extended 14-day trial is ready and waiting.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 24px 16px; border-top: 1px solid #262626; text-align: center;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 13px; color: #525252;">
                                <span style="color: #22c55e; font-weight: 600;">telos</span>
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #404040;">
                                <a href="mailto:support@telos.dev?subject=Unsubscribe" style="color: #525252; text-decoration: underline;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    </div>
</body>
</html>`;
}

/**
 * Generate referral nudge email for active users
 */
function generateReferralNudgeHTML(email, referralCode) {
  return `
<!DOCTYPE html>
<html lang="en" style="background-color: #0a0a0a; background: #0a0a0a;">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="color-scheme" content="dark only">
    <meta name="supported-color-schemes" content="dark only">
    <title>Share Telos, Get Pro Free</title>
    <style>
        :root { color-scheme: dark only; supported-color-schemes: dark only; }
        body, html { background-color: #0a0a0a !important; }
        .dark-bg { background-color: #0a0a0a !important; }
        u + .body { background-color: #0a0a0a !important; }
    </style>
</head>
<body class="body dark-bg" style="margin: 0; padding: 0; background-color: #0a0a0a; background: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; -webkit-text-size-adjust: none;" bgcolor="#0a0a0a">
    <div class="dark-bg" style="background-color: #0a0a0a; background: #0a0a0a; width: 100%; table-layout: fixed;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #0a0a0a; background: #0a0a0a;" bgcolor="#0a0a0a" class="dark-bg">
        <tr>
            <td align="center" style="padding: 20px 10px;" bgcolor="#0a0a0a">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px;" bgcolor="#0a0a0a">
                    <tr>
                        <td style="padding: 20px 16px 10px;" bgcolor="#0a0a0a">
                            <p style="margin: 0; font-family: monospace; font-size: 20px; font-weight: 700; color: #22c55e;">telos</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 16px 20px;" bgcolor="#0a0a0a">
                            <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 700; color: #ededed;">
                                Share Telos, Get Pro Free 🎁
                            </h1>
                            <p style="margin: 0 0 16px 0; font-size: 15px; color: #d4d4d4; line-height: 1.6;">
                                Enjoying Telos? Share it with a friend and you'll both benefit:
                            </p>
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #111111; border-radius: 10px;" bgcolor="#111111">
                                <tr>
                                    <td style="padding: 20px;" bgcolor="#111111">
                                        <p style="margin: 0 0 8px 0; font-size: 14px; color: #d4d4d4;">✅ <strong style="color: #ededed;">You get</strong>: 1 month of Pro access (per friend)</p>
                                        <p style="margin: 0 0 16px 0; font-size: 14px; color: #d4d4d4;">✅ <strong style="color: #ededed;">They get</strong>: 14-day extended trial</p>
                                        <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 11px; color: #525252; text-transform: uppercase;">Your Referral Link</p>
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 12px 16px; background-color: #1a1a1a; border-radius: 6px; font-family: monospace; font-size: 14px; color: #22c55e;" bgcolor="#1a1a1a">
                                                    ${(process.env.FRONTEND_URL || 'https://gen-lang-client-0772617718.web.app').replace(/\/$/, '')}/?ref=${referralCode}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 16px 0 0 0; font-size: 13px; color: #737373;">
                                You can earn up to 12 months of free Pro. Invite 3 friends and you're set for a quarter!
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 24px 16px; border-top: 1px solid #262626; text-align: center;" bgcolor="#0a0a0a">
                            <p style="margin: 0 0 8px 0; font-family: monospace; font-size: 13px; color: #525252;">
                                <span style="color: #22c55e; font-weight: 600;">telos</span>
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #404040;">
                                <a href="mailto:support@telos.dev?subject=Unsubscribe" style="color: #525252; text-decoration: underline;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    </div>
</body>
</html>`;
}

/**
 * Send an invitation email to a waitlist user
 * 
 * @param {string} recipientEmail - Email to send to
 * @returns {object} Result with success, messageId
 */
export async function sendInvitationEmail(recipientEmail) {
  await initializeSendGrid();

  const msg = {
    to: recipientEmail,
    from: {
      email: process.env.SENDGRID_FROM_EMAIL || 'hello@telos.dev',
      name: 'Telos'
    },
    replyTo: 'anuragkurle27@gmail.com',
    subject: "Where does your time actually go?",
    html: generateInvitationHTML(recipientEmail),
    text: `Your Telos access is ready.\n\nYou signed up for Telos, and we're ready for you.\n\nTelos maps your screen time, automatically. It runs quietly in the background, uses AI to understand what you're working on, and turns your day into a clear, searchable timeline. No manual logging. No browser extensions. Just clarity about where your hours actually go.\n\nScreenshots are analyzed in real-time and immediately deleted — only the insights stay.\n\nWHAT YOU'LL SEE\n- Your real patterns — deep work vs. meetings vs. browsing, by app and activity\n- Where your time drifts — context switches, rabbit holes, apps that quietly ate an hour\n- Answers on demand — "How much time did I spend coding today?" in plain English\n- A daily summary in your inbox — time breakdowns, focus scores, and insights\n\nGET STARTED\n  $ pip install telos-tracker\n  $ telos setup\n\nThat's it. Windows and macOS.\nDon't have Python? https://www.python.org/downloads/\n\n14 DAYS OF PRO, ON US\nBecause you signed up early, you get the full Pro experience — no credit card needed.\n- AI-powered activity tracking & timeline\n- Ask questions about your day in plain English\n- Daily email reports in your inbox\n- Data export (CSV & JSON)\n- Unlimited history retention\n\nABOUT PRICING\nEvery screen analysis is an AI call that costs money — servers, encryption, storage. Pro is $3/month after your 14 days.\n\nBut you don't have to pay. Bring your own Gemini API key (free from Google) and Telos runs entirely on your machine, forever. Get your key: https://aistudio.google.com/app/apikey\n\nAfter 14 days: keep Pro for $3/mo, switch to free BYOK, or stop. No card on file.\n\nWANT PRO WITHOUT PAYING?\nFind your referral link in Settings. Every friend who signs up = 1 month of Pro free (up to 12).\n\n— Telos\nhttps://telos.dev`,
  };

  try {
    const result = await sgMail.send(msg);
    const messageId = result?.[0]?.headers?.['x-message-id'] || null;
    console.log(`[INVITE-EMAIL] Invitation sent to ${recipientEmail} (messageId: ${messageId})`);
    return { success: true, messageId };
  } catch (error) {
    console.error(`[INVITE-EMAIL] Failed to send invitation to ${recipientEmail}:`, error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send a reminder email to an invited but not activated user
 * 
 * @param {string} recipientEmail
 * @param {number} activeUserCount - For social proof
 */
export async function sendReminderEmail(recipientEmail, activeUserCount = 0) {
  await initializeSendGrid();

  const msg = {
    to: recipientEmail,
    from: {
      email: process.env.SENDGRID_FROM_EMAIL || 'hello@telos.dev',
      name: 'Telos'
    },
    replyTo: 'anuragkurle27@gmail.com',
    subject: 'Your Telos invite is still waiting 👋',
    html: generateReminderHTML(recipientEmail, activeUserCount),
    text: `Your Telos invite is still waiting!\n\nInstall: pip install telos-tracker\n\nYour 14-day trial is ready.\n\n— Telos`,
  };

  try {
    const result = await sgMail.send(msg);
    const messageId = result?.[0]?.headers?.['x-message-id'] || null;
    console.log(`[INVITE-EMAIL] Reminder sent to ${recipientEmail}`);
    return { success: true, messageId };
  } catch (error) {
    console.error(`[INVITE-EMAIL] Failed to send reminder to ${recipientEmail}:`, error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Send a referral nudge email to an active user
 * 
 * @param {string} recipientEmail
 * @param {string} referralCode
 */
export async function sendReferralNudgeEmail(recipientEmail, referralCode) {
  await initializeSendGrid();

  const msg = {
    to: recipientEmail,
    from: {
      email: process.env.SENDGRID_FROM_EMAIL || 'hello@telos.dev',
      name: 'Telos'
    },
    replyTo: 'anuragkurle27@gmail.com',
    subject: 'Share Telos, get Pro free 🎁',
    html: generateReferralNudgeHTML(recipientEmail, referralCode),
    text: `Share Telos with friends and get 1 month of Pro for each signup!\n\nYour referral link: ${(process.env.FRONTEND_URL || 'https://gen-lang-client-0772617718.web.app').replace(/\/$/, '')}/?ref=${referralCode}\n\n— Telos`,
  };

  try {
    const result = await sgMail.send(msg);
    console.log(`[INVITE-EMAIL] Referral nudge sent to ${recipientEmail}`);
    return { success: true };
  } catch (error) {
    console.error(`[INVITE-EMAIL] Failed to send referral nudge to ${recipientEmail}:`, error.message);
    return { success: false, error: error.message };
  }
}

export {
  generateInvitationHTML,
  generateReminderHTML,
  generateReferralNudgeHTML,
};
