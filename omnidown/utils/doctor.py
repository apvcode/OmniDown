import sys
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from omnidown import __version__
from omnidown.utils.config import config, CONFIG_FILE, BIN_DIR
from omnidown.utils.ffmpeg import FFmpegLocator
from omnidown.utils.ytdlp_bin import YtDlpEngine

console = Console()

def run_doctor_diagnostics():
    """Runs a complete system health check for OmniDown."""
    console.print(f"[bold cyan]🩺 Running OmniDown v{__version__} Diagnostics...[/bold cyan]\n")

    table = Table(title="System & Dependency Status", border_style="cyan")
    table.add_column("Component", style="bold white")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="dim")

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({sys.platform})"
    table.add_row("Python", "[green]✔ OK[/green]", py_ver)

    # 2. yt-dlp Engine
    ytdlp_cmd = YtDlpEngine.get_executable_command()
    ytdlp_ver = YtDlpEngine.get_version()
    ytdlp_loc = " ".join(ytdlp_cmd)
    if ytdlp_ver != "Unknown":
        table.add_row("yt-dlp Engine", "[green]✔ OK[/green]", f"v{ytdlp_ver} ({ytdlp_loc})")
    else:
        table.add_row("yt-dlp Engine", "[red]❌ Error[/red]", "Executable not working")

    # 3. FFmpeg & FFprobe
    ff_ver, probe_ver = FFmpegLocator.get_version()
    ff_path = FFmpegLocator.get_ffmpeg_path()
    probe_path = FFmpegLocator.get_ffprobe_path()

    if ff_path:
        table.add_row("FFmpeg", "[green]✔ OK[/green]", f"{ff_ver or 'Found'} ({ff_path})")
    else:
        table.add_row("FFmpeg", "[red]❌ Missing[/red]", "Install or run with imageio-ffmpeg")

    if probe_path:
        table.add_row("FFprobe", "[green]✔ OK[/green]", f"{probe_ver or 'Found'} ({probe_path})")
    else:
        table.add_row("FFprobe", "[yellow]⚠️ Missing[/yellow]", "Muxing separate 1080p+ streams may require ffprobe")

    # 4. Config & Paths
    table.add_row("Config File", "[green]✔ OK[/green]", str(CONFIG_FILE))
    table.add_row("Managed Bin Dir", "[green]✔ OK[/green]", str(BIN_DIR))
    table.add_row("Default Download Dir", "[green]✔ OK[/green]", str(config.get("download_dir")))

    # 5. Network Connectivity (Non-fatal, with timeout, parallelized)
    import concurrent.futures

    sites = [
        ("VK (vk.com)", "https://vk.com"),
        ("Rutube", "https://rutube.ru"),
        ("YouTube", "https://www.youtube.com"),
        ("TikTok", "https://www.tiktok.com")
    ]

    def check_site(site_info):
        site_name, url = site_info
        try:
            res = requests.get(url, timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code < 500:
                return (site_name, "[green]✔ Reachable[/green]", f"HTTP {res.status_code}")
            else:
                return (site_name, "[yellow]⚠️ Warning[/yellow]", f"HTTP {res.status_code}")
        except Exception:
            return (site_name, "[yellow]⚠️ Offline/Blocked[/yellow]", "Timeout or no connection")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sites)) as executor:
        results = list(executor.map(check_site, sites))

    for site_name, status_str, detail in results:
        table.add_row(f"Network: {site_name}", status_str, detail)

    console.print(table)
    console.print()

    # Recommendations
    recs = []
    if not probe_path:
        recs.append("• [yellow]FFprobe is missing:[/yellow] Installing full FFmpeg (with ffprobe) enables best-quality stream muxing.")
    if sys.platform == "win32":
        recs.append("• [cyan]Windows Cookie Note:[/cyan] Chrome 127+ uses App-Bound encryption. For private video downloads, [bold]Firefox[/bold] is recommended.")

    if recs:
        console.print(Panel("\n".join(recs), title="💡 Recommendations", border_style="yellow"))
    else:
        console.print(Panel("[bold green]All systems operational and ready to download![/bold green]", border_style="green"))
