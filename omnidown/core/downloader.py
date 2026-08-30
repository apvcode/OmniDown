import os
import sys
import subprocess
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)

from omnidown.utils.config import config
from omnidown.utils.sanitizer import sanitize_filename, resolve_collision
from omnidown.utils.ffmpeg import FFmpegLocator
from omnidown.utils.ytdlp_bin import YtDlpEngine, parse_progress_line, ProgressInfo
from omnidown.core.format_selector import build_yt_dlp_format_spec
from omnidown.extractors.router import URLRouter

console = Console()

@dataclass
class DownloadResult:
    success: bool
    file_path: Optional[str] = None
    title: Optional[str] = None
    error_message: Optional[str] = None


class VideoDownloader:
    """Subprocess & in-process video and audio download manager with Rich progress."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        quality: str = "best",
        audio_only: bool = False,
        audio_format: str = "mp3",
        proxy: Optional[str] = None,
        cookies_browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        embed_subtitles: bool = True,
        embed_thumbnail: bool = True,
        embed_metadata: bool = True,
    ):
        self.output_dir = output_dir or config.get("download_dir")
        self.quality = quality
        self.audio_only = audio_only
        self.audio_format = audio_format
        self.proxy = proxy or config.get("proxy")
        self.cookies_browser = cookies_browser or config.get("browser_cookies")
        self.cookies_file = cookies_file
        self.embed_subtitles = embed_subtitles
        self.embed_thumbnail = embed_thumbnail
        self.embed_metadata = embed_metadata

        os.makedirs(self.output_dir, exist_ok=True)

    def download(
        self,
        url: str,
        custom_format_spec: Optional[str] = None,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> DownloadResult:
        normalized_url = URLRouter.normalize_url(url)
        platform_name, platform_cfg = URLRouter.identify_platform(normalized_url)

        has_ff = FFmpegLocator.has_ffprobe()
        format_spec = custom_format_spec or build_yt_dlp_format_spec(
            target_quality=self.quality,
            allow_muxing=has_ff,
            codec_priority=config.get("codec_priority", ["h264", "vp9", "av1"]),
            audio_only=self.audio_only
        )

        out_template = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        # 1. Subprocess path if standalone binary exists
        if YtDlpEngine.has_executable_binary():
            cmd = YtDlpEngine.get_executable_command()
            base_args = YtDlpEngine.build_base_args(
                proxy=self.proxy,
                cookies_browser=self.cookies_browser,
                cookies_file=self.cookies_file
            )

            progress_tpl = "download:%(progress.downloaded_bytes)s|%(progress.total_bytes_estimate)s|%(progress.total_bytes)s|%(progress.speed)s|%(progress.eta)s"

            args = [
                *cmd,
                *base_args,
                *platform_cfg.extra_args,
                "-f", format_spec,
                "-o", out_template,
                "--progress-template", progress_tpl,
                "--print", "after_move:filepath",
                "--print", "title",
            ]

            if self.audio_only:
                args.extend([
                    "-x",
                    "--audio-format", self.audio_format,
                    "--audio-quality", "0",
                ])

            if self.embed_subtitles:
                args.extend(["--embed-subs", "--sub-langs", "all,-live_chat"])

            if self.embed_thumbnail:
                args.append("--embed-thumbnail")

            if self.embed_metadata:
                args.append("--embed-metadata")

            args.append(normalized_url)

            final_filepath = None
            extracted_title = None
            error_lines = []

            try:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1
                )

                if process.stdout:
                    for raw_line in process.stdout:
                        line = raw_line.strip()
                        if not line:
                            continue

                        # Progress parsing
                        p_info = parse_progress_line(line)
                        if p_info:
                            if progress_callback:
                                progress_callback(p_info)
                            continue

                        # Capture final filepath
                        if os.path.exists(line) and os.path.isfile(line):
                            final_filepath = line
                            continue

                        if not extracted_title and not line.startswith(("[", "ERROR", "WARNING", "frame=", "Input #", "Stream #", "Output #", "Metadata:")):
                            if len(line) > 2 and not line.startswith("download:"):
                                extracted_title = line

                        if "ERROR" in line or "error" in line.lower():
                            error_lines.append(line)

                        if status_callback:
                            if line.startswith(("[Merger]", "[ExtractAudio]", "[Fixup", "[Embed", "[ffmpeg]")):
                                status_callback(line)

                retcode = process.wait()

                if retcode != 0:
                    err_msg = "\n".join(error_lines) if error_lines else f"Process exited with code {retcode}"
                    return DownloadResult(success=False, error_message=err_msg)

                return DownloadResult(
                    success=True,
                    file_path=final_filepath,
                    title=extracted_title
                )

            except Exception:
                pass

        # 2. In-Process fallback with embedded yt_dlp
        try:
            import yt_dlp
            final_filepath = None
            extracted_title = None

            def ydl_progress_hook(d):
                nonlocal final_filepath
                status = d.get('status')
                if status == 'downloading':
                    downloaded = d.get('downloaded_bytes')
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    speed = d.get('speed')
                    eta = d.get('eta')
                    pct = (downloaded / total * 100.0) if (downloaded and total and total > 0) else None
                    if progress_callback:
                        progress_callback(ProgressInfo(
                            downloaded_bytes=downloaded,
                            total_bytes=total,
                            speed_bytes_per_sec=speed,
                            eta_seconds=eta,
                            percent=pct
                        ))
                elif status == 'finished':
                    final_filepath = d.get('filename')
                    if status_callback:
                        status_callback("Muxing and embedding metadata...")

            ydl_opts = {
                'format': format_spec,
                'outtmpl': out_template,
                'ffmpeg_location': FFmpegLocator.get_ffmpeg_dir(),
                'progress_hooks': [ydl_progress_hook],
                'concurrent_fragment_downloads': 4,
                'quiet': True,
                'no_warnings': True,
            }

            postprocessors = []
            if self.audio_only:
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': self.audio_format,
                    'preferredquality': '0',
                })
            if self.embed_subtitles:
                ydl_opts['writesubtitles'] = True
                ydl_opts['allsubtitles'] = True
                postprocessors.append({'key': 'FFmpegEmbedSubtitle'})
            if self.embed_thumbnail:
                ydl_opts['writethumbnail'] = True
                postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
                postprocessors.append({'key': 'EmbedThumbnail'})
            if self.embed_metadata:
                postprocessors.append({'key': 'FFmpegMetadata'})

            if postprocessors:
                ydl_opts['postprocessors'] = postprocessors

            if self.proxy: ydl_opts['proxy'] = self.proxy
            if self.cookies_file: ydl_opts['cookiefile'] = self.cookies_file
            elif self.cookies_browser: ydl_opts['cookiesfrombrowser'] = (self.cookies_browser,)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(normalized_url, download=True)
                extracted_title = info_dict.get('title') if info_dict else None
                if not final_filepath and info_dict:
                    final_filepath = ydl.prepare_filename(info_dict)
                    if self.audio_only:
                        base, _ = os.path.splitext(final_filepath)
                        candidate = f"{base}.{self.audio_format}"
                        if os.path.exists(candidate):
                            final_filepath = candidate

            return DownloadResult(success=True, file_path=final_filepath, title=extracted_title)

        except Exception as e:
            return DownloadResult(success=False, error_message=str(e))


def download_with_rich_progress(
    url: str,
    output_dir: Optional[str] = None,
    quality: str = "best",
    audio_only: bool = False,
    audio_format: str = "mp3"
) -> DownloadResult:
    """Convenience function running download with a Rich progress bar and dynamic speed/ETA."""
    downloader = VideoDownloader(
        output_dir=output_dir,
        quality=quality,
        audio_only=audio_only,
        audio_format=audio_format
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bold green", finished_style="bold green"),
        TaskProgressColumn(),
        TextColumn("[cyan]{task.fields[info]}[/cyan]"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Downloading media...", total=100.0, info="")

        def on_progress(p: ProgressInfo):
            if p.status_text:
                progress.update(task_id, description=f"[yellow]{p.status_text}[/yellow]")
            else:
                info_str = ""
                if p.speed_bytes_per_sec:
                    spd_mb = p.speed_bytes_per_sec / (1024 * 1024)
                    info_str = f" {spd_mb:.1f} MB/s"

                if p.downloaded_bytes and p.total_bytes and p.total_bytes > 0:
                    d_mb = p.downloaded_bytes / (1024 * 1024)
                    t_mb = p.total_bytes / (1024 * 1024)
                    pct = (p.downloaded_bytes / p.total_bytes) * 100.0
                    progress.update(
                        task_id,
                        completed=pct,
                        total=100.0,
                        info=f"[{d_mb:.1f}/{t_mb:.1f} MB{info_str}]",
                        description="[cyan]Downloading..."
                    )
                elif p.percent is not None:
                    progress.update(
                        task_id,
                        completed=p.percent,
                        total=100.0,
                        info=f"[{p.percent:.1f}%{info_str}]",
                        description="[cyan]Downloading..."
                    )

        def on_status(status_msg: str):
            progress.update(task_id, description=f"[yellow]{status_msg}[/yellow]")

        result = downloader.download(
            url=url,
            progress_callback=on_progress,
            status_callback=on_status
        )

    return result
