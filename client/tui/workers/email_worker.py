"""
Email Worker

Background worker for scheduled email reports in TUI mode.
"""

import asyncio
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.database import Database
    from core.daily_aggregator import DailyAggregator
    from core.email_reporter import EmailReporter


class EmailWorker:
    """Background worker for scheduled email sending."""

    def __init__(
        self,
        db: 'Database',
        daily_aggregator: 'DailyAggregator',
        email_reporter: 'EmailReporter',
        send_time: str
    ):
        """Initialize email worker.

        Args:
            db: Database instance
            daily_aggregator: Daily aggregator instance
            email_reporter: Email reporter instance
            send_time: Time to send email (HH:MM format, e.g., "21:00")
        """
        self.db = db
        self.daily_aggregator = daily_aggregator
        self.email_reporter = email_reporter
        self.send_time = send_time
        self.last_email_date: Optional[str] = None
        self.running = False

    async def start(self):
        """Start email worker loop."""
        self.running = True

        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                current_time = now.strftime('%H:%M')
                current_date = now.strftime('%Y-%m-%d')

                # Check if it's time to send
                if current_time != self.send_time:
                    continue

                # Check if already sent today
                if self.last_email_date == current_date:
                    continue

                # Generate and send report
                await self._send_daily_report(now)

                # Mark as sent
                self.last_email_date = current_date

            except Exception as e:
                # Log error but don't crash worker
                print(f"[Email Worker] Error: {e}")

    async def _send_daily_report(self, date: datetime):
        """Generate and send daily report.

        Args:
            date: Date to generate report for
        """
        try:
            # Get or generate summary
            summary = await asyncio.to_thread(
                self.db.get_daily_summary,
                date
            )

            if not summary:
                # Generate new summary
                summary_id = await asyncio.to_thread(
                    self.daily_aggregator.generate_daily_summary,
                    date
                )

                if summary_id:
                    await asyncio.to_thread(self.db.increment_api_usage)
                    summary = await asyncio.to_thread(
                        self.db.get_daily_summary,
                        date
                    )
                else:
                    print("[Email Worker] Failed to generate summary (no data?)")
                    return

            # Send email
            success = await asyncio.to_thread(
                self.email_reporter.send_daily_report,
                summary
            )

            if success:
                print(f"[Email Worker] ✓ Daily report sent for {date.strftime('%Y-%m-%d')}")
            else:
                print(f"[Email Worker] ✗ Failed to send daily report")

        except Exception as e:
            print(f"[Email Worker] Error sending report: {e}")

    def stop(self):
        """Stop email worker."""
        self.running = False

