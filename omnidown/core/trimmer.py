import os
import sys
import subprocess
from dataclasses import dataclass
from typing import Optional, Callable
from rich.console import Console

from omnidown.utils.config import config
from omnidown.utils.ffmpeg import FFmpegLocator
from omnidown.utils.sanitizer import sanitize_filename, resolve_collision
from omnidown.utils.time_parser import parse_time_range, TimeRange
from omnidown.utils.ytdlp_bin import YtDlpEngine, parse_progress_line, ProgressInfo
from omnidown.core.format_selector import build_yt_dlp_format_spec
from omnidown.core.compressor import parse_ffmpeg_progress_line

console = Console()

@dataclass
class TrimmerResult:
    success: bool
    file_path: Optional[str] = None
    time_range: Optional[TimeRange] = None
    error_message: Optional[str] = None


class MediaTrimmer:
    """Handles both remote stream slicing (zero redundant download) and local video slicing."""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or config.get("download_dir")
        self.ffmpeg = FFmpegLocator.get_ffmpeg_path()
        os.makedirs(self.output_dir, exist_ok=True)

    def trim_stream_url(
        self,
        url: str,
        time_range_str: str,
        quality: str = "best",
        exact: bool = False,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> TrimmerResult:
        """
        Downloads only the specified segment directly from the video stream.
        - exact=False (Fast): Keyframe cut via yt-dlp section slicing (zero re-encoding).
        - exact=True (Accurate): Frame-exact cuts via --force-keyframes-at-cuts.
        """
        try:
            t_range = parse_time_range(time_range_str)
        except ValueError as e:
            return TrimmerResult(success=False, error_message=str(e))

        has_ff = FFmpegLocator.has_ffprobe()
        format_spec = build_yt_dlp_format_spec(
            target_quality=quality,
            allow_muxing=has_ff,
            codec_priority=config.get("codec_priority", ["h264", "vp9", "av1"])
        )

        out_template = os.path.join(self.output_dir, "%(title)s_trimmed.%(ext)s")

        # 1. Subprocess if standalone binary exists
        if YtDlpEngine.has_executable_binary():
            cmd = YtDlpEngine.get_executable_command()
            base_args = YtDlpEngine.build_base_args()

            progress_tpl = "download:%(progress.downloaded_bytes)s|%(progress.total_bytes_estimate)s|%(progress.total_bytes)s|%(progress.speed)s|%(progress.eta)s"

            args = [
                *cmd,
                *base_args,
                "-f", format_spec,
                "-o", out_template,
                "--download-sections", t_range.ytdlp_section_spec,
                "--newline",
                "--progress-template", progress_tpl,
                "--no-warnings",
                "--print", "after_move:filepath",
                "--print", "title",
            ]

            if exact:
                args.append("--force-keyframes-at-cuts")

            args.append(url)

            final_filepath = None
            error_lines = []
            proc = None

            try:
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1
                )

                if proc.stdout:
                    for raw_line in proc.stdout:
                        line = raw_line.strip()
                        if not line:
                            continue

                        if line.startswith("download:"):
                            p_info = parse_progress_line(line)
                            if p_info and progress_callback:
                                progress_callback(p_info)
                            continue

                        if os.path.exists(line) and os.path.isfile(line):
                            final_filepath = line
                            continue

                        if "ERROR" in line or "error" in line.lower():
                            error_lines.append(line)

                        if status_callback and line.startswith(("[Merger]", "[ExtractAudio]", "[Fixup")):
                            status_callback(line)

                ret = proc.wait()
                if ret != 0:
                    err = "\n".join(error_lines) if error_lines else f"Process exited with code {ret}"
                    return TrimmerResult(success=False, error_message=err, time_range=t_range)

                return TrimmerResult(
                    success=True,
                    file_path=final_filepath,
                    time_range=t_range
                )
            except Exception:
                pass
            finally:
                if proc and proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=2)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass

        # 2. In-Process fallback
        try:
            import yt_dlp
            final_filepath = None

            def ydl_progress_hook(d):
                nonlocal final_filepath
                status = d.get('status')
                if status == 'downloading':
                    downloaded = d.get('downloaded_bytes')
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    speed = d.get('speed')
                    eta = d.get('eta')
                    pct = (downloaded / total * 100.0) if (downloaded and total and total > 0) else None
                    if progress_callback:
                        progress_callback(ProgressInfo(
                            downloaded_bytes=downloaded,
                            total_bytes=total,
                            speed_bytes_per_sec=speed,
                            eta_seconds=eta,
                            percent=pct
                        ))
                elif status == 'finished':
                    final_filepath = d.get('filename')

            def range_callback(info_dict, ydl):
                return [{
                    'start_time': t_range.start_seconds,
                    'end_time': t_range.end_seconds,
                    'title': 'section'
                }]

            ydl_opts = {
                'format': format_spec,
                'outtmpl': out_template,
                'ffmpeg_location': FFmpegLocator.get_ffmpeg_dir(),
                'download_ranges': range_callback,
                'force_keyframes_at_cuts': exact,
                'progress_hooks': [ydl_progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                if not final_filepath and info_dict:
                    final_filepath = ydl.prepare_filename(info_dict)

            return TrimmerResult(success=True, file_path=final_filepath, time_range=t_range)

        except Exception as e:
            return TrimmerResult(success=False, error_message=str(e), time_range=t_range)

    def trim_local_file(
        self,
        input_path: str,
        time_range_str: str,
        output_path: Optional[str] = None,
        exact: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> TrimmerResult:
        """
        Trims a local video file.
        - exact=False (Fast copy): -ss before -i with -c copy -avoid_negative_ts make_zero
        - exact=True (Re-encode): -ss before -i with -c:v libx264 -c:a aac -avoid_negative_ts make_zero
        """
        if not os.path.exists(input_path):
            return TrimmerResult(success=False, error_message=f"Local file not found: {input_path}")
        if not self.ffmpeg:
            return TrimmerResult(success=False, error_message="FFmpeg not found.")

        try:
            t_range = parse_time_range(time_range_str)
        except ValueError as e:
            return TrimmerResult(success=False, error_message=str(e))

        if not output_path:
            dir_name = os.path.dirname(input_path) or self.output_dir
            base, ext = os.path.splitext(os.path.basename(input_path))
            out_name = f"{base}_clip_{int(t_range.start_seconds)}s_{int(t_range.end_seconds)}s{ext}"
            output_path = resolve_collision(os.path.join(dir_name, out_name))

        start_fmt = t_range.formatted_start
        dur_fmt = f"{t_range.duration_seconds:.3f}"

        if exact:
            codec_args = ["-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-b:a", "192k"]
        else:
            codec_args = ["-c", "copy"]

        cmd = [
            self.ffmpeg,
            "-y",
            "-ss", start_fmt,
            "-t", dur_fmt,
            "-i", input_path,
            *codec_args,
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-nostats",
            "-loglevel", "error",
            output_path
        ]

        try:
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
                            pct = min(100.0, (p_info.out_time_sec / max(0.1, t_range.duration_seconds)) * 100.0)
                            progress_callback(pct)

            ret = proc.wait()
            if ret != 0:
                err = proc.stderr.read() if proc.stderr else f"Exit code {ret}"
                return TrimmerResult(success=False, error_message=err, time_range=t_range)

            if os.path.exists(output_path):
                return TrimmerResult(success=True, file_path=output_path, time_range=t_range)
            return TrimmerResult(success=False, error_message="Output file not found.", time_range=t_range)

        except Exception as e:
            return TrimmerResult(success=False, error_message=str(e), time_range=t_range)
        finally:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
