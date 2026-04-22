from src.core.video_info import _from_dict


def test_from_dict_landscape_video():
    raw = {
        "id": "abc",
        "title": "Landscape Clip",
        "duration": 300,
        "thumbnail": "https://example.com/thumb.jpg",
        "uploader": "Author",
        "width": 1920,
        "height": 1080,
        "webpage_url": "https://www.youtube.com/watch?v=abc",
    }
    info = _from_dict(raw)
    assert info.id == "abc"
    assert info.title == "Landscape Clip"
    assert info.duration == 300
    assert info.thumbnail_url == "https://example.com/thumb.jpg"
    assert info.uploader == "Author"
    assert info.is_short is False
    assert info.is_vertical is False


def test_from_dict_detects_shorts_url():
    raw = {
        "id": "xyz",
        "title": "A Short",
        "duration": 30,
        "thumbnails": [{"url": "https://example.com/s.jpg"}],
        "width": 1080,
        "height": 1920,
        "was_live": False,
        "webpage_url": "https://www.youtube.com/shorts/xyz",
    }
    info = _from_dict(raw)
    assert info.is_short is True
    assert info.is_vertical is True
    assert info.thumbnail_url == "https://example.com/s.jpg"


def test_from_dict_vertical_under_60s_treated_as_short():
    raw = {
        "id": "v1",
        "title": "Vertical 30s",
        "duration": 30,
        "width": 720,
        "height": 1280,
        "was_live": False,
        "webpage_url": "https://www.youtube.com/watch?v=v1",
    }
    info = _from_dict(raw)
    assert info.is_short is True


def test_from_dict_defaults_when_fields_missing():
    info = _from_dict({})
    assert info.id == ""
    assert info.title == "Untitled"
    assert info.duration == 0
    assert info.thumbnail_url is None
