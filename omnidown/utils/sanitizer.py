import os
import re
from pathlib import Path
from typing import Tuple

# Windows reserved device names
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

# Illegal characters for Windows / Linux / macOS
ILLEGAL_CHARS_PATTERN = re.compile(r'[\<\>\:\"\/\\\|\?\*\x00-\x1f]')

def sanitize_filename(name: str, max_length: int = 150, default: str = "video") -> str:
    """
    Sanitizes a string for use as a safe filename across Windows, Linux, and macOS.
    
    - Removes illegal characters (< > : \" / \\ | ? * and control chars).
    - Prevents Windows DOS reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9).
    - Strips leading/trailing dots and spaces.
    - Limits character length to prevent MAX_PATH filesystem errors.
    """
    if not name or not name.strip():
        name = default

    # Replace illegal characters with underscore or space
    cleaned = ILLEGAL_CHARS_PATTERN.sub("_", name)

    # Collapse consecutive spaces or underscores
    cleaned = re.sub(r'[\s_]+', ' ', cleaned).strip()

    # Split base and extension if present
    base, ext = os.path.splitext(cleaned)

    # Strip trailing dots/spaces from base
    base = base.strip(". ")

    if not base:
        base = default

    # Check for Windows reserved names
    if base.upper() in RESERVED_NAMES:
        base = f"_{base}_"

    # Truncate base if total length exceeds max_length
    max_base_len = max(10, max_length - len(ext))
    if len(base) > max_base_len:
        base = base[:max_base_len].rstrip(". ")

    return f"{base}{ext}"


def resolve_collision(target_path: str) -> str:
    """
    If target_path already exists, generates collision-safe name:
    'video.mp4' -> 'video (1).mp4' -> 'video (2).mp4'
    """
    if not os.path.exists(target_path):
        return target_path

    directory = os.path.dirname(target_path) or "."
    filename = os.path.basename(target_path)
    base, ext = os.path.splitext(filename)

    counter = 1
    # Match existing trailing (N)
    match = re.search(r'\((\d+)\)$', base)
    if match:
        counter = int(match.group(1)) + 1
        base = base[:match.start()].rstrip()

    while True:
        candidate = os.path.join(directory, f"{base} ({counter}){ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1
