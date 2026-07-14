from __future__ import annotations

import json
import os
from contextlib import suppress
from enum import StrEnum
from pathlib import Path

from ai_newsroom.models import F0Error, StoryPackagePayload
from ai_newsroom.package_builder import load_validated_package


class ExportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    ALL = "all"


def render_json(payload: StoryPackagePayload) -> bytes:
    value = payload.model_dump(mode="json")
    value["sources"] = sorted(value["sources"], key=lambda source: source["id"])
    value["claims"] = sorted(value["claims"], key=lambda claim: claim["id"])
    for claim in value["claims"]:
        claim["source_ids"] = sorted(claim["source_ids"])
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _escape_markdown(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for character in "`*_{}[]<>()#+-.!|":
        escaped = escaped.replace(character, f"\\{character}")
    return escaped


def _shown(value: str | None) -> str:
    return "null" if value is None else _escape_markdown(value)


def render_markdown(payload: StoryPackagePayload) -> bytes:
    source = payload.sources[0]
    claim = payload.claims[0]
    lines = [
        "# Story Package",
        "",
        "Generation mode: MOCK",
        "Publishable: false",
        "Warning: Demo-only package; no human verification; do not publish.",
        "",
        f"Package ID: `{payload.package_id}`",
        f"Story ID: `{payload.story.id}`",
        f"Story title: {_escape_markdown(payload.story.title)}",
        "",
        "## Source",
        "",
        f"Source ID: `{source.id}`",
        f"Canonical URL: {_escape_markdown(source.canonical_url)}",
        f"Content hash: `{source.content_hash}`",
        f"Published at: {_shown(source.published_at)}",
    ]
    if source.published_at_raw is not None:
        lines.append(f"Published at raw: {_escape_markdown(source.published_at_raw)}")
    lines.extend(
        [
            f"Title: {_escape_markdown(source.title)}",
            "",
            "## Claim",
            "",
            f"Claim ID: `{claim.id}`",
            f"Text: {_escape_markdown(claim.text)}",
            f"Type: {claim.type}",
            f"Status: {claim.status}",
            f"Qualifier: {_escape_markdown(claim.qualifier)}",
            f"Source IDs: {', '.join(f'`{source_id}`' for source_id in claim.source_ids)}",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _write_temp(path: Path, content: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def export_package(
    data_dir: Path,
    requested_story_id: str,
    export_format: ExportFormat,
    *,
    force: bool = False,
) -> tuple[int, int, list[Path]]:
    _snapshot, payload = load_validated_package(data_dir, requested_story_id)
    output_dir = data_dir / "exports" / payload.story.id
    rendered = {
        "json": render_json(payload),
        "markdown": render_markdown(payload),
    }
    requested = ["json", "markdown"] if export_format is ExportFormat.ALL else [export_format.value]
    filenames = {"json": "story-package.json", "markdown": "story-package.md"}
    paths = {kind: output_dir / filenames[kind] for kind in requested}
    existing: dict[str, bytes | None] = {}
    try:
        for kind, path in paths.items():
            existing[kind] = path.read_bytes() if path.exists() else None
    except OSError:
        raise F0Error("E_EXPORT_CONFLICT", "existing export cannot be read safely") from None

    identical = {kind: existing[kind] == rendered[kind] for kind in requested}
    if export_format is ExportFormat.ALL and not force and len(set(identical.values())) > 1:
        raise F0Error(
            "E_EXPORT_PARTIAL", "export pair is partial; review it and rerun all with --force"
        )
    if not force:
        differing = [
            kind
            for kind in requested
            if existing[kind] is not None and existing[kind] != rendered[kind]
        ]
        if differing:
            raise F0Error(
                "E_EXPORT_CONFLICT", "existing export differs; review it or use explicit --force"
            )

    replacements = [kind for kind in requested if not identical[kind]]
    if not replacements:
        return 0, len(requested), [paths[kind] for kind in requested]
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise F0Error("E_EXPORT_CONFLICT", "export directory cannot be created safely") from None

    temporary: dict[str, Path] = {}
    try:
        for kind in replacements:
            temp = paths[kind].with_name(f".{paths[kind].name}.tmp")
            _write_temp(temp, rendered[kind])
            temporary[kind] = temp
        for kind in replacements:
            os.replace(temporary[kind], paths[kind])
        return len(replacements), len(requested) - len(replacements), [
            paths[kind] for kind in requested
        ]
    except OSError:
        raise F0Error(
            "E_EXPORT_PARTIAL", "export replacement was interrupted; review the output pair"
        ) from None
    finally:
        for temp in temporary.values():
            with suppress(OSError):
                temp.unlink(missing_ok=True)
