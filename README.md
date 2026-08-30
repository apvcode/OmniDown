# 🎬 OmniDown

<div align="center">

```
  ██████╗ ███╗   ███╗███╗   ██╗██╗██████╗  ██████╗ ██╗    ██╗███╗   ██╗
 ██╔═══██╗████╗ ████║████╗  ██║██║██╔══██╗██╔═══██╗██║    ██║████╗  ██║
 ██║   ██║██╔████╔██║██╔██╗ ██║██║██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║
 ██║   ██║██║╚██╔╝██║██║╚██╗██║██║██║  ██║██║   ██║██║███╗██║██║╚██╗██║
 ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║
  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝
```

**Universal High-Speed Multi-Platform Video & Audio Downloader, Stream Trimmer, and Smart Messenger Compressor.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Platforms](https://img.shields.io/badge/Platforms-VK%20%7C%20YouTube%20%7C%20Rutube%20%7C%20OK%20%7C%20TikTok-red.svg)]()

[🇬🇧 English](#-english) | [🇷🇺 Русский](#-русский)

</div>

---

## 🇬🇧 English

### 🌟 Key Features

- **🌐 Multi-Platform Engine:** Universal support for **VK (Videos & Clips), YouTube (Videos & Shorts), Rutube, OK.ru (Odnoklassniki), TikTok, Twitch, Dzen, Vimeo**, and 1000+ other sites.
- **🔍 Smart Video Inspector:** Analyzes streams before downloading — shows a clean matrix of resolutions (4K, 2K, 1080p, 720p, etc.), FPS, codecs (H.264, VP9, AV1), and estimated file sizes.
- **✂️ Stream Time-Trimmer (Slicing on the fly):** Need only 15 seconds from a 2-hour podcast? OmniDown downloads **only that specific segment** directly from the online stream without downloading the full video.
- **📦 Smart Messenger Compressor:** Two-pass intelligent video compressor with ladder downscaling (1080p → 720p → 480p) to keep high visual crispness under **Discord (10/25 MiB), Telegram (49 MiB), and WhatsApp (16 MiB)** limits.
- **🎵 Lossless Audio Extractor:** Rip high-quality **MP3 (320k), FLAC (Lossless), M4A (AAC), or OPUS** with embedded thumbnails and metadata.
- **🍪 Browser Cookie Manager:** Easy authentication for private groups, age-restricted VK videos, and subscriber-only streams from Firefox, Chrome, Edge, and Brave.
- **🩺 Self-Healing Diagnostics (`doctor`):** Built-in diagnostic tool to verify FFmpeg, FFprobe, engine versions, and platform network reachability.
- **🔄 Dynamic Engine Auto-Updater:** Update the core downloading engine (`yt-dlp`) with a single click inside the standalone `.exe` without reinstalling the app.

---

### 💻 Quick Start & Usage

#### 1. Interactive TUI Mode (Arrow keys navigation)
Simply run without arguments:
```bash
python main.py
# or if compiled:
OmniDown.exe
```

#### 2. Direct CLI Commands

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
python main.py trim "my_video.mp4" "01:00-01:30" --exact

# 📦 Smart-compress video for Discord (25 MiB limit)
python main.py compress "my_video.mp4" --preset discord

# 🩺 Run system diagnostics
python main.py doctor

# 🔄 Update the underlying downloader engine
python main.py update-engine
```

---

## 🇷🇺 Русский

### 🌟 Ключевые возможности

- **🌐 Мультиплатформенный комбайн:** Скачивание с **VK (Видео и Клипы), YouTube (Видео и Shorts), Rutube, OK.ru (Одноклассники), TikTok, Twitch, Дзен, Vimeo** и еще 1000+ сервисов.
- **🔍 Инспектор качества:** Моментальный предпросмотр видео без скачивания (таблица качеств от 4K до 144p, FPS, кодеки H.264/VP9/AV1 и примерный вес).
- **✂️ Нарезка стримов на лету:** Нужно 15 секунд из 3-часового стрима? Программа скачивает **только этот отрезок** прямо из потока, экономя гигабайты трафика и время.
- **📦 Умный сжиматель под соцсети:** Двухпроходное сжатие видео под лимиты **Discord (25 МБ / 10 МБ), Telegram (49 МБ), WhatsApp (16 МБ)** с умной лестницей разрешений (авто-подгон разрешения, чтобы видео не превращалось в кашу).
- **🎵 Извлечение чистого аудио:** Выгрузка аудиодорожки в **MP3 320k, Lossless FLAC, M4A или OPUS** со встроенной обложкой.
- **🍪 Менеджер куков:** Простая авторизация через браузеры (Firefox, Edge, Chrome, Brave) для скачивания из закрытых групп VK и 18+ видео.
- **🩺 Врач системы (`doctor`):** Встроенная диагностика FFmpeg, FFprobe, версий движка и проверка связи с VK, Rutube, YouTube, TikTok.
- **🔄 Автообновление движка:** Обновление базы парсеров (`yt-dlp`) в один клик даже внутри готового `.exe` файла.

---

### 🔨 Сборка автономного `.exe` (PyInstaller)

```bash
python scripts/build_exe.py
```
Готовый исполняемый файл будет сохранен в `exe/OmniDown.exe`.

---

### 📄 Лицензия

Распространяется под лицензией MIT. Разработано с ❤️ автором **ApvCode**.
