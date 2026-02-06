"""Help screen with collapsible sections, keyboard shortcuts, and documentation."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Collapsible
from textual.binding import Binding


class HelpScreen(Screen):
    """Help and documentation screen with collapsible sections."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Back", show=True),
        Binding("q", "dismiss_screen", "Back", show=False),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 92;
        max-height: 44;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        padding-bottom: 1;
    }

    #help-content {
        height: 1fr;
        margin-bottom: 1;
    }

    Collapsible {
        margin: 0;
        padding: 0;
        background: $surface;
    }

    CollapsibleTitle {
        color: $success;
        text-style: bold;
        padding: 1 1;
    }

    .help-block {
        padding: 0 2 1 2;
    }

    .help-text {
        color: $text;
        margin: 0;
    }

    .help-muted {
        color: $text-muted;
        margin: 0;
    }

    .help-key {
        color: $accent;
        text-style: bold;
    }

    .help-heading {
        color: $warning;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    .help-tip {
        color: $success;
        margin-top: 1;
    }

    #button-container {
        height: auto;
        padding-top: 1;
    }

    #close-btn {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical(id="help-container"):
            yield Static("Help & Documentation", id="help-title")

            with ScrollableContainer(id="help-content"):

                # ── Quick Start ──────────────────────────────────
                with Collapsible(title="Quick Start", collapsed=False):
                    with Container(classes="help-block"):
                        yield Static(
                            "Telos runs in the background, captures your screen every\n"
                            "30 seconds, and uses AI to understand what you're doing.\n"
                            "Screenshots are [bold]deleted immediately[/bold] after analysis.\n"
                            "\n"
                            "Your first data appears within 1-2 minutes. Just keep\n"
                            "working normally. Use the screens below to explore:",
                            classes="help-text",
                        )
                        yield Static(
                            "\n"
                            "  [bold cyan]D[/]  Dashboard    — live overview of your day\n"
                            "  [bold cyan]T[/]  Timeline     — detailed activity feed\n"
                            "  [bold cyan]S[/]  Summary      — daily insights and stats\n"
                            "  [bold cyan]A[/]  AI Chat      — ask questions about your work\n"
                            "  [bold cyan]C[/]  Settings     — preferences and account",
                            classes="help-text",
                        )

                # ── All Keyboard Shortcuts ────────────────────────
                with Collapsible(title="Keyboard Shortcuts"):
                    with Container(classes="help-block"):
                        yield Static("[bold]Navigation[/bold]", classes="help-heading")
                        yield Static(
                            "  [bold cyan]D[/]  Dashboard         [bold cyan]T[/]  Timeline\n"
                            "  [bold cyan]S[/]  Summary           [bold cyan]A[/]  AI Chat\n"
                            "  [bold cyan]C[/]  Settings          [bold cyan]H[/]  Help (this screen)\n"
                            "  [bold cyan]Q[/]  Quit Telos",
                            classes="help-text",
                        )
                        yield Static("[bold]Actions[/bold]", classes="help-heading")
                        yield Static(
                            "  [bold cyan]F[/]  Submit feedback   [bold cyan]G[/]  Edit analysis goals\n"
                            "  [bold cyan]E[/]  Email settings    [bold cyan]R[/]  Get referral link\n"
                            "  [bold cyan]U[/]  Upgrade to Pro",
                            classes="help-text",
                        )
                        yield Static("[bold]Within Screens[/bold]", classes="help-heading")
                        yield Static(
                            "  [bold cyan]ESC[/]    Go back / close modal\n"
                            "  [bold cyan]Enter[/]  Confirm / submit\n"
                            "  [bold cyan]Tab[/]    Move between fields\n"
                            "  [bold cyan]↑ / ↓[/]  Scroll content",
                            classes="help-text",
                        )

                # ── AI Chat Tips ──────────────────────────────────
                with Collapsible(title="AI Chat — How to Use"):
                    with Container(classes="help-block"):
                        yield Static(
                            "Press [bold cyan]A[/] to open the AI Chat. Ask questions\n"
                            "about your work in plain English:\n"
                            "\n"
                            '  [italic]"What did I do this morning?"[/]\n'
                            '  [italic]"How much time did I spend coding today?"[/]\n'
                            '  [italic]"What apps did I use the most?"[/]\n'
                            '  [italic]"When was my most productive hour?"[/]\n'
                            '  [italic]"Summarize my work this week"[/]\n'
                            "\n"
                            "The AI can see your full activity history stored\n"
                            "locally — captures, sessions, and daily summaries.",
                            classes="help-text",
                        )
                        yield Static(
                            "Tip: Be specific with time ranges for better answers.",
                            classes="help-tip",
                        )

                # ── Email Reports ─────────────────────────────────
                with Collapsible(title="Email Reports — Setup"):
                    with Container(classes="help-block"):
                        yield Static(
                            "Get a daily email summary of your screen time.\n"
                            "\n"
                            "[bold]Cloud mode[/bold] (recommended):\n"
                            "  Press [bold cyan]E[/] in Settings to enable email reports.\n"
                            "  Choose your send time and timezone — that's it.\n"
                            "  Reports are generated and sent by our backend.\n"
                            "\n"
                            "[bold]If emails aren't arriving:[/bold]\n"
                            "  1. Check your spam / junk folder\n"
                            "  2. Ensure email is enabled in Settings → Email\n"
                            "  3. Make sure you've been active (Telos needs data)\n"
                            "  4. Reports are sent at your preferred hour (UTC-aware)",
                            classes="help-text",
                        )

                # ── MCP / AI Integration ──────────────────────────
                with Collapsible(title="AI Tools Integration (MCP)"):
                    with Container(classes="help-block"):
                        yield Static(
                            "Telos includes an MCP server so AI assistants\n"
                            "(Claude, Cursor, etc.) can query your work history.\n"
                            "\n"
                            "[bold]Setup:[/bold]\n"
                            "  1. Open your AI tool's MCP configuration\n"
                            "  2. Add this entry:\n"
                            '     [bold cyan]"telos"[/]: {\n'
                            '       "command": "python",\n'
                            '       "args": ["<path>/mcp_server.py"]\n'
                            "     }\n"
                            "  3. Restart the AI tool — Telos tools appear\n"
                            "\n"
                            "  The exact path is shown in [bold cyan]Settings[/bold cyan].\n"
                            "\n"
                            "[bold]7 available tools:[/bold]\n"
                            "  get_activity_today     — today's time breakdown\n"
                            "  get_sessions           — work sessions for a date\n"
                            "  get_daily_summary      — AI-generated daily report\n"
                            "  query_activity         — natural language queries\n"
                            "  get_recent_captures    — latest screen analyses\n"
                            "  get_productivity_trends — multi-day trends\n"
                            "  get_top_apps           — most-used applications",
                            classes="help-text",
                        )

                # ── Troubleshooting ───────────────────────────────
                with Collapsible(title="Troubleshooting"):
                    with Container(classes="help-block"):
                        yield Static("[bold]No captures appearing?[/bold]", classes="help-heading")
                        yield Static(
                            "  • Check the status banner at the top of the Dashboard\n"
                            "  • Make sure you're not idle — move mouse or type\n"
                            "  • First data takes 1-2 minutes to appear\n"
                            "  • If stuck, press [bold cyan]Q[/] and relaunch Telos",
                            classes="help-text",
                        )
                        yield Static("[bold]Backend connection issues?[/bold]", classes="help-heading")
                        yield Static(
                            "  • Check internet connectivity\n"
                            "  • Telos falls back to local analysis automatically\n"
                            "  • A yellow banner shows when in fallback mode",
                            classes="help-text",
                        )
                        yield Static("[bold]Trial expired?[/bold]", classes="help-heading")
                        yield Static(
                            "  • Press [bold cyan]U[/] to upgrade to Pro ($3/month)\n"
                            "  • Or press [bold cyan]R[/] to get a referral link —\n"
                            "    each friend who signs up = 1 month of Pro free\n"
                            "  • Or switch to Local mode (bring your own API key)",
                            classes="help-text",
                        )
                        yield Static("[bold]High API usage?[/bold]", classes="help-heading")
                        yield Static(
                            "  • Adjust capture interval in Settings\n"
                            "  • Default: 30s interval, ~2800 captures/day\n"
                            "  • Reducing to 60s halves your API usage",
                            classes="help-text",
                        )

                # ── Support ───────────────────────────────────────
                with Collapsible(title="Support & Feedback"):
                    with Container(classes="help-block"):
                        yield Static(
                            "[bold]Submit feedback from anywhere:[/bold]\n"
                            "  Press [bold cyan]F[/] on any screen to report issues,\n"
                            "  suggest features, or flag AI errors.\n"
                            "\n"
                            "[bold]Contact:[/bold]\n"
                            "  Email: anuragkurle27@gmail.com\n"
                            "  Website: https://gen-lang-client-0772617718.web.app\n"
                            "\n"
                            "[bold]Version:[/bold] 0.2.1-beta",
                            classes="help-text",
                        )

            with Container(id="button-container"):
                yield Button("Close", variant="primary", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.action_dismiss_screen()

    def action_dismiss_screen(self) -> None:
        """Dismiss the screen."""
        self.dismiss()
