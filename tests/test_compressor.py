import pytest
from omnidown.core.compressor import parse_ffmpeg_progress_line

def test_parse_ffmpeg_progress_line():
    block = """
    frame=240
    fps=60.0
    out_time_us=4000000
    speed=2.0x
    progress=continue
    """
    p = parse_ffmpeg_progress_line(block)
    assert p is not None
    assert p.out_time_sec == 4.0
    assert p.fps == 60.0
    assert p.speed_multiplier == 2.0
    assert p.is_done is False

def test_parse_ffmpeg_progress_line_done():
    block = """
    frame=1200
    fps=55.2
    out_time_ms=20000
    speed=1.85x
    progress=end
    """
    p = parse_ffmpeg_progress_line(block)
    assert p is not None
    assert p.out_time_sec == 20.0
    assert p.fps == 55.2
    assert p.speed_multiplier == 1.85
    assert p.is_done is True

def test_parse_ffmpeg_progress_empty():
    assert parse_ffmpeg_progress_line("") is None
    assert parse_ffmpeg_progress_line("no equals sign here") is None
