from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import unicodedata
from datetime import UTC
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ai_newsroom.models import F0Error

FORBIDDEN_CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TITLE_WHITESPACE = re.compile(r"\s+")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _reject_controls(value: str) -> None:
    if FORBIDDEN_CONTROLS.search(value):
        raise F0Error("E_FIXTURE_INVALID", "fixture contains a forbidden control character")


def normalize_title(value: str) -> str:
    value = normalize_newlines(value)
    _reject_controls(value)
    normalized = unicodedata.normalize("NFC", TITLE_WHITESPACE.sub(" ", value).strip())
    if not normalized or len(normalized) > 500:
        raise F0Error("E_FIXTURE_INVALID", "fixture title is empty or exceeds 500 characters")
    return normalized


def normalize_summary(value: str) -> str:
    value = normalize_newlines(value)
    _reject_controls(value)
    normalized = unicodedata.normalize("NFC", value.strip())
    if len(normalized) > 10_000:
        raise F0Error("E_FIXTURE_INVALID", "fixture summary exceeds 10000 characters")
    return normalized


def normalize_date(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    raw = unicodedata.normalize("NFC", normalize_newlines(value).strip())
    if not raw:
        return None, None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        return None, raw
    if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
        return None, raw
    normalized = parsed.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    return normalized, None


def canonicalize_url(value: str) -> tuple[str, str]:
    original = value.strip()
    if not original or len(original) > 4096:
        raise F0Error("E_FIXTURE_INVALID", "fixture URL is empty or too long")
    try:
        parts = urlsplit(original)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ValueError
        if parts.username is not None or parts.password is not None:
            raise ValueError
        port = parts.port
        hostname = parts.hostname
        try:
            is_ipv6 = isinstance(ipaddress.ip_address(hostname), ipaddress.IPv6Address)
        except ValueError:
            is_ipv6 = False
        if is_ipv6:
            host = f"[{hostname.lower()}]"
        else:
            host = hostname.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        raise F0Error("E_FIXTURE_INVALID", "fixture URL is invalid") from None

    scheme = parts.scheme.lower()
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = host if port is None or default_port else f"{host}:{port}"
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    kept = [
        (key, item_value)
        for key, item_value in pairs
        if not (key.casefold().startswith("utm_") or key.casefold() in {"fbclid", "gclid"})
    ]
    canonical = urlunsplit((scheme, netloc, parts.path or "/", urlencode(kept), ""))
    return original, canonical


def content_hash(
    title: str,
    summary_text: str,
    published_at: str | None,
    published_at_raw: str | None,
) -> str:
    item = {
        "title": title,
        "summary_text": summary_text,
        "published_at": published_at,
        "published_at_raw": published_at_raw,
    }
    return sha256_text(canonical_json(item))


def source_id(canonical_url: str, item_content_hash: str) -> str:
    return "src_" + sha256_text(f"{canonical_url}\n{item_content_hash}")[:24]


def story_id(source_snapshot_id: str) -> str:
    return "story_" + sha256_text(source_snapshot_id)[:24]


def claim_text(title: str) -> str:
    return f"RSS item reports: {title}"


def claim_id(source_snapshot_id: str, text: str) -> str:
    preimage = f"{source_snapshot_id}\n{text}\nVENDOR_CLAIM\nUNVERIFIED"
    return "claim_" + sha256_text(preimage)[:24]


def package_input_json(story_snapshot_id: str, sources: list[dict[str, str]]) -> str:
    value = {
        "schema_version": 1,
        "generator_name": "mock",
        "generator_version": "mock-v1",
        "story_id": story_snapshot_id,
        "sources": sorted(sources, key=lambda source: source["id"]),
    }
    return canonical_json(value)


def package_identity(story_snapshot_id: str, sources: list[dict[str, str]]) -> tuple[str, str]:
    fingerprint = sha256_text(package_input_json(story_snapshot_id, sources))
    package_snapshot_id = "pkg_" + sha256_text(f"story-package\n{fingerprint}")[:24]
    return fingerprint, package_snapshot_id


def deepseek_package_identity(
    story_snapshot_id: str,
    source: dict[str, str | None],
    prompt_sha256: str,
) -> tuple[str, str]:
    value = {
        "schema_version": 2,
        "generator": {
            "provider": "deepseek",
            "model": "deepseek-v4-flash",
            "api_format": "openai-chat-completions",
            "thinking": "disabled",
            "temperature": 0.2,
        },
        "prompt_version": "f1f2-story-package-v1",
        "prompt_sha256": prompt_sha256,
        "request": {
            "max_tokens": 3000,
            "response_format": {"type": "json_object"},
            "stream": False,
        },
        "story_id": story_snapshot_id,
        "source": source,
    }
    fingerprint = sha256_text(canonical_json(value))
    package_snapshot_id = "pkg_" + sha256_text(
        f"deepseek-story-package\n{fingerprint}"
    )[:24]
    return fingerprint, package_snapshot_id
