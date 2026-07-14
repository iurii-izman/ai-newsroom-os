from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

from pydantic import ValidationError

from ai_newsroom.database import (
    find_stored_package,
    load_stored_package,
    load_story_source,
    save_package,
)
from ai_newsroom.deepseek import (
    MODEL,
    PROMPT_SHA256,
    PROMPT_VERSION,
    create_client,
    load_runtime_prompt,
    request_completion,
)
from ai_newsroom.models import (
    BuildGenerator,
    DeepSeekGenerator,
    F0Error,
    MockClaim,
    PackageGenerator,
    PackageSource,
    PackageStory,
    ProviderStoryPackageDraft,
    RealStoryPackagePayload,
    SourceSnapshot,
    Story,
    StoryPackage,
    StoryPackagePayload,
    StoryPackageSnapshot,
    UsageMetadata,
)
from ai_newsroom.normalization import (
    canonical_json,
    claim_id,
    claim_text,
    content_hash,
    deepseek_package_identity,
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


def _source_input(source: SourceSnapshot) -> dict[str, str | None]:
    hostname = urlsplit(source.canonical_url).hostname or "unknown"
    return {
        "source_name": source.source_name or hostname,
        "source_id": source.id,
        "canonical_url": source.canonical_url,
        "title": source.title,
        "summary_text": source.summary_text,
        "published_at": source.published_at,
        "published_at_raw": source.published_at_raw,
    }


def expected_deepseek_identity(
    story: Story, source: SourceSnapshot
) -> tuple[str, str, dict[str, str | None]]:
    validate_story_source(story, source)
    public_source = _source_input(source)
    fingerprint, package_id = deepseek_package_identity(
        story.id, public_source, PROMPT_SHA256
    )
    return fingerprint, package_id, public_source


def _raise_validation(code: str, message: str) -> None:
    raise F0Error(code, message)


def validate_real_payload(
    payload: RealStoryPackagePayload,
    story: Story,
    source: SourceSnapshot,
    *,
    error_code: str,
) -> None:
    try:
        fingerprint, package_id, _public_source = expected_deepseek_identity(story, source)
    except F0Error:
        if error_code == "E_DB_SCHEMA":
            raise
        _raise_validation(error_code, "Story source lineage is invalid")
    expected_generator = DeepSeekGenerator(
        provider="deepseek",
        model="deepseek-v4-flash",
        api_format="openai-chat-completions",
        thinking="disabled",
        temperature=0.2,
    )
    if (
        payload.package_id != package_id
        or payload.story_id != story.id
        or payload.source_id != source.id
        or payload.input_fingerprint != fingerprint
        or payload.generator != expected_generator
        or payload.prompt_version != PROMPT_VERSION
    ):
        _raise_validation(error_code, "provider output identity or generator metadata is invalid")
    reference = payload.source_references[0]
    if reference.source_id != source.id or reference.canonical_url != source.canonical_url:
        _raise_validation(error_code, "provider output source reference is invalid")


def _build_mock_package(
    data_dir: Path, requested_story_id: str, built_at: str
) -> tuple[str, bool]:
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


def _usage_metadata(response: Any, *, repair_used: bool) -> UsageMetadata:
    usage = getattr(response, "usage", None)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    return UsageMetadata(
        input_tokens=getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
        cache_hit_tokens=getattr(prompt_details, "cached_tokens", None),
        repair_used=repair_used,
    )


def _validation_summary(error: ValidationError | F0Error | json.JSONDecodeError) -> str:
    if isinstance(error, ValidationError):
        parts = []
        for item in error.errors(include_input=False, include_url=False)[:8]:
            location = ".".join(str(value) for value in item["loc"])
            parts.append(f"{location or 'object'}: {item['type']}")
        return "; ".join(parts)
    if isinstance(error, json.JSONDecodeError):
        return "response is not valid JSON"
    return error.message


def _provider_payload(
    response: Any,
    story: Story,
    source: SourceSnapshot,
    *,
    package_id: str,
    fingerprint: str,
    repair_used: bool,
) -> RealStoryPackagePayload:
    try:
        choice = response.choices[0]
        finish_reason = choice.finish_reason
        content = choice.message.content
    except (AttributeError, IndexError, TypeError):
        raise F0Error("E_PROVIDER_OUTPUT", "DeepSeek returned an invalid response shape") from None
    if finish_reason == "length":
        raise F0Error("E_PROVIDER_OUTPUT", "DeepSeek output was truncated")
    if not isinstance(content, str) or not content.strip():
        raise F0Error("E_PROVIDER_OUTPUT", "DeepSeek returned empty content")
    try:
        decoded = json.loads(content)
        draft = ProviderStoryPackageDraft.model_validate(decoded)
        if draft.story_id != story.id or draft.source_id != source.id:
            raise F0Error("E_PROVIDER_OUTPUT", "provider output Story lineage is invalid")
        reference = draft.source_references[0]
        if reference.canonical_url != source.canonical_url:
            raise F0Error("E_PROVIDER_OUTPUT", "provider output source URL is invalid")
        value = {
            **draft.model_dump(mode="json"),
            "schema_version": 2,
            "package_id": package_id,
            "input_fingerprint": fingerprint,
            "generator": {
                "provider": "deepseek",
                "model": MODEL,
                "api_format": "openai-chat-completions",
                "thinking": "disabled",
                "temperature": 0.2,
            },
            "prompt_version": PROMPT_VERSION,
            "usage_metadata": _usage_metadata(
                response, repair_used=repair_used
            ).model_dump(mode="json"),
        }
        finalized = RealStoryPackagePayload.model_validate(value)
        validate_real_payload(finalized, story, source, error_code="E_PROVIDER_OUTPUT")
        return finalized
    except (json.JSONDecodeError, ValidationError) as error:
        raise error


def _build_deepseek_package(
    data_dir: Path,
    requested_story_id: str,
    built_at: str,
    *,
    api_key: str | None,
    client: Any | None,
) -> tuple[str, bool]:
    if api_key is None or not api_key.strip():
        raise F0Error(
            "E_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY is required for the deepseek generator"
        )
    story, source = load_story_source(data_dir, requested_story_id)
    fingerprint, package_id, public_source = expected_deepseek_identity(story, source)
    stored = find_stored_package(data_dir, package_id)
    if stored is not None:
        _snapshot, _payload = load_validated_package(
            data_dir, requested_story_id, package_id=package_id
        )
        return package_id, False

    prompt = load_runtime_prompt()
    selected_client = client if client is not None else create_client(api_key)
    expected = {
        "story_id": story.id,
        "source_id": source.id,
    }
    public_request = {"expected": expected, "source": public_source}
    validation_error = ""
    payload: RealStoryPackagePayload | None = None
    for attempt in range(2):
        user_value: dict[str, Any] = public_request
        if attempt == 1:
            user_value = {
                **public_request,
                "repair": {
                    "instruction": "Исправь схему и верни только полный JSON-объект.",
                    "validation_errors": validation_error,
                },
            }
        response = request_completion(
            selected_client,
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": canonical_json(user_value)},
            ],
        )
        try:
            payload = _provider_payload(
                response,
                story,
                source,
                package_id=package_id,
                fingerprint=fingerprint,
                repair_used=attempt == 1,
            )
            break
        except (ValidationError, json.JSONDecodeError, F0Error) as error:
            if isinstance(error, F0Error) and error.code != "E_PROVIDER_OUTPUT":
                raise
            validation_error = _validation_summary(error)
            if attempt == 1:
                raise F0Error(
                    "E_PROVIDER_OUTPUT", "DeepSeek output failed validation after one repair"
                ) from None
    assert payload is not None
    payload_json = canonical_json(payload.model_dump(mode="json"))
    snapshot = StoryPackageSnapshot(
        package_id=package_id,
        story_id=story.id,
        schema_version=2,
        generator_name="deepseek",
        generator_version=MODEL,
        input_fingerprint=fingerprint,
        payload_json=payload_json,
        built_at=built_at,
    )
    created = save_package(data_dir, snapshot)
    if not created:
        load_validated_package(data_dir, story.id, package_id=package_id)
    return package_id, created


