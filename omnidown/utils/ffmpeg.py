import os
import sys
import io
import shutil
import zipfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Callable
import requests

from omnidown.utils.config import BIN_DIR

WINDOWS_FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
LINUX_FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

class FFmpegLocator:
    """
    Robust FFmpeg and FFprobe binary locator and manager.
    Fallback chain:
    1. System PATH
    2. Managed ~/.omnidown/bin/ directory
    3. Auto-download static full build (ffmpeg + ffprobe)
    4. Bundled imageio-ffmpeg (ffmpeg only fallback)
    """

    @classmethod
    def _ensure_imageio_linked(cls):
        """If ffmpeg.exe is missing from BIN_DIR, copy it from imageio-ffmpeg as fallback."""
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        managed_ffmpeg = BIN_DIR / exe_name

        if not managed_ffmpeg.exists():
            try:
                import imageio_ffmpeg
                src = imageio_ffmpeg.get_ffmpeg_exe()
                if src and os.path.exists(src):
                    try:
                        shutil.copy2(src, managed_ffmpeg)
                    except Exception:
                        pass
            except Exception:
                pass

    @classmethod
    def get_ffmpeg_path(cls) -> Optional[str]:
        # 1. System PATH
        path_ffmpeg = shutil.which("ffmpeg")
        if path_ffmpeg:
            return path_ffmpeg

        # 2. Managed bin dir
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        managed_ffmpeg = BIN_DIR / exe_name
        if managed_ffmpeg.exists() and os.access(managed_ffmpeg, os.X_OK):
            return str(managed_ffmpeg)

        # 3. Fallback to imageio-ffmpeg copy
        cls._ensure_imageio_linked()
        if managed_ffmpeg.exists() and os.access(managed_ffmpeg, os.X_OK):
            return str(managed_ffmpeg)

        return None

    @classmethod
    def get_ffprobe_path(cls) -> Optional[str]:
        # 1. System PATH
        path_ffprobe = shutil.which("ffprobe")
        if path_ffprobe:
            return path_ffprobe

        # 2. Managed bin dir
        exe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
        managed_ffprobe = BIN_DIR / exe_name
        if managed_ffprobe.exists() and os.access(managed_ffprobe, os.X_OK):
            return str(managed_ffprobe)

        return None

    @classmethod
    def get_ffmpeg_dir(cls) -> Optional[str]:
        """Returns the directory containing ffmpeg/ffprobe for yt-dlp --ffmpeg-location."""
        ffmpeg_path = cls.get_ffmpeg_path()
        if ffmpeg_path:
            return os.path.dirname(ffmpeg_path)
        return None

    @classmethod
    def has_ffprobe(cls) -> bool:
        return cls.get_ffprobe_path() is not None

    @classmethod
    def get_version(cls) -> Tuple[Optional[str], Optional[str]]:
        """Returns (ffmpeg_version, ffprobe_version)."""
        ffmpeg_ver = None
        ffprobe_ver = None

        ffmpeg_path = cls.get_ffmpeg_path()
        if ffmpeg_path:
            try:
                out = subprocess.check_output([ffmpeg_path, "-version"], stderr=subprocess.STDOUT, text=True, timeout=5)
                first_line = out.splitlines()[0] if out else ""
                ffmpeg_ver = first_line.split("version")[1].strip().split()[0] if "version" in first_line else first_line
            except Exception:
                ffmpeg_ver = "Unknown"

        ffprobe_path = cls.get_ffprobe_path()
        if ffprobe_path:
            try:
                out = subprocess.check_output([ffprobe_path, "-version"], stderr=subprocess.STDOUT, text=True, timeout=5)
                first_line = out.splitlines()[0] if out else ""
                ffprobe_ver = first_line.split("version")[1].strip().split()[0] if "version" in first_line else first_line
            except Exception:
                ffprobe_ver = "Unknown"

        return ffmpeg_ver, ffprobe_ver

    @classmethod
    def download_static_binaries(cls, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Downloads and unpacks static FFmpeg + FFprobe into ~/.omnidown/bin/
        """
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        if sys.platform != "win32":
            # For Linux/macOS, rely on package managers or standard archives
            return False

        try:
            url = WINDOWS_FFMPEG_URL
            resp = requests.get(url, stream=True, timeout=30)
            if resp.status_code != 200:
                return False

            total_len = int(resp.headers.get("content-length", 0))
            downloaded = 0
            zip_buffer = io.BytesIO()

            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if chunk:
                    zip_buffer.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_len > 0:
                        progress_callback(downloaded, total_len)

            zip_buffer.seek(0)
            with zipfile.ZipFile(zip_buffer) as z:
                for member in z.namelist():
                    basename = os.path.basename(member)
                    if basename.lower() in ("ffmpeg.exe", "ffprobe.exe"):
                        target_file = BIN_DIR / basename
                        with z.open(member) as source, open(target_file, "wb") as target:
                            shutil.copyfileobj(source, target)

            return cls.has_ffprobe()
        except Exception:
            return False
