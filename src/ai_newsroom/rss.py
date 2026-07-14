from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

from ai_newsroom.models import F0Error, SourceSnapshot
from ai_newsroom.normalization import (
    canonicalize_url,
    content_hash,
    normalize_date,
    normalize_summary,
    normalize_title,
    source_id,
)

MAX_FIXTURE_BYTES = 5 * 1024 * 1024
MAX_ITEMS = 500
MAX_LIVE_ITEMS = 2_000
ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
XML_ENCODING = re.compile(r"<\?xml[^>]*\bencoding\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)
PROHIBITED_XML = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)


def _invalid(message: str) -> F0Error:
    return F0Error("E_FIXTURE_INVALID", message)


def _element_text(element: ET.Element) -> str:
    return "".join(element.itertext())


def _selected(item: ET.Element, tag: str, *, required: bool = False) -> ET.Element | None:
    matches = [child for child in list(item) if child.tag == tag]
    if len(matches) > 1 or (required and len(matches) != 1):
        raise _invalid(f"fixture item has an invalid {tag} field")
    return matches[0] if matches else None


def parse_rss_bytes(data: bytes, discovered_at: str) -> list[SourceSnapshot]:
    if len(data) > MAX_FIXTURE_BYTES:
        raise _invalid("fixture exceeds 5 MiB")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _invalid("fixture is not strict UTF-8") from None
    declaration = XML_ENCODING.search(text)
    if declaration and declaration.group(2).casefold().replace("_", "-") != "utf-8":
        raise _invalid("fixture declares an unsupported encoding")
    if PROHIBITED_XML.search(text):
        raise _invalid("fixture contains a prohibited XML declaration")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        raise _invalid("fixture XML is malformed") from None
    if root.tag != "rss":
        raise _invalid("fixture root must be rss")
    channels = [child for child in list(root) if child.tag == "channel"]
    if len(channels) != 1:
        raise _invalid("fixture must contain exactly one channel")
    items = [child for child in list(channels[0]) if child.tag == "item"]
    if len(items) > MAX_ITEMS:
        raise _invalid("fixture exceeds 500 items")

    snapshots: list[SourceSnapshot] = []
    for item in items:
        title_element = _selected(item, "title", required=True)
        link_element = _selected(item, "link", required=True)
        description_element = _selected(item, "description")
        summary_element = _selected(item, "summary")
        date_element = _selected(item, "pubDate")
        assert title_element is not None and link_element is not None
        title = normalize_title(_element_text(title_element))
        summary_source = description_element if description_element is not None else summary_element
        summary_text = normalize_summary(
            _element_text(summary_source) if summary_source is not None else ""
        )
        published_at, published_at_raw = normalize_date(
            _element_text(date_element) if date_element is not None else None
        )
        original_url, canonical_url = canonicalize_url(_element_text(link_element))
        digest = content_hash(title, summary_text, published_at, published_at_raw)
        snapshots.append(
            SourceSnapshot(
                id=source_id(canonical_url, digest),
                original_url=original_url,
                canonical_url=canonical_url,
                title=title,
                summary_text=summary_text,
                published_at=published_at,
                published_at_raw=published_at_raw,
                discovered_at=discovered_at,
                content_hash=digest,
            )
        )
    return snapshots


def read_rss_fixture(path: Path, discovered_at: str) -> list[SourceSnapshot]:
    try:
        if not path.is_file():
            raise _invalid("fixture path is not a regular file")
        size = path.stat().st_size
        if size > MAX_FIXTURE_BYTES:
            raise _invalid("fixture exceeds 5 MiB")
        return parse_rss_bytes(path.read_bytes(), discovered_at)
    except F0Error:
        raise
    except OSError:
        raise _invalid("fixture cannot be read") from None


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.casefold() in {"script", "style"}:
            self.ignored_depth += 1
        elif self.ignored_depth == 0 and tag.casefold() in {
            "br",
            "p",
            "div",
            "li",
            "section",
            "article",
        }:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif self.ignored_depth == 0:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self.ignored_depth == 0:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    try:
        parser.feed(value)
        parser.close()
    except (ValueError, AssertionError):
        raise F0Error("E_LIVE_FEED_INVALID", "feed item contains invalid HTML text") from None
    return " ".join("".join(parser.parts).split())


def _live_invalid(message: str) -> F0Error:
    return F0Error("E_LIVE_FEED_INVALID", message)


def _decode_live_xml(data: bytes) -> ET.Element:
    if len(data) > MAX_FIXTURE_BYTES:
        raise _live_invalid("feed exceeds 5 MiB")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _live_invalid("feed is not strict UTF-8") from None
    declaration = XML_ENCODING.search(text)
    if declaration and declaration.group(2).casefold().replace("_", "-") != "utf-8":
        raise _live_invalid("feed declares an unsupported encoding")
    if PROHIBITED_XML.search(text):
        raise _live_invalid("feed contains a prohibited XML declaration")
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        raise _live_invalid("feed XML is malformed") from None


