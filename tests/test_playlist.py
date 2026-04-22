from src.core.playlist import _from_dict


def test_from_dict_filters_empty_entries():
    raw = {
        "id": "PL_test",
        "title": "My Playlist",
        "uploader": "Channel",
        "entries": [
            {
                "id": "vid1",
                "title": "First Video",
                "duration": 120,
                "url": "https://www.youtube.com/watch?v=vid1",
                "thumbnail": "https://example.com/t1.jpg",
            },
            None,  # yt-dlp can return None for unavailable videos
            {
                "id": "vid2",
                "title": "Second Video",
                "duration": 0,
                "thumbnails": [{"url": "https://example.com/t2.jpg"}],
            },
            {"id": "", "title": "Bogus"},  # missing id should be skipped
        ],
    }
    info = _from_dict(raw)
    assert info.id == "PL_test"
    assert info.title == "My Playlist"
    assert info.uploader == "Channel"
    assert len(info.entries) == 2
    first, second = info.entries
    assert first.id == "vid1"
    assert first.duration == 120
    assert first.thumbnail_url == "https://example.com/t1.jpg"
    assert second.id == "vid2"
    assert second.thumbnail_url == "https://example.com/t2.jpg"
    # url falls back to constructed watch URL when missing
    assert second.url == "https://www.youtube.com/watch?v=vid2"
    assert info.total_duration == 120


def test_from_dict_handles_missing_metadata():
    raw = {"entries": []}
    info = _from_dict(raw)
    assert info.title == "Playlist"
    assert info.entries == ()
    assert info.total_duration == 0
