from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

from pydantic import ValidationError

from ai_newsroom.models import F0Error, RealClaim, RealStoryPackagePayload
from ai_newsroom.normalization import canonical_json
from ai_newsroom.package_builder import load_validated_package
from ai_newsroom.script_models import ProductionScript, ScriptScene, count_spoken_words

SCRIPT_SCHEMA_VERSION: Final = 1
GENERATOR_VERSION: Final = "safe-local-v1"
TEMPLATE_VERSION: Final = "claim-safe-script-v1"
TARGET_WORDS: Final = 110
MIN_PILOT_WORDS: Final = 90
MAX_WORDS: Final = 170
NEEDS_TEST_NOTICE: Final = "В отдельном практическом тесте это пока не проверено."  # noqa: RUF001
FALLBACK_TITLE: Final = "Разбор официального AI-анонса"
CAPTION: Final = (
    "Краткий разбор официального AI-анонса.\n"
    "Источник и ограничения указаны в ролике.\n"
    "Материал требует ручной редакционной проверки."
)
TAKEAWAY: Final = (
    "Практический вывод: перед использованием проверьте первоисточник, "
    "доступность функции и указанные ограничения."
)
TRANSITIONS: Final = (
    "Что известно:",
    "Ещё один подтверждённый пункт:",
    "При этом важно уточнить:",
    "Источник также указывает:",
)
PADDING_PHRASES: Final = (
    "Это важно отделять от рекламной формулировки и от результата независимого теста.",
    "В этом пилоте мы не проверяли функцию самостоятельно.",  # noqa: RUF001
    "Поэтому вывод ограничен содержимым указанного первоисточника.",
    "Перед рабочим применением потребуется отдельная практическая проверка.",
)
EVIDENCE_PHRASES: Final = {
    "VERIFIED": "Это утверждение отмечено в пакете как подтверждённое указанным источником.",
    "VENDOR_CLAIM": (
        "Это заявление поставщика, а не результат независимого теста."  # noqa: RUF001
    ),
    "INFERENCE": "Этот вывод отмечен как интерпретация и требует отдельной проверки.",
    "OPINION": (
        "Это редакционная оценка, а не результат независимого теста."  # noqa: RUF001
    ),
}


