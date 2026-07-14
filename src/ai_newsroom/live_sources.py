from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai_newsroom.models import F0Error
from ai_newsroom.rss import MAX_FIXTURE_BYTES

SOURCE_NAMES: Final = ("openai-news", "google-ai", "microsoft-ai")
APPROVED_HOSTS: Final = {
    "openai-news": frozenset({"openai.com"}),
    "google-ai": frozenset({"blog.google"}),
    "microsoft-ai": frozenset({"news.microsoft.com"}),
}
CONFIG_PATH: Final = Path(__file__).resolve().parents[2] / "config" / "live_sources.toml"
FETCH_TIMEOUT_SECONDS: Final = 20.0
USER_AGENT: Final = (
    "AI-Newsroom-OS/0.1 (+https://github.com/iurii-izman/ai-newsroom-os)"
)


class LiveSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    name: str
    feed_url: str
    allowed_hosts: list[str] = Field(min_length=1, max_length=3)
    feed_format: str
    enabled: bool


def _validate_destination(url: str, allowed_hosts: frozenset[str]) -> None:
    try:
        parts = urlsplit(url)
        hostname = parts.hostname.casefold() if parts.hostname else None
        if (
            parts.scheme.casefold() != "https"
            or hostname is None
            or hostname not in allowed_hosts
            or parts.username is not None
            or parts.password is not None
            or parts.port not in {None, 443}
        ):
            raise ValueError
    except ValueError:
        raise F0Error(
            "E_LIVE_FETCH", "feed destination is outside its HTTPS host allowlist"
        ) from None


def load_live_sources(path: Path = CONFIG_PATH) -> dict[str, LiveSource]:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        values = raw.get("sources")
        if not isinstance(values, list):
            raise ValueError
        parsed = [LiveSource.model_validate(value) for value in values]
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, ValidationError, ValueError, TypeError):
        raise F0Error("E_SOURCE_CONFIG", "tracked live-source configuration is invalid") from None

    sources = {source.name: source for source in parsed}
    if len(sources) != len(parsed) or set(sources) != set(SOURCE_NAMES):
        raise F0Error("E_SOURCE_CONFIG", "tracked source set must contain exactly three names")
    for source in sources.values():
        allowed = frozenset(host.casefold() for host in source.allowed_hosts)
        if (
            not source.enabled
            or source.feed_format not in {"rss2", "atom1"}
            or len(allowed) != len(source.allowed_hosts)
            or any(host != host.casefold() or not host for host in source.allowed_hosts)
            or allowed != APPROVED_HOSTS[source.name]
        ):
            raise F0Error("E_SOURCE_CONFIG", "tracked live-source entry is invalid")
        try:
            _validate_destination(source.feed_url, allowed)
        except F0Error:
            raise F0Error(
                "E_SOURCE_CONFIG", "tracked live-source destination is invalid"
            ) from None
    return sources


class AllowlistedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: frozenset[str]) -> None:
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Request | None:
        _validate_destination(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_feed(source: LiveSource, *, opener: Any | None = None) -> bytes:
    allowed = frozenset(host.casefold() for host in source.allowed_hosts)
    _validate_destination(source.feed_url, allowed)
    selected_opener = opener or build_opener(AllowlistedRedirectHandler(allowed))
    request = Request(
        source.feed_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    try:
        with selected_opener.open(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            status = int(response.status)
            final_url = str(response.geturl())
            content_type = str(response.headers.get("Content-Type", "")).casefold()
            data = bytes(response.read(MAX_FIXTURE_BYTES + 1))
    except HTTPError as error:
        raise F0Error("E_LIVE_FETCH", f"feed returned HTTP {error.code}") from None
    except (TimeoutError, URLError) as error:
        reason = getattr(error, "reason", None)
        if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError):
            raise F0Error("E_LIVE_TIMEOUT", "feed request timed out") from None
        raise F0Error("E_LIVE_FETCH", "feed request failed") from None
    except OSError:
        raise F0Error("E_LIVE_FETCH", "feed request failed") from None

    _validate_destination(final_url, allowed)
    if status != 200:
        raise F0Error("E_LIVE_FETCH", f"feed returned HTTP {status}")
    if len(data) > MAX_FIXTURE_BYTES:
        raise F0Error("E_LIVE_FETCH", "feed response exceeds 5 MiB")
    xml_content_type = any(
        marker in content_type for marker in ("xml", "rss", "atom")
    )
    if not xml_content_type and not data.lstrip().startswith((b"<", b"\xef\xbb\xbf<")):
        raise F0Error("E_LIVE_FETCH", "feed response is not XML")
    return data
