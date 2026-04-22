# YouTube Downloader — Windows

Windows masaüstü için yt-dlp tabanlı, PySide6 (Qt 6) arayüzlü YouTube indirici.
Normal videolar, **Shorts** ve **oynatma listeleri (playlist)** desteklenir; arayüz ekran boyutuna otomatik uyum sağlar (HiDPI, dar pencerede ikon-only araç çubuğu).

## Özellikler

- Normal video, **Shorts** ve **oynatma listesi** indirme
- Mixed URL (`watch?v=...&list=...`) için video / playlist seçimi
- Kalite seçimi: en iyi (otomatik), 1080p / 720p / 480p / 360p, sadece ses (MP3 192k)
- Format: MP4 / WEBM / MP3
- Eşzamanlı indirme kuyruğu (varsayılan 3, ayarlardan değiştirilebilir)
- İlerleme, hız, ETA, iptal etme
- HiDPI uyumlu, ekranın %70'iyle açılan ortalanmış pencere
- Ayarlarda kalıcı indirme klasörü tercihi

## Geliştirme

Gereksinimler: Python 3.11+, ffmpeg (PATH'te veya `ffmpeg/bin/ffmpeg.exe`).

```sh
python -m pip install -r requirements.txt
python -m src.main
```

Testler:

```sh
python -m pytest
```

## Windows .exe üretimi

```bat
build.bat
```

`dist\YoutubeDownloader.exe` üretilir; ffmpeg ikilisi `--add-binary` ile gömülür. ffmpeg statik Windows build'ini önceden `ffmpeg\bin\ffmpeg.exe` konumuna koymanız gerekir.

## Branch Düzeni

Bu depodaki diğer platformlar (`ios`, `android`, `macos`) ayrı branch'lerde geliştirilir. Bu branch (`claude/youtube-downloader-windows-VUU63`) yalnızca Windows uygulamasını içerir.
