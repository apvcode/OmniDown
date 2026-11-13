# OmniDown

**Download video, extract audio, trim clips, and compress media from one command-line app.**

OmniDown combines an interactive terminal menu with direct CLI commands. It uses yt-dlp for media extraction and FFmpeg for merging, conversion, trimming, and compression.

[Русская версия](README.ru.md) · [Releases](https://github.com/apvcode/OmniDown/releases) · [Issues](https://github.com/apvcode/OmniDown/issues)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Platforms](https://img.shields.io/badge/Windows%20%7C%20Linux%20%7C%20macOS-supported-blue?style=flat-square)](#installation)

## Features

- **Video downloads** with automatic quality selection or an interactive list of available streams, codecs, frame rates, and estimated sizes.
- **TikTok playback streams** preferred over watermarked download formats for both downloads and trimming. Availability depends on what TikTok provides.
- **Audio extraction** to MP3, M4A, FLAC, or Opus, with metadata and thumbnails where supported.
- **Online trimming** that downloads only the requested time range. Local files can also be trimmed.
- **Messenger compression** with presets for Discord, Telegram, and WhatsApp, two-pass encoding, resolution scaling, and faststart playback.
- **Hardware encoding** through NVIDIA NVENC, Intel QSV, or AMD AMF when available, with CPU fallback.
- **Session and network settings** for browser cookies, a proxy, default quality, and the download directory.
- **Diagnostics and updates** through the built-in `doctor` and `update-engine` commands.

### Supported platforms

Built-in handling includes VK Video and Clips, YouTube and Shorts, Rutube, OK.ru, TikTok, Twitch, Dzen, Vimeo, Pinterest, and X/Twitter. Other sites supported by yt-dlp may also work.

## Installation

### Windows executable

Download `OmniDown.exe` from [Releases](https://github.com/apvcode/OmniDown/releases) and run it. No Python installation is required.

### From source

Requires **Python 3.10 or newer**.

```bash
git clone https://github.com/apvcode/OmniDown.git
cd OmniDown
python -m venv venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# Linux and macOS
source venv/bin/activate
```

Install and run:

```bash
python -m pip install -e .
omnidown
```

You can also use `python main.py` instead of `omnidown` in all examples below.

### FFmpeg

FFmpeg and FFprobe must be available on `PATH`. FFmpeg is used for merging separate video and audio streams, audio conversion, exact trimming, and local video compression. FFprobe is used for media analysis.

```bash
omnidown doctor
```

Run diagnostics after installation if media processing fails.

## Usage

Start the interactive menu:

```bash
omnidown
```

Or call a command directly:

```bash
omnidown --help
omnidown COMMAND --help
```

| Command | Purpose |
| --- | --- |
| `download` | Download video or extract audio |
| `inspect` | Show metadata and available stream qualities |
| `trim` | Cut a segment from a URL or local file |
| `compress` | Compress a local video to a target size |
| `doctor` | Check dependencies and site connectivity |
| `update-engine` | Update the yt-dlp engine |

### Download video

```bash
# Best available quality
omnidown download "https://www.youtube.com/watch?v=VIDEO_ID"

# Request a specific resolution
omnidown download "https://www.youtube.com/shorts/VIDEO_ID" -q 1080p

# Choose from the available streams before downloading
omnidown download "https://www.tiktok.com/@user/video/VIDEO_ID" --choose-quality

# Set the output directory
omnidown download "https://x.com/user/status/POST_ID" -o ./downloads
```

Supported quality values include `best`, `4k`, `2k`, `1080p`, `720p`, `480p`, and `360p`. If the requested resolution is unavailable, the closest lower quality is selected.

### Extract audio

```bash
omnidown download "URL" --audio-only --audio-format mp3
omnidown download "URL" -a --audio-format flac
```

Available formats: `mp3`, `m4a`, `flac`, and `opus`.

### Inspect a video

```bash
omnidown inspect "URL"
omnidown inspect "URL" --browser firefox
omnidown inspect "URL" --proxy "http://127.0.0.1:8080"
```

Browser cookies can help with private or age-restricted media that you are authorized to access. Close the selected browser if your operating system locks its cookie database.

### Trim video

```bash
# Download only seconds 15 through 30
omnidown trim "https://www.youtube.com/watch?v=VIDEO_ID" "00:15-00:30"

# Start at one minute and capture 45 seconds
omnidown trim "URL" "01:00+45s"

# Trim a local file
omnidown trim "video.mp4" "01:00-01:30" --output clip.mp4
```

The default mode uses fast keyframe-aligned cuts. Add `--exact` to re-encode for frame-accurate cuts; this is slower. For remote videos, exact cutting may require downloading additional data around the requested range.

### Compress video

```bash
omnidown compress "video.mp4" --preset discord
omnidown compress "video.mp4" --preset telegram
omnidown compress "video.mp4" --preset whatsapp
omnidown compress "video.mp4" --target-mb 20 --output compressed.mp4
```

| Preset | Target size |
| --- | ---: |
| `discord_free` | 10 MiB |
| `discord` / `discord_nitro` | 25 MiB |
| `whatsapp` | 16 MiB |
| `telegram` | 49 MiB |

The target is a size limit, not a guarantee of visual quality. Long videos may require a lower resolution and bitrate. Actual messenger upload limits can change.

## Settings

The interactive menu provides settings for:

- Default download directory and video quality
- Cookies from Firefox, Chrome, Edge, Brave, or Opera
- HTTP or SOCKS proxy
- Resetting all settings to defaults

Download only content you have the right to access and save. Site support can break when platforms change; run `omnidown update-engine` or update the package before reporting an extraction problem.

## Development

Install development dependencies and run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Build the standalone Windows executable:

```bash
python scripts/build_exe.py
```

The build script writes the executable to `exe/OmniDown.exe`.

## License

OmniDown is available under the [MIT License](LICENSE).
