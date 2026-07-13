from __future__ import annotations

import pytest

from ai_newsroom.models import F0Error
from ai_newsroom.normalization import (
    canonical_json,
    canonicalize_url,
    claim_id,
    claim_text,
    content_hash,
    normalize_date,
    normalize_summary,
    normalize_title,
    package_identity,
    package_input_json,
    source_id,
    story_id,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Новый AI-релиз  ", "Новый AI-релиз"),
        ("Cafe\u0301", "Café"),
        ("  Новый\t  AI\n релиз  ", "Новый AI релиз"),
    ],
)
def test_title_vectors(value: str, expected: str) -> None:
    assert normalize_title(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("строка 1\r\nстрока 2\rстрока 3", "строка 1\nстрока 2\nстрока 3"),
        ("  first  \n second\tvalue  ", "first  \n second\tvalue"),
        ("<b>AI</b>", "<b>AI</b>"),
    ],
)
def test_summary_vectors(value: str, expected: str) -> None:
    assert normalize_summary(value) == expected


@pytest.mark.parametrize("value", ["bad\x00title", "bad\x0bsummary", "bad\x7ftext"])
def test_forbidden_controls(value: str) -> None:
    with pytest.raises(F0Error, match="control"):
        normalize_summary(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, (None, None)),
        ("Mon, 13 Jul 2026 15:04:05 +0300", ("2026-07-13T12:04:05Z", None)),
        ("Mon, 13 Jul 2026 15:04:05", (None, "Mon, 13 Jul 2026 15:04:05")),
        ("  not-a-date  ", (None, "not-a-date")),
    ],
)
def test_date_vectors(value: str | None, expected: tuple[str | None, str | None]) -> None:
    assert normalize_date(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" HTTPS://Example.COM/News ", "https://example.com/News"),
        ("http://Example.com:80", "http://example.com/"),
        ("https://Example.com:443/a", "https://example.com/a"),
        ("https://Example.com:8443/a", "https://example.com:8443/a"),
        ("https://example.com/a#part", "https://example.com/a"),
        ("https://example.com/?a=1&a=2", "https://example.com/?a=1&a=2"),
        ("https://example.com/?a=&b", "https://example.com/?a=&b="),
        (
            "https://example.com/?A=1&UtM_Source=x&b=2&FBCLID=y&GCLID=z",
            "https://example.com/?A=1&b=2",
        ),
        ("https://example.com/?b=2&a=1", "https://example.com/?b=2&a=1"),
        ("https://example.com/?q=a%20b&x=%2f", "https://example.com/?q=a+b&x=%2F"),
        ("https://пример.рф/путь", "https://xn--e1afmkfd.xn--p1ai/путь"),
        ("http://[2001:DB8::1]:80/a", "http://[2001:db8::1]/a"),
    ],
)
def test_url_vectors(value: str, expected: str) -> None:
    assert canonicalize_url(value)[1] == expected


@pytest.mark.parametrize(
    "value", ["https://user:pass@example.com/a", "https://example.com:99999/a", "ftp://x/a"]
)
def test_invalid_url_vectors(value: str) -> None:
    with pytest.raises(F0Error) as error:
        canonicalize_url(value)
    assert error.value.code == "E_FIXTURE_INVALID"


def test_independent_reference_vector() -> None:
    item_json = canonical_json(
        {
            "published_at": None,
            "published_at_raw": "2026-07-13 10:00",
            "summary_text": "Кратко",
            "title": "Тест AI",
        }
    )
    assert item_json == (
        '{"published_at":null,"published_at_raw":"2026-07-13 10:00",'
        '"summary_text":"Кратко","title":"Тест AI"}'
    )
    digest = content_hash("Тест AI", "Кратко", None, "2026-07-13 10:00")
    assert digest == "e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d"
    source = source_id("https://example.com/news", digest)
    assert source == "src_58343a9a5ffae3037a3f73bf"
    story = story_id(source)
    assert story == "story_55c2bc7f60628d20cb9acd4c"
    text = claim_text("Тест AI")
    assert text == "RSS item reports: Тест AI"
    assert claim_id(source, text) == "claim_11806810946d69ba4de2ccd4"
    package_input = package_input_json(story, [{"id": source, "content_hash": digest}])
    assert package_input == (
        '{"generator_name":"mock","generator_version":"mock-v1","schema_version":1,'
        '"sources":[{"content_hash":"e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa'
        '43b5eacbbbadbc7d","id":"src_58343a9a5ffae3037a3f73bf"}],'
        '"story_id":"story_55c2bc7f60628d20cb9acd4c"}'
    )
    fingerprint, package = package_identity(story, [{"id": source, "content_hash": digest}])
    assert fingerprint == "bd9e982b780c713eaad078c3129e6ddebec56fcc6b5cba0bf951547ae31fda8f"
    assert package == "pkg_17e9b7502f7bc00db437b993"
