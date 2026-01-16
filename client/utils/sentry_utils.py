"""Sentry Error Tracking Utilities

Initializes and manages Sentry SDK for error tracking and performance monitoring.
"""

import os
import logging

# Make Sentry optional - gracefully handle if not installed
try:
    import sentry_sdk
    from sentry_sdk.integrations.threading import ThreadingIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logging.debug("sentry_sdk not installed - error tracking disabled")

_sentry_initialized = False


def initialize_sentry(dsn=None, environment=None, release=None, enable_performance=True):
    """Initialize Sentry SDK for error tracking.

    Args:
        dsn: Sentry DSN (from environment or parameter)
        environment: Environment name (production, staging, development)
        release: Release version
        enable_performance: Enable performance monitoring
    """
    global _sentry_initialized

    if _sentry_initialized:
        return

    # Check if Sentry SDK is available
    if not SENTRY_AVAILABLE:
        logging.debug("[SENTRY] sentry_sdk not installed, skipping initialization")
        return

    # Get DSN from parameter or environment
    sentry_dsn = dsn or os.environ.get('SENTRY_DSN')

    # Skip initialization if DSN not provided (local dev)
    if not sentry_dsn:
        logging.info("[SENTRY] DSN not provided, skipping initialization")
        return

    try:
        # Configure integrations
        integrations = [
            # Threading integration for background workers
            ThreadingIntegration(propagate_hub=True),
            # Logging integration
            LoggingIntegration(
                level=logging.INFO,       # Capture info and above as breadcrumbs
                event_level=logging.ERROR # Capture errors as events
            ),
        ]

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment or os.environ.get('SENTRY_ENVIRONMENT', 'development'),
            release=release or f"telos-client@{os.environ.get('TELOS_VERSION', '0.1.9')}",
            integrations=integrations,

            # Performance Monitoring
            traces_sample_rate=0.1 if environment == 'production' else 1.0,

            # Enable debugging in development
            debug=environment == 'development',

            # Before sending events, filter sensitive data
            before_send=_before_send_filter,

            # Attach stack locals (helpful for debugging)
            attach_stacktrace=True,

            # Max breadcrumbs (helps trace user actions before error)
            max_breadcrumbs=50,
        )

        _sentry_initialized = True
        logging.info("✅ Sentry initialized successfully")

    except Exception as error:
        logging.error(f"❌ Failed to initialize Sentry: {error}")


def _before_send_filter(event, hint):
    """Filter and modify events before sending to Sentry.

    Args:
        event: Sentry event dict
        hint: Additional context about the event

    Returns:
        Modified event or None to drop the event
    """
    # Don't send events in development unless explicitly enabled
    if os.environ.get('SENTRY_ENVIRONMENT') == 'development' and not os.environ.get('SENTRY_SEND_IN_DEV'):
        return None

    # Filter out sensitive data from breadcrumbs
    if 'breadcrumbs' in event:
        for breadcrumb in event['breadcrumbs']:
            # Redact API keys, tokens, passwords
            if 'message' in breadcrumb:
                message = breadcrumb['message']
                # Simple redaction (you can enhance this)
                if any(keyword in message.lower() for keyword in ['api_key', 'token', 'password', 'secret']):
                    breadcrumb['message'] = '[Filtered - contains sensitive data]'

    # Filter out specific exception types we don't want to track
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            # Don't track KeyboardInterrupt (user exits)
            if exception.get('type') == 'KeyboardInterrupt':
                return None

    return event


def capture_exception(error, context=None):
    """Manually capture an exception.

    Args:
        error: Exception to capture
        context: Additional context dict with tags, user, extra data
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    scope_data = {}

    if context:
        if 'tags' in context:
            scope_data['tags'] = context['tags']
        if 'extra' in context:
            scope_data['extra'] = context['extra']
        if 'user' in context:
            scope_data['user'] = context['user']

    sentry_sdk.capture_exception(error, **scope_data)


def capture_message(message, level='info', context=None):
    """Capture a message manually.

    Args:
        message: Message string
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context dict
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    scope_data = {}

    if context:
        if 'tags' in context:
            scope_data['tags'] = context['tags']
        if 'extra' in context:
            scope_data['extra'] = context['extra']

    sentry_sdk.capture_message(message, level=level, **scope_data)


def set_user(user_id, email=None, username=None):
    """Set user context for subsequent errors.

    Args:
        user_id: User ID
        email: User email (optional)
        username: Username (optional)
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    sentry_sdk.set_user({
        'id': user_id,
        'email': email,
        'username': username
    })


def add_breadcrumb(message, category='default', level='info', data=None):
    """Add a breadcrumb for debugging.

    Args:
        message: Breadcrumb message
        category: Category (e.g., 'auth', 'capture', 'analysis')
        level: Severity level
        data: Additional data dict
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    sentry_sdk.add_breadcrumb({
        'message': message,
        'category': category,
        'level': level,
        'data': data or {}
    })


def set_tag(key, value):
    """Set a tag for filtering events.

    Args:
        key: Tag key
        value: Tag value
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    sentry_sdk.set_tag(key, value)


def set_context(context_name, data):
    """Set context data.

    Args:
        context_name: Context name (e.g., 'device', 'os')
        data: Context data dict
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    sentry_sdk.set_context(context_name, data)


def is_initialized():
    """Check if Sentry is initialized."""
    return _sentry_initialized


def flush(timeout=2):
    """Flush pending events (useful before app exit).

    Args:
        timeout: Timeout in seconds
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized:
        return

    sentry_sdk.flush(timeout=timeout)
