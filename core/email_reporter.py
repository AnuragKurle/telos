"""
Email Reporter

Generates and sends daily email reports with AI-powered summaries.
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
import json


class EmailReporter:
    """Handles email report generation and sending."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        recipient_email: str
    ):
        """Initialize email reporter.

        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (typically 587 for TLS)
            sender_email: Sender email address
            sender_password: Sender email password (Gmail app password)
            recipient_email: Recipient email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email

    def generate_html_email(self, summary_data: Dict[str, Any]) -> str:
        """Generate beautiful HTML email from summary data.

        Args:
            summary_data: Daily summary dictionary from database

        Returns:
            HTML string for email body
        """
        date = datetime.fromisoformat(summary_data['date']).strftime('%A, %B %d, %Y')
        productivity_score = summary_data['productivity_score']
        daily_narrative = summary_data['daily_narrative']

        # Time breakdown
        work_min = summary_data['work_seconds'] // 60
        learning_min = summary_data['learning_seconds'] // 60
        browsing_min = summary_data['browsing_seconds'] // 60
        entertainment_min = summary_data['entertainment_seconds'] // 60
        idle_min = summary_data['idle_seconds'] // 60
        total_min = work_min + learning_min + browsing_min + entertainment_min

        # Key learnings
        key_learnings = json.loads(summary_data['key_learnings_json'])
        learnings_html = ""
        if key_learnings:
            learnings_items = "".join([f"<li style='margin: 8px 0;'>{learning}</li>" for learning in key_learnings])
            learnings_html = f"""
            <div style="margin: 25px 0;">
                <h2 style="color: #2c3e50; margin-bottom: 15px;">🎓 Key Learnings</h2>
                <ul style="color: #34495e; line-height: 1.6;">
                    {learnings_items}
                </ul>
            </div>
            """

        # Focus blocks
        focus_blocks = json.loads(summary_data['focus_blocks_json'])
        focus_html = ""
        if focus_blocks:
            focus_items = ""
            for block in focus_blocks:
                start_time = datetime.fromisoformat(block['start']).strftime('%I:%M %p')
                duration = block['duration_minutes']
                task = block['task']
                category = block['category'].title()
                focus_items += f"""
                <div style="background: #f8f9fa; padding: 12px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #3498db;">
                    <strong style="color: #2c3e50;">{start_time}</strong> - {duration} minutes
                    <br>
                    <span style="color: #7f8c8d; font-size: 14px;">[{category}]</span> {task}
                </div>
                """
            focus_html = f"""
            <div style="margin: 25px 0;">
                <h2 style="color: #2c3e50; margin-bottom: 15px;">🎯 Focus Blocks</h2>
                <div style="color: #34495e;">
                    {focus_items}
                </div>
            </div>
            """

        # Productivity score color
        if productivity_score >= 75:
            score_color = "#27ae60"
            score_emoji = "🌟"
        elif productivity_score >= 50:
            score_color = "#f39c12"
            score_emoji = "⭐"
        else:
            score_color = "#e74c3c"
            score_emoji = "📊"

        # Category colors
        category_colors = {
            'work': '#3498db',
            'learning': '#9b59b6',
            'browsing': '#95a5a6',
            'entertainment': '#e67e22'
        }

        # Generate progress bars
        progress_bars = ""
        for category, minutes in [('Work', work_min), ('Learning', learning_min), 
                                   ('Browsing', browsing_min), ('Entertainment', entertainment_min)]:
            if total_min > 0:
                percentage = (minutes / total_min) * 100
            else:
                percentage = 0
            
            color = category_colors.get(category.lower(), '#95a5a6')
            
            progress_bars += f"""
            <div style="margin: 15px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #2c3e50; font-weight: 500;">{category}</span>
                    <span style="color: #7f8c8d;">{minutes}m ({percentage:.0f}%)</span>
                </div>
                <div style="background: #ecf0f1; height: 24px; border-radius: 12px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {percentage}%; transition: width 0.3s;"></div>
                </div>
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f6fa; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px;">📊 Daily Activity Report</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">{date}</p>
        </div>

        <!-- Productivity Score -->
        <div style="text-align: center; padding: 30px 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
            <div style="font-size: 48px; margin-bottom: 10px;">{score_emoji}</div>
            <div style="font-size: 42px; font-weight: bold; color: {score_color}; margin-bottom: 5px;">
                {productivity_score:.0f}/100
            </div>
            <div style="color: #6c757d; font-size: 16px;">Productivity Score</div>
        </div>

        <!-- Content -->
        <div style="padding: 30px;">
            <!-- Daily Narrative -->
            <div style="margin-bottom: 25px;">
                <h2 style="color: #2c3e50; margin-bottom: 15px;">📝 Daily Summary</h2>
                <p style="color: #34495e; line-height: 1.7; font-size: 15px; background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
                    {daily_narrative}
                </p>
            </div>

            <!-- Time Breakdown -->
            <div style="margin: 25px 0;">
                <h2 style="color: #2c3e50; margin-bottom: 15px;">⏱️ Time Breakdown</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #dee2e6;">
                        <span style="font-size: 32px; font-weight: bold; color: #2c3e50;">{total_min}</span>
                        <span style="color: #7f8c8d; font-size: 16px; margin-left: 5px;">minutes</span>
                        <div style="color: #6c757d; font-size: 14px; margin-top: 5px;">Total Active Time</div>
                    </div>
                    {progress_bars}
                </div>
            </div>

            {learnings_html}

            {focus_html}

            <!-- Stats Footer -->
            <div style="margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                <div style="color: #6c757d; font-size: 14px;">
                    <strong style="color: #2c3e50;">{summary_data['context_switches']}</strong> context switches
                    {' • ' if focus_blocks else ''}
                    {f"<strong style='color: #2c3e50;'>{len(focus_blocks)}</strong> deep focus blocks" if focus_blocks else ''}
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="background: #2c3e50; padding: 20px; text-align: center;">
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px;">
                Generated by Screen Time Tracker
            </p>
            <p style="color: rgba(255,255,255,0.5); margin: 5px 0 0 0; font-size: 12px;">
                AI-powered activity insights
            </p>
        </div>
    </div>
