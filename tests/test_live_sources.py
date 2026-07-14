from __future__ import annotations

from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.request import Request

import pytest
from typer.testing import CliRunner

import ai_newsroom.cli as cli_module
from ai_newsroom.cli import app
from ai_newsroom.database import init_database, list_stories
from ai_newsroom.live_sources import (
    FETCH_TIMEOUT_SECONDS,
    AllowlistedRedirectHandler,
    LiveSource,
    fetch_feed,
    load_live_sources,
)
from ai_newsroom.models import F0Error
from ai_newsroom.rss import MAX_FIXTURE_BYTES, html_to_text, parse_live_feed_bytes

NOW = "2026-07-14T12:00:00Z"
runner = CliRunner()


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        final_url: str = "https://openai.com/news/rss.xml",
        content_type: str = "text/plain",
    ) -> None:
        self.body = body
        self.status = status
        self.final_url = final_url
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.body

    def geturl(self) -> str:
        return self.final_url


class FakeOpener:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.request: Request | None = None
        self.timeout: float | None = None

    def open(self, request: Request, timeout: float) -> FakeResponse:
        self.request = request
        self.timeout = timeout
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def source() -> LiveSource:
    return LiveSource(
        name="openai-news",
        feed_url="https://openai.com/news/rss.xml",
        allowed_hosts=["openai.com"],
        feed_format="rss2",
        enabled=True,
    )


def rss(link: str = "https://openai.com/item") -> bytes:
    return (
        "<rss><channel><item><title>AI launch</title>"
        f"<link>{link}</link>"
        "<description>&lt;p&gt;Useful &amp;amp; safe&lt;/p&gt;"
        "&lt;script&gt;ignore me&lt;/script&gt;</description>"
        "<pubDate>Tue, 14 Jul 2026 12:00:00 +0000</pubDate>"
        "</item></channel></rss>"
    ).encode()


def test_tracked_source_configuration_is_exact() -> None:
    sources = load_live_sources()
    assert list(sources) == ["openai-news", "google-ai", "microsoft-ai"]
    assert all(value.feed_url.startswith("https://") for value in sources.values())
    assert sources["microsoft-ai"].allowed_hosts == ["news.microsoft.com"]


def test_invalid_source_configuration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "sources.toml"
    path.write_text(
        '[[sources]]\nname="openai-news"\nfeed_url="https://127.0.0.1/x"\n'
        'allowed_hosts=["127.0.0.1"]\nfeed_format="rss2"\nenabled=true\n',
        encoding="utf-8",
    )
    with pytest.raises(F0Error) as error:
        load_live_sources(path)
    assert error.value.code == "E_SOURCE_CONFIG"


def test_fetch_checks_headers_timeout_final_host_and_weak_content_type() -> None:
    opener = FakeOpener(FakeResponse(rss()))
    assert fetch_feed(source(), opener=opener) == rss()
    assert opener.request is not None
    assert opener.request.get_header("Accept-encoding") == "identity"
    assert "AI-Newsroom-OS" in str(opener.request.get_header("User-agent"))
    assert opener.timeout == FETCH_TIMEOUT_SECONDS


def test_redirect_escape_is_rejected_before_following() -> None:
    handler = AllowlistedRedirectHandler(frozenset({"openai.com"}))
    request = Request("https://openai.com/news/rss.xml")
    with pytest.raises(F0Error) as error:
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            SimpleNamespace(),
            "https://127.0.0.1/private",
        )
    assert error.value.code == "E_LIVE_FETCH"


def test_same_host_https_redirect_is_allowed() -> None:
    handler = AllowlistedRedirectHandler(frozenset({"openai.com"}))
    redirected = handler.redirect_request(
        Request("https://openai.com/news"),
        None,
        302,
        "Found",
        Message(),
        "https://openai.com/news/rss.xml",
    )
    assert redirected is not None
    assert redirected.full_url == "https://openai.com/news/rss.xml"


