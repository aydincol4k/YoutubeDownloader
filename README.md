# YouTube Downloader — Windows

**Sürüm: v1.0.0** · İkili: `YoutubeDownloader-v1.0.0.exe`

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

### Yerel (Windows makinesinde)

```bat
build.bat
```

`dist\YoutubeDownloader-v<sürüm>.exe` üretilir (ör. `YoutubeDownloader-v1.0.0.exe`). ffmpeg ikilisi `--add-binary` ile gömülür; statik Windows ffmpeg build'ini önceden `ffmpeg\bin\ffmpeg.exe` konumuna koymanız gerekir.

### Otomatik (GitHub Actions)

Repo'da `.github/workflows/build-windows.yml` workflow'u tanımlı. Tag oluşturup push ettiğinizde Windows runner'da otomatik `.exe` üretilir ve GitHub Release'e eklenir:

```sh
git tag v1.0.0
git push origin v1.0.0
```

Manuel tetikleme için Actions sekmesinden **Run workflow** seçilebilir; çıktı build artifact'i olarak indirilebilir.

> Not: `.exe` ikilisi git repo'sunda saklanmaz; GitHub Releases üzerinden dağıtılır.
