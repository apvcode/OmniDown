<div align="center">

# 🎬 OmniDown

**The Ultimate Universal Video Downloader, Stream Slicer & Smart Messenger Compressor.**  
*VK Video & Clips • YouTube • Rutube • OK.ru • TikTok • Twitch • Dzen • Stream Trimming • Messenger Compressor • Lossless Audio • Faststart • Interactive TUI*

[![GitHub Release](https://img.shields.io/github/v/release/apvcode/OmniDown?color=2ecc71&style=for-the-badge&logo=github)](https://github.com/apvcode/OmniDown/releases)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-3498db.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-9b59b6.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange.svg?style=for-the-badge)](#)

<br/>

[🇬🇧 **English**](#-why-omnidown) &nbsp;•&nbsp; [🇷🇺 **Русский**](#-почему-omnidown)

<br/>

```text
  ██████╗ ███╗   ███╗███╗   ██╗██╗██████╗  ██████╗ ██╗    ██╗███╗   ██╗
 ██╔═══██╗████╗ ████║████╗  ██║██║██╔══██╗██╔═══██╗██║    ██║████╗  ██║
 ██║   ██║██╔████╔██║██╔██╗ ██║██║██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║
 ██║   ██║██║╚██╔╝██║██║╚██╗██║██║██║  ██║██║   ██║██║███╗██║██║╚██╗██║
 ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║
  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝
```

</div>

---

## ⚡ Why OmniDown?

| Feature | OmniDown | Vanilla yt-dlp / Generic Downloaders |
| :--- | :---: | :---: |
| **🎨 Interactive Rich TUI Menu** | ✅ Arrow-key navigation & UI | ❌ Complex flags & commands only |
| **✂️ Online Stream Time-Trimmer** | ✅ Downloads ONLY requested segment | ❌ Downloads entire gigabytes first |
| **📦 Smart Messenger Compressor** | ✅ Intelligent Resolution Ladder (bpp) | ❌ Crushes 1080p into ugly pixel artifacts |
| **🩺 Self-Healing Diagnostics (`doctor`)** | ✅ Auto-detects & tests network/binaries | ❌ Cryptic terminal crash traces |
| **🍪 Browser Session Manager** | ✅ 1-Click Firefox / Edge / Chrome import | ❌ Manual cookie extraction hassles |
| **🔄 1-Click Engine Auto-Updater** | ✅ Updates core parser inside `.exe` | ❌ Re-download full app on API breakages |
| **🎵 Lossless Audio Rip (320k / FLAC)** | ✅ Embedded covers & ID3 tags | ⚠️ Raw stream dumps |
| **📦 Zero-Config Windows Standalone `.exe`** | ✅ Bundled FFmpeg & FFprobe | ❌ Requires manual Python / PATH setup |
| **🛡️ Windows File Safety Guard** | ✅ DOS reserved names (`CON`, `PRN`) fix | ❌ Crashes on Windows reserved files |
| **⚡ Faststart Messenger Web Playback** | ✅ Built-in `-movflags +faststart` | ❌ Buffering delays in Discord / Telegram |

---

## ✨ Features

* 🌐 **Universal Platform Support:** Native support for **VK (Videos & Clips), YouTube (Videos & Shorts), Rutube, OK.ru (Odnoklassniki), TikTok, Twitch, Dzen, Vimeo**, and 1000+ other sites.
* 🔍 **Pre-Download Stream Inspector:** Scan any link in 1 second. Displays an interactive matrix of resolutions (4K, 2K, 1080p, 720p, etc.), FPS, video codecs (**H.264, VP9, AV1**), and estimated file sizes before downloading.
* ✂️ **Stream Slicing On-the-Fly:** Need a 15-second snippet from a 3-hour podcast? OmniDown downloads **only that exact time-range** directly from the stream without downloading the full video.
* 📦 **Smart Messenger Compressor:** Two-pass intelligent video compression for **Discord (10/25 MiB), Telegram (49 MiB), and WhatsApp (16 MiB)** limits. Automatically steps down resolution ladder (1080p → 720p → 480p → 360p) based on **Bits-Per-Pixel (bpp)** density to preserve crystal-clear visuals.
* 🎚️ **Lossless Audio Extractor:** Extract clean audio in **MP3 (320 kbps CBR), FLAC (Lossless), M4A (AAC / Apple Music), or OPUS** with embedded cover art and metadata.
* 🍪 **Browser Cookie Manager:** Easy session import from **Firefox, Chrome, Edge, Brave, and Opera** to download private group videos, subscriber-only streams, and age-restricted 18+ content.
* 🩺 **System Doctor (`doctor`):** Built-in diagnostics that verify Python, yt-dlp, FFmpeg, FFprobe, and tests live network reachability to VK, Rutube, YouTube, and TikTok.
* 🔄 **Dynamic Engine Updater:** YouTube and VK frequently update algorithms. OmniDown allows 1-click updating of the underlying downloader engine right from the menu!
* 🚀 **Hardware Acceleration:** Auto-probes **NVIDIA NVENC, Intel QSV, and AMD AMF** encoders with CPU 2-pass fallback.

---

## 🚀 Quick Start

### 📦 Option 1: Standalone `.exe` (Windows — Recommended)
1. Head over to the **[Releases](https://github.com/apvcode/OmniDown/releases)** tab.
2. Download `OmniDown.exe`.
3. Run it! *(Zero installation, FFmpeg & FFprobe included)*

---

### 🐍 Option 2: Run from Source (Windows, Linux, macOS)

```bash
# 1. Clone the repository
git clone https://github.com/apvcode/OmniDown.git
cd OmniDown

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\activate

# Linux / macOS:
# source venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Launch OmniDown
python main.py
```

---

## 🎮 How to Use

### 1. 🖥️ Interactive TUI Mode (Default)
Simply run without arguments to launch the arrow-key menu:
```bash
python main.py
# or if compiled:
OmniDown.exe
```

```text
? What would you like to do?
 > 📥 Quick Download Video [Default: BEST]
   🔍 Inspect URL & Pick Exact Quality
   ✂️ Download Video Segment (Stream Trim)
   🎵 Extract Audio Only (MP3 / FLAC / M4A / Opus)
   📦 Smart Compress Video (Discord / Telegram / WhatsApp)
   🩺 Run System Diagnostics (Doctor)
   🔄 Update Downloader Engine (yt-dlp)
   ⚙️ Settings
   ❌ Exit
```

### 2. ⚡ Direct CLI Commands

```bash
# 📥 Download best available quality
python main.py download "https://vk.com/video-220754053_456241088"

# 📥 Download specific quality (1080p)
python main.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -q 1080p

# 🎵 Extract audio only (MP3 320k)
python main.py download "https://vk.com/video-220754053_456241088" --audio-only --audio-format mp3

# 🔍 Inspect stream without downloading
python main.py inspect "https://rutube.ru/video/..."

# ✂️ Download a 15-second snippet directly from online stream
python main.py trim "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "00:15-00:30"

# ✂️ Trim a local file with frame-exact accuracy
python main.py trim "video.mp4" "01:00-01:30" --exact

# 📦 Smart-compress video for Discord (25 MiB limit)
python main.py compress "video.mp4" --preset discord

# 🩺 Run system diagnostics
python main.py doctor

# 🔄 Update the downloader engine
python main.py update-engine
```

---

<br/>

## 🇷🇺 Русский

<div align="center">

### ⚡ Почему OmniDown?

</div>

| Функция | OmniDown | Обычный yt-dlp / Сторонние утилиты |
| :--- | :---: | :---: |
| **🎨 Интерактивное TUI меню** | ✅ Управление стрелочками и подсказки | ❌ Только сложные флаги в терминале |
| **✂️ Нарезка стримов на лету** | ✅ Скачивает ТОЛЬКО нужный отрезок | ❌ Выкачивает всё видео целиком |
| **📦 Умный сжиматель под соцсети** | ✅ Умная лестница разрешений (bpp) | ❌ Сжимает 1080p в мыльные кубики |
| **🩺 Врач системы (`doctor`)** | ✅ Авто-проверка FFmpeg и пинга сервисов | ❌ Непонятные ошибки при падении |
| **🍪 Менеджер сессий браузера** | ✅ Авто-подхват куков из Firefox/Edge | ❌ Сложный ручной экспорт файлов |
| **🔄 Обновление движка в 1 клик** | ✅ Обновляет парсер прямо внутри `.exe` | ❌ Перекачивать приложение целиком |
| **🎵 Извлечение звука (MP3 / FLAC)** | ✅ Вшитые обложки и ID3 теги | ⚠️ Сырые аудиопотоки |
| **📦 Автономный `.exe` без настроек** | ✅ Встроенный FFmpeg/FFprobe | ❌ Требует установки Python и FFmpeg |

---

### ✨ Возможности

* 🌐 **Все платформы в одном месте:** Поддержка **VK (Видео и Клипы), YouTube (Видео и Shorts), Rutube, OK.ru (Одноклассники), TikTok, Twitch, Дзен, Vimeo** и 1000+ других сайтов.
* 🔍 **Инспектор стримов:** Просмотр доступных качеств (от 4K до 144p), частоты кадров (FPS), кодеков (**H.264, VP9, AV1**) и примерного размера до скачивания.
* ✂️ **Стримовая нарезка:** Указывай интервал (например, `00:15-00:30` или `01:00+45s`) — программа скачает **только этот кусок**, сэкономив трафик.
* 📦 **Умный компрессор для мессенджеров:** Сжатие под лимиты **Discord (10/25 МБ), Telegram (49 МБ) и WhatsApp (16 МБ)**. Автоматически снижает разрешение (1080p → 720p → 480p → 360p) при нехватке битрейта, сохраняя картинку четкой.
* 🎵 **Чистый звук:** Сохранение музыки в **MP3 320 kbps, Lossless FLAC, M4A (Apple Music) или OPUS** со встроенными обложками.
* 🍪 **Подхват куков:** Быстрая авторизация через Firefox, Edge, Chrome или Brave для доступа к закрытым группам VK и 18+ видео.
* 🩺 **Диагностика системы (`doctor`):** Проверка здоровья FFmpeg, движка загрузки и сетевой доступности VK, Rutube, YouTube, TikTok.

---

### 🚀 Быстрый старт

#### 📦 Вариант 1: Готовый `.exe` (Windows — Рекомендуется)
1. Перейди во вкладку **[Releases](https://github.com/apvcode/OmniDown/releases)**.
2. Скачай `OmniDown.exe`.
3. Запускай и пользуйся!

---

### 🔨 Сборка автономного `.exe` (PyInstaller)

```bash
python scripts/build_exe.py
```
Собранный исполняемый файл будет доступен в папке `exe/OmniDown.exe`.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](https://github.com/apvcode/OmniDown/issues).

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.  
Created with ❤️ by **[ApvCode](https://github.com/apvcode)**.
