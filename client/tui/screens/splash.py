"""Splash / loading screen shown while the main app initializes.

Displays rotating tips and a subtle animation so the user
knows the app is alive during the startup gap.
"""

import math
import random
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Center
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text


# Tips shown during loading — rotates every few seconds
TIPS = [
    "Press [bold]A[/bold] anytime to chat with your work history",
    "Press [bold]S[/bold] to see your daily summary with AI insights",
    "Press [bold]T[/bold] to browse your detailed activity timeline",
    "Your daily email briefing arrives every evening",
    "Press [bold]V[/bold] on the dashboard to switch graph views",
    "All your data stays local — only on your machine",
    "Press [bold]H[/bold] for all keyboard shortcuts",
    "Ask the AI anything — \"What did I work on yesterday?\"",
    "Telos learns your patterns to give better insights over time",
    "Press [bold]F[/bold] from any screen to send feedback",
]


class SplashScreen(Screen):
    """Loading screen with rotating tips while the app boots."""

    tick = reactive(0)
    tip_index = reactive(0)

    CSS = """
    SplashScreen {
        align: center middle;
        background: $surface;
    }

    #splash-outer {
        width: 64;
        height: auto;
        padding: 1 2;
    }

    #splash-logo {
        text-align: center;
        color: #50b4a0;
        text-style: bold;
        margin-bottom: 0;
    }

    #splash-tagline {
        text-align: center;
        color: #345c54;
        margin-bottom: 2;
    }

    #splash-bar {
        text-align: center;
        color: #50b4a0;
        height: 1;
        margin-bottom: 1;
    }

    #splash-status {
        text-align: center;
        color: $text-muted;
        margin-bottom: 3;
    }

    #splash-divider {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #splash-tip {
        text-align: center;
        color: $text;
        margin-bottom: 0;
    }
    """

    def compose(self) -> ComposeResult:
        # Pick a random starting tip
        self.tip_index = random.randint(0, len(TIPS) - 1)
        with Center():
            with Vertical(id="splash-outer"):
                yield Static("TELOS", id="splash-logo")
                yield Static("understand your screen time", id="splash-tagline")
                yield Static("", id="splash-bar")
                yield Static("Preparing your dashboard...", id="splash-status")
                yield Static("─" * 36, id="splash-divider")
                yield Static("", id="splash-tip")

    def on_mount(self) -> None:
        self.set_interval(0.15, self._tick)
        self.set_interval(3.0, self._rotate_tip)
        # Set first tip
        self._update_tip(self.tip_index)

    def _tick(self) -> None:
        self.tick += 1

    def _rotate_tip(self) -> None:
        self.tip_index = (self.tip_index + 1) % len(TIPS)

    def watch_tick(self, _old: int, _new: int) -> None:
        t = self.tick
        # Smooth loading bar animation
        bar_width = 36
        # A wave that sweeps back and forth
        progress = (math.sin(t * 0.08) + 1.0) / 2.0  # 0..1
        filled = int(progress * bar_width)

        result = Text()
        # Pre-computed colors: #50b4a0 blended toward #1e1e1e background
        #   100% = #50b4a0, 70% = #417d72, 30% = #2f4540, dim = #2a2a3a
        for i in range(bar_width):
            dist = abs(i - filled)
            if dist == 0:
                result.append("━", style="#50b4a0")
            elif dist <= 2:
                result.append("─", style="#417d72")
            elif dist <= 5:
                result.append("─", style="#2f4540")
            else:
                result.append("─", style="#2a2a3a")

        try:
            self.query_one("#splash-bar", Static).update(result)
        except Exception:
            pass

    def _update_tip(self, idx: int) -> None:
        try:
            self.query_one("#splash-tip", Static).update(
                f"💡  {TIPS[idx]}"
            )
        except Exception:
            pass

    def watch_tip_index(self, _old: int, new: int) -> None:
        self._update_tip(new)
