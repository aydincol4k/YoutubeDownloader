"""URL parsing and classification for YouTube links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

UrlKind = Literal["video", "shorts", "playlist", "mixed", "unknown"]

_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


@dataclass(frozen=True)
class ParsedUrl:
    kind: UrlKind
    video_id: str | None
    playlist_id: str | None
    canonical: str


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _is_youtube(url: str) -> bool:
    return _host(url) in _HOSTS


def parse(url: str) -> ParsedUrl:
    """Classify a YouTube URL and return a canonical form.

    - /shorts/<id> is rewritten to /watch?v=<id>
    - youtu.be/<id> is rewritten to /watch?v=<id>
    - tracking params (si, pp, feature, t for non-watch) are stripped
    - if both video id and list id present, kind is "mixed"
    - bare /playlist?list=... is "playlist"
    """
    url = url.strip()
    if not url or not _is_youtube(url):
        return ParsedUrl("unknown", None, None, url)

    parsed = urlparse(url)
    path = parsed.path or "/"
    query = parse_qs(parsed.query)

    video_id: str | None = None
    playlist_id: str | None = query.get("list", [None])[0]
    is_shorts = False

    if parsed.netloc.lower() == "youtu.be":
        video_id = path.lstrip("/").split("/", 1)[0] or None
    elif path.startswith("/shorts/"):
        video_id = path.split("/shorts/", 1)[1].split("/", 1)[0] or None
        is_shorts = True
    elif path == "/watch":
        video_id = query.get("v", [None])[0]
    elif path == "/playlist":
        # playlist-only URL
        pass
    elif path.startswith("/embed/"):
        video_id = path.split("/embed/", 1)[1].split("/", 1)[0] or None

    if video_id and playlist_id:
        kind: UrlKind = "mixed"
    elif video_id:
        kind = "shorts" if is_shorts else "video"
    elif playlist_id:
        kind = "playlist"
    else:
        kind = "unknown"

    canonical = _canonicalize(video_id, playlist_id, kind)
    return ParsedUrl(kind=kind, video_id=video_id, playlist_id=playlist_id, canonical=canonical)


def _canonicalize(video_id: str | None, playlist_id: str | None, kind: UrlKind) -> str:
    base = "https://www.youtube.com"
    if kind == "playlist":
        return f"{base}/playlist?{urlencode({'list': playlist_id})}"
    if video_id and playlist_id:
        return f"{base}/watch?{urlencode({'v': video_id, 'list': playlist_id})}"
    if video_id:
        return f"{base}/watch?{urlencode({'v': video_id})}"
    return urlunparse(("https", "www.youtube.com", "/", "", "", ""))


def is_supported(url: str) -> bool:
    return parse(url).kind != "unknown"