def test_fetch_rejects_oversize_timeout_and_non_200() -> None:
    with pytest.raises(F0Error, match="5 MiB"):
        fetch_feed(
            source(),
            opener=FakeOpener(FakeResponse(b"<" + b"x" * MAX_FIXTURE_BYTES)),
        )
    with pytest.raises(F0Error) as timeout:
        fetch_feed(source(), opener=FakeOpener(TimeoutError()))
    assert timeout.value.code == "E_LIVE_TIMEOUT"
    with pytest.raises(F0Error, match="503"):
        fetch_feed(source(), opener=FakeOpener(FakeResponse(b"", status=503)))


def test_rss_html_is_plain_text_and_scripts_are_removed() -> None:
    snapshot = parse_live_feed_bytes(rss(), NOW, "openai-news", 20)[0]
    assert snapshot.source_name == "openai-news"
    assert snapshot.summary_text == "Useful & safe"
    assert snapshot.published_at == "2026-07-14T12:00:00Z"
    assert "<" not in snapshot.summary_text
    assert html_to_text("<style>bad</style><p>A<br>B</p>") == "A B"


def test_atom_mapping_and_iso_date() -> None:
    atom = b"""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Atom AI</title>
        <link rel="alternate" href="https://blog.google/item" />
        <summary>&lt;b&gt;Summary&lt;/b&gt;</summary>
        <updated>2026-07-14T10:30:00+03:00</updated>
      </entry>
    </feed>"""
    snapshot = parse_live_feed_bytes(atom, NOW, "google-ai", 1)[0]
    assert snapshot.title == "Atom AI"
    assert snapshot.summary_text == "Summary"
    assert snapshot.published_at == "2026-07-14T07:30:00Z"
    assert snapshot.published_at_raw is None


def test_selected_invalid_item_rejects_entire_feed() -> None:
    mixed = (
        b"<rss><channel>"
        b"<item><title>Valid</title><link>https://openai.com/valid</link></item>"
        b"<item><title>Invalid</title><link>file:///private</link></item>"
        b"</channel></rss>"
    )
    with pytest.raises(F0Error) as error:
        parse_live_feed_bytes(mixed, NOW, "openai-news", 2)
    assert error.value.code == "E_LIVE_FEED_INVALID"


def test_live_cli_attempts_all_sources_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    init_database(tmp_path)
    calls: list[str] = []

    def fake_fetch(config: Any) -> bytes:
        calls.append(str(config.name))
        return rss(f"https://{config.allowed_hosts[0]}/{config.name}")

    monkeypatch.setattr(cli_module, "fetch_feed", fake_fetch)
    command = [
        "--data-dir",
        str(tmp_path),
        "harvest",
        "live",
        "--source",
        "all",
        "--limit",
        "5",
    ]
    first = runner.invoke(app, command)
    second = runner.invoke(app, command)
    assert first.exit_code == second.exit_code == 0
    assert "created=1 unchanged=0" in first.stdout
    assert "created=0 unchanged=1" in second.stdout
    assert calls == [
        "openai-news",
        "google-ai",
        "microsoft-ai",
        "openai-news",
        "google-ai",
        "microsoft-ai",
    ]
    assert len(list_stories(tmp_path)) == 3


def test_live_cli_reports_failure_after_attempting_every_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    init_database(tmp_path)
    calls: list[str] = []

    def fake_fetch(config: Any) -> bytes:
        calls.append(str(config.name))
        if config.name == "google-ai":
            raise F0Error("E_LIVE_TIMEOUT", "timeout")
        return rss(f"https://{config.allowed_hosts[0]}/{config.name}")

    monkeypatch.setattr(cli_module, "fetch_feed", fake_fetch)
    result = runner.invoke(
        app,
        ["--data-dir", str(tmp_path), "harvest", "live", "--source", "all"],
    )
    assert result.exit_code != 0
    assert calls == ["openai-news", "google-ai", "microsoft-ai"]
    assert "source=google-ai error=E_LIVE_TIMEOUT" in result.stderr
    assert "E_LIVE_HARVEST" in result.stderr
    assert "Traceback" not in result.output


def test_live_cli_limit_range_is_enforced_before_fetch(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--data-dir",
            str(tmp_path),
            "harvest",
            "live",
            "--source",
            "openai-news",
            "--limit",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "Traceback" not in result.output
