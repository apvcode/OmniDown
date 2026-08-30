import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

SUPPORTED_BROWSERS = [
    ("firefox", "🦊 Mozilla Firefox (Recommended on Windows)"),
    ("chrome", "🌐 Google Chrome"),
    ("edge", "🌊 Microsoft Edge"),
    ("brave", "🦁 Brave Browser"),
    ("opera", "🔴 Opera"),
    ("vivaldi", "🎭 Vivaldi"),
    ("chromium", "⚪ Chromium"),
]

class CookieManager:
    """Manages browser cookies and custom cookies.txt files for authenticated downloads."""

    @staticmethod
    def get_supported_browsers() -> List[Tuple[str, str]]:
        return SUPPORTED_BROWSERS

    @staticmethod
    def get_browser_warning(browser_name: str) -> Optional[str]:
        """Returns warnings for known browser encryption limitations."""
        if sys.platform == "win32" and browser_name.lower() in ("chrome", "edge", "brave", "opera"):
            return (
                "⚠️ Note: Chrome 127+ (and Chromium-based browsers) on Windows uses App-Bound encryption.\n"
                "If age-restricted or private video extraction fails, use Firefox or a cookies.txt file."
            )
        return None

    @staticmethod
    def validate_cookie_file(file_path: str) -> bool:
        """Validates that a custom cookie file exists and is not empty."""
        if not file_path:
            return False
        p = Path(file_path)
        return p.exists() and p.is_file() and p.stat().st_size > 10
