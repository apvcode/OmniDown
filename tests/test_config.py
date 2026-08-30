import json
import pytest
from omnidown.utils.config import ConfigManager

def test_config_defaults(tmp_path, monkeypatch):
    test_config_file = tmp_path / "config.json"
    monkeypatch.setattr("omnidown.utils.config.CONFIG_FILE", test_config_file)
    monkeypatch.setattr("omnidown.utils.config.CONFIG_DIR", tmp_path)

    mgr = ConfigManager()
    assert mgr.get("default_quality") == "best"
    assert mgr.get("concurrent_fragments") == 4
    assert mgr.get("codec_priority") == ["h264", "vp9", "av1"]

    mgr.set("default_quality", "1080p")
    assert mgr.get("default_quality") == "1080p"

    # Reload from file
    mgr2 = ConfigManager()
    assert mgr2.get("default_quality") == "1080p"
