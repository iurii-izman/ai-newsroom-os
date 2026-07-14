from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from ai_newsroom.database import load_stored_package, load_story_source, save_package
from ai_newsroom.models import (
    F0Error,
    MockClaim,
    PackageGenerator,
    PackageSource,
    PackageStory,
    SourceSnapshot,
    Story,
    StoryPackagePayload,
    StoryPackageSnapshot,
)
from ai_newsroom.normalization import (
    canonical_json,
    claim_id,
    claim_text,
    content_hash,
    package_identity,
    source_id,
    story_id,
)

MOCK_NOTICE: Final = "Demo-only package; no human verification; do not publish."
CLAIM_QUALIFIER: Final = "Fixture metadata only; no independent or human verification."


def validate_story_source(story: Story, source: SourceSnapshot) -> None:
    digest = content_hash(
        source.title,
        source.summary_text,
        source.published_at,
        source.published_at_raw,
    )
    if digest != source.content_hash:
        raise F0Error("E_DB_SCHEMA", "source content hash does not match normalized content")
    if source_id(source.canonical_url, digest) != source.id:
        raise F0Error("E_DB_SCHEMA", "source ID does not match canonical URL and content hash")
    if story.primary_source_id != source.id or story_id(source.id) != story.id:
        raise F0Error("E_DB_SCHEMA", "Story identity does not match its primary source")


def expected_payload(story: Story, source: SourceSnapshot) -> StoryPackagePayload:
    validate_story_source(story, source)
    fingerprint, package_id = package_identity(
        story.id, [{"id": source.id, "content_hash": source.content_hash}]
    )
    text = claim_text(source.title)
    return StoryPackagePayload(
        schema_version=1,
        package_id=package_id,
        generation_mode="MOCK",
        publishable=False,
        mock_notice=MOCK_NOTICE,
        generator=PackageGenerator(name="mock", version="mock-v1"),
        input_fingerprint=fingerprint,
        story=PackageStory(id=story.id, title=source.title),
        sources=[
            PackageSource(
                canonical_url=source.canonical_url,
                content_hash=source.content_hash,
                id=source.id,
                published_at=source.published_at,
                published_at_raw=source.published_at_raw,
                title=source.title,
            )
        ],
        claims=[
            MockClaim(
                id=claim_id(source.id, text),
                text=text,
                type="VENDOR_CLAIM",
                status="UNVERIFIED",
                source_ids=[source.id],
                qualifier=CLAIM_QUALIFIER,
            )
        ],
    )


def build_package(data_dir: Path, requested_story_id: str, built_at: str) -> tuple[str, bool]:
    story, source = load_story_source(data_dir, requested_story_id)
    payload = expected_payload(story, source)
    payload_json = canonical_json(payload.model_dump(mode="json"))
    snapshot = StoryPackageSnapshot(
        package_id=payload.package_id,
        story_id=story.id,
        schema_version=1,
        generator_name="mock",
        generator_version="mock-v1",
        input_fingerprint=payload.input_fingerprint,
        payload_json=payload_json,
        built_at=built_at,
    )
    return snapshot.package_id, save_package(data_dir, snapshot)


def load_validated_package(
    data_dir: Path, requested_story_id: str
) -> tuple[StoryPackageSnapshot, StoryPackagePayload]:
    snapshot = load_stored_package(data_dir, requested_story_id)
    try:
        story, source = load_story_source(data_dir, requested_story_id)
    except F0Error as error:
        if error.code == "E_STORY_NOT_FOUND":
            raise F0Error("E_DB_SCHEMA", "stored package Story foreign key is missing") from None
        raise
    expected = expected_payload(story, source)
    try:
        decoded = json.loads(snapshot.payload_json)
        actual = StoryPackagePayload.model_validate(decoded)
    except (json.JSONDecodeError, ValidationError, TypeError):
        raise F0Error("E_DB_SCHEMA", "stored package payload is invalid") from None
    if actual != expected:
        raise F0Error("E_DB_SCHEMA", "stored package payload or lineage is inconsistent")
    canonical = canonical_json(actual.model_dump(mode="json"))
    if canonical != snapshot.payload_json:
        raise F0Error("E_DB_SCHEMA", "stored package payload is not canonical JSON")
    if (
        snapshot.package_id != expected.package_id
        or snapshot.story_id != expected.story.id
        or snapshot.input_fingerprint != expected.input_fingerprint
        or snapshot.schema_version != 1
        or snapshot.generator_name != "mock"
        or snapshot.generator_version != "mock-v1"
    ):
        raise F0Error("E_DB_SCHEMA", "stored package identity or fingerprint is inconsistent")
    return snapshot, actual
