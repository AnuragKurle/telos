"""Zen of Telos completion screen — philosophy, living art, and launch."""

import math
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Center
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text


class BreathingOrb(Widget):
    """Minimal breathing animation — concentric ripples on still water.

    Design principles:
    - Mostly negative space
    - Only '·' characters — nothing heavy
    - Rings expand outward and fade, like ripples
    - A single center point that pulses gently
    - Monochrome teal palette, no jarring color shifts
    - Feels like watching something alive breathe in silence
    """

    tick = reactive(0)

    def on_mount(self) -> None:
        self._ripples: list = [0]  # birth ticks
        self.set_interval(0.1, self._advance)

    def _advance(self) -> None:
        self.tick += 1
        # Spawn a new ripple every ~35 ticks (~3.5 seconds)
        if self.tick % 35 == 0:
            self._ripples.append(self.tick)
        # Keep only the last 4 ripples
        if len(self._ripples) > 4:
            self._ripples = self._ripples[-4:]

    def watch_tick(self, _old: int, _new: int) -> None:
        self.refresh()

    def _lerp_color(self, brightness: float) -> str:
        """Interpolate a teal color from dim to bright.

        Args:
            brightness: 0.0 (invisible) to 1.0 (full brightness)
        """
        b = max(0.0, min(1.0, brightness))
        # Base: #1a2a35 (dark)  →  Bright: #5eb5e0 (teal)
        r = int(26 + b * 68)
        g = int(42 + b * 139)
        bl = int(53 + b * 171)
        return f"#{r:02x}{g:02x}{bl:02x}"

    def render(self) -> Text:
        w = self.size.width
        h = self.size.height
        cx = w / 2.0
        cy = h / 2.0

        t = self.tick

        # Slow global breath for the center point
        breath = (math.sin(t * 0.06) + 1.0) / 2.0  # 0…1

        # Build empty grid
        chars = [[" "] * w for _ in range(h)]
        styles = [[""] * w for _ in range(h)]

        # --- Center point: a single dot that pulses ---
        ix, iy = int(cx), int(cy)
        if 0 <= iy < h and 0 <= ix < w:
            center_bright = 0.3 + breath * 0.7
            chars[iy][ix] = "·"
            styles[iy][ix] = self._lerp_color(center_bright)

        # --- Ripples: expanding rings that fade ---
        for birth in self._ripples:
            age = t - birth  # ticks since birth
            if age < 0:
                continue

            # Ring expands over time
            radius = age * 0.12  # slow expansion
            max_radius = 9.0

            if radius > max_radius:
                continue

            # Fade out as ring expands
            life = radius / max_radius  # 0…1
            brightness = 1.0 - life * life  # quadratic fade
            if brightness < 0.05:
                continue

            color = self._lerp_color(brightness)

            # Draw sparse ring: only place dots at well-spaced angles
            # Fewer dots when ring is small, more when large
            n_dots = max(6, int(radius * 4))
            for i in range(n_dots):
                angle = (2.0 * math.pi * i / n_dots)
                # Gentle wobble so ring feels organic, not mechanical
                wobble = math.sin(angle * 3 + t * 0.03) * 0.3
                r = radius + wobble

                px = cx + math.cos(angle) * r * 2.0  # *2 for aspect ratio
                py = cy + math.sin(angle) * r

                ix2 = int(round(px))
                iy2 = int(round(py))

                if 0 <= iy2 < h and 0 <= ix2 < w:
                    # Don't overwrite a brighter dot
                    if chars[iy2][ix2] == " ":
                        chars[iy2][ix2] = "·"
                        styles[iy2][ix2] = color

        # --- Assemble output ---
        result = Text()
        for y in range(h):
            line = Text()
            for x in range(w):
                ch = chars[y][x]
                if ch == " ":
                    line.append(" ")
                else:
                    line.append(ch, style=styles[y][x])
            result.append(line)
            if y < h - 1:
                result.append("\n")

        return result


class ZenCompleteScreen(Screen):
    """The Zen of Telos — final screen before tracking begins.

    Features a minimal breathing animation and philosophical copy.
    """

    BINDINGS = [
        Binding("enter", "begin", "Begin", show=True),
    ]

    CSS = """
    ZenCompleteScreen {
        align: center middle;
        background: $surface;
    }

    #zen-outer {
        width: 80;
        height: auto;
    }

    #zen-orb {
        height: 17;
        width: 100%;
        margin-bottom: 0;
    }

    #zen-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
    }

    .zen-line {
        text-align: center;
        color: $text;
        margin: 1 0;
    }

    .zen-line.emphasis {
        color: $accent;
        text-style: italic;
    }

    #begin-container {
        margin-top: 2;
        height: auto;
    }

    Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="zen-outer"):
                yield BreathingOrb(id="zen-orb")

                yield Static("The Zen of Telos", id="zen-title")

                yield Static("A great product disappears into the background.", classes="zen-line")
                yield Static("", classes="zen-line")
                yield Static("Telos will quietly observe and understand.", classes="zen-line")
                yield Static("You'll receive your daily insights by email.", classes="zen-line")
                yield Static("Visit anytime to explore, chat, or reflect.", classes="zen-line")
                yield Static("", classes="zen-line")
                yield Static("Now, go do meaningful work.", classes="zen-line emphasis")
                yield Static("We'll be here when you need us.", classes="zen-line emphasis")

                with Container(id="begin-container"):
                    yield Button("Start tracking", variant="success", id="begin-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "begin-btn":
            self.action_begin()

    def action_begin(self) -> None:
        self.dismiss(True)