def _optional_direct(item: ET.Element, tag: str) -> ET.Element | None:
    matches = [child for child in list(item) if child.tag == tag]
    if len(matches) > 1:
        raise _live_invalid(f"feed item has duplicate {tag} fields")
    return matches[0] if matches else None


def _required_text(item: ET.Element, tag: str) -> str:
    selected = _optional_direct(item, tag)
    if selected is None:
        raise _live_invalid(f"feed item is missing {tag}")
    return _element_text(selected)


def _snapshot_from_values(
    *,
    source_name: str,
    title_value: str,
    link_value: str,
    summary_value: str,
    date_value: str | None,
    discovered_at: str,
) -> SourceSnapshot:
    try:
        title = normalize_title(html_to_text(title_value))
        summary_text = normalize_summary(html_to_text(summary_value))
        published_at, published_at_raw = normalize_date(date_value)
        if published_at is None and published_at_raw is not None:
            try:
                parsed = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
                if parsed.tzinfo is not None and parsed.utcoffset() is not None:
                    published_at = (
                        parsed.astimezone(UTC)
                        .replace(microsecond=0)
                        .strftime("%Y-%m-%dT%H:%M:%SZ")
                    )
                    published_at_raw = None
            except ValueError:
                pass
        original_url, canonical_url = canonicalize_url(link_value)
    except F0Error as error:
        if error.code == "E_LIVE_FEED_INVALID":
            raise
        raise _live_invalid("feed item failed normalization") from None
    digest = content_hash(title, summary_text, published_at, published_at_raw)
    return SourceSnapshot(
        id=source_id(canonical_url, digest),
        original_url=original_url,
        canonical_url=canonical_url,
        title=title,
        summary_text=summary_text,
        published_at=published_at,
        published_at_raw=published_at_raw,
        discovered_at=discovered_at,
        content_hash=digest,
        source_name=source_name,
    )


def _parse_live_rss(
    root: ET.Element, source_name: str, discovered_at: str, limit: int
) -> list[SourceSnapshot]:
    channels = [child for child in list(root) if child.tag == "channel"]
    if len(channels) != 1:
        raise _live_invalid("RSS feed must contain exactly one channel")
    items = [child for child in list(channels[0]) if child.tag == "item"]
    if len(items) > MAX_LIVE_ITEMS:
        raise _live_invalid("feed exceeds 2000 items")
    snapshots: list[SourceSnapshot] = []
    for item in items[:limit]:
        description = _optional_direct(item, "description")
        summary = _optional_direct(item, "summary")
        date = _optional_direct(item, "pubDate")
        summary_element = description if description is not None else summary
        snapshots.append(
            _snapshot_from_values(
                source_name=source_name,
                title_value=_required_text(item, "title"),
                link_value=_required_text(item, "link"),
                summary_value=(
                    _element_text(summary_element) if summary_element is not None else ""
                ),
                date_value=_element_text(date) if date is not None else None,
                discovered_at=discovered_at,
            )
        )
    return snapshots


def _parse_live_atom(
    root: ET.Element, source_name: str, discovered_at: str, limit: int
) -> list[SourceSnapshot]:
    prefix = f"{{{ATOM_NAMESPACE}}}"
    entries = [child for child in list(root) if child.tag == f"{prefix}entry"]
    if len(entries) > MAX_LIVE_ITEMS:
        raise _live_invalid("feed exceeds 2000 entries")
    snapshots: list[SourceSnapshot] = []
    for entry in entries[:limit]:
        title = _optional_direct(entry, f"{prefix}title")
        if title is None:
            raise _live_invalid("Atom entry is missing title")
        links = [
            child
            for child in list(entry)
            if child.tag == f"{prefix}link" and child.attrib.get("rel", "alternate") == "alternate"
        ]
        if len(links) != 1 or not links[0].attrib.get("href"):
            raise _live_invalid("Atom entry must contain one alternate link")
        summary = _optional_direct(entry, f"{prefix}summary")
        content = _optional_direct(entry, f"{prefix}content")
        published = _optional_direct(entry, f"{prefix}published")
        updated = _optional_direct(entry, f"{prefix}updated")
        summary_element = summary if summary is not None else content
        date_element = published if published is not None else updated
        snapshots.append(
            _snapshot_from_values(
                source_name=source_name,
                title_value=_element_text(title),
                link_value=links[0].attrib["href"],
                summary_value=(
                    _element_text(summary_element) if summary_element is not None else ""
                ),
                date_value=_element_text(date_element) if date_element is not None else None,
                discovered_at=discovered_at,
            )
        )
    return snapshots


def parse_live_feed_bytes(
    data: bytes, discovered_at: str, source_name: str, limit: int
) -> list[SourceSnapshot]:
    if limit < 1 or limit > 50:
        raise _live_invalid("live item limit must be between 1 and 50")
    root = _decode_live_xml(data)
    if root.tag == "rss":
        return _parse_live_rss(root, source_name, discovered_at, limit)
    if root.tag == f"{{{ATOM_NAMESPACE}}}feed":
        return _parse_live_atom(root, source_name, discovered_at, limit)
    raise _live_invalid("feed root must be RSS 2.0 or Atom 1.0")
