from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class CompressionPlan:
    target_mib: float
    target_bytes: int
    duration_sec: float
    target_width: int
    target_height: int
    video_kbps: int
    audio_kbps: int
    bpp: float
    is_downscaled: bool
    is_extreme_compression: bool

    @property
    def scale_filter(self) -> Optional[str]:
        """Returns ffmpeg scale filter if downscaling is required."""
        if not self.is_downscaled:
            return None
        # Ensures width and height are divisible by 2 for H.264
        return f"scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2"


def calculate_audio_bitrate(total_kbps: float) -> int:
    """Audio ladder based on overall budget."""
    if total_kbps > 1500:
        return 192
    elif total_kbps > 800:
        return 128
    elif total_kbps > 400:
        return 96
    else:
        return 64


def calculate_compression_plan(
    target_mib: float,
    duration_sec: float,
    orig_width: int = 1920,
    orig_height: int = 1080,
    fps: float = 30.0,
    safety_margin: float = 0.97
) -> CompressionPlan:
    """
    Pure calculation engine for intelligent target-size video compression.
    
    - Incorporates a 3% safety margin against container and muxing overhead.
    - Computes video & audio bitrate.
    - Performs resolution ladder stepping (1080p -> 720p -> 480p -> 360p) based on Bits Per Pixel (bpp).
    """
    if duration_sec <= 0:
        raise ValueError("Video duration must be strictly positive.")
    if target_mib <= 0:
        raise ValueError("Target size in MiB must be strictly positive.")

    # Target bytes with safety margin
    target_bytes = int(target_mib * 1024 * 1024 * safety_margin)
    total_kbps = (target_bytes * 8) / (duration_sec * 1000)

    audio_kbps = calculate_audio_bitrate(total_kbps)
    video_kbps = max(50, int(total_kbps - audio_kbps))

    is_portrait = orig_height > orig_width
    fps = max(1.0, fps)

    # Standard landscape reference resolutions
    # If portrait, swap width & height
    standard_ladders = [
        (1920, 1080, 0.075),
        (1280, 720, 0.070),
        (854, 480, 0.065),
        (640, 360, 0.055),
    ]

    selected_w = orig_width
    selected_h = orig_height
    selected_bpp = (video_kbps * 1000) / (orig_width * orig_height * fps)
    is_downscaled = False

    # Check if downscaling ladder is needed
    for std_w, std_h, min_bpp in standard_ladders:
        ref_w = std_h if is_portrait else std_w
        ref_h = std_w if is_portrait else std_h

        if orig_width >= ref_w or orig_height >= ref_h:
            bpp = (video_kbps * 1000) / (ref_w * ref_h * fps)
            if bpp >= min_bpp:
                # Good quality density at this resolution
                if ref_w < orig_width:
                    selected_w = ref_w
                    selected_h = ref_h
                    selected_bpp = bpp
                    is_downscaled = True
                break
            else:
                # Too low bpp for this resolution, will check next lower resolution in ladder
                selected_w = ref_w
                selected_h = ref_h
                selected_bpp = bpp
                if ref_w < orig_width:
                    is_downscaled = True

    # Ensure even dimensions (divisible by 2)
    selected_w = selected_w - (selected_w % 2)
    selected_h = selected_h - (selected_h % 2)

    is_extreme = (video_kbps < 150)

    return CompressionPlan(
        target_mib=target_mib,
        target_bytes=target_bytes,
        duration_sec=duration_sec,
        target_width=selected_w,
        target_height=selected_h,
        video_kbps=video_kbps,
        audio_kbps=audio_kbps,
        bpp=selected_bpp,
        is_downscaled=is_downscaled,
        is_extreme_compression=is_extreme
    )
