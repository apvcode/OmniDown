import pytest
from omnidown.core.compressor_calc import calculate_compression_plan, calculate_audio_bitrate

def test_audio_bitrate_ladder():
    assert calculate_audio_bitrate(2000) == 192
    assert calculate_audio_bitrate(1000) == 128
    assert calculate_audio_bitrate(500) == 96
    assert calculate_audio_bitrate(200) == 64

def test_calculate_compression_plan_short_video():
    # 30-second video targeting 25 MiB (Discord limit)
    # Total bitrate will be very high (~6.7 Mbps) -> should stay 1080p
    plan = calculate_compression_plan(target_mib=25.0, duration_sec=30.0, orig_width=1920, orig_height=1080)
    assert plan.target_mib == 25.0
    assert plan.audio_kbps == 192
    assert plan.video_kbps > 5000
    assert plan.target_width == 1920
    assert plan.target_height == 1080
    assert plan.is_downscaled is False
    assert plan.is_extreme_compression is False

def test_calculate_compression_plan_long_video_downscale():
    # 10-minute (600s) video targeting 25 MiB (Discord limit)
    # Total bitrate will be low (~339 kbps) -> 1080p would be ugly, should downscale to 720p or 480p
    plan = calculate_compression_plan(target_mib=25.0, duration_sec=600.0, orig_width=1920, orig_height=1080)
    assert plan.audio_kbps == 64
    assert plan.video_kbps > 200
    assert plan.target_width <= 1280
    assert plan.is_downscaled is True
    assert plan.scale_filter is not None

def test_calculate_compression_plan_portrait_video():
    # Vertical TikTok/Reel 1080x1920, 60s targeting 10 MiB
    plan = calculate_compression_plan(target_mib=10.0, duration_sec=60.0, orig_width=1080, orig_height=1920)
    assert plan.target_height > plan.target_width
    assert plan.target_width % 2 == 0
    assert plan.target_height % 2 == 0

def test_calculate_compression_plan_invalid():
    with pytest.raises(ValueError):
        calculate_compression_plan(target_mib=-5, duration_sec=10)
    with pytest.raises(ValueError):
        calculate_compression_plan(target_mib=25, duration_sec=0)
