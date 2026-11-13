"""Terminal animations for OmniDown, built on Rich Live.

All functions degrade gracefully: if the output is not an interactive TTY
(or OMNIDOWN_NO_ANIM is set) they print the static version instead.
"""
import os
import sys
import time
from typing import Optional

from rich.live import Live
from rich.text import Text
from rich.panel import Panel

__all__ = [
    "supports_animation",
    "animated_banner",
    "animated_panel",
    "result_panel",
    "stream_sweep",
    "typewriter",
]

# Border styles cycled through during pulse/sweep animations.
_PULSE_STYLES = ["cyan", "bright_cyan", "bold white", "bright_cyan"]
_SUCCESS_STYLES = ["bold green", "green", "bright_green", "green"]
_ERROR_STYLES = ["bold red", "red", "bright_red", "red"]
_LOGO_STYLES = ["bold cyan", "cyan", "bright_cyan"]


def supports_animation(console) -> bool:
    """True if the terminal can render inline animation.

    Set OMNIDOWN_NO_ANIM=1 to disable all animations (piped output, scripts,
    exotic terminals where cursor tricks misbehave).
    """
    if os.environ.get("OMNIDOWN_NO_ANIM"):
        return False
    try:
        return bool(console.is_terminal) and sys.stdout.isatty()
    except Exception:
        return False


def animated_banner(console, logo: str, cycles: int = 2, frame_delay: float = 0.045) -> None:
    """Reveal the ASCII logo line by line, shimmer over it, then settle.

    `logo` may contain Rich markup; it is split into lines and each line is
    tinted so a light band travels across the sign.
    """
    lines = logo.splitlines()
    if not lines:
        return

    if not supports_animation(console):
        console.print(logo)
        return

    total = len(lines)

    def render(revealed: int, band: int) -> Text:
        grid = Text()
        for i, line in enumerate(lines):
            if i:
                grid.append("\n")
            if i >= revealed:
                continue
            if i == band:
                grid.append(line, style="bold white")
            else:
                grid.append(line, style=_LOGO_STYLES[i % len(_LOGO_STYLES)])
        return grid

    try:
        with Live(console=console, transient=True, refresh_per_second=30) as live:
            # Phase 1: lines appear one by one.
            for revealed in range(1, total + 1):
                live.update(render(revealed, -1))
                time.sleep(frame_delay)
            # Phase 2: a highlight band sweeps down a few times.
            for _ in range(cycles):
                for band in range(total):
                    live.update(render(total, band))
                    time.sleep(frame_delay * 0.7)
    except Exception:
        pass
    # Settle on the final static logo.
    console.print(logo)


def animated_panel(
    console,
    content: str,
    title: Optional[str] = None,
    kind: str = "info",
    cycles: int = 2,
    frame_delay: float = 0.05,
) -> None:
    """Print a panel whose border pulses with color before settling.

    kind: "info" (cyan), "success" (green), "error" (red).
    `content` and `title` may contain Rich markup.
    """
    styles = {
        "info": _PULSE_STYLES,
        "success": _SUCCESS_STYLES,
        "error": _ERROR_STYLES,
    }.get(kind, _PULSE_STYLES)
    settle_style = styles[0]

    def make(frame: int) -> Panel:
        if frame < 0:
            style = settle_style
        else:
            style = styles[frame % len(styles)]
        return Panel.fit(content, title=title, border_style=style)

    if not supports_animation(console):
        console.print(make(-1))
        return

    try:
        with Live(console=console, transient=True, refresh_per_second=30) as live:
            for f in range(cycles * len(styles)):
                live.update(make(f))
                time.sleep(frame_delay)
    except Exception:
        pass
    console.print(make(-1))


def typewriter(console, text: str, delay: float = 0.008) -> None:
    """Type plain text out character by character (markup not supported)."""
    if not supports_animation(console):
        console.print(text)
        return
    try:
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write("\n")
    except Exception:
        console.print(text)


def result_panel(console, kind: str, content: str, title: Optional[str] = None) -> None:
    """Animated result panel: success = green pulse, error = red pulse."""
    animated_panel(console, content, title=title, kind=kind, cycles=2)


def stream_sweep(console, width: int = 40, delay: float = 0.03) -> None:
    """A short horizontal bar fill used as a transition before downloads."""
    if not supports_animation(console):
        return
    try:
        with Live(console=console, transient=True, refresh_per_second=30) as live:
            bar = Text()
            for i in range(width + 1):
                filled = "━" * i
                rest = "─" * (width - i)
                bar = Text(f"[{filled}{rest}]", style="bold cyan")
                live.update(bar)
                time.sleep(delay)
    except Exception:
        pass
