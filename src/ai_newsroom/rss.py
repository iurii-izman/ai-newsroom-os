from __future__ import annotations

import re
import xml.etree.ElementTree as ET
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
