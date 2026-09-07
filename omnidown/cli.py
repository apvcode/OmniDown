import sys
import os
import time
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

from omnidown import __version__, __author__, __github__
from omnidown.utils.config import config
from omnidown.core.inspector import VideoInspector
from omnidown.core.downloader import download_with_rich_progress, VideoDownloader
from omnidown.core.trimmer import MediaTrimmer
from omnidown.core.compressor import VideoCompressor, probe_video_file
from omnidown.utils.doctor import run_doctor_diagnostics
from omnidown.utils.updater import EngineUpdater
from omnidown.utils.cookies import CookieManager
from omnidown.utils.ytdlp_bin import ProgressInfo

LOGO = """[bold cyan]
  ██████╗ ███╗   ███╗███╗   ██╗██╗██████╗  ██████╗ ██╗    ██╗███╗   ██╗
 ██╔═══██╗████╗ ████║████╗  ██║██║██╔══██╗██╔═══██╗██║    ██║████╗  ██║
 ██║   ██║██╔████╔██║██╔██╗ ██║██║██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║
 ██║   ██║██║╚██╔╝██║██║╚██╗██║██║██║  ██║██║   ██║██║███╗██║██║╚██╗██║
 ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║
  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝[/bold cyan]"""

app = typer.Typer(
    help="🎬 OmniDown - Industrial-grade multi-platform video downloader and media processor.",
    no_args_is_help=False
)
console = Console()

def get_default_download_dir() -> str:
    return str(config.get("download_dir") or (Path.home() / "Downloads"))

def ask_download_directory() -> str:
    default_path = get_default_download_dir()
    use_default = inquirer.confirm(
        message=f"Save to default folder? ({default_path})",
        default=True
    ).execute()
    
    if use_default:
        return default_path
    else:
        return inquirer.filepath(
            message="Enter download directory:",
            default=os.getcwd(),
            validate=PathValidator(is_dir=True, message="Must be a valid directory"),
            only_directories=True,
        ).execute()

# -----------------------------------------------------------------------------
# DIRECT CLI COMMANDS
# -----------------------------------------------------------------------------

@app.command("inspect")
def inspect_cli(
    url: str = typer.Argument(..., help="Video or playlist URL to inspect"),
    proxy: Optional[str] = typer.Option(None, "--proxy", "-p", help="Proxy URL"),
    browser: Optional[str] = typer.Option(None, "--browser", "-b", help="Browser to load cookies from (e.g. firefox, chrome)")
):
    """Inspect video streams, available resolutions, codecs, and sizes without downloading."""
    with Status("[cyan]Analyzing video streams...", spinner="dots", console=console):
        try:
            meta = VideoInspector.inspect(url, proxy=proxy, cookies_browser=browser)
        except Exception as e:
            console.print(f"[bold red]❌ Inspection Error:[/bold red] {e}")
            raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold white]{meta.title}[/bold white]\n"
        f"👤 [bold]Channel/Uploader:[/bold] [green]{meta.uploader}[/green]\n"
        f"⏱️ [bold]Duration:[/bold] [yellow]{meta.formatted_duration}[/yellow]\n"
        f"🌐 [bold]Platform:[/bold] [cyan]{meta.platform}[/cyan]"
        + (f" 📑 ([bold magenta]{meta.playlist_count} videos in playlist[/bold magenta])" if meta.is_playlist else ""),
        title=f"🎬 {meta.platform} Stream Info",
        border_style="cyan"
    ))

    if meta.quality_options:
        table = Table(title="Available Video Qualities", border_style="green")
        table.add_column("#", style="dim")
        table.add_column("Resolution / Label", style="bold white")
        table.add_column("FPS", style="yellow")
        table.add_column("Codec", style="magenta")
        table.add_column("Est. Size", style="cyan")
        table.add_column("Type", style="green")

        for idx, opt in enumerate(meta.quality_options, 1):
            fps_str = str(opt.fps) if opt.fps else "-"
            size_mb = opt.formatted_size
            stream_type = "Progressive (AV)" if opt.is_progressive else "Adaptive Stream"
            table.add_row(str(idx), opt.label, fps_str, opt.vcodec.upper(), size_mb, stream_type)

        console.print(table)
    else:
        console.print("[yellow]ℹ️ Stream qualities will be negotiated dynamically at download time.[/yellow]")


