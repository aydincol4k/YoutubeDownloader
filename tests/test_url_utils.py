from src.core.url_utils import is_supported, parse


def test_classify_regular_video():
    p = parse("https://www.youtube.com/watch?v=abcdef12345")
    assert p.kind == "video"
    assert p.video_id == "abcdef12345"
    assert p.playlist_id is None
    assert p.canonical == "https://www.youtube.com/watch?v=abcdef12345"


def test_classify_shorts_normalizes_to_watch():
    p = parse("https://youtube.com/shorts/XYZ123abcde?si=tracking")
    assert p.kind == "shorts"
    assert p.video_id == "XYZ123abcde"
    assert p.canonical == "https://www.youtube.com/watch?v=XYZ123abcde"


def test_classify_youtu_be_shortlink():
    p = parse("https://youtu.be/abc12345678?si=foo")
    assert p.kind == "video"
    assert p.video_id == "abc12345678"
    assert p.canonical == "https://www.youtube.com/watch?v=abc12345678"


def test_classify_playlist_only():
    p = parse("https://www.youtube.com/playlist?list=PL12345")
    assert p.kind == "playlist"
    assert p.playlist_id == "PL12345"
    assert p.video_id is None
    assert "list=PL12345" in p.canonical


def test_classify_mixed_video_and_playlist():
    p = parse("https://www.youtube.com/watch?v=abc12345678&list=PL999")
    assert p.kind == "mixed"
    assert p.video_id == "abc12345678"
    assert p.playlist_id == "PL999"
    assert "v=abc12345678" in p.canonical
    assert "list=PL999" in p.canonical


def test_classify_mobile_host():
    p = parse("https://m.youtube.com/watch?v=foo12345678")
    assert p.kind == "video"
    assert p.video_id == "foo12345678"


def test_classify_embed():
    p = parse("https://www.youtube.com/embed/abc12345678")
    assert p.kind == "video"
    assert p.video_id == "abc12345678"


def test_unknown_url():
    p = parse("https://example.com/video/123")
    assert p.kind == "unknown"
    assert not is_supported("https://example.com/video/123")


def test_empty_url():
    p = parse("   ")
    assert p.kind == "unknown"


def test_is_supported_true_for_youtube():
    assert is_supported("https://www.youtube.com/watch?v=abc12345678")
    assert is_supported("https://youtu.be/abc12345678")
    assert is_supported("https://www.youtube.com/shorts/abc12345678")
    assert is_supported("https://www.youtube.com/playlist?list=PL1")
