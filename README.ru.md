# OmniDown

**Загрузка видео, извлечение звука, обрезка фрагментов и сжатие медиа в одном приложении.**

OmniDown объединяет интерактивное меню в терминале и прямые CLI-команды. Для получения медиа используется yt-dlp, а для объединения потоков, конвертации, обрезки и сжатия — FFmpeg.

[English version](README.md) · [Релизы](https://github.com/apvcode/OmniDown/releases) · [Сообщить о проблеме](https://github.com/apvcode/OmniDown/issues)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Лицензия: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Платформы](https://img.shields.io/badge/Windows%20%7C%20Linux%20%7C%20macOS-supported-blue?style=flat-square)](#установка)

## Возможности

- **Загрузка видео** с автоматическим выбором качества или интерактивным списком потоков, кодеков, частоты кадров и примерного размера.
- **Потоки воспроизведения TikTok** имеют приоритет над форматами с водяным знаком при загрузке и обрезке. Результат зависит от потоков, которые предоставляет TikTok.
- **Извлечение аудио** в MP3, M4A, FLAC или Opus с метаданными и обложкой, если они доступны.
- **Обрезка онлайн-видео** с загрузкой только выбранного диапазона. Также поддерживаются локальные файлы.
- **Сжатие для мессенджеров** с пресетами Discord, Telegram и WhatsApp, двухпроходным кодированием, изменением разрешения и быстрым началом воспроизведения.
- **Аппаратное кодирование** через NVIDIA NVENC, Intel QSV или AMD AMF при наличии поддержки; иначе используется процессор.
- **Настройки сети и сессий**: cookies браузера, прокси, качество по умолчанию и каталог загрузок.
- **Диагностика и обновления** с помощью встроенных команд `doctor` и `update-engine`.

### Поддерживаемые платформы

Встроенная обработка предусмотрена для VK Видео и Клипов, YouTube и Shorts, Rutube, OK.ru, TikTok, Twitch, Дзена, Vimeo, Pinterest и X/Twitter. Другие сайты, поддерживаемые yt-dlp, также могут работать.

## Установка

### Исполняемый файл для Windows

Скачайте `OmniDown.exe` на странице [релизов](https://github.com/apvcode/OmniDown/releases) и запустите его. Устанавливать Python не требуется.

### Из исходного кода

Требуется **Python 3.10 или новее**.

```bash
git clone https://github.com/apvcode/OmniDown.git
cd OmniDown
python -m venv venv
```

Активируйте окружение:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# Linux и macOS
source venv/bin/activate
```

Установите и запустите приложение:

```bash
python -m pip install -e .
omnidown
```

Во всех примерах ниже вместо `omnidown` можно использовать `python main.py`.

### FFmpeg

FFmpeg и FFprobe должны быть доступны в `PATH`. FFmpeg нужен для объединения видео- и аудиопотоков, конвертации звука, точной обрезки и сжатия локальных видео. FFprobe используется для анализа медиа.

```bash
omnidown doctor
```

Если обработка медиа не работает, запустите диагностику после установки.

## Использование

Запуск интерактивного меню:

```bash
omnidown
```

Прямой вызов команд:

```bash
omnidown --help
omnidown КОМАНДА --help
```

| Команда | Назначение |
| --- | --- |
| `download` | Скачать видео или извлечь аудио |
| `inspect` | Показать метаданные и доступные качества |
| `trim` | Вырезать фрагмент из ссылки или локального файла |
| `compress` | Сжать локальное видео до заданного размера |
| `doctor` | Проверить зависимости и доступность сайтов |
| `update-engine` | Обновить движок yt-dlp |

### Загрузка видео

```bash
# Лучшее доступное качество
omnidown download "https://www.youtube.com/watch?v=VIDEO_ID"

# Запрос конкретного разрешения
omnidown download "https://www.youtube.com/shorts/VIDEO_ID" -q 1080p

# Выбор из доступных потоков перед загрузкой
omnidown download "https://www.tiktok.com/@user/video/VIDEO_ID" --choose-quality

# Каталог для сохранения
omnidown download "https://x.com/user/status/POST_ID" -o ./downloads
```

Поддерживаются значения качества `best`, `4k`, `2k`, `1080p`, `720p`, `480p` и `360p`. Если запрошенного разрешения нет, выбирается ближайшее более низкое качество.

### Извлечение аудио

```bash
omnidown download "URL" --audio-only --audio-format mp3
omnidown download "URL" -a --audio-format flac
```

Доступные форматы: `mp3`, `m4a`, `flac` и `opus`.

### Информация о видео

```bash
omnidown inspect "URL"
omnidown inspect "URL" --browser firefox
omnidown inspect "URL" --proxy "http://127.0.0.1:8080"
```

Cookies браузера помогают открывать закрытые или возрастные материалы, к которым у вас есть доступ. Если операционная система блокирует базу cookies, закройте выбранный браузер.

### Обрезка видео

```bash
# Загрузить только интервал с 15 по 30 секунду
omnidown trim "https://www.youtube.com/watch?v=VIDEO_ID" "00:15-00:30"

# Начать с первой минуты и сохранить 45 секунд
omnidown trim "URL" "01:00+45s"

# Обрезать локальный файл
omnidown trim "video.mp4" "01:00-01:30" --output clip.mp4
```

По умолчанию используется быстрая обрезка по ключевым кадрам. Флаг `--exact` включает перекодирование для покадровой точности, но работает медленнее. Для онлайн-видео точная обрезка может потребовать загрузки дополнительных данных вокруг выбранного диапазона.

### Сжатие видео

```bash
omnidown compress "video.mp4" --preset discord
omnidown compress "video.mp4" --preset telegram
omnidown compress "video.mp4" --preset whatsapp
omnidown compress "video.mp4" --target-mb 20 --output compressed.mp4
```

| Пресет | Целевой размер |
| --- | ---: |
| `discord_free` | 10 МиБ |
| `discord` / `discord_nitro` | 25 МиБ |
| `whatsapp` | 16 МиБ |
| `telegram` | 49 МиБ |

Целевой размер ограничивает объём файла, но не гарантирует качество изображения. Для длинных видео может потребоваться снижение разрешения и битрейта. Фактические лимиты загрузки в мессенджерах могут меняться.

## Настройки

В интерактивном меню можно изменить:

- Каталог загрузок и качество видео по умолчанию
- Импорт cookies из Firefox, Chrome, Edge, Brave или Opera
- HTTP- или SOCKS-прокси
- Сброс всех настроек к значениям по умолчанию

Скачивайте только материалы, которые у вас есть право открывать и сохранять. Поддержка сайтов может нарушаться после изменений на платформах: перед отправкой отчёта выполните `omnidown update-engine` или обновите пакет.

## Разработка

Установка зависимостей и запуск тестов:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Сборка автономного исполняемого файла Windows:

```bash
python scripts/build_exe.py
```

Скрипт сохраняет исполняемый файл в `exe/OmniDown.exe`.

## Лицензия

OmniDown распространяется по [лицензии MIT](LICENSE).
