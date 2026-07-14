from __future__ import annotations

from pathlib import Path

import pytest

from ai_newsroom.models import F0Error
from ai_newsroom.rss import MAX_FIXTURE_BYTES, parse_rss_bytes, read_rss_fixture

NOW = "2026-07-14T12:00:00Z"


def feed(item: str = "") -> bytes:
    return f"<rss><channel>{item}</channel></rss>".encode()


def item(**fields: str) -> str:
    body = "".join(f"<{key}>{value}</{key}>" for key, value in fields.items())
    return f"<item>{body}</item>"


def test_official_fixture_and_bom() -> None:
    path = Path("tests/fixtures/feeds/sample.xml")
    expected = read_rss_fixture(path, NOW)[0]
    actual = parse_rss_bytes(b"\xef\xbb\xbf" + path.read_bytes(), NOW)[0]
    assert actual == expected
    assert actual.id == "src_58343a9a5ffae3037a3f73bf"
    assert actual.canonical_url == "https://example.com/news"


def test_description_precedes_summary_and_encoded_markup_is_text() -> None:
    data = feed(
        item(
            title="AI",
            link="https://example.com",
            description="&lt;b&gt;AI&lt;/b&gt;",
            summary="ignored",
        )
    )
    assert parse_rss_bytes(data, NOW)[0].summary_text == "<b>AI</b>"


@pytest.mark.parametrize(
    "data",
    [
        b"\xff",
        b'<?xml version="1.0" encoding="windows-1251"?><rss><channel/></rss>',
        b"<feed/>",
        b"<rss><channel/><channel/></rss>",
        b"<!DOCTYPE rss><rss><channel/></rss>",
        b"<!ENTITY x 'y'><rss><channel/></rss>",
        b"<rss>",
        feed(item(title="", link="https://example.com")),
        feed("<item><title>A</title><title>B</title><link>https://example.com</link></item>"),
        feed(item(title="A", link="file:///tmp/x")),
    ],
)
def test_invalid_fixtures(data: bytes) -> None:
    with pytest.raises(F0Error) as error:
        parse_rss_bytes(data, NOW)
    assert error.value.code == "E_FIXTURE_INVALID"


def test_empty_and_item_limit() -> None:
    assert parse_rss_bytes(feed(), NOW) == []
    valid = item(title="A", link="https://example.com")
    assert len(parse_rss_bytes(feed(valid * 500), NOW)) == 500
    with pytest.raises(F0Error):
        parse_rss_bytes(feed(valid * 501), NOW)


def test_size_limit_and_non_file(tmp_path: Path) -> None:
    oversized = tmp_path / "large.xml"
    oversized.write_bytes(b" " * (MAX_FIXTURE_BYTES + 1))
    with pytest.raises(F0Error):
        read_rss_fixture(oversized, NOW)
    with pytest.raises(F0Error):
        read_rss_fixture(tmp_path, NOW)
