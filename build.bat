@echo off
REM Build script for Windows YouTube Downloader
REM Produces a single-file .exe in dist\YoutubeDownloader.exe
REM
REM Requirements:
REM   - Python 3.11+ on PATH
REM   - ffmpeg.exe placed at ffmpeg\bin\ffmpeg.exe (download from https://www.gyan.dev/ffmpeg/builds/)

setlocal

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [2/3] Verifying ffmpeg...
if not exist "ffmpeg\bin\ffmpeg.exe" (
    echo ERROR: ffmpeg\bin\ffmpeg.exe not found.
    echo Download a static Windows build and place ffmpeg.exe there.
    goto :fail
)

echo [3/3] Building executable with PyInstaller...
pyinstaller --noconfirm --onefile --windowed ^
    --name YoutubeDownloader ^
    --add-binary "ffmpeg\bin\ffmpeg.exe;ffmpeg\bin" ^
    src\main.py
if errorlevel 1 goto :fail

echo.
echo Build complete: dist\YoutubeDownloader.exe
exit /b 0

:fail
echo.
echo Build FAILED.
exit /b 1
