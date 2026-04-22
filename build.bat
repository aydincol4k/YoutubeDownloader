@echo off
REM Build script for Windows YouTube Downloader
REM Produces a versioned single-file .exe in dist\YoutubeDownloader-v<version>.exe
REM
REM Requirements:
REM   - Python 3.11+ on PATH
REM   - ffmpeg.exe placed at ffmpeg\bin\ffmpeg.exe (download from https://www.gyan.dev/ffmpeg/builds/)

setlocal

echo [1/4] Reading version...
for /f "tokens=2 delims== " %%v in ('findstr /R "^__version__" src\__init__.py') do set VERSION=%%~v
set VERSION=%VERSION:"=%
if "%VERSION%"=="" (
    echo ERROR: could not read version from src\__init__.py
    goto :fail
)
set EXE_NAME=YoutubeDownloader-v%VERSION%
echo Building %EXE_NAME%.exe

echo [2/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [3/4] Verifying ffmpeg...
if not exist "ffmpeg\bin\ffmpeg.exe" (
    echo ERROR: ffmpeg\bin\ffmpeg.exe not found.
    echo Download a static Windows build and place ffmpeg.exe there.
    goto :fail
)

echo [4/4] Building executable with PyInstaller...
pyinstaller --noconfirm --onefile --windowed ^
    --name %EXE_NAME% ^
    --add-binary "ffmpeg\bin\ffmpeg.exe;ffmpeg\bin" ^
    src\main.py
if errorlevel 1 goto :fail

echo.
echo Build complete: dist\%EXE_NAME%.exe
exit /b 0

:fail
echo.
echo Build FAILED.
exit /b 1
