"""yt-dlp download worker exposed as a QThread with Qt signals."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yt_dlp
from PySide6.QtCore import QObject, QThread, Signal


QUALITY_CHOICES = ("best", "1080p", "720p", "480p", "360p", "audio")
FORMAT_CHOICES = ("mp4", "webm", "mp3")


@dataclass
class DownloadJob:
    url: str
    output_dir: Path
    quality: str = "best"
    container: str = "mp4"
    playlist_subdir: str | None = None  # if set, files go under output_dir / playlist_subdir
    title_hint: str | None = None  # display label until yt-dlp reports the real title


@dataclass
class Progress:
    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed: float | None = None  # bytes/sec
    eta: int | None = None
    status: str = "queued"
    filename: str | None = None
    title: str | None = None
    error: str | None = None


class _Signals(QObject):
    progress = Signal(object)  # Progress
    finished = Signal(str)  # final filepath
    failed = Signal(str)  # error message


class DownloadWorker(QThread):
    """Runs a single yt-dlp download. Emits progress / finished / failed."""

    def __init__(self, job: DownloadJob, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.job = job
        self.signals = _Signals()
        self._cancel = False
        self._final_path: str | None = None

    # Public API ----------------------------------------------------------
    def cancel(self) -> None:
        self._cancel = True

    # QThread -------------------------------------------------------------
    def run(self) -> None:  # pragma: no cover - exercised manually
        try:
            opts = self._build_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.job.url])
            if self._cancel:
                self.signals.failed.emit("Cancelled")
                return
            self.signals.finished.emit(self._final_path or "")
        except _CancelledError:
            self.signals.failed.emit("Cancelled")
        except Exception as exc:  # noqa: BLE001 - surface yt-dlp errors to UI
            self.signals.failed.emit(str(exc))

    # Internals -----------------------------------------------------------
    def _build_opts(self) -> dict:
        target_dir = self.job.output_dir
        if self.job.playlist_subdir:
            target_dir = target_dir / _sanitize(self.job.playlist_subdir)
        target_dir.mkdir(parents=True, exist_ok=True)

        opts: dict = {
            "outtmpl": str(target_dir / "%(title)s [%(id)s].%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            "progress_hooks": [self._on_progress],
            "postprocessor_hooks": [self._on_postprocess],
            "ffmpeg_location": _bundled_ffmpeg_dir(),
        }
        opts.update(_format_opts(self.job.quality, self.job.container))
        return opts

    def _on_progress(self, d: dict) -> None:
        if self._cancel:
            raise _CancelledError()
        status = d.get("status", "downloading")
        progress = Progress(status=status)
        progress.title = (d.get("info_dict") or {}).get("title")
        progress.filename = d.get("filename")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            progress.downloaded_bytes = int(downloaded)
            if total:
                progress.total_bytes = int(total)
                progress.percent = min(100.0, downloaded * 100.0 / total)
            progress.speed = d.get("speed")
            progress.eta = d.get("eta")
        elif status == "finished":
            progress.percent = 100.0
            self._final_path = d.get("filename") or self._final_path
        self.signals.progress.emit(progress)

    def _on_postprocess(self, d: dict) -> None:
        if d.get("status") == "finished":
            info = d.get("info_dict") or {}
            self._final_path = info.get("filepath") or self._final_path


class _CancelledError(Exception):
    pass


def _format_opts(quality: str, container: str) -> dict:
    quality = quality.lower()
    container = container.lower()
    if quality == "audio" or container == "mp3":
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    if quality == "best":
        fmt = "bestvideo*+bestaudio/best"
    else:
        height = quality.rstrip("p")
        fmt = f"bv*[height<={height}]+ba/b[height<={height}]"
    return {"format": fmt, "merge_output_format": container}


_INVALID_FS = '<>:"/\\|?*'


def _sanitize(name: str) -> str:
    return "".join("_" if c in _INVALID_FS else c for c in name).strip().rstrip(".") or "playlist"


def _bundled_ffmpeg_dir() -> str | None:
    """Return PyInstaller-bundled ffmpeg dir if present, else let yt-dlp use PATH."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidate = Path(base) / "ffmpeg" / "bin"
        if candidate.exists():
            return str(candidate)
    local = Path(os.getcwd()) / "ffmpeg" / "bin"
    if local.exists():
        return str(local)
    return None
