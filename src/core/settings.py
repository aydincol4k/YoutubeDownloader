"""Persistent user preferences via QSettings."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings


_ORG = "YoutubeDownloader"
_APP = "YoutubeDownloader"


def _store() -> QSettings:
    return QSettings(_ORG, _APP)


def default_download_dir() -> Path:
    return Path.home() / "Downloads" / "YouTube"


def download_dir() -> Path:
    raw = _store().value("download_dir", str(default_download_dir()))
    return Path(str(raw))


def set_download_dir(path: Path) -> None:
    _store().setValue("download_dir", str(path))


def default_quality() -> str:
    return str(_store().value("default_quality", "best"))


def set_default_quality(quality: str) -> None:
    _store().setValue("default_quality", quality)


def default_format() -> str:
    return str(_store().value("default_format", "mp4"))


def set_default_format(fmt: str) -> None:
    _store().setValue("default_format", fmt)


def concurrent_downloads() -> int:
    try:
        return int(_store().value("concurrent_downloads", 3))
    except (TypeError, ValueError):
        return 3


def set_concurrent_downloads(n: int) -> None:
    _store().setValue("concurrent_downloads", max(1, min(10, int(n))))
