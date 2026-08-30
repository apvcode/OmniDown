import re
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class TimeRange:
    start_seconds: float
    end_seconds: float
    duration_seconds: float

    @property
    def formatted_start(self) -> str:
        return format_seconds(self.start_seconds)

    @property
    def formatted_end(self) -> str:
        return format_seconds(self.end_seconds)

    @property
    def ytdlp_section_spec(self) -> str:
        """Returns the section string for yt-dlp e.g. '*00:01:30-00:02:45'."""
        return f"*{self.formatted_start}-{self.formatted_end}"


def format_seconds(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or HH:MM:SS.mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if abs(secs - round(secs)) < 0.001:
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_single_timestamp(ts_str: str) -> float:
    """
    Parses a timestamp string into float seconds.
    Supported formats:
    - Pure numbers: '90', '90s', '90.5'
    - Units: '1h20m30s', '1h30s', '15m', '1.5m'
    - Clock formats: '01:30', '1:30', '01:30:45', '1:30:45.500'
    
    Raises:
        ValueError if string is invalid or contains invalid clock values (e.g. seconds >= 60 in clock format).
    """
    s = ts_str.strip().lower()
    if not s:
        raise ValueError("Empty timestamp string.")

    # 1. Trailing 's' (e.g. '90s', '15.5s')
    if s.endswith("s") and not any(c in s for c in ("h", "m", ":")):
        s = s[:-1].strip()

    # 2. Pure float / int seconds
    try:
        val = float(s)
        if val < 0:
            raise ValueError(f"Timestamp cannot be negative: {ts_str}")
        return val
    except ValueError:
        pass

    # 3. Units format: e.g. 1h20m30s, 15m, 1.5m, 2h30s
    unit_pattern = re.compile(r'^(?:(?P<h>\d+(?:\.\d+)?)h)?(?:(?P<m>\d+(?:\.\d+)?)m)?(?:(?P<s>\d+(?:\.\d+)?)s?)?$')
    if any(u in s for u in ("h", "m")):
        match = unit_pattern.match(s)
        if match:
            h = float(match.group("h") or 0)
            m = float(match.group("m") or 0)
            sec = float(match.group("s") or 0)
            total = h * 3600 + m * 60 + sec
            if total >= 0 and s != "":
                return total

    # 4. Clock format: HH:MM:SS.mmm or MM:SS.mmm
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            m_str, s_str = parts
            h_val = 0.0
            m_val = float(m_str)
            s_val = float(s_str)
        elif len(parts) == 3:
            h_str, m_str, s_str = parts
            h_val = float(h_str)
            m_val = float(m_str)
            s_val = float(s_str)
        else:
            raise ValueError(f"Invalid clock format: '{ts_str}'")

        if m_val < 0 or s_val < 0 or h_val < 0:
            raise ValueError(f"Clock values cannot be negative: '{ts_str}'")
        if m_val >= 60:
            raise ValueError(f"Minutes cannot be 60 or more in clock format '{ts_str}'")
        if s_val >= 60:
            raise ValueError(f"Seconds cannot be 60 or more in clock format '{ts_str}'")

        return h_val * 3600 + m_val * 60 + s_val

    raise ValueError(f"Unrecognized timestamp format: '{ts_str}'")


def parse_time_range(
    range_str: str,
    max_duration: Optional[float] = None
) -> TimeRange:
    """
    Parses a time range string into a TimeRange object.
    
    Supported formats:
    - 'start-end': e.g. '00:30-01:45', '10-30', '1m-2m30s'
    - 'start+duration': e.g. '00:30+15s', '10+5', '1h+10m'
    
    Args:
        range_str: The range input string.
        max_duration: Optional total video duration to clamp end time.
        
    Raises:
        ValueError if range is invalid or start >= end.
    """
    s = range_str.strip()
    if not s:
        raise ValueError("Time range cannot be empty.")

    if "+" in s:
        parts = s.split("+", 1)
        start_sec = parse_single_timestamp(parts[0])
        dur_sec = parse_single_timestamp(parts[1])
        if dur_sec <= 0:
            raise ValueError(f"Duration in range must be positive: '{range_str}'")
        end_sec = start_sec + dur_sec
    elif "-" in s:
        # Care for timestamps with hyphens if any (split on first valid range hyphen)
        # Match 'start - end'
        parts = s.split("-", 1)
        start_sec = parse_single_timestamp(parts[0])
        end_sec = parse_single_timestamp(parts[1])
    else:
        raise ValueError(f"Time range must contain '-' (start-end) or '+' (start+duration). Given: '{range_str}'")

    if start_sec < 0:
        raise ValueError(f"Start time cannot be negative: {start_sec}")

    if end_sec <= start_sec:
        raise ValueError(f"End time ({end_sec}s) must be strictly greater than start time ({start_sec}s).")

    if max_duration and max_duration > 0:
        if start_sec >= max_duration:
            raise ValueError(f"Start time ({start_sec}s) exceeds total video duration ({max_duration}s).")
        if end_sec > max_duration:
            end_sec = max_duration

    return TimeRange(
        start_seconds=start_sec,
        end_seconds=end_sec,
        duration_seconds=end_sec - start_sec
    )
