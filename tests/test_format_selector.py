import pytest
from omnidown.core.format_selector import (
    normalize_codec,
    build_yt_dlp_format_spec,
    extract_quality_options,
)
from omnidown.utils.ytdlp_bin import parse_progress_line

def test_normalize_codec():
    assert normalize_codec("avc1.640028") == "h264"
    assert normalize_codec("vp09.00.51.08") == "vp9"
    assert normalize_codec("av01.0.08M.08") == "av1"
    assert normalize_codec("mp4a.40.2") == "aac"
    assert normalize_codec("opus") == "opus"
    assert normalize_codec("none") == "none"
    assert normalize_codec(None) == "none"

def test_build_format_spec_progressive_fallback():
    spec = build_yt_dlp_format_spec(target_quality="1080p", allow_muxing=False)
    assert "best[height<=1080][vcodec!=none][acodec!=none]" in spec
    assert "+" not in spec

def test_build_format_spec_muxing():
    spec = build_yt_dlp_format_spec(target_quality="1080p", allow_muxing=True)
    assert "+bestaudio/best" in spec
    assert "bestvideo[height<=1080]" in spec

def test_build_format_spec_audio():
    spec = build_yt_dlp_format_spec(target_quality="mp3", audio_only=True)
    assert spec == "bestaudio/best"

def test_extract_quality_options():
    mock_formats = [
        {"format_id": "18", "height": 360, "vcodec": "avc1.42001E", "acodec": "mp4a.40.2", "tbr": 500, "filesize": 5000000},
        {"format_id": "136", "height": 720, "vcodec": "avc1.4d401f", "acodec": "none", "tbr": 1200, "filesize": 15000000},
        {"format_id": "137", "height": 1080, "vcodec": "avc1.640028", "acodec": "none", "fps": 60, "tbr": 3000, "filesize": 40000000},
        {"format_id": "248", "height": 1080, "vcodec": "vp9", "acodec": "none", "fps": 60, "tbr": 2800, "filesize": 38000000},
    ]

    opts = extract_quality_options(mock_formats)
    assert len(opts) == 3
    assert opts[0].height == 1080
    assert opts[0].fps == 60
    assert opts[0].vcodec == "h264" # preferred due to higher tbr
    assert opts[1].height == 720
    assert opts[2].height == 360
    assert opts[2].is_progressive is True

def test_parse_progress_line():
    line = "download:1048576|10485760|10485760|1048576.0|9"
    p = parse_progress_line(line)
    assert p is not None
    assert p.downloaded_bytes == 1048576
    assert p.total_bytes == 10485760
    assert p.speed_bytes_per_sec == 1048576.0
    assert p.eta_seconds == 9
    assert p.percent == 10.0

def test_parse_progress_line_na():
    line = "download:524288|NA|NA|524288.0|NA"
    p = parse_progress_line(line)
    assert p is not None
    assert p.downloaded_bytes == 524288
    assert p.total_bytes is None
    assert p.percent is None

def test_parse_progress_line_formats():
    # Test standard yt-dlp format
    p = parse_progress_line("[download]  50.0% of 10.00MiB at 2.00MiB/s ETA 00:05")
    assert p is not None
    assert p.percent == 50.0
    assert p.total_bytes == 10 * 1024 * 1024
    assert p.eta_seconds == 5

def test_parse_progress_line_invalid():
    assert parse_progress_line("Random log message without progress") is None
    assert parse_progress_line("error: failed to connect") is None


def test_quality_option_formatted_size():
    from omnidown.core.format_selector import QualityOption
    opt1 = QualityOption(label="1080p", height=1080, fps=30, vcodec="h264", filesize_approx=10485760, format_id="137", is_progressive=False)
    assert opt1.formatted_size == "~10.0 MB"

    opt2 = QualityOption(label="4K", height=2160, fps=60, vcodec="vp9", filesize_approx=1073741824 * 2, format_id="313", is_progressive=False)
    assert opt2.formatted_size == "~2.00 GB"

    opt3 = QualityOption(label="Unknown", height=720, fps=None, vcodec="h264", filesize_approx=None, format_id="1", is_progressive=True)
    assert opt3.formatted_size == "Dynamic / Unknown"


def test_extract_quality_options_smart_size():
    # 60-second video with adaptive video and audio
    mock_formats = [
        {"format_id": "audio_1", "vcodec": "none", "acodec": "mp4a", "abr": 128, "filesize": 960000},
        {"format_id": "video_1080", "height": 1080, "width": 1920, "vcodec": "avc1.640028", "acodec": "none", "tbr": 4000, "filesize": None},
        {"format_id": "video_720", "height": 720, "width": 1280, "vcodec": "avc1.4d401f", "acodec": "none", "tbr": 2000, "filesize": None},
    ]

    opts = extract_quality_options(mock_formats, duration_sec=60.0)
    assert len(opts) == 2
    # 1080p: (4000 kbps * 1000 / 8) * 60 = 30,000,000 bytes + 960,000 audio = 30,960,000 bytes (~29.5 MB)
    assert opts[0].filesize_approx == 30960000
    assert opts[0].formatted_size == "~29.5 MB"
    assert opts[0].format_spec == "video_1080+bestaudio/best"


def test_extract_quality_options_portrait_video():
    # Vertical video (e.g. TikTok/VK Clip): width 1080, height 1920
    mock_formats = [
        {"format_id": "v1080", "height": 1920, "width": 1080, "vcodec": "avc1.640028", "acodec": "none", "tbr": 5000, "filesize": 20000000},
        {"format_id": "v720", "height": 1280, "width": 720, "vcodec": "avc1.4d401f", "acodec": "none", "tbr": 2500, "filesize": 10000000},
    ]

    opts = extract_quality_options(mock_formats)
    assert len(opts) == 2
    # Res should be min(w, h) -> 1080 and 720
    assert opts[0].height == 1080
    assert opts[0].label == "1080p (Full HD)"
    assert opts[1].height == 720
    assert opts[1].label == "720p (HD)"


