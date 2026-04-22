"""Fetch video metadata using yt-dlp without downloading."""

from __future__ import annotations

from dataclasses import dataclass

import yt_dlp


@dataclass(frozen=True)
class VideoInfo:
    id: str
    title: str
    duration: int  # seconds
    thumbnail_url: str | None
    uploader: str | None
    is_short: bool
    width: int | None
    height: int | None

    @property
    def is_vertical(self) -> bool:
        if self.width and self.height:
            return self.height > self.width
        return self.is_short


_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
}


def fetch(url: str) -> VideoInfo:
    """Blocking metadata fetch. Run from a worker thread."""
    with yt_dlp.YoutubeDL(_BASE_OPTS) as ydl:
        data = ydl.extract_info(url, download=False)
    return _from_dict(data)


def _from_dict(data: dict) -> VideoInfo:
    width = data.get("width")
    height = data.get("height")
    thumb = data.get("thumbnail")
    if not thumb and data.get("thumbnails"):
        thumb = data["thumbnails"][-1].get("url")
    is_short = bool(
        data.get("was_live") is False
        and (
            "/shorts/" in (data.get("webpage_url") or "")
            or (height and width and height > width and (data.get("duration") or 0) <= 60)
        )
    )
    return VideoInfo(
        id=str(data.get("id") or ""),
        title=str(data.get("title") or "Untitled"),
        duration=int(data.get("duration") or 0),
        thumbnail_url=thumb,
        uploader=data.get("uploader"),
        is_short=is_short,
        width=width,
        height=height,
    )