def choose_quality_and_download(url: str, output_dir: Optional[str] = None):
    """Interactively inspects video streams and lets the user pick quality with estimated file size."""
    url = url.strip()
    if not url:
        return

    with Status("[cyan]Analyzing video streams and calculating file sizes...", spinner="dots", console=console):
        try:
            meta = VideoInspector.inspect(url, cookies_browser=config.get("browser_cookies"))
        except Exception as e:
            console.print(f"[bold red]❌ Inspection Error:[/bold red] {e}")
            return

    console.print(Panel.fit(
        f"[bold white]{meta.title}[/bold white]\n"
        f"👤 [bold]Channel/Author:[/bold] [green]{meta.uploader}[/green]   "
        f"⏱️ [bold]Duration:[/bold] [yellow]{meta.formatted_duration}[/yellow]   "
        f"🌐 [bold]Platform:[/bold] [cyan]{meta.platform}[/cyan]",
        title=f"🎬 {meta.platform} Video Info",
        border_style="cyan"
    ))

    if not meta.quality_options:
        console.print("[yellow]ℹ️ No fixed stream list found. Downloading in best available quality.[/yellow]")
        selected_quality = "best"
        custom_spec = None
        is_audio = False
    else:
        best_sz = f" ({meta.quality_options[0].formatted_size})" if meta.quality_options[0].filesize_approx else ""
        choices = [f"✨ Best Available Quality{best_sz}"]
        for opt in meta.quality_options:
            stream_tag = " [AV Combined]" if opt.is_progressive else ""
            choices.append(f"🎬 {opt.label} [{opt.vcodec.upper()}]{stream_tag} ({opt.formatted_size})")

        choices.append("🎵 Audio Only (MP3 320k)")
        choices.append("⬅️ Back / Cancel")

        selected_choice = inquirer.select(
            message="Select video quality to download:",
            choices=choices,
            pointer="> "
        ).execute()

        if selected_choice == "⬅️ Back / Cancel":
            return

        if selected_choice.startswith("🎵 Audio Only"):
            selected_quality = "mp3"
            custom_spec = None
            is_audio = True
        elif selected_choice.startswith("✨ Best Available"):
            selected_quality = "best"
            custom_spec = None
            is_audio = False
        else:
            idx = choices.index(selected_choice) - 1
            selected_opt = meta.quality_options[idx]
            selected_quality = f"{selected_opt.height}p"
            custom_spec = selected_opt.format_spec
            is_audio = False

    out_dir = output_dir or ask_download_directory()

    console.print(f"\n[cyan]🚀 Downloading video in [{selected_quality.upper()}] quality...[/cyan]")
    res = download_with_rich_progress(
        url=url,
        output_dir=out_dir,
        quality=selected_quality,
        custom_format_spec=custom_spec,
        audio_only=is_audio,
        audio_format="mp3"
    )

    if res.success:
        title_str = f"🎵 [bold white]{res.title or meta.title}[/bold white]\n" if (res.title or meta.title) else ""
        file_str = f"📁 [yellow]{res.file_path}[/yellow]" if res.file_path else f"📁 Saved to folder: [yellow]{out_dir}[/yellow]"
        console.print(Panel.fit(
            f"[bold green]✅ Download Completed Successfully![/bold green]\n"
            f"{title_str}{file_str}",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ Download Failed[/bold red]\n{res.error_message}",
            border_style="red"
        ))