</body>
</html>
        """

        return html

    def generate_plain_text(self, summary_data: Dict[str, Any]) -> str:
        """Generate plain text version of email.

        Args:
            summary_data: Daily summary dictionary from database

        Returns:
            Plain text string for email body
        """
        date = datetime.fromisoformat(summary_data['date']).strftime('%A, %B %d, %Y')
        productivity_score = summary_data['productivity_score']
        daily_narrative = summary_data['daily_narrative']

        # Time breakdown
        work_min = summary_data['work_seconds'] // 60
        learning_min = summary_data['learning_seconds'] // 60
        browsing_min = summary_data['browsing_seconds'] // 60
        entertainment_min = summary_data['entertainment_seconds'] // 60
        total_min = work_min + learning_min + browsing_min + entertainment_min

        # Key learnings
        key_learnings = json.loads(summary_data['key_learnings_json'])
        learnings_text = ""
        if key_learnings:
            learnings_text = "\n\nKEY LEARNINGS:\n"
            for i, learning in enumerate(key_learnings, 1):
                learnings_text += f"  {i}. {learning}\n"

        # Focus blocks
        focus_blocks = json.loads(summary_data['focus_blocks_json'])
        focus_text = ""
        if focus_blocks:
            focus_text = "\n\nFOCUS BLOCKS:\n"
            for block in focus_blocks:
                start_time = datetime.fromisoformat(block['start']).strftime('%I:%M %p')
                duration = block['duration_minutes']
                task = block['task']
                category = block['category'].title()
                focus_text += f"  • {start_time} - {duration}min [{category}] {task}\n"

        text = f"""
DAILY ACTIVITY REPORT
{date}

PRODUCTIVITY SCORE: {productivity_score:.0f}/100

DAILY SUMMARY:
{daily_narrative}

TIME BREAKDOWN:
  Total Active Time: {total_min} minutes
  
  Work:          {work_min}m ({work_min*100//total_min if total_min > 0 else 0}%)
  Learning:      {learning_min}m ({learning_min*100//total_min if total_min > 0 else 0}%)
  Browsing:      {browsing_min}m ({browsing_min*100//total_min if total_min > 0 else 0}%)
  Entertainment: {entertainment_min}m ({entertainment_min*100//total_min if total_min > 0 else 0}%)
{learnings_text}
{focus_text}

STATS:
  Context Switches: {summary_data['context_switches']}
  Deep Focus Blocks: {len(focus_blocks)}

---
Generated by Screen Time Tracker
AI-powered activity insights
        """

        return text.strip()

    def send_daily_report(
        self,
        summary_data: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """Send daily report email with retry logic.

        Args:
            summary_data: Daily summary dictionary from database
            max_retries: Maximum number of retry attempts

        Returns:
            True if email sent successfully, False otherwise
        """
        date = datetime.fromisoformat(summary_data['date']).strftime('%B %d, %Y')
        subject = f"Daily Activity Report - {date}"

        # Generate email content
        html_content = self.generate_html_email(summary_data)
        text_content = self.generate_plain_text(summary_data)

        # Create multipart message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.sender_email
        message['To'] = self.recipient_email

        # Attach both plain text and HTML versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        message.attach(text_part)
        message.attach(html_part)

        # Retry logic with exponential backoff
        for attempt in range(1, max_retries + 1):
            try:
                # Connect to SMTP server
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()  # Enable TLS encryption
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)

                print(f"✓ Email sent successfully to {self.recipient_email}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                print(f"✗ Email authentication failed: {e}")
                print("  Make sure you're using a Gmail App Password, not your regular password")
                return False  # Don't retry auth errors

            except smtplib.SMTPException as e:
                print(f"✗ SMTP error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {max_retries} attempts")
                    return False

            except Exception as e:
                print(f"✗ Unexpected error sending email (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {max_retries} attempts")
                    return False

        return False

