"""Playlist expansion via yt-dlp's flat extraction."""

from __future__ import annotations

from dataclasses import dataclass

import yt_dlp


@dataclass(frozen=True)
class PlaylistEntry:
    id: str
    title: str
    duration: int  # seconds, may be 0 if unknown in flat mode
    url: str
    thumbnail_url: str | None


@dataclass(frozen=True)
class PlaylistInfo:
    id: str
    title: str
    uploader: str | None
    entries: tuple[PlaylistEntry, ...]

    @property
    def total_duration(self) -> int:
        return sum(e.duration for e in self.entries)


_FLAT_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extract_flat": True,
}


def fetch(url: str) -> PlaylistInfo:
    """Blocking playlist metadata fetch. Run from a worker thread."""
    with yt_dlp.YoutubeDL(_FLAT_OPTS) as ydl:
        data = ydl.extract_info(url, download=False)
    return _from_dict(data)


def _from_dict(data: dict) -> PlaylistInfo:
    raw_entries = data.get("entries") or []
    entries: list[PlaylistEntry] = []
    for entry in raw_entries:
        if not entry:
            continue
        vid = str(entry.get("id") or "")
        if not vid:
            continue
        thumb = entry.get("thumbnail")
        if not thumb and entry.get("thumbnails"):
            thumb = entry["thumbnails"][-1].get("url")
        entries.append(
            PlaylistEntry(
                id=vid,
                title=str(entry.get("title") or "Untitled"),
                duration=int(entry.get("duration") or 0),
                url=str(entry.get("url") or f"https://www.youtube.com/watch?v={vid}"),
                thumbnail_url=thumb,
            )
        )
    return PlaylistInfo(
        id=str(data.get("id") or ""),
        title=str(data.get("title") or "Playlist"),
        uploader=data.get("uploader"),
        entries=tuple(entries),
    )
