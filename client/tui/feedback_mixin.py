"""Shared feedback submission mixin for all screens.

Eliminates duplicated feedback code across Dashboard, Timeline,
Summary, Settings, and Chat screens.
"""

import asyncio
from typing import Optional


class FeedbackMixin:
    """Mixin providing feedback modal and submission functionality.

    Any screen class that inherits this mixin gains:
    - action_show_feedback(): opens the feedback modal
    - _submit_feedback_async(): sends feedback to the backend

    The screen must have access to self.app.config and self.app.push_screen.
    """

    def get_feedback_context(self) -> dict:
        """Override in subclass to provide screen-specific context.

        Returns:
            Dict with feedback context (type, screen, etc.)
        """
        screen_name = self.__class__.__name__.replace('Screen', '').lower()
        return {
            'type': 'general',
            'screen': screen_name,
        }

    def action_show_feedback(self) -> None:
        """Show the feedback modal with screen-specific context."""
        from tui.screens.feedback_modal import FeedbackModal

        try:
            config = self.app.config
            backend_enabled = config.get('backend', 'enabled', default=False)
            context = self.get_feedback_context()

            def handle_feedback(result: Optional[str]) -> None:
                if not result or not result.strip():
                    return
                if not backend_enabled:
                    self.app.notify(
                        "Feedback collected but backend not configured.",
                        severity="warning",
                        timeout=5,
                    )
                    return
                self.run_worker(self._submit_feedback_async(result.strip(), context))

            self.app.push_screen(FeedbackModal(context), handle_feedback)
        except Exception as e:
            self.app.notify(
                f"Error opening feedback modal: {str(e)}",
                severity="error",
                timeout=5,
            )

    async def _submit_feedback_async(self, feedback_text: str, context: dict) -> None:
        """Submit feedback to the backend asynchronously."""
        from core.backend_client import BackendClient, BackendError, AuthenticationError

        try:
            config = self.app.config
            backend_url = config.get('backend', 'url')
            firebase_api_key = config.get('firebase', 'api_key')

            backend_client = BackendClient(
                backend_url=backend_url,
                firebase_api_key=firebase_api_key,
            )

            metadata = {
                'screen': context.get('screen', 'unknown'),
                'app_version': '0.2.1',
            }

            response = await asyncio.to_thread(
                backend_client.submit_feedback,
                feedback_type=context.get('type', 'general'),
                feedback_text=feedback_text,
                context=context,
                metadata=metadata,
            )

            if response.get('slack_notified', True):
                self.app.notify(
                    "Feedback submitted successfully!",
                    severity="information",
                    timeout=3,
                )
            else:
                self.app.notify(
                    "Feedback saved but Slack notification failed.",
                    severity="warning",
                    timeout=5,
                )
        except (BackendError, AuthenticationError) as e:
            self.app.notify(
                f"Failed to submit feedback: {str(e)}",
                severity="error",
                timeout=5,
            )
        except Exception as e:
            self.app.notify(
                f"Unexpected error: {str(e)}",
                severity="error",
                timeout=5,
            )
