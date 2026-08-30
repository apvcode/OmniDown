import os
import sys
import re
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Callable
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)

from omnidown.utils.ffmpeg import FFmpegLocator
from omnidown.utils.sanitizer import sanitize_filename, resolve_collision
from omnidown.core.compressor_calc import calculate_compression_plan, CompressionPlan

console = Console()

@dataclass
class FFmpegProgress:
    out_time_sec: Optional[float] = None
    fps: Optional[float] = None
    speed_multiplier: Optional[float] = None
    is_done: bool = False


def parse_ffmpeg_progress_line(key_value_block: str) -> Optional[FFmpegProgress]:
    """
    Parses FFmpeg -progress pipe:1 key=value pairs.
    Example lines:
      frame=120
      fps=30.5
      out_time_us=4000000
      speed=1.95x
      progress=continue
    """
    if not key_value_block:
        return None

    data = {}
    for line in key_value_block.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()

    if not data:
        return None

    out_time_sec = None
    if "out_time_us" in data:
        try:
            out_time_sec = float(data["out_time_us"]) / 1_000_000.0
        except ValueError:
            pass
    elif "out_time_ms" in data:
        try:
            out_time_sec = float(data["out_time_ms"]) / 1_000.0
        except ValueError:
            pass

    fps_val = None
    if "fps" in data:
        try:
            fps_val = float(data["fps"])
        except ValueError:
            pass

    speed_val = None
    if "speed" in data:
        speed_raw = data["speed"].rstrip("x").strip()
        try:
            speed_val = float(speed_raw)
        except ValueError:
            pass

    is_done = (data.get("progress") == "end")

    return FFmpegProgress(
        out_time_sec=out_time_sec,
        fps=fps_val,
        speed_multiplier=speed_val,
        is_done=is_done
    )


@dataclass
class VideoStreamInfo:
    duration_sec: float
    width: int
    height: int
    fps: float
    filesize_bytes: int


def probe_video_file(file_path: str) -> VideoStreamInfo:
    """Uses ffprobe to extract exact video dimensions, duration, and fps."""
    ffprobe = FFmpegLocator.get_ffprobe_path()
    if not ffprobe:
        # Fallback to file size and default 1080p
        size = os.path.getsize(file_path)
        return VideoStreamInfo(duration_sec=60.0, width=1920, height=1080, fps=30.0, filesize_bytes=size)

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration,size",
        "-of", "json",
        file_path
    ]

    try:
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=10)
        data = json.loads(res)
        
        streams = data.get("streams", [])
        fmt = data.get("format", {})

        width = 1920
        height = 1080
        fps = 30.0
        dur = float(fmt.get("duration") or 0.0)

        if streams:
            s0 = streams[0]
            width = int(s0.get("width") or 1920)
            height = int(s0.get("height") or 1080)
            if not dur:
                dur = float(s0.get("duration") or 0.0)

            r_fps = s0.get("r_frame_rate", "30/1")
            if "/" in r_fps:
                num, den = r_fps.split("/")
                fps = float(num) / max(1.0, float(den))
            else:
                fps = float(r_fps or 30.0)

        size = int(fmt.get("size") or os.path.getsize(file_path))
        return VideoStreamInfo(
            duration_sec=max(1.0, dur),
            width=width,
            height=height,
            fps=fps,
            filesize_bytes=size
        )
    except Exception:
        size = os.path.getsize(file_path)
        return VideoStreamInfo(duration_sec=60.0, width=1920, height=1080, fps=30.0, filesize_bytes=size)


def detect_hardware_encoder(ffmpeg_path: str) -> Optional[str]:
    """Tests if NVENC, QSV, or AMF encoders are genuinely supported by hardware."""
    candidates = ["h264_nvenc", "h264_qsv", "h264_amf"]
    for enc in candidates:
        cmd = [
            ffmpeg_path,
            "-f", "lavfi",
            "-i", "color=c=black:s=64x64:d=0.04",
            "-c:v", enc,
            "-f", "null",
            "-"
        ]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=3)
            return enc
        except Exception:
            continue
    return None


@dataclass
class CompressionResult:
    success: bool
    output_path: Optional[str] = None
    orig_bytes: int = 0
    final_bytes: int = 0
    plan: Optional[CompressionPlan] = None
    error_message: Optional[str] = None


