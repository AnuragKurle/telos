"""Email Settings Modal - Configure daily email reports."""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Static, Button, Select, Switch
from textual.containers import Vertical, Horizontal
from typing import Callable, Optional
import asyncio

from core.backend_client import BackendClient, BackendError, AuthenticationError


class EmailSettingsModal(ModalScreen[bool]):
    """Modal screen for editing email report settings."""

    DEFAULT_CSS = """
    EmailSettingsModal {
        align: center middle;
    }

    #email-dialog {
        width: 70;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #email-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #action-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #action-buttons Button {
        margin: 0 1;
    }

    .setting-row {
        height: auto;
        padding: 1 0;
    }

    .setting-label {
        color: $text;
        padding: 0 1;
    }

    .setting-description {
        color: $text-muted;
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, config, on_save: Callable = None):
        """Initialize email settings modal.

        Args:
            config: Configuration manager instance
            on_save: Optional callback when settings are saved
        """
        super().__init__()
        self.config = config
        self.on_save = on_save

        # Load current email settings
        self.current_enabled = config.get('email', 'enabled', default=True)
        self.current_time = config.get('email', 'send_time', default='21:00')
        self.current_timezone = config.get('email', 'timezone', default='Asia/Kolkata')

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Common send time options
        time_options = [
            ("07:00 - 7:00 AM", "07:00"),
            ("08:00 - 8:00 AM", "08:00"),
            ("09:00 - 9:00 AM", "09:00"),
            ("10:00 - 10:00 AM", "10:00"),
            ("18:00 - 6:00 PM", "18:00"),
            ("19:00 - 7:00 PM", "19:00"),
            ("20:00 - 8:00 PM", "20:00"),
            ("21:00 - 9:00 PM", "21:00"),
            ("22:00 - 10:00 PM", "22:00"),
        ]

        # Timezone options (common ones)
        timezone_options = [
            ("Asia/Kolkata (IST)", "Asia/Kolkata"),
            ("America/New_York (EST)", "America/New_York"),
            ("America/Los_Angeles (PST)", "America/Los_Angeles"),
            ("Europe/London (GMT)", "Europe/London"),
            ("Europe/Paris (CET)", "Europe/Paris"),
            ("Asia/Tokyo (JST)", "Asia/Tokyo"),
            ("Australia/Sydney (AEDT)", "Australia/Sydney"),
            ("UTC", "UTC"),
        ]

        with Vertical(id="email-dialog"):
            yield Static("📧 Email Report Settings", classes="dialog-title")
            yield Static("")

            # Enable/Disable toggle
            yield Static("Daily Email Reports:", classes="setting-label")
            yield Static(
                "Receive a daily summary of your activity via email",
                classes="setting-description"
            )
            yield Switch(value=self.current_enabled, id="email-enabled")
            yield Static("")

            # Send time select
            yield Static("Report Time:", classes="setting-label")
            yield Static(
                "What time would you like to receive your daily report?",
                classes="setting-description"
            )
            yield Select(
                options=time_options,
                value=self.current_time,
                id="send-time-select"
            )
            yield Static("")

            # Timezone select
            yield Static("Timezone:", classes="setting-label")
            yield Static(
                "Select your timezone for accurate delivery",
                classes="setting-description"
            )
            yield Select(
                options=timezone_options,
                value=self.current_timezone,
                id="timezone-select"
            )
            yield Static("")

            # Action buttons
            yield Static("Manual Actions:", classes="setting-label")
            yield Static(
                "Force sync data or send a test email now",
                classes="setting-description"
            )
            with Horizontal(id="action-buttons"):
                yield Button("Sync Data Now", variant="success", id="sync-button")
                yield Button("Send Test Email", variant="warning", id="test-email-button")

            yield Static("")

            # Buttons
            with Horizontal(id="email-buttons"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "save-button":
            self._save_settings()
        elif event.button.id == "cancel-button":
            self.dismiss(False)
        elif event.button.id == "sync-button":
            self._trigger_sync()
        elif event.button.id == "test-email-button":
            self._trigger_test_email()

    def _trigger_sync(self) -> None:
        """Trigger a manual Firestore sync."""
        self.app.notify("Syncing data to server...", severity="information", timeout=2)
        self.run_worker(self._do_sync_async(), exclusive=True)

    async def _do_sync_async(self) -> None:
        """Perform the sync operation."""
        try:
            # Try to get the firestore_sync instance from the app
            if hasattr(self.app, 'firestore_sync') and self.app.firestore_sync:
                success = await self.app.firestore_sync.force_sync()
                if success:
                    self.app.notify("✓ Data sync complete!", severity="information", timeout=3)
                else:
                    self.app.notify("⚠️ Sync completed with some errors", severity="warning", timeout=5)
            else:
                self.app.notify("⚠️ Firestore sync not available", severity="warning", timeout=3)
        except Exception as e:
            self.app.notify(f"✗ Sync failed: {str(e)}", severity="error", timeout=5)

    def _trigger_test_email(self) -> None:
        """Trigger a test email send."""
        self.app.notify("Triggering test email...", severity="information", timeout=2)
        self.run_worker(self._do_test_email_async(), exclusive=True)

    async def _do_test_email_async(self) -> None:
        """Send a test email via the backend."""
        try:
            backend_url = self.config.get('backend', 'url', default="")
            firebase_api_key = self.config.get('firebase', 'api_key', default="")

            if not backend_url or not firebase_api_key:
                self.app.notify("⚠️ Backend not configured", severity="warning", timeout=3)
                return

            backend_client = BackendClient(backend_url, firebase_api_key)

            # First, sync data to make sure it's available
            if hasattr(self.app, 'firestore_sync') and self.app.firestore_sync:
                self.app.notify("Syncing data first...", severity="information", timeout=2)
                await self.app.firestore_sync.force_sync()

            # Then trigger the email
            result = await asyncio.to_thread(backend_client.force_trigger_email)

            if result.get('success'):
                self.app.notify(
                    "✓ Email sent! Check your inbox (and spam folder)",
                    severity="information",
                    timeout=5
                )
            else:
                self.app.notify(
                    f"⚠️ Email trigger completed but may not have sent",
                    severity="warning",
                    timeout=5
                )

        except (BackendError, AuthenticationError) as e:
            self.app.notify(f"✗ Failed to send email: {str(e)}", severity="error", timeout=5)
        except Exception as e:
            self.app.notify(f"✗ Error: {str(e)}", severity="error", timeout=5)

    def _save_settings(self) -> None:
        """Save email settings to config and sync with backend."""
        try:
            # Get values from widgets
            enabled = self.query_one("#email-enabled", Switch).value
            send_time = self.query_one("#send-time-select", Select).value
            timezone = self.query_one("#timezone-select", Select).value

            # Save to local config
            self.config.set('email', 'enabled', enabled)
            self.config.set('email', 'send_time', send_time)
            self.config.set('email', 'timezone', timezone)

            # Sync with backend asynchronously
            self.run_worker(
                self._sync_to_backend_async(enabled, send_time, timezone),
                exclusive=True
            )

            # Call on_save callback if provided
            if self.on_save:
                self.on_save()

            self.app.notify(
                "✓ Email settings saved!",
                severity="information",
                timeout=3
            )

            self.dismiss(True)

        except Exception as e:
            self.app.notify(
                f"Failed to save settings: {str(e)}",
                severity="error",
                timeout=5
            )

    async def _sync_to_backend_async(
        self,
        enabled: bool,
        send_time: str,
        timezone: str
    ) -> None:
        """Sync email preferences to backend."""
        try:
            backend_url = self.config.get('backend', 'url', default="")
            firebase_api_key = self.config.get('firebase', 'api_key', default="")

            if not backend_url or not firebase_api_key:
                # Backend not configured, skip sync
                return

            backend_client = BackendClient(backend_url, firebase_api_key)

            # Extract hour from send_time (format: "HH:MM")
            preferred_hour = int(send_time.split(':')[0])

            preferences = {
                'enabled': enabled,
                'sendTime': send_time,
                'timezone': timezone,
                'frequency': 'daily',
                'preferredHour': preferred_hour
            }

            # Call backend API to update preferences
            await asyncio.to_thread(
                backend_client.update_email_preferences,
                preferences
            )

            self.app.notify(
                "✓ Synced with server",
                severity="information",
                timeout=2
            )

        except (BackendError, AuthenticationError) as e:
            self.app.notify(
                f"⚠️ Saved locally but failed to sync: {str(e)}",
                severity="warning",
                timeout=5
            )
        except Exception as e:
            self.app.notify(
                f"⚠️ Sync error: {str(e)}",
                severity="warning",
                timeout=5
            )
