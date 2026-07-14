from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

from pydantic import ValidationError

from ai_newsroom.deepseek import MODEL, create_client, request_completion
from ai_newsroom.models import F0Error, RealStoryPackagePayload
from ai_newsroom.normalization import canonical_json
from ai_newsroom.package_builder import load_validated_package
from ai_newsroom.script_models import (
    ProductionScript,
    ProviderScriptDraft,
    ScriptScene,
    count_spoken_words,
)

PROMPT_VERSION: Final = "short-video-script-v2"
PROMPT_SHA256: Final = "8e758f3b7d96e8292d7649152b5e23ce728db6de6736486799879ba0f389288d"
PROMPT_PATH: Final = Path(__file__).resolve().parents[2] / "prompts" / "short_video_script_v2.txt"
SCRIPT_SCHEMA_VERSION: Final = 1
NEEDS_TEST_NOTICE: Final = (
    "В отдельном практическом тесте это пока не проверено."  # noqa: RUF001
)


def load_runtime_script_prompt(path: Path = PROMPT_PATH) -> str:
    try:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        raise F0Error("E_SCRIPT_PROMPT", "tracked script prompt cannot be read") from None
    if digest != PROMPT_SHA256:
        raise F0Error("E_SCRIPT_PROMPT", "script prompt changed without a version update")
    return text


