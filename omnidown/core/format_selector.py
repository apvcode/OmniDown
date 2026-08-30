from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class QualityOption:
    label: str               # e.g. "1080p (FHD)"
    height: int              # e.g. 1080
    fps: Optional[int]       # e.g. 60
    vcodec: str              # e.g. "h264" or "av1"
    filesize_approx: Optional[int] # in bytes
    format_id: str           # yt-dlp format_id or selector
    is_progressive: bool     # True if video+audio combined


def normalize_codec(codec: Optional[str]) -> str:
    if not codec or codec == "none":
        return "none"
    codec = codec.lower()
    if "avc" in codec or "h264" in codec or "mp4v" in codec:
        return "h264"
    if "vp9" in codec or "vp09" in codec:
        return "vp9"
    if "av01" in codec or "av1" in codec:
        return "av1"
    if "hevc" in codec or "h265" in codec:
        return "h265"
    if "mp4a" in codec or "aac" in codec:
        return "aac"
    if "opus" in codec:
        return "opus"
    if "mp3" in codec:
        return "mp3"
    return codec.split(".")[0]


def build_yt_dlp_format_spec(
    target_quality: str = "best",
    allow_muxing: bool = True,
    codec_priority: Optional[List[str]] = None,
    audio_only: bool = False
) -> str:
    """
    Builds a yt-dlp -f / --format string.
    
    Args:
        target_quality: "best", "4k", "2160p", "1440p", "1080p", "720p", "480p", "360p", "audio"
        allow_muxing: If False (e.g. no ffmpeg/ffprobe), restricts to progressive combined streams.
        codec_priority: List of codec preferences e.g. ["h264", "vp9", "av1"]
        audio_only: If True, returns best audio format spec.
    """
    if audio_only or target_quality.lower() in ("audio", "audio-only", "mp3", "m4a", "flac", "opus"):
        return "bestaudio/best"

    target_quality = target_quality.lower().replace("p", "").strip()

    # Determine height limit
    height_limit = None
    if target_quality in ("4k", "2160"):
        height_limit = 2160
    elif target_quality in ("2k", "1440"):
        height_limit = 1440
    elif target_quality.isdigit():
        height_limit = int(target_quality)

    if not allow_muxing:
        # Single file with video AND audio
        if height_limit:
            return f"best[height<={height_limit}][vcodec!=none][acodec!=none]/best[vcodec!=none][acodec!=none]"
        return "best[vcodec!=none][acodec!=none]/best"

    # Build codec preference string
    codec_priority = codec_priority or ["h264", "vp9", "av1"]
    
    # Priority sorting expressions
    video_selectors = []
    if height_limit:
        for codec in codec_priority:
            if codec == "h264":
                video_selectors.append(f"bestvideo[height<={height_limit}][vcodec^=avc1]")
                video_selectors.append(f"bestvideo[height<={height_limit}][vcodec^=mp4v]")
            elif codec == "vp9":
                video_selectors.append(f"bestvideo[height<={height_limit}][vcodec^=vp9]")
                video_selectors.append(f"bestvideo[height<={height_limit}][vcodec^=vp09]")
            elif codec == "av1":
                video_selectors.append(f"bestvideo[height<={height_limit}][vcodec^=av01]")
        
        video_selectors.append(f"bestvideo[height<={height_limit}]")
    else:
        for codec in codec_priority:
            if codec == "h264":
                video_selectors.append("bestvideo[vcodec^=avc1]")
            elif codec == "vp9":
                video_selectors.append("bestvideo[vcodec^=vp9]")
            elif codec == "av1":
                video_selectors.append("bestvideo[vcodec^=av01]")
        video_selectors.append("bestvideo")

    primary_video = "/".join(video_selectors)
    return f"{primary_video}+bestaudio/best"


def extract_quality_options(formats: List[Dict[str, Any]]) -> List[QualityOption]:
    """
    Parses a raw yt-dlp formats list into deduplicated QualityOption objects sorted by height descending.
    """
    if not formats:
        return []

    # Map height -> best format
    by_height: Dict[int, Dict[str, Any]] = {}

    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        if not height or vcodec == "none":
            continue

        existing = by_height.get(height)
        if not existing:
            by_height[height] = f
        else:
            # Prefer formats with higher tbr / bitrate or better codec
            curr_tbr = f.get("tbr") or f.get("vbr") or 0
            ex_tbr = existing.get("tbr") or existing.get("vbr") or 0
            if curr_tbr > ex_tbr:
                by_height[height] = f

    options: List[QualityOption] = []
    for height in sorted(by_height.keys(), reverse=True):
        f = by_height[height]
        fps = f.get("fps")
        vcodec = normalize_codec(f.get("vcodec"))
        acodec = normalize_codec(f.get("acodec"))
        is_prog = (vcodec != "none" and acodec != "none")

        size = f.get("filesize") or f.get("filesize_approx")
        
        label_prefix = f"{height}p"
        if height >= 2160:
            label = f"{label_prefix} (4K UHD)"
        elif height >= 1440:
            label = f"{label_prefix} (2K QHD)"
        elif height >= 1080:
            label = f"{label_prefix} (Full HD)"
        elif height >= 720:
            label = f"{label_prefix} (HD)"
        else:
            label = f"{label_prefix} (SD)"

        if fps and fps >= 50:
            label += f" {fps}fps"

        options.append(QualityOption(
            label=label,
            height=height,
            fps=fps,
            vcodec=vcodec,
            filesize_approx=size,
            format_id=str(f.get("format_id", "")),
            is_progressive=is_prog
        ))

    return options
