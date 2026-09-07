import json
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from omnidown.utils.ytdlp_bin import YtDlpEngine
from omnidown.utils.ffmpeg import FFmpegLocator
from omnidown.core.format_selector import QualityOption, extract_quality_options
from omnidown.extractors.router import URLRouter

@dataclass
class VideoMetadata:
    url: str
    platform: str
    title: str
    uploader: str
    duration_sec: Optional[int]
    thumbnail_url: Optional[str]
    is_playlist: bool
    playlist_count: Optional[int]
    quality_options: List[QualityOption]
    raw_info: Dict[str, Any]

    @property
    def formatted_duration(self) -> str:
        if not self.duration_sec:
            return "Live / Unknown"
        mins, secs = divmod(self.duration_sec, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


class VideoInspector:
    """Extracts rich metadata and available format options using yt-dlp."""

    @staticmethod
    def inspect(
        url: str,
        proxy: Optional[str] = None,
        cookies_browser: Optional[str] = None,
        cookies_file: Optional[str] = None
    ) -> VideoMetadata:
        normalized_url = URLRouter.normalize_url(url)
        platform_name, platform_cfg = URLRouter.identify_platform(normalized_url)

        data = None

        # 1. Try Subprocess if binary is present
        if YtDlpEngine.has_executable_binary():
            cmd = YtDlpEngine.get_executable_command()
            base_args = YtDlpEngine.build_base_args(
                proxy=proxy,
                cookies_browser=cookies_browser,
                cookies_file=cookies_file
            )

            args = [
                *cmd,
                *base_args,
                *platform_cfg.extra_args,
                "--dump-single-json",
                "--flat-playlist",
                "--no-warnings",
                normalized_url
            ]

            try:
                res = subprocess.run(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=True
                )
                data = json.loads(res.stdout)
            except Exception:
                data = None

        # 2. Fallback to in-process module
        if data is None:
            try:
                import yt_dlp
                ydl_opts = {
                    'extract_flat': True,
                    'quiet': True,
                    'no_warnings': True,
                    'ffmpeg_location': FFmpegLocator.get_ffmpeg_dir(),
                }
                if proxy: ydl_opts['proxy'] = proxy
                if cookies_file: ydl_opts['cookiefile'] = cookies_file
                elif cookies_browser: ydl_opts['cookiesfrombrowser'] = (cookies_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    data = ydl.extract_info(normalized_url, download=False)
            except Exception as e:
                raise RuntimeError(f"Failed to inspect video metadata: {e}")

        if not data:
            raise RuntimeError(f"Could not retrieve metadata for: {normalized_url}")

        # Check if playlist
        is_playlist = data.get("_type") == "playlist" or "entries" in data
        entries = data.get("entries") or []
        playlist_count = len(entries) if is_playlist else None

        title = data.get("title") or "Unknown Title"
        uploader = data.get("uploader") or data.get("channel") or "Unknown Uploader"
        duration = data.get("duration")
        thumbnail = data.get("thumbnail")
        
        formats = data.get("formats", [])
        if is_playlist and entries:
            first = entries[0] if len(entries) > 0 else {}
            title = data.get("title") or first.get("title") or "Playlist"
            formats = first.get("formats", [])

        dur_sec = float(duration) if duration else None
        qualities = extract_quality_options(formats, duration_sec=dur_sec)

        return VideoMetadata(
            url=normalized_url,
            platform=platform_name,
            title=title,
            uploader=uploader,
            duration_sec=int(duration) if duration else None,
            thumbnail_url=thumbnail,
            is_playlist=is_playlist,
            playlist_count=playlist_count,
            quality_options=qualities,
            raw_info=data
        )