def render_script_json(script: ProductionScript) -> bytes:
    return (
        json.dumps(
            script.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n"
    ).encode("utf-8")


def _markdown(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\n", " ")
    for character in "`*_{}[]<>()#+-.!|":
        escaped = escaped.replace(character, f"\\{character}")
    return escaped


def render_script_markdown(script: ProductionScript) -> bytes:
    lines = [
        f"# {_markdown(script.working_title)}",
        "",
        f"Script ID: `{script.script_id}`",
        f"Story ID: `{script.story_id}`",
        f"Package ID: `{script.package_id}`",
        f"Prompt version: `{script.prompt_version}`",
        f"Target duration: {script.target_duration_seconds} seconds",
        f"Word count: {script.word_count}",
        "",
        "## Hook",
        "",
        _markdown(script.hook),
        "",
        "## Spoken narration",
        "",
        _markdown(script.spoken_text),
        "",
        "## Scenes",
        "",
        "| # | Narration | On-screen text | Source |",
        "|---:|---|---|---|",
    ]
    for scene in script.scenes:
        lines.append(
            f"| {scene.order} | {_markdown(scene.narration)} | "
            f"{_markdown(scene.on_screen_text)} | {_markdown(scene.source_label)} |"
        )
    lines.extend(["", "## Sources", ""])
    lines.extend(
        f"- `{source.source_id}` — {_markdown(source.canonical_url)}"
        for source in script.source_references
    )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {_markdown(value)}" for value in script.limitations)
    lines.extend(
        [
            "",
            "## Caption",
            "",
            _markdown(script.caption),
            "",
            "Manual approval required before publication: **true**",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def expected_script_identity(package: RealStoryPackagePayload) -> tuple[str, str]:
    package_json = canonical_json(package.model_dump(mode="json")).encode("utf-8")
    package_digest = hashlib.sha256(package_json).hexdigest()
    identity = {
        "package_json_sha256": package_digest,
        "package_id": package.package_id,
        "generator": {
            "provider": "deepseek",
            "model": MODEL,
            "api_format": "openai-chat-completions",
            "thinking": "disabled",
            "temperature": 0.2,
        },
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT_SHA256,
        "script_schema_version": SCRIPT_SCHEMA_VERSION,
    }
    fingerprint = hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()
    script_id = "script_" + hashlib.sha256(
        f"f3-script:{fingerprint}".encode()
    ).hexdigest()[:24]
    return fingerprint, script_id


def _allowed_request(package: RealStoryPackagePayload) -> dict[str, Any]:
    allowed_claims = [
        claim.model_dump(mode="json") for claim in package.claims if claim.use_in_script
    ]
    if not allowed_claims:
        raise F0Error("E_SCRIPT_PACKAGE", "package has no claims approved for script use")
    return {
        "publication_verdict": package.publication_verdict,
        "allowed_claims": allowed_claims,
        "limitations": package.limitations,
    }


def validate_script_against_package(
    script: ProductionScript, package: RealStoryPackagePayload
) -> None:
    fingerprint, script_id = expected_script_identity(package)
    if (
        script.script_id != script_id
        or script.story_id != package.story_id
        or script.package_id != package.package_id
        or script.input_fingerprint != fingerprint
        or script.generator.model != MODEL
        or script.prompt_version != PROMPT_VERSION
    ):
        raise F0Error("E_SCRIPT_OUTPUT", "script identity or generator metadata is invalid")
    if script.source_references != package.source_references:
        raise F0Error("E_SCRIPT_OUTPUT", "script source references were not inherited exactly")
    if script.limitations != package.limitations:
        raise F0Error("E_SCRIPT_OUTPUT", "script limitations were not inherited exactly")
    if package.publication_verdict == "NEEDS_TEST" and NEEDS_TEST_NOTICE not in script.spoken_text:
        raise F0Error("E_SCRIPT_OUTPUT", "NEEDS_TEST narration must state the test limitation")
    if package.publication_verdict == "READY_WITH_QUALIFICATION":
        qualifications = [
            claim.qualification for claim in package.claims if claim.use_in_script
        ]
        if not any(value in script.spoken_text for value in qualifications):
            raise F0Error(
                "E_SCRIPT_OUTPUT", "qualified package narration must retain a qualification"
            )


def _draft_from_response(response: Any) -> ProviderScriptDraft:
    try:
        choice = response.choices[0]
        finish_reason = choice.finish_reason
        content = choice.message.content
    except (AttributeError, IndexError, TypeError):
        raise F0Error("E_SCRIPT_OUTPUT", "DeepSeek returned an invalid response shape") from None
    if finish_reason == "length":
        raise F0Error("E_SCRIPT_OUTPUT", "DeepSeek script output was truncated")
    if not isinstance(content, str) or not content.strip():
        raise F0Error("E_SCRIPT_OUTPUT", "DeepSeek returned empty script content")
    try:
        return ProviderScriptDraft.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as error:
        raise F0Error("E_SCRIPT_OUTPUT", _validation_summary(error)) from None


def _validation_summary(error: json.JSONDecodeError | ValidationError | F0Error) -> str:
    if isinstance(error, ValidationError):
        parts = []
        for item in error.errors(include_input=False, include_url=False)[:8]:
            location = ".".join(str(value) for value in item["loc"])
            parts.append(f"{location or 'object'}: {item['type']}")
        return "; ".join(parts)
    if isinstance(error, json.JSONDecodeError):
        return "response is not valid JSON"
    return error.message


def _finalize_script(
    draft: ProviderScriptDraft,
    package: RealStoryPackagePayload,
    *,
    fingerprint: str,
    script_id: str,
) -> ProductionScript:
    claims = {claim.claim_id: claim for claim in package.claims}
    reference_hosts = {
        reference.source_id: urlsplit(reference.canonical_url).hostname or reference.source_id
        for reference in package.source_references
    }
    scenes: list[ScriptScene] = []
    for order, provider_scene in enumerate(draft.scenes, start=1):
        source_hosts: list[str] = []
        for claim_id in provider_scene.claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                raise F0Error("E_SCRIPT_OUTPUT", "provider draft references an unknown claim")
            if not claim.use_in_script or claim.status == "UNVERIFIED":
                raise F0Error("E_SCRIPT_OUTPUT", "provider draft references a forbidden claim")
            host = reference_hosts.get(claim.evidence_source_id)
            if host is None:
                raise F0Error("E_SCRIPT_OUTPUT", "claim source reference is missing")
            if host not in source_hosts:
                source_hosts.append(host)
        source_label = "Источник: " + ", ".join(source_hosts)
        if len(source_label) > 100:
            raise F0Error("E_SCRIPT_OUTPUT", "derived scene source label is too long")
        scenes.append(
            ScriptScene(
                order=order,
                narration=provider_scene.narration,
                on_screen_text=provider_scene.on_screen_text,
                source_label=source_label,
                visual_kind="TEXT_CARD",
            )
        )
    spoken_text = " ".join(scene.narration for scene in scenes)
    word_count = count_spoken_words(spoken_text)
    if not 110 <= word_count <= 170:
        raise F0Error("E_SCRIPT_OUTPUT", "script narration must contain 110 to 170 words")
    script = ProductionScript.model_validate(
        {
            "schema_version": 1,
            "script_id": script_id,
            "story_id": package.story_id,
            "package_id": package.package_id,
            "input_fingerprint": fingerprint,
            "generator": {
                "provider": "deepseek",
                "model": MODEL,
                "api_format": "openai-chat-completions",
                "thinking": "disabled",
                "temperature": 0.2,
            },
            "prompt_version": PROMPT_VERSION,
            "language": "ru",
            "target_duration_seconds": 60,
            "working_title": draft.working_title,
            "hook": draft.hook,
            "spoken_text": spoken_text,
            "word_count": word_count,
            "scenes": [scene.model_dump(mode="json") for scene in scenes],
            "source_references": [
                reference.model_dump(mode="json") for reference in package.source_references
            ],
            "limitations": package.limitations,
            "caption": draft.caption,
            "manual_approval_required": True,
        }
    )
    validate_script_against_package(script, package)
    return script


def _load_existing_pair(
    json_path: Path,
    markdown_path: Path,
    package: RealStoryPackagePayload,
) -> ProductionScript | None:
    exists = (json_path.exists(), markdown_path.exists())
    if exists[0] != exists[1]:
        raise F0Error("E_SCRIPT_PARTIAL", "script JSON/Markdown pair is partial")
    if not exists[0]:
        return None
    try:
        raw = json_path.read_bytes()
        script = ProductionScript.model_validate_json(raw)
        expected_markdown = render_script_markdown(script)
        if raw != render_script_json(script) or markdown_path.read_bytes() != expected_markdown:
            raise ValueError
        validate_script_against_package(script, package)
    except (OSError, ValueError, ValidationError, F0Error):
        raise F0Error("E_SCRIPT_CONFLICT", "existing script pair is invalid or differs") from None
    return script


def _write_temp(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _write_pair(json_path: Path, markdown_path: Path, script: ProductionScript) -> None:
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise F0Error("E_SCRIPT_OUTPUT", "script output directory cannot be created") from None
    temporary = [
        json_path.with_name(f".{json_path.name}.tmp"),
        markdown_path.with_name(f".{markdown_path.name}.tmp"),
    ]
    try:
        _write_temp(temporary[0], render_script_json(script))
        _write_temp(temporary[1], render_script_markdown(script))
        os.replace(temporary[0], json_path)
        os.replace(temporary[1], markdown_path)
    except OSError:
        raise F0Error("E_SCRIPT_PARTIAL", "script pair write was interrupted") from None
    finally:
        for path in temporary:
            with suppress(OSError):
                path.unlink(missing_ok=True)


def build_script(
    data_dir: Path,
    story_id: str,
    package_id: str,
    *,
    output_dir: Path | None = None,
    api_key: str | None,
    client: Any | None = None,
) -> tuple[ProductionScript, bool, Path, Path, bool | None]:
    _snapshot, loaded = load_validated_package(data_dir, story_id, package_id=package_id)
    if not isinstance(loaded, RealStoryPackagePayload):
        raise F0Error("E_SCRIPT_PACKAGE", "mock packages cannot generate a production script")
    package = loaded
    if package.publication_verdict in {"HOLD", "REJECT"}:
        raise F0Error("E_SCRIPT_VERDICT", "package verdict does not permit script generation")
    request_value = _allowed_request(package)
    fingerprint, script_id = expected_script_identity(package)
    selected_dir = output_dir if output_dir is not None else data_dir / "scripts" / story_id
    json_path = selected_dir / f"{script_id}.json"
    markdown_path = selected_dir / f"{script_id}.md"
    existing = _load_existing_pair(json_path, markdown_path, package)
    if existing is not None:
        return existing, False, json_path, markdown_path, None
    if api_key is None or not api_key.strip():
        raise F0Error("E_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY is required to build a script")

    selected_client = client if client is not None else create_client(api_key)
    prompt = load_runtime_script_prompt()
    validation_error = ""
    script: ProductionScript | None = None
    repair_used = False
    for attempt in range(2):
        user_value = request_value
        if attempt == 1:
            user_value = {
                **request_value,
                "repair": {
                    "instruction": (
                        "Верни полный исправленный JSON-объект на замену, без пояснений."
                    ),
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
            draft = _draft_from_response(response)
            script = _finalize_script(
                draft, package, fingerprint=fingerprint, script_id=script_id
            )
            repair_used = attempt == 1
            break
        except (ValidationError, F0Error) as error:
            if isinstance(error, F0Error) and error.code != "E_SCRIPT_OUTPUT":
                raise
            validation_error = _validation_summary(error)
            if attempt == 1:
                raise F0Error(
                    "E_SCRIPT_OUTPUT", "DeepSeek script failed validation after one repair"
                ) from None
    assert script is not None
    _write_pair(json_path, markdown_path, script)
    return script, True, json_path, markdown_path, repair_used


def load_script(path: Path) -> ProductionScript:
    try:
        raw = path.read_bytes()
        script = ProductionScript.model_validate_json(raw)
    except (OSError, ValidationError, ValueError):
        raise F0Error("E_SCRIPT_INVALID", "script JSON is missing or invalid") from None
    expected_id = "script_" + hashlib.sha256(
        f"f3-script:{script.input_fingerprint}".encode()
    ).hexdigest()[:24]
    if script.script_id != expected_id or raw != render_script_json(script):
        raise F0Error("E_SCRIPT_INVALID", "script JSON is not a canonical F3 snapshot")
    return script
