import os
import pytest
from omnidown.utils.sanitizer import sanitize_filename, resolve_collision

def test_sanitize_illegal_characters():
    dirty = 'My: Cool / Video * "Title" <2026>?.mp4'
    clean = sanitize_filename(dirty)
    assert ":" not in clean
    assert "/" not in clean
    assert "*" not in clean
    assert '"' not in clean
    assert "<" not in clean
    assert ">" not in clean
    assert "?" not in clean
    assert clean.endswith(".mp4")

def test_sanitize_windows_reserved_names():
    assert sanitize_filename("CON.mp4") == "_CON_.mp4"
    assert sanitize_filename("aux.mkv") == "_aux_.mkv"
    assert sanitize_filename("NUL") == "_NUL_"
    assert sanitize_filename("com1.mp3") == "_com1_.mp3"
    assert sanitize_filename("LPT3.wav") == "_LPT3_.wav"

def test_sanitize_trailing_dots_and_spaces():
    dirty = "Epic Clip.... .mp4"
    clean = sanitize_filename(dirty)
    assert clean == "Epic Clip.mp4"

def test_sanitize_length_truncation():
    super_long = "A" * 300 + ".mp4"
    clean = sanitize_filename(super_long, max_length=50)
    assert len(clean) <= 50
    assert clean.endswith(".mp4")

def test_resolve_collision(tmp_path):
    f1 = tmp_path / "video.mp4"
    f1.write_text("dummy")

    resolved_1 = resolve_collision(str(f1))
    assert resolved_1 == str(tmp_path / "video (1).mp4")

    # Create the collision
    f2 = tmp_path / "video (1).mp4"
    f2.write_text("dummy")

    resolved_2 = resolve_collision(str(f1))
    assert resolved_2 == str(tmp_path / "video (2).mp4")
