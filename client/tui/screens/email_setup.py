"""Dedicated email report setup screen for onboarding."""

import time
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button, Select
from textual.binding import Binding


# Common send times with friendly labels
SEND_TIME_OPTIONS = [
    ("7:00 AM", "07:00"),
    ("8:00 AM", "08:00"),
    ("9:00 AM", "09:00"),
    ("5:00 PM", "17:00"),
    ("6:00 PM", "18:00"),
    ("7:00 PM", "19:00"),
    ("8:00 PM", "20:00"),
    ("9:00 PM", "21:00"),
    ("10:00 PM", "22:00"),
]


class EmailSetupScreen(Screen):
    """Dedicated screen for configuring the daily email briefing."""

    BINDINGS = [
        Binding("enter", "confirm", "Continue", show=True),
        Binding("escape", "skip", "Skip", show=False),
    ]

    CSS = """
    EmailSetupScreen {
        align: center middle;
    }

    #email-setup-container {
        width: 68;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 3 5;
    }

    #email-setup-icon {
        text-align: center;
        margin-bottom: 1;
    }

    #email-setup-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
    }

    #email-setup-body {
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }

    #email-setup-example {
        border: solid $panel;
        background: $panel;
        padding: 1 2;
        margin: 1 0 2 0;
        color: $text-muted;
        text-style: italic;
    }

    #email-setup-example-title {
        color: $success;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    .example-line {
        color: $text-muted;
        margin: 0;
    }

    #time-prompt {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    #email-time-select-container {
        align: center middle;
        height: auto;
        margin-bottom: 0;
    }

    #email-time-select {
        width: 30;
    }

    #email-time-hint {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    #timezone-hint {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 2;
    }

    #email-btn-container {
        height: auto;
    }

    #email-btn-container Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="email-setup-container"):
                yield Static("📧", id="email-setup-icon")
                yield Static("Your Daily Briefing", id="email-setup-title")

                yield Static(
                    "Every evening, Telos emails you a rich visual summary\n"
                    "of your day — with charts, insights, and AI analysis.",
                    id="email-setup-body",
                )

                # Example email snippet — closer to the actual rich report
                with Container(id="email-setup-example"):
                    yield Static("📊 Your Day — Thursday, Feb 5", id="email-setup-example-title")
                    yield Static("", classes="example-line")
                    yield Static("  Active Time   6h 15m       Score  78/100", classes="example-line")
                    yield Static("  ─────────────────────────────────────────", classes="example-line")
                    yield Static("  💼 Coding       3h 12m  ████████████░░ 52%", classes="example-line")
                    yield Static("  💬 Comms          47m   ████░░░░░░░░░░ 13%", classes="example-line")
                    yield Static("  🌐 Research     1h 05m  █████░░░░░░░░░ 18%", classes="example-line")
                    yield Static("  📝 Writing        38m   ███░░░░░░░░░░░ 10%", classes="example-line")
                    yield Static("", classes="example-line")
                    yield Static("  Focus Blocks: 10am-12pm (deep coding) ⭐", classes="example-line")
                    yield Static("  AI: \"Your mornings are 2x more productive", classes="example-line")
                    yield Static("  than afternoons. Protect your 10-12 slot.\"", classes="example-line")

                yield Static("When should we send your daily summary?", id="time-prompt")

                with Container(id="email-time-select-container"):
                    yield Select(
                        [(label, value) for label, value in SEND_TIME_OPTIONS],
                        value="21:00",
                        id="email-time-select",
                        prompt="Select time",
                    )

                # Detect timezone
                try:
                    tz_name = time.tzname[0] if time.tzname else "local"
                except Exception:
                    tz_name = "local"
                yield Static(f"Times are in your local timezone ({tz_name})", id="timezone-hint")
                yield Static("You can change or turn this off anytime in Settings.", id="email-time-hint")

                with Container(id="email-btn-container"):
                    yield Button("Set it up", variant="success", id="confirm-btn")
                    yield Button("Skip for now", variant="default", id="skip-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            self.action_confirm()
        elif event.button.id == "skip-btn":
            self.action_skip()

    def action_confirm(self) -> None:
        select = self.query_one("#email-time-select", Select)
        time_value = select.value if select.value != Select.BLANK else "21:00"
        self.dismiss({"send_time": time_value, "enabled": True})

    def action_skip(self) -> None:
        self.dismiss({"send_time": "21:00", "enabled": False})
