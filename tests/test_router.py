import pytest
from omnidown.extractors.router import URLRouter

def test_router_normalizes_and_identifies():
    cases = [
        ("https://vk.com/video-123_456", "VK Video", "https://vk.com/video-123_456"),
        ("https://vkvideo.ru/video-123_456", "VK Video", "https://vk.com/video-123_456"),
        ("https://vkvideo.ru/live-237788503_456239055", "VK Video", "https://vk.com/video-237788503_456239055"),
        ("https://vk.com/live-237788503_456239055", "VK Video", "https://vk.com/video-237788503_456239055"),
        ("https://vkvideo.ru/live/-237788503_456239055", "VK Video", "https://vk.com/video-237788503_456239055"),
        ("https://vk.com/clip-123_456", "VK Clips", "https://vk.com/clip-123_456"),
        ("https://vkvideo.ru/clip-123_456", "VK Clips", "https://vk.com/clip-123_456"),
        ("https://vkvideo.ru/clips-123_456", "VK Clips", "https://vk.com/clip-123_456"),
        ("https://live.vkvideo.ru/streamer", "VK Play Live", "https://live.vkvideo.ru/streamer"),
        ("https://m.rutube.ru/video/abcdef/", "Rutube", "https://rutube.ru/video/abcdef/"),
        ("https://m.ok.ru/video/123456", "OK.ru", "https://ok.ru/video/123456"),
        ("https://youtu.be/dQw4w9WgXcQ", "YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=abc", "YouTube", "https://www.youtube.com/watch?v=abc"),
        ("https://www.tiktok.com/@user/video/123", "TikTok", "https://www.tiktok.com/@user/video/123"),
        ("https://dzen.ru/video/watch/123", "Dzen", "https://dzen.ru/video/watch/123"),
    ]

    for raw_url, expected_name, expected_normalized in cases:
        norm = URLRouter.normalize_url(raw_url)
        name, config = URLRouter.identify_platform(raw_url)
        assert norm == expected_normalized
        assert name == expected_name
