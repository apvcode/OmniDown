import os
import sys
import shutil
import subprocess
from typing import Tuple, Optional, Callable
import requests
from packaging import version

from omnidown import __version__, __github__
from omnidown.utils.config import BIN_DIR
from omnidown.utils.ytdlp_bin import YtDlpEngine

YTDLP_WINDOWS_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_LINUX_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_API_URL = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"

class EngineUpdater:
    """Updates the underlying yt-dlp engine dynamically in ~/.omnidown/bin/."""

    @staticmethod
    def check_ytdlp_update() -> Tuple[bool, str, str]:
        """
        Checks if a newer yt-dlp release is available.
        Returns: (has_update, current_version, latest_version)
        """
        current_ver = YtDlpEngine.get_version()
        try:
            resp = requests.get(YTDLP_API_URL, headers={"User-Agent": "OmniDown-Updater"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if latest_tag and current_ver != "Unknown":
                    try:
                        if version.parse(latest_tag) > version.parse(current_ver):
                            return True, current_ver, latest_tag
                    except Exception:
                        pass
                return False, current_ver, latest_tag or current_ver
        except Exception:
            pass
        return False, current_ver, "Unknown"

    @classmethod
    def update_ytdlp_engine(cls, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[bool, str]:
        """
        Downloads the latest standalone yt-dlp binary directly into ~/.omnidown/bin/.
        This works seamlessly inside frozen PyInstaller executables!
        """
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        exe_name = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
        target_path = BIN_DIR / exe_name
        temp_path = BIN_DIR / f"{exe_name}.tmp"

        url = YTDLP_WINDOWS_URL if sys.platform == "win32" else YTDLP_LINUX_URL

        try:
            resp = requests.get(url, stream=True, timeout=30, headers={"User-Agent": "OmniDown-Updater"})
            if resp.status_code != 200:
                return False, f"HTTP Error {resp.status_code} while downloading yt-dlp."

            total_len = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_len > 0:
                            progress_callback(downloaded, total_len)

            if sys.platform != "win32":
                os.chmod(temp_path, 0o755)

            if target_path.exists():
                try:
                    os.remove(target_path)
                except Exception:
                    pass

            shutil.move(str(temp_path), str(target_path))
            new_version = YtDlpEngine.get_version()
            return True, f"Engine updated successfully to v{new_version}!"

        except Exception as e:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return False, f"Update failed: {str(e)}"
