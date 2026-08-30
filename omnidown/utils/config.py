import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".omnidown"
CONFIG_FILE = CONFIG_DIR / "config.json"
BIN_DIR = CONFIG_DIR / "bin"

DEFAULT_CONFIG: Dict[str, Any] = {
    "download_dir": str(Path.home() / "Downloads"),
    "default_quality": "best",
    "default_audio_format": "mp3",
    "codec_priority": ["h264", "vp9", "av1"],
    "concurrent_fragments": 4,
    "embed_subtitles": True,
    "embed_thumbnail": True,
    "embed_metadata": True,
    "proxy": None,
    "browser_cookies": None,
    "telegram_bot_token": None,
}

class ConfigManager:
    def __init__(self):
        self._ensure_dirs()
        self.data: Dict[str, Any] = self._load()

    def _ensure_dirs(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BIN_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save(self):
        self._ensure_dirs()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def reset(self):
        self.data = DEFAULT_CONFIG.copy()
        self.save()

# Global config singleton
config = ConfigManager()
