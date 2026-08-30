from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PlatformConfig:
    platform_name: str
    icon: str
    extra_args: List[str]
    headers: Dict[str, str]

def get_platform_config(platform_name: str) -> PlatformConfig:
    """Returns platform-specific yt-dlp arguments and headers."""
    name = platform_name.lower()

    if name in ("vk", "vk video", "vk clips"):
        return PlatformConfig(
            platform_name="VK Video",
            icon="🔵",
            extra_args=["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
            headers={"Referer": "https://vk.com/"}
        )
    elif name == "rutube":
        return PlatformConfig(
            platform_name="Rutube",
            icon="🔴",
            extra_args=["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
            headers={"Referer": "https://rutube.ru/"}
        )
    elif name == "ok.ru":
        return PlatformConfig(
            platform_name="Одноклассники (OK.ru)",
            icon="🟠",
            extra_args=[],
            headers={"Referer": "https://ok.ru/"}
        )
    elif name == "youtube":
        return PlatformConfig(
            platform_name="YouTube",
            icon="▶️",
            extra_args=[],
            headers={}
        )
    elif name == "tiktok":
        return PlatformConfig(
            platform_name="TikTok",
            icon="🎵",
            extra_args=[],
            headers={}
        )
    elif name == "twitch":
        return PlatformConfig(
            platform_name="Twitch",
            icon="🟣",
            extra_args=[],
            headers={}
        )
    elif name == "dzen":
        return PlatformConfig(
            platform_name="Dzen",
            icon="⚪",
            extra_args=["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"],
            headers={"Referer": "https://dzen.ru/"}
        )
    
    return PlatformConfig(
        platform_name="General Video",
        icon="🎬",
        extra_args=[],
        headers={}
    )