@app.command("download")
def download_cli(
    url: str = typer.Argument(..., help="Video URL to download"),
    quality: str = typer.Option("best", "--quality", "-q", help="Target quality: best, 4k, 1080p, 720p, 480p, 360p"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Target output folder"),
    audio_only: bool = typer.Option(False, "--audio-only", "-a", help="Extract audio only"),
    audio_format: str = typer.Option("mp3", "--audio-format", help="Audio codec: mp3, m4a, flac, opus"),
    choose_quality: bool = typer.Option(False, "--choose-quality", "-c", "--interactive", "-i", help="Interactively choose video quality and show file sizes before downloading")
):
    """Download video or audio from supported platforms."""
    if choose_quality and not audio_only:
        choose_quality_and_download(url=url, output_dir=output)
        return

    out_dir = output or get_default_download_dir()
    console.print(f"[cyan]🚀 Initializing download for:[/cyan] [bold white]{url}[/bold white]")

    result = download_with_rich_progress(
        url=url,
        output_dir=out_dir,
        quality=quality,
        audio_only=audio_only,
        audio_format=audio_format
    )

    if result.success:
        title_str = f"🎵 [bold white]{result.title}[/bold white]\n" if result.title else ""
        file_str = f"📁 [yellow]{result.file_path}[/yellow]" if result.file_path else f"📁 Saved to folder: [yellow]{out_dir}[/yellow]"
        console.print(Panel.fit(
            f"[bold green]✅ Download Completed Successfully![/bold green]\n"
            f"{title_str}{file_str}",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ Download Failed[/bold red]\n{result.error_message}",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("trim")
def trim_cli(
    target: str = typer.Argument(..., help="Video URL or local file path to trim"),
    time_range: str = typer.Argument(..., help="Time range e.g. '00:30-01:45' or '00:30+15s'"),
    quality: str = typer.Option("best", "--quality", "-q", help="Target quality if URL (best, 1080p, 720p)"),
    exact: bool = typer.Option(False, "--exact", help="Frame-exact cut with re-encoding (slower, frame-accurate)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory or filepath")
):
    """Download or trim a specific segment of a video without downloading the entire file."""
    trimmer = MediaTrimmer(output_dir=output if (output and os.path.isdir(output)) else None)
    is_url = target.startswith(("http://", "https://"))

    console.print(f"[bold cyan]✂️ Starting Video Trim [{time_range}] ({'Frame-Exact' if exact else 'Fast Keyframe'})...[/bold cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bold green", finished_style="bold green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Processing segment...", total=100)

        if is_url:
            def on_progress(p: ProgressInfo):
                if p.percent is not None:
                    progress.update(task_id, completed=p.percent, total=100)

            def on_status(status_msg: str):
                progress.update(task_id, description=f"[yellow]{status_msg}[/yellow]")

            res = trimmer.trim_stream_url(
                url=target,
                time_range_str=time_range,
                quality=quality,
                exact=exact,
                progress_callback=on_progress,
                status_callback=on_status
            )
        else:
            def on_local_prog(pct: float):
                progress.update(task_id, completed=pct, total=100)

            res = trimmer.trim_local_file(
                input_path=target,
                time_range_str=time_range,
                output_path=output if (output and not os.path.isdir(output)) else None,
                exact=exact,
                progress_callback=on_local_prog
            )

    if res.success:
        dur_str = f"{res.time_range.duration_seconds:.1f}s" if res.time_range else "Clip"
        console.print(Panel.fit(
            f"[bold green]✅ Segment Trimmed Successfully![/bold green]\n"
            f"⏱️ Duration: [yellow]{dur_str}[/yellow] ({res.time_range.formatted_start} → {res.time_range.formatted_end})\n"
            f"📁 Saved to: [yellow]{res.file_path}[/yellow]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ Trim Failed[/bold red]\n{res.error_message}",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("compress")
def compress_cli(
    input_file: str = typer.Argument(..., help="Path to input video file"),
    target_mb: Optional[float] = typer.Option(None, "--target-mb", "-m", help="Target size in MiB (e.g. 25 for Discord, 49 for Telegram)"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Preset: discord (25MB), discord_free (10MB), telegram (49MB), whatsapp (16MB)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Target output file path")
):
    """Smart-compress a video to fit messenger limits with ladder downscaling & faststart."""
    if not os.path.exists(input_file):
        console.print(f"[bold red]❌ Input file not found:[/bold red] {input_file}")
        raise typer.Exit(1)

    target_size = 25.0
    if preset:
        p_key = preset.lower()
        if p_key in ("discord", "discord_nitro"):
            target_size = 25.0
        elif p_key == "discord_free":
            target_size = 10.0
        elif p_key == "telegram":
            target_size = 49.0
        elif p_key == "whatsapp":
            target_size = 16.0
    elif target_mb is not None:
        target_size = float(target_mb)

    info = probe_video_file(input_file)
    compressor = VideoCompressor(target_mib=target_size)

    console.print(f"[bold cyan]📦 Analyzing video for compression ({target_size:.1f} MiB limit)...[/bold cyan]")
    orig_mb = info.filesize_bytes / (1024 * 1024)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bold green", finished_style="bold green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task(f"[cyan]Compressing video ({orig_mb:.1f} MB → ≤{target_size:.1f} MB)...", total=100)

        def on_prog(pct: float, speed: Optional[float]):
            spd_str = f" [{speed:.1f}x]" if speed else ""
            progress.update(task_id, completed=pct, total=100, description=f"[cyan]Compressing video{spd_str}...")

        res = compressor.compress_file(
            input_path=input_file,
            output_path=output,
            progress_callback=on_prog
        )

    if res.success:
        final_mb = res.final_bytes / (1024 * 1024)
        saved_pct = max(0.0, (1.0 - (res.final_bytes / max(1, res.orig_bytes))) * 100.0)
        
        downscale_msg = f"\n🔄 Ladder Downscaled to: [cyan]{res.plan.target_width}x{res.plan.target_height}[/cyan] for crisp quality" if (res.plan and res.plan.is_downscaled) else ""

        console.print(Panel.fit(
            f"[bold green]✅ Video Compressed Successfully![/bold green]\n"
            f"📊 Size: [yellow]{orig_mb:.1f} MB[/yellow] → [bold green]{final_mb:.1f} MB[/bold green] ([green]-{saved_pct:.1f}%[/green])\n"
            f"🎬 Bitrate: [cyan]{res.plan.video_kbps} kbps[/cyan] video + [cyan]{res.plan.audio_kbps} kbps[/cyan] aac{downscale_msg}\n"
            f"📁 Output: [yellow]{res.output_path}[/yellow]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ Compression Failed[/bold red]\n{res.error_message}",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("doctor")
def doctor_cli():
    """Run full system diagnostics and dependency checks."""
    run_doctor_diagnostics()


@app.command("update-engine")
def update_engine_cli():
    """Update the core yt-dlp downloader engine to the latest version."""
    console.print("[bold cyan]🔄 Checking for yt-dlp engine updates...[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Downloading latest engine...", total=100)

        def on_update_prog(downloaded: int, total: int):
            progress.update(task_id, completed=downloaded, total=total)

        success, msg = EngineUpdater.update_ytdlp_engine(progress_callback=on_update_prog)

    if success:
        console.print(Panel.fit(f"[bold green]✅ {msg}[/bold green]", border_style="green"))
    else:
        console.print(Panel.fit(f"[bold red]❌ {msg}[/bold red]", border_style="red"))

# -----------------------------------------------------------------------------
# INTERACTIVE TUI MODE
# -----------------------------------------------------------------------------

def run_interactive_tui():
    """Interactive TUI navigation menu for OmniDown."""
    console.clear()
    console.print(LOGO)

    console.print(Panel(
        f"[bold white]🎬 OmniDown - Universal Video Downloader & Media Processor[/bold white]\n"
        f"[dim]• VK Video & Clips • YouTube • Rutube • OK.ru • TikTok • Twitch • Dzen[/dim]\n"
        f"[dim]• Stream Slicing (Trim) • Smart Compressor • Lossless Audio • Faststart[/dim]\n"
        f"[dim cyan]v{__version__} • GitHub: {__github__}[/dim cyan]",
        border_style="cyan"
    ))

    while True:
        try:
            cur_q = str(config.get("default_quality", "best")).upper()
            action = inquirer.select(
                message="\nWhat would you like to do?",
                choices=[
                    "📥 Download Video (Pick Quality & Size)",
                    f"⚡ Quick Download [Default: {cur_q}]",
                    "🔍 Inspect Stream Matrix & Info",
                    "✂️ Download Video Segment (Stream Trim)",
                    "🎵 Extract Audio Only (MP3 / FLAC / M4A / Opus)",
                    "📦 Smart Compress Video (Discord / Telegram / WhatsApp)",
                    "🩺 Run System Diagnostics (Doctor)",
                    "🔄 Update Downloader Engine (yt-dlp)",
                    "⚙️ Settings",
                    "❌ Exit"
                ],
                pointer="> "
            ).execute()

            if action == "❌ Exit":
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            # -------------------------------------------------------------
            # 1. DOWNLOAD WITH QUALITY & SIZE PICKER
            # -------------------------------------------------------------
            if action.startswith("📥 Download Video (Pick Quality & Size)"):
                url = inquirer.text(message="Enter video URL:").execute()
                if url and url.strip():
                    choose_quality_and_download(url.strip())

            # -------------------------------------------------------------
            # 2. QUICK DOWNLOAD
            # -------------------------------------------------------------
            elif action.startswith("⚡ Quick Download"):
                url = inquirer.text(message="Enter video URL:").execute()
                if not url or not url.strip():
                    continue

                out_dir = ask_download_directory()
                quality = config.get("default_quality", "best")

                console.print(f"\n[cyan]🚀 Downloading in [{quality.upper()}] quality...[/cyan]")
                res = download_with_rich_progress(url=url.strip(), output_dir=out_dir, quality=quality)
                if res.success:
                    console.print(Panel.fit(
                        f"[bold green]✅ Downloaded successfully![/bold green]\n"
                        f"📁 Saved to: [yellow]{res.file_path or out_dir}[/yellow]",
                        border_style="green"
                    ))
                else:
                    console.print(Panel.fit(f"[bold red]❌ Error:[/bold red] {res.error_message}", border_style="red"))

            # -------------------------------------------------------------
            # 3. INSPECT STREAMS
            # -------------------------------------------------------------
            elif action.startswith("🔍 Inspect Stream Matrix"):
                url = inquirer.text(message="Enter video URL to inspect:").execute()
                if not url or not url.strip():
                    continue

                with Status("[cyan]Inspecting stream qualities...", spinner="dots", console=console):
                    try:
                        meta = VideoInspector.inspect(url.strip(), cookies_browser=config.get("browser_cookies"))
                    except Exception as e:
                        console.print(f"[bold red]❌ Inspection Error:[/bold red] {e}")
                        continue

                console.print(Panel.fit(
                    f"[bold white]{meta.title}[/bold white]\n"
                    f"👤 [bold]Channel/Uploader:[/bold] [green]{meta.uploader}[/green]\n"
                    f"⏱️ [bold]Duration:[/bold] [yellow]{meta.formatted_duration}[/yellow]\n"
                    f"🌐 [bold]Platform:[/bold] [cyan]{meta.platform}[/cyan]"
                    + (f" 📑 ([bold magenta]{meta.playlist_count} videos in playlist[/bold magenta])" if meta.is_playlist else ""),
                    title=f"🎬 {meta.platform} Stream Info",
                    border_style="cyan"
                ))

                if meta.quality_options:
                    table = Table(title="Available Video Qualities & Estimated Sizes", border_style="green")
                    table.add_column("#", style="dim")
                    table.add_column("Resolution / Label", style="bold white")
                    table.add_column("FPS", style="yellow")
                    table.add_column("Codec", style="magenta")
                    table.add_column("Est. Size", style="cyan")
                    table.add_column("Type", style="green")

                    for idx, opt in enumerate(meta.quality_options, 1):
                        fps_str = str(opt.fps) if opt.fps else "-"
                        stream_type = "Progressive (AV)" if opt.is_progressive else "Adaptive Stream"
                        table.add_row(str(idx), opt.label, fps_str, opt.vcodec.upper(), opt.formatted_size, stream_type)

                    console.print(table)
                else:
                    console.print("[yellow]ℹ️ Stream qualities will be negotiated dynamically at download time.[/yellow]")

            # -------------------------------------------------------------
            # 3. STREAM TRIM
            # -------------------------------------------------------------
            elif action == "✂️ Download Video Segment (Stream Trim)":
                url = inquirer.text(message="Enter video URL:").execute()
                if not url or not url.strip():
                    continue

                range_str = inquirer.text(
                    message="Enter time range (e.g. '00:30-01:45' or '00:30+15s'):",
                    default="00:00-00:30"
                ).execute()

                exact = inquirer.confirm(message="Use frame-exact re-encoding (slower, microsecond-accurate)?", default=False).execute()
                out_dir = ask_download_directory()

                trimmer = MediaTrimmer(output_dir=out_dir)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(complete_style="bold green", finished_style="bold green"),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task("[cyan]Trimming segment...", total=100)

                    def on_p(p: ProgressInfo):
                        if p.percent is not None:
                            progress.update(task_id, completed=p.percent, total=100)

                    res = trimmer.trim_stream_url(
                        url=url.strip(),
                        time_range_str=range_str.strip(),
                        quality=config.get("default_quality", "best"),
                        exact=exact,
                        progress_callback=on_p
                    )

                if res.success:
                    console.print(Panel.fit(
                        f"[bold green]✅ Segment Trimmed Successfully![/bold green]\n"
                        f"⏱️ Range: [yellow]{res.time_range.formatted_start} → {res.time_range.formatted_end}[/yellow]\n"
                        f"📁 Saved to: [yellow]{res.file_path}[/yellow]",
                        border_style="green"
                    ))
                else:
                    console.print(Panel.fit(f"[bold red]❌ Trim Failed:[/bold red] {res.error_message}", border_style="red"))

            # -------------------------------------------------------------
            # 4. EXTRACT AUDIO
            # -------------------------------------------------------------
            elif action.startswith("🎵 Extract Audio Only"):
                url = inquirer.text(message="Enter video URL:").execute()
                if not url or not url.strip():
                    continue

                audio_fmt = inquirer.select(
                    message="Select audio format:",
                    choices=["MP3 (Universal 320k)", "FLAC (Lossless)", "M4A (AAC Apple Music)", "OPUS (High efficiency)"],
                    default="MP3 (Universal 320k)"
                ).execute()

                fmt_code = "mp3"
                if "FLAC" in audio_fmt: fmt_code = "flac"
                elif "M4A" in audio_fmt: fmt_code = "m4a"
                elif "OPUS" in audio_fmt: fmt_code = "opus"

                out_dir = ask_download_directory()
                res = download_with_rich_progress(url=url.strip(), output_dir=out_dir, audio_only=True, audio_format=fmt_code)
                if res.success:
                    console.print(Panel.fit(
                        f"[bold green]✅ Audio Extracted Successfully ({fmt_code.upper()})![/bold green]\n"
                        f"📁 Saved to: [yellow]{res.file_path or out_dir}[/yellow]",
                        border_style="green"
                    ))
                else:
                    console.print(Panel.fit(f"[bold red]❌ Error:[/bold red] {res.error_message}", border_style="red"))

            # -------------------------------------------------------------
            # 5. SMART COMPRESSOR
            # -------------------------------------------------------------
            elif action.startswith("📦 Smart Compress Video"):
                file_path = inquirer.filepath(
                    message="Select local video file to compress:",
                    validate=PathValidator(is_file=True, message="Must be a valid video file"),
                    only_files=True
                ).execute()
                if not file_path or not os.path.exists(file_path):
                    continue

                preset_choice = inquirer.select(
                    message="Select target compression preset:",
                    choices=[
                        "Discord Nitro / Standard (25 MiB)",
                        "Discord Free Limit (10 MiB)",
                        "Telegram Bot Limit (49 MiB)",
                        "WhatsApp Standard (16 MiB)",
                        "Custom Target Size (MiB)"
                    ]
                ).execute()

                target_mb = 25.0
                if "10 MiB" in preset_choice: target_mb = 10.0
                elif "49 MiB" in preset_choice: target_mb = 49.0
                elif "16 MiB" in preset_choice: target_mb = 16.0
                elif "Custom" in preset_choice:
                    custom_raw = inquirer.text(message="Enter target size in MiB (e.g. 50):", default="25").execute()
                    try:
                        target_mb = float(custom_raw)
                    except ValueError:
                        target_mb = 25.0

                compressor = VideoCompressor(target_mib=target_mb)
                info = probe_video_file(file_path)
                orig_mb = info.filesize_bytes / (1024 * 1024)

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(complete_style="bold green", finished_style="bold green"),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"[cyan]Compressing ({orig_mb:.1f} MB → ≤{target_mb:.1f} MB)...", total=100)

                    def on_comp(pct: float, speed: Optional[float]):
                        spd = f" [{speed:.1f}x]" if speed else ""
                        progress.update(task_id, completed=pct, total=100, description=f"[cyan]Compressing video{spd}...")

                    res = compressor.compress_file(input_path=file_path, progress_callback=on_comp)

                if res.success:
                    final_mb = res.final_bytes / (1024 * 1024)
                    saved_pct = max(0.0, (1.0 - (res.final_bytes / max(1, res.orig_bytes))) * 100.0)
                    downscale_msg = f"\n🔄 Ladder Downscaled to: [cyan]{res.plan.target_width}x{res.plan.target_height}[/cyan]" if (res.plan and res.plan.is_downscaled) else ""
                    console.print(Panel.fit(
                        f"[bold green]✅ Video Compressed Successfully![/bold green]\n"
                        f"📊 Size: [yellow]{orig_mb:.1f} MB[/yellow] → [bold green]{final_mb:.1f} MB[/bold green] ([green]-{saved_pct:.1f}%[/green])\n"
                        f"🎬 Bitrate: [cyan]{res.plan.video_kbps} kbps[/cyan] video + [cyan]{res.plan.audio_kbps} kbps[/cyan] aac{downscale_msg}\n"
                        f"📁 Saved to: [yellow]{res.output_path}[/yellow]",
                        border_style="green"
                    ))
                else:
                    console.print(Panel.fit(f"[bold red]❌ Compression Failed:[/bold red] {res.error_message}", border_style="red"))

            # -------------------------------------------------------------
            # 6. DOCTOR
            # -------------------------------------------------------------
            elif action.startswith("🩺 Run System Diagnostics"):
                run_doctor_diagnostics()

            # -------------------------------------------------------------
            # 7. UPDATE ENGINE
            # -------------------------------------------------------------
            elif action.startswith("🔄 Update Downloader Engine"):
                console.print("[bold cyan]🔄 Updating core downloader engine (yt-dlp)...[/bold cyan]")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task("[cyan]Downloading latest engine...", total=100)

                    def on_up(downloaded: int, total: int):
                        progress.update(task_id, completed=downloaded, total=total)

                    success, msg = EngineUpdater.update_ytdlp_engine(progress_callback=on_up)

                if success:
                    console.print(Panel.fit(f"[bold green]✅ {msg}[/bold green]", border_style="green"))
                else:
                    console.print(Panel.fit(f"[bold red]❌ {msg}[/bold red]", border_style="red"))

            # -------------------------------------------------------------
            # 8. SETTINGS
            # -------------------------------------------------------------
            elif action == "⚙️ Settings":
                while True:
                    cur_dir = config.get("download_dir")
                    cur_q = config.get("default_quality")
                    cur_cookies = config.get("browser_cookies") or "None"
                    cur_proxy = config.get("proxy") or "None"

                    s_choice = inquirer.select(
                        message="Settings Menu:",
                        choices=[
                            f"📁 Change Download Directory [Current: {cur_dir}]",
                            f"🎬 Change Default Quality [Current: {cur_q.upper()}]",
                            f"🍪 Configure Browser Cookies [Current: {cur_cookies}]",
                            f"🌐 Configure Proxy [Current: {cur_proxy}]",
                            "🔄 Reset Settings to Default",
                            "⬅️ Back to Main Menu"
                        ]
                    ).execute()

                    if s_choice == "⬅️ Back to Main Menu":
                        break
                    elif s_choice.startswith("📁 Change Download Directory"):
                        new_dir = inquirer.filepath(
                            message="Select default download directory:",
                            default=cur_dir,
                            validate=PathValidator(is_dir=True, message="Must be a valid directory"),
                            only_directories=True
                        ).execute()
                        if new_dir:
                            config.set("download_dir", new_dir)
                            console.print(f"[green]✔ Download directory updated to: {new_dir}[/green]")
                    elif s_choice.startswith("🎬 Change Default Quality"):
                        new_q = inquirer.select(
                            message="Select default video quality:",
                            choices=["Best Available", "4K (2160p)", "2K (1440p)", "1080p (Full HD)", "720p (HD)", "480p (SD)"]
                        ).execute()
                        q_map = {
                            "Best Available": "best",
                            "4K (2160p)": "4k",
                            "2K (1440p)": "2k",
                            "1080p (Full HD)": "1080p",
                            "720p (HD)": "720p",
                            "480p (SD)": "480p"
                        }
                        config.set("default_quality", q_map.get(new_q, "best"))
                        console.print(f"[green]✔ Default quality set to: {q_map.get(new_q, 'best').upper()}[/green]")
                    elif s_choice.startswith("🍪 Configure Browser Cookies"):
                        b_choices = [b_desc for _, b_desc in CookieManager.get_supported_browsers()]
                        b_choices.append("❌ None (Disable browser cookies)")
                        selected_b = inquirer.select(
                            message="Select browser for importing cookies (for private & 18+ videos):",
                            choices=b_choices
                        ).execute()
                        if "None" in selected_b:
                            config.set("browser_cookies", None)
                            console.print("[green]✔ Browser cookies disabled.[/green]")
                        else:
                            # Map description to name
                            for b_name, b_desc in CookieManager.get_supported_browsers():
                                if b_desc == selected_b:
                                    config.set("browser_cookies", b_name)
                                    warn = CookieManager.get_browser_warning(b_name)
                                    if warn:
                                        console.print(f"[yellow]{warn}[/yellow]")
                                    console.print(f"[green]✔ Cookies will be imported from {b_name}.[/green]")
                                    break
                    elif s_choice.startswith("🌐 Configure Proxy"):
                        new_proxy = inquirer.text(message="Enter proxy URL (e.g. http://127.0.0.1:8080 or socks5://... leave empty to disable):", default=config.get("proxy") or "").execute()
                        config.set("proxy", new_proxy.strip() or None)
                        console.print("[green]✔ Proxy setting saved.[/green]")
                    elif s_choice.startswith("🔄 Reset Settings"):
                        if inquirer.confirm("Are you sure you want to reset all settings to defaults?", default=False).execute():
                            config.reset()
                            console.print("[green]✔ All settings reset to defaults.[/green]")

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break
        except typer.Exit:
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ Error:[/bold red] {e}")


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]OmniDown[/bold cyan] v{__version__} by [green]{__author__}[/green]")
        console.print(f"GitHub: [link={__github__}]{__github__}[/link]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True
    )
):
    """
    OmniDown - Beautiful multi-platform video downloader by ApvCode.
    If no command is provided, it starts the interactive TUI mode.
    """
    if ctx.invoked_subcommand is None:
        run_interactive_tui()


if __name__ == "__main__":
    app()
