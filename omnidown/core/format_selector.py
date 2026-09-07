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
    format_spec: Optional[str] = None
    width: Optional[int] = None

    @property
    def formatted_size(self) -> str:
        if not self.filesize_approx or self.filesize_approx <= 0:
            return "Dynamic / Unknown"
        mb = self.filesize_approx / (1024 * 1024)
        if mb >= 1024:
            return f"~{mb / 1024:.2f} GB"
        return f"~{mb:.1f} MB"


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


def extract_quality_options(
    formats: List[Dict[str, Any]],
    duration_sec: Optional[float] = None
) -> List[QualityOption]:
    """
    Parses a raw yt-dlp formats list into deduplicated QualityOption objects sorted by resolution descending.
    Includes smart file size calculation for adaptive (DASH) and progressive streams.
    """
    if not formats:
        return []

    # 1. Estimate best audio stream size/bitrate for muxed adaptive streams
    best_audio_bitrate = 128.0
    best_audio_size = 0
    for f in formats:
        vc = f.get("vcodec")
        ac = f.get("acodec")
        if (vc == "none" or vc is None) and (ac and ac != "none"):
            abr = f.get("abr") or f.get("tbr") or 0
            if abr > best_audio_bitrate:
                best_audio_bitrate = float(abr)
            sz = f.get("filesize") or f.get("filesize_approx")
            if sz and sz > best_audio_size:
                best_audio_size = int(sz)

    if not best_audio_size and duration_sec and duration_sec > 0:
        best_audio_size = int((best_audio_bitrate * 1000.0 / 8.0) * duration_sec)

    # 2. Group best video format by effective resolution height
    # by_res: res -> (score, format_dict, calculated_total_size)
    by_res: Dict[int, Tuple[float, Dict[str, Any], Optional[int]]] = {}

    for f in formats:
        height = f.get("height")
        width = f.get("width")
        vcodec = f.get("vcodec")
        if not height or vcodec in (None, "none"):
            continue

        # Effective resolution height: for portrait/vertical videos (e.g. 1080x1920), min(w, h) is 1080
        res = min(width, height) if (width and height and width > 0 and height > 0) else height

        # Calculate stream size
        stream_sz = f.get("filesize") or f.get("filesize_approx")
        tbr = f.get("tbr") or f.get("vbr") or 0
        if not stream_sz and tbr and duration_sec and duration_sec > 0:
            stream_sz = int((float(tbr) * 1000.0 / 8.0) * duration_sec)

        acodec = f.get("acodec")
        is_prog = (vcodec not in (None, "none") and acodec not in (None, "none"))
        total_sz = stream_sz
        if not is_prog and total_sz is not None and best_audio_size > 0:
            total_sz += best_audio_size

        # Compute format priority score:
        # Prefer known size (+1000)
        # Prefer standard https over m3u8_native (+500)
        norm_c = normalize_codec(vcodec)
        codec_bonus = 300 if norm_c == "h264" else (200 if norm_c == "vp9" else (100 if norm_c == "av1" else 0))
        proto_bonus = 500 if f.get("protocol") == "https" else 0
        size_bonus = 1000 if stream_sz else 0
        score = size_bonus + proto_bonus + codec_bonus + float(tbr)

        if res not in by_res or score > by_res[res][0]:
            by_res[res] = (score, f, total_sz)

    options: List[QualityOption] = []
    for res in sorted(by_res.keys(), reverse=True):
        _, f, est_size = by_res[res]
        w = f.get("width")
        fps = f.get("fps")
        vcodec = normalize_codec(f.get("vcodec"))
        acodec = normalize_codec(f.get("acodec"))
        is_prog = (vcodec != "none" and acodec != "none")
        fid = str(f.get("format_id", ""))

        label_prefix = f"{res}p"
        if res >= 2160:
            label = f"{label_prefix} (4K UHD)"
        elif res >= 1440:
            label = f"{label_prefix} (2K QHD)"
        elif res >= 1080:
            label = f"{label_prefix} (Full HD)"
        elif res >= 720:
            label = f"{label_prefix} (HD)"
        else:
            label = f"{label_prefix} (SD)"

        if fps and fps >= 50:
            label += f" {fps}fps"

        format_spec = fid if is_prog else f"{fid}+bestaudio/best"

        options.append(QualityOption(
            label=label,
            height=res,
            fps=fps,
            vcodec=vcodec,
            filesize_approx=est_size,
            format_id=fid,
            is_progressive=is_prog,
            format_spec=format_spec,
            width=w
        ))

    return options
