import os
import sys
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from omnidown.utils.config import BIN_DIR
from omnidown.utils.ffmpeg import FFmpegLocator

@dataclass
class ProgressInfo:
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed_bytes_per_sec: Optional[float] = None
    eta_seconds: Optional[int] = None
    percent: Optional[float] = None
    status_text: Optional[str] = None


def parse_bytes_str(size_str: str) -> Optional[int]:
    """Parses strings like '72.34MiB', '1.2GB', '500kB' to integer bytes."""
    s = size_str.strip().replace("~", "").replace("i", "").upper()
    units = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024 * 1024,
        "MB": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }
    match = re.match(r'^([\d\.]+)\s*([A-Z]*)$', s)
    if match:
        val = float(match.group(1))
        unit = match.group(2) or "B"
        mult = units.get(unit, 1)
        return int(val * mult)
    return None


def parse_progress_line(line: str) -> Optional[ProgressInfo]:
    """
    Parses numerical or standard progress output from yt-dlp and FFmpeg.
    Supports:
    1. download:1048576|10485760|NA|1048576|9
    2. [download]  45.2% of  72.34MiB at  3.50MiB/s ETA 00:12
    3. frame= 120 fps=30 size= 1234KiB time=00:00:04.50 speed=1.95x
    """
    line = line.strip()
    if not line:
        return None

    # 1. Custom template format: download:<downloaded>|<total_est>|<total>|<speed>|<eta>
    if "download:" in line or ("|" in line and len(line.split("|")) >= 5):
        raw = line.split("download:", 1)[-1].strip()
        parts = raw.split("|")
        if len(parts) >= 5:
            def to_int(v: str) -> Optional[int]:
                v = v.strip()
                if not v or v.upper() in ("NA", "NONE"):
                    return None
                try:
                    return int(float(v))
                except (ValueError, TypeError):
                    return None

            def to_float(v: str) -> Optional[float]:
                v = v.strip()
                if not v or v.upper() in ("NA", "NONE"):
                    return None
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None

            downloaded = to_int(parts[0])
            total_est = to_int(parts[1])
            total_exact = to_int(parts[2])
            speed = to_float(parts[3])
            eta = to_int(parts[4])

            total = total_exact if total_exact is not None else total_est
            percent = None
            if downloaded is not None and total is not None and total > 0:
                percent = min(100.0, (downloaded / total) * 100.0)

            return ProgressInfo(
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed_bytes_per_sec=speed,
                eta_seconds=eta,
                percent=percent
            )

    # 2. Standard yt-dlp line: [download]  45.2% of  72.34MiB at  3.50MiB/s ETA 00:12
    ytdlp_match = re.search(
        r'\[download\]\s+([\d\.]+)%\s+of\s+~?([\d\.]+\s*[KMGT]?i?B)(?:\s+at\s+([\d\.]+\s*[KMGT]?i?B/s))?(?:\s+ETA\s+([\d:]+))?',
        line,
        re.IGNORECASE
    )
    if ytdlp_match:
        pct = float(ytdlp_match.group(1))
        total_str = ytdlp_match.group(2)
        total_b = parse_bytes_str(total_str)
        downloaded_b = int((pct / 100.0) * total_b) if total_b else None
        
        speed_b = None
        if ytdlp_match.group(3):
            speed_b = float(parse_bytes_str(ytdlp_match.group(3).replace("/s", "")) or 0)

        eta_sec = None
        if ytdlp_match.group(4):
            eta_raw = ytdlp_match.group(4)
            parts = eta_raw.split(":")
            if len(parts) == 2:
                eta_sec = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                eta_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        return ProgressInfo(
            downloaded_bytes=downloaded_b,
            total_bytes=total_b,
            speed_bytes_per_sec=speed_b,
            eta_seconds=eta_sec,
            percent=pct
        )

    # 3. FFmpeg stream line: frame=... size= 12.5MiB time=00:01:23.45 bitrate=... speed=2.5x
    if "time=" in line and ("size=" in line or "speed=" in line):
        time_match = re.search(r'time=([\d:\.]+)', line)
        size_match = re.search(r'size=\s*([\d\.]+\s*[KMGT]?i?B)', line)
        speed_match = re.search(r'speed=\s*([\d\.]+)x', line)

        time_str = time_match.group(1) if time_match else ""
        size_str = size_match.group(1) if size_match else ""
        speed_val = speed_match.group(1) if speed_match else ""

        status_msg = f"Muxing {size_str} ({time_str})"
        if speed_val:
            status_msg += f" [{speed_val}x]"

        return ProgressInfo(status_text=status_msg)

    return None


class YtDlpEngine:
    """Subprocess runner and fallback engine for yt-dlp."""

    @classmethod
    def has_executable_binary(cls) -> bool:
        """Checks if a standalone yt-dlp binary is available on disk or in PATH."""
        exe_name = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
        if (BIN_DIR / exe_name).exists():
            return True
        near_exe = Path(sys.argv[0]).parent / exe_name
        if near_exe.exists() and os.access(near_exe, os.X_OK):
            return True
        if shutil.which("yt-dlp"):
            return True
        if not getattr(sys, "frozen", False):
            return True
        return False

    @staticmethod
    def get_executable_command() -> List[str]:
        exe_name = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"

        # 1. Managed bin dir
        managed = BIN_DIR / exe_name
        if managed.exists() and os.access(managed, os.X_OK):
            return [str(managed)]

        # 2. Next to executable
        near_exe = Path(sys.argv[0]).parent / exe_name
        if near_exe.exists() and os.access(near_exe, os.X_OK):
            return [str(near_exe)]

        # 3. System PATH
        which_path = shutil.which("yt-dlp")
        if which_path:
            return [which_path]

        # 4. If running from source (not PyInstaller frozen), use sys.executable -m yt_dlp
        if not getattr(sys, "frozen", False):
            return [sys.executable, "-m", "yt_dlp"]

        return [exe_name]

    @classmethod
    def get_version(cls) -> str:
        if cls.has_executable_binary():
            cmd = cls.get_executable_command() + ["--version"]
            try:
                res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=5)
                return res.strip()
            except Exception:
                pass
        
        try:
            import yt_dlp
            return getattr(yt_dlp, "__version__", "Embedded")
        except Exception:
            return "Unknown"

    @classmethod
    def build_base_args(
        cls,
        proxy: Optional[str] = None,
        cookies_browser: Optional[str] = None,
        cookies_file: Optional[str] = None
    ) -> List[str]:
        """Builds standard yt-dlp arguments."""
        args: List[str] = [
            "--no-colors",
            "--encoding", "utf-8",
            "--concurrent-fragments", "4",
            "--progress",
            "--newline",
        ]

        ffmpeg_dir = FFmpegLocator.get_ffmpeg_dir()
        if ffmpeg_dir:
            args.extend(["--ffmpeg-location", ffmpeg_dir])

        if proxy:
            args.extend(["--proxy", proxy])

        if cookies_file and os.path.exists(cookies_file):
            args.extend(["--cookies", cookies_file])
        elif cookies_browser:
            args.extend(["--cookies-from-browser", cookies_browser])

        return args