class VideoCompressor:
    """Intelligent target-size video compressor with ladder downscaling and hardware acceleration."""

    PRESETS = {
        "discord_free": 10.0,     # Discord 10 MiB free limit
        "discord_nitro": 25.0,    # Discord 25 MiB standard limit
        "telegram": 49.0,         # Telegram Bot 50 MB limit (49 MiB safe)
        "whatsapp": 16.0,         # WhatsApp standard limit
    }

    def __init__(self, target_mib: float = 25.0):
        self.target_mib = target_mib
        self.ffmpeg = FFmpegLocator.get_ffmpeg_path()
        if not self.ffmpeg:
            raise RuntimeError("FFmpeg executable not found. Cannot perform video compression.")

    def compress_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, Optional[float]], None]] = None
    ) -> CompressionResult:
        if not os.path.exists(input_path):
            return CompressionResult(success=False, error_message=f"Input file not found: {input_path}")

        info = probe_video_file(input_path)
        plan = calculate_compression_plan(
            target_mib=self.target_mib,
            duration_sec=info.duration_sec,
            orig_width=info.width,
            orig_height=info.height,
            fps=info.fps
        )

        if not output_path:
            dir_name = os.path.dirname(input_path) or "."
            base, ext = os.path.splitext(os.path.basename(input_path))
            out_filename = f"{base}_compressed_{int(self.target_mib)}MB.mp4"
            output_path = resolve_collision(os.path.join(dir_name, out_filename))

        hw_enc = detect_hardware_encoder(self.ffmpeg)

        # Filters
        v_filters = []
        if plan.scale_filter:
            v_filters.append(plan.scale_filter)

        filter_arg = ["-vf", ",".join(v_filters)] if v_filters else []

        try:
            if hw_enc:
                # Hardware accelerated single-pass VBR
                cmd = [
                    self.ffmpeg,
                    "-y",
                    "-i", input_path,
                    *filter_arg,
                    "-c:v", hw_enc,
                    "-b:v", f"{plan.video_kbps}k",
                    "-maxrate", f"{int(plan.video_kbps * 1.3)}k",
                    "-bufsize", f"{int(plan.video_kbps * 2.0)}k",
                    "-c:a", "aac",
                    "-b:a", f"{plan.audio_kbps}k",
                    "-movflags", "+faststart",
                    "-progress", "pipe:1",
                    "-nostats",
                    "-loglevel", "error",
                    output_path
                ]
                self._run_ffmpeg_with_progress(cmd, info.duration_sec, progress_callback)
            else:
                # 2-Pass CPU libx264
                pass1_cmd = [
                    self.ffmpeg,
                    "-y",
                    "-i", input_path,
                    *filter_arg,
                    "-c:v", "libx264",
                    "-b:v", f"{plan.video_kbps}k",
                    "-pass", "1",
                    "-an",
                    "-f", "null",
                    os.devnull if sys.platform == "win32" else "/dev/null"
                ]
                subprocess.run(pass1_cmd, check=True, stderr=subprocess.PIPE)

                pass2_cmd = [
                    self.ffmpeg,
                    "-y",
                    "-i", input_path,
                    *filter_arg,
                    "-c:v", "libx264",
                    "-b:v", f"{plan.video_kbps}k",
                    "-pass", "2",
                    "-c:a", "aac",
                    "-b:a", f"{plan.audio_kbps}k",
                    "-movflags", "+faststart",
                    "-progress", "pipe:1",
                    "-nostats",
                    "-loglevel", "error",
                    output_path
                ]
                self._run_ffmpeg_with_progress(pass2_cmd, info.duration_sec, progress_callback)

            # Cleanup 2-pass log files if created
            for p_file in ("ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"):
                if os.path.exists(p_file):
                    try:
                        os.remove(p_file)
                    except Exception:
                        pass

            if os.path.exists(output_path):
                final_bytes = os.path.getsize(output_path)
                return CompressionResult(
                    success=True,
                    output_path=output_path,
                    orig_bytes=info.filesize_bytes,
                    final_bytes=final_bytes,
                    plan=plan
                )
            return CompressionResult(success=False, error_message="Output file was not created.", plan=plan)

        except Exception as e:
            return CompressionResult(success=False, error_message=str(e), plan=plan)

    def _run_ffmpeg_with_progress(
        self,
        cmd: list,
        total_duration_sec: float,
        progress_callback: Optional[Callable[[float, Optional[float]], None]]
    ):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        current_block = []
        if proc.stdout:
            for raw_line in proc.stdout:
                line = raw_line.strip()
                current_block.append(line)
                if line.startswith("progress="):
                    p_info = parse_ffmpeg_progress_line("\n".join(current_block))
                    current_block = []
                    if p_info and p_info.out_time_sec is not None and progress_callback:
                        pct = min(100.0, (p_info.out_time_sec / max(0.1, total_duration_sec)) * 100.0)
                        progress_callback(pct, p_info.speed_multiplier)

        proc.wait()
        if proc.returncode != 0:
            err = proc.stderr.read() if proc.stderr else f"Exit code {proc.returncode}"
            raise RuntimeError(f"FFmpeg compression failed: {err}")
