"""
Live Platform Smoke Test Script.
Validates extraction of live video streams across major video platforms.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.table import Table
from omnidown.core.inspector import VideoInspector

console = Console()

TEST_URLS = [
    ("YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("VK Video", "https://vk.com/video-220754053_456241088"),
]

def run_platform_checks():
    console.print("[bold cyan]🔍 Running Live Platform Extraction Tests...[/bold cyan]\n")
    table = Table(title="Platform Live Validation Results", border_style="cyan")
    table.add_column("Platform", style="bold white")
    table.add_column("Status", style="yellow")
    table.add_column("Title / Details", style="dim")
    table.add_column("Qualities Found", style="magenta")

    for platform_name, url in TEST_URLS:
        try:
            meta = VideoInspector.inspect(url)
            qualities_cnt = len(meta.quality_options)
            table.add_row(
                platform_name,
                "[green]✔ Success[/green]",
                meta.title[:40],
                f"{qualities_cnt} streams"
            )
        except Exception as e:
            table.add_row(
                platform_name,
                "[red]❌ Failed[/red]",
                str(e)[:40],
                "-"
            )

    console.print(table)

if __name__ == "__main__":
    run_platform_checks()
