import re
from urllib.parse import urlparse
from typing import Tuple, Optional
from omnidown.extractors.platform_fixes import PlatformConfig, get_platform_config

class URLRouter:
    """Normalizes URLs and identifies target video platforms."""

    @staticmethod
    def normalize_url(url: str) -> str:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Clean mobile YouTube links
        url = re.sub(r'https?://m\.youtube\.com/', 'https://www.youtube.com/', url)
        url = re.sub(r'https?://youtu\.be/([a-zA-Z0-9_\-]+)', r'https://www.youtube.com/watch?v=\1', url)

        # Clean mobile VK links
        url = re.sub(r'https?://m\.vk\.com/', 'https://vk.com/', url)
        url = re.sub(r'https?://vk\.ru/', 'https://vk.com/', url)
        url = re.sub(r'https?://vkvideo\.ru/video', 'https://vk.com/video', url)

        # Clean mobile Rutube links
        url = re.sub(r'https?://m\.rutube\.ru/', 'https://rutube.ru/', url)

        # Clean mobile OK links
        url = re.sub(r'https?://m\.ok\.ru/', 'https://ok.ru/', url)

        return url

    @classmethod
    def identify_platform(cls, url: str) -> Tuple[str, PlatformConfig]:
        normalized = cls.normalize_url(url)
        parsed = urlparse(normalized)
        domain = parsed.netloc.lower()

        if any(d in domain for d in ("vk.com", "vk.ru", "vkvideo.ru")):
            if "/clip" in parsed.path:
                return "VK Clips", get_platform_config("vk clips")
            return "VK Video", get_platform_config("vk")
        elif "rutube.ru" in domain:
            return "Rutube", get_platform_config("rutube")
        elif any(d in domain for d in ("ok.ru", "odnoklassniki.ru")):
            return "OK.ru", get_platform_config("ok.ru")
        elif any(d in domain for d in ("youtube.com", "youtu.be")):
            return "YouTube", get_platform_config("youtube")
        elif "tiktok.com" in domain:
            return "TikTok", get_platform_config("tiktok")
        elif "twitch.tv" in domain:
            return "Twitch", get_platform_config("twitch")
        elif any(d in domain for d in ("dzen.ru", "zen.yandex.ru")):
            return "Dzen", get_platform_config("dzen")
        elif "vimeo.com" in domain:
            return "Vimeo", get_platform_config("vimeo")
        elif "pinterest.com" in domain or "pin.it" in domain:
            return "Pinterest", get_platform_config("pinterest")
        elif any(d in domain for d in ("twitter.com", "x.com")):
            return "X / Twitter", get_platform_config("twitter")

        return "General Video", get_platform_config("general")