def render_script_json(script: ProductionScript) -> bytes:
    return (
        json.dumps(script.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2)
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
        f"Generator: `{script.generator}`",
        f"Template version: `{script.template_version}`",
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
        "| # | Narration | On-screen text | Claim IDs | Source |",
        "|---:|---|---|---|---|",
    ]
    for scene in script.scenes:
        claim_ids = ", ".join(f"`{value}`" for value in scene.claim_ids) or "—"
        lines.append(
            f"| {scene.order} | {_markdown(scene.narration)} | "
            f"{_markdown(scene.on_screen_text)} | {claim_ids} | "
            f"{_markdown(scene.source_label)} |"
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
    identity = {
        "package_json_sha256": hashlib.sha256(package_json).hexdigest(),
        "package_id": package.package_id,
        "script_schema_version": SCRIPT_SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "template_version": TEMPLATE_VERSION,
    }
    fingerprint = hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()
    script_id = "script_" + hashlib.sha256(f"f3-script:{fingerprint}".encode()).hexdigest()[:24]
    return fingerprint, script_id


def _allowed_claims(package: RealStoryPackagePayload) -> list[RealClaim]:
    claims = [
        claim for claim in package.claims if claim.use_in_script and claim.status != "UNVERIFIED"
    ]
    if not claims:
        raise F0Error("E_SCRIPT_PACKAGE", "package has no claims approved for script use")
    return claims


def _strongest_claim(claims: list[RealClaim]) -> RealClaim:
    for status in ("VERIFIED", "VENDOR_CLAIM"):
        selected = next((claim for claim in claims if claim.status == status), None)
        if selected is not None:
            return selected
    return claims[0]


def _sentence(value: str) -> str:
    return value if value.endswith((".", "!", "?")) else f"{value}."


def _source_label(package: RealStoryPackagePayload, claim_ids: list[str]) -> str:
    claims = {claim.claim_id: claim for claim in package.claims}
    source_ids = (
        [claims[claim_id].evidence_source_id for claim_id in claim_ids]
        if claim_ids
        else [reference.source_id for reference in package.source_references]
    )
    references = {
        reference.source_id: urlsplit(reference.canonical_url).hostname or reference.source_id
        for reference in package.source_references
    }
    hosts: list[str] = []
    for source_id in source_ids:
        host = references.get(source_id)
        if host is None:
            raise F0Error("E_SCRIPT_OUTPUT", "claim source reference is missing")
        if host not in hosts:
            hosts.append(host)
    label = "Источник: " + ", ".join(hosts)
    if len(label) > 100:
        raise F0Error("E_SCRIPT_OUTPUT", "derived scene source label is too long")
    return label


def _scene(
    package: RealStoryPackagePayload,
    narration: str,
    on_screen_text: str,
    claim_ids: list[str],
) -> dict[str, Any]:
    return {
        "narration": narration,
        "on_screen_text": on_screen_text,
        "source_label": _source_label(package, claim_ids),
        "claim_ids": claim_ids,
        "visual_kind": "TEXT_CARD",
    }


def _compose_scene_values(package: RealStoryPackagePayload) -> list[dict[str, Any]]:
    allowed = _allowed_claims(package)
    strongest = _strongest_claim(allowed)
    remaining = [claim for claim in allowed if claim.claim_id != strongest.claim_id]
    values = [
        _scene(
            package,
            f"Главный факт: {strongest.text}",
            "Главный факт",
            [strongest.claim_id],
        )
    ]

    chunk_size = max(1, (len(remaining) + 3) // 4)
    chunks = [
        remaining[index : index + chunk_size] for index in range(0, len(remaining), chunk_size)
    ]
    transition_index = 0
    for chunk in chunks:
        fragments: list[str] = []
        claim_ids: list[str] = []
        for claim in chunk:
            fragments.append(
                f"{TRANSITIONS[transition_index % len(TRANSITIONS)]} "
                f"{claim.text} {_sentence(claim.qualification)}"
            )
            claim_ids.append(claim.claim_id)
            transition_index += 1
        values.append(_scene(package, " ".join(fragments), "Что известно", claim_ids))

    evidence = f"{_sentence(strongest.qualification)} {EVIDENCE_PHRASES[strongest.status]}"
    if package.publication_verdict == "NEEDS_TEST":
        evidence = f"{evidence} {NEEDS_TEST_NOTICE}"
    values.append(_scene(package, evidence, "Статус доказательств", []))
    values.append(_scene(package, " ".join(package.limitations), "Ограничения", []))
    values.append(_scene(package, TAKEAWAY, "Практический вывод", []))

    editorial_index: int | None = None
    used_padding = 0
    if len(values) < 5:
        editorial_index = len(values) - 1
        values.insert(
            editorial_index,
            _scene(package, PADDING_PHRASES[0], "Граница материала", []),
        )
        used_padding = 1

    def current_word_count() -> int:
        return count_spoken_words(" ".join(str(value["narration"]) for value in values))

    while current_word_count() < TARGET_WORDS and used_padding < len(PADDING_PHRASES):
        phrase = PADDING_PHRASES[used_padding]
        if editorial_index is None and len(values) < 8:
            editorial_index = len(values) - 1
            values.insert(
                editorial_index,
                _scene(package, phrase, "Граница материала", []),
            )
        else:
            target = editorial_index if editorial_index is not None else len(values) - 3
            values[target]["narration"] = f"{values[target]['narration']} {phrase}"
        used_padding += 1

    word_count = current_word_count()
    if word_count < MIN_PILOT_WORDS:
        raise F0Error(
            "E_SCRIPT_OUTPUT",
            "safe script cannot reach the 90-word pilot minimum without invention",
        )
    if word_count > MAX_WORDS:
        raise F0Error("E_SCRIPT_OUTPUT", "safe script narration exceeds 170 words")
    if not 5 <= len(values) <= 8:
        raise F0Error("E_SCRIPT_OUTPUT", "safe script must contain 5 to 8 scenes")
    return values


def _finalize_script(package: RealStoryPackagePayload) -> ProductionScript:
    fingerprint, script_id = expected_script_identity(package)
    scene_values = _compose_scene_values(package)
    scenes = [
        ScriptScene.model_validate({"order": order, **value})
        for order, value in enumerate(scene_values, start=1)
    ]
    spoken_text = " ".join(scene.narration for scene in scenes)
    script = ProductionScript.model_validate(
        {
            "schema_version": SCRIPT_SCHEMA_VERSION,
            "script_id": script_id,
            "story_id": package.story_id,
            "package_id": package.package_id,
            "input_fingerprint": fingerprint,
            "generator": GENERATOR_VERSION,
            "template_version": TEMPLATE_VERSION,
            "language": "ru",
            "target_duration_seconds": 60,
            "working_title": (
                package.working_title if len(package.working_title) <= 300 else FALLBACK_TITLE
            ),
            "hook": scenes[0].narration,
            "spoken_text": spoken_text,
            "word_count": count_spoken_words(spoken_text),
            "scenes": [scene.model_dump(mode="json") for scene in scenes],
            "source_references": [
                reference.model_dump(mode="json") for reference in package.source_references
            ],
            "limitations": package.limitations,
            "caption": CAPTION,
            "manual_approval_required": True,
        }
    )
    validate_script_against_package(script, package)
    return script


def validate_script_against_package(
    script: ProductionScript, package: RealStoryPackagePayload
) -> None:
    fingerprint, script_id = expected_script_identity(package)
    if (
        script.script_id != script_id
        or script.story_id != package.story_id
        or script.package_id != package.package_id
        or script.input_fingerprint != fingerprint
        or script.generator != GENERATOR_VERSION
        or script.template_version != TEMPLATE_VERSION
    ):
        raise F0Error("E_SCRIPT_OUTPUT", "script identity or generator metadata is invalid")
    if script.source_references != package.source_references:
        raise F0Error("E_SCRIPT_OUTPUT", "script source references were not inherited exactly")
    if script.limitations != package.limitations:
        raise F0Error("E_SCRIPT_OUTPUT", "script limitations were not inherited exactly")

    claims = {claim.claim_id: claim for claim in package.claims}
    referenced_ids: list[str] = []
    for scene in script.scenes:
        for claim_id in scene.claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                raise F0Error("E_SCRIPT_OUTPUT", "script references an unknown claim")
            if not claim.use_in_script or claim.status == "UNVERIFIED":
                raise F0Error("E_SCRIPT_OUTPUT", "script references a forbidden claim")
            if claim.text not in scene.narration:
                raise F0Error("E_SCRIPT_OUTPUT", "claim scene does not retain its factual core")
            referenced_ids.append(claim_id)
    allowed_ids = [claim.claim_id for claim in _allowed_claims(package)]
    if sorted(referenced_ids) != sorted(allowed_ids):
        raise F0Error("E_SCRIPT_OUTPUT", "script claim coverage differs from the package")
    for claim_id in allowed_ids:
        if claims[claim_id].qualification not in script.spoken_text:
            raise F0Error("E_SCRIPT_OUTPUT", "script does not retain a required qualification")

    expected_values = _compose_scene_values(package)
    actual_values = [scene.model_dump(mode="json", exclude={"order"}) for scene in script.scenes]
    if actual_values != expected_values:
        raise F0Error("E_SCRIPT_OUTPUT", "script narration is not template-built")


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
    api_key: str | None = None,
    client: Any | None = None,
) -> tuple[ProductionScript, bool, Path, Path, bool]:
    _snapshot, loaded = load_validated_package(data_dir, story_id, package_id=package_id)
    if not isinstance(loaded, RealStoryPackagePayload):
        raise F0Error("E_SCRIPT_PACKAGE", "mock packages cannot generate a production script")
    package = loaded
    if package.publication_verdict in {"HOLD", "REJECT"}:
        raise F0Error("E_SCRIPT_VERDICT", "package verdict does not permit script generation")

    _ = (api_key, client)
    fingerprint, script_id = expected_script_identity(package)
    selected_dir = output_dir if output_dir is not None else data_dir / "scripts" / story_id
    json_path = selected_dir / f"{script_id}.json"
    markdown_path = selected_dir / f"{script_id}.md"
    existing = _load_existing_pair(json_path, markdown_path, package)
    if existing is not None:
        return existing, False, json_path, markdown_path, False

    script = _finalize_script(package)
    if script.input_fingerprint != fingerprint:
        raise F0Error("E_SCRIPT_OUTPUT", "safe script identity changed during construction")
    _write_pair(json_path, markdown_path, script)
    return script, True, json_path, markdown_path, False


def load_script(path: Path) -> ProductionScript:
    try:
        raw = path.read_bytes()
        script = ProductionScript.model_validate_json(raw)
    except (OSError, ValidationError, ValueError):
        raise F0Error("E_SCRIPT_INVALID", "script JSON is missing or invalid") from None
    expected_id = (
        "script_"
        + hashlib.sha256(f"f3-script:{script.input_fingerprint}".encode()).hexdigest()[:24]
    )
    if script.script_id != expected_id or raw != render_script_json(script):
        raise F0Error("E_SCRIPT_INVALID", "script JSON is not a canonical F3 snapshot")
    return script