def build_package(
    data_dir: Path,
    requested_story_id: str,
    built_at: str,
    generator: BuildGenerator = BuildGenerator.MOCK,
    *,
    api_key: str | None = None,
    client: Any | None = None,
) -> tuple[str, bool]:
    if generator is BuildGenerator.MOCK:
        return _build_mock_package(data_dir, requested_story_id, built_at)
    return _build_deepseek_package(
        data_dir,
        requested_story_id,
        built_at,
        api_key=api_key,
        client=client,
    )


def load_validated_package(
    data_dir: Path,
    requested_story_id: str,
    *,
    package_id: str | None = None,
) -> tuple[StoryPackageSnapshot, StoryPackage]:
    snapshot = load_stored_package(data_dir, requested_story_id, package_id=package_id)
    try:
        story, source = load_story_source(data_dir, requested_story_id)
    except F0Error as error:
        if error.code == "E_STORY_NOT_FOUND":
            raise F0Error("E_DB_SCHEMA", "stored package Story foreign key is missing") from None
        raise
    try:
        decoded = json.loads(snapshot.payload_json)
        if snapshot.generator_name == "mock":
            actual: StoryPackage = StoryPackagePayload.model_validate(decoded)
        else:
            actual = RealStoryPackagePayload.model_validate(decoded)
    except (json.JSONDecodeError, ValidationError, TypeError):
        raise F0Error("E_DB_SCHEMA", "stored package payload is invalid") from None
    canonical = canonical_json(actual.model_dump(mode="json"))
    if canonical != snapshot.payload_json:
        raise F0Error("E_DB_SCHEMA", "stored package payload is not canonical JSON")

    if isinstance(actual, StoryPackagePayload):
        expected = expected_payload(story, source)
        if actual != expected:
            raise F0Error("E_DB_SCHEMA", "stored mock package or lineage is inconsistent")
        if (
            snapshot.package_id != expected.package_id
            or snapshot.story_id != expected.story.id
            or snapshot.input_fingerprint != expected.input_fingerprint
            or snapshot.schema_version != 1
            or snapshot.generator_name != "mock"
            or snapshot.generator_version != "mock-v1"
        ):
            raise F0Error("E_DB_SCHEMA", "stored mock package identity is inconsistent")
    else:
        validate_real_payload(actual, story, source, error_code="E_DB_SCHEMA")
        if (
            snapshot.package_id != actual.package_id
            or snapshot.story_id != actual.story_id
            or snapshot.input_fingerprint != actual.input_fingerprint
            or snapshot.schema_version != 2
            or snapshot.generator_name != "deepseek"
            or snapshot.generator_version != MODEL
        ):
            raise F0Error("E_DB_SCHEMA", "stored DeepSeek package identity is inconsistent")
    return snapshot, actual
