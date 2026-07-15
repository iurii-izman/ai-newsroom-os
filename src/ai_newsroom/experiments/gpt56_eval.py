from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import random
import re
import tempfile
import time
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from typing import Annotated, Any, Final

import typer
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

SCHEMA_VERSION: Final = 1
RUN_ORDER: Final = ("terra", "sol", "sol", "terra", "terra", "sol")
RUN_IDS: Final = tuple(f"run_{number:02d}" for number in range(1, 7))
OUTPUT_IDS: Final = tuple("ABCDEF")
VISIBLE_FIXTURES: Final = (
    "01_incident_brief.md",
    "02_event_log.csv",
    "03_acceptance_criteria.md",
)
PROMPT_FILE: Final = "master_prompt.md"
REFERENCE_FILE: Final = "04_reference_key_NOT_FOR_MODELS.md"
RUBRIC_FILE: Final = "scoring_rubric.md"
MAX_FIXTURE_BYTES: Final = 256_000
CSV_HEADER: Final = (
    "event_id",
    "received_at",
    "external_lead_id",
    "request_id",
    "http_status",
    "response_time_ms",
    "retry_number",
    "crm_record_id",
    "assigned_manager",
    "expected_manager",
    "result",
)
SCORE_FIELDS: Final = (
    "output_id",
    "factual_accuracy",
    "root_cause_reasoning",
    "idempotency",
    "timeout_retry",
    "assignment",
    "remediation",
    "uat",
    "risks_assumptions",
    "practical_usability",
    "critical_error_count",
    "critical_error_notes",
    "review_complete",
)
CORRECTION_FIELDS: Final = (
    "output_id",
    "minutes",
    "accepted",
    "critical_fixes",
    "major_additions",
    "minor_edits",
    "notes",
    "timer_complete",
)
MAPPING_FIELDS: Final = (
    "output_id",
    "run_id",
    "model_key",
    "model_id",
    "redaction_count",
    "source_sha256",
)
SCORE_RANGES: Final[dict[str, tuple[int, int]]] = {
    "factual_accuracy": (0, 2),
    "root_cause_reasoning": (0, 1),
    "idempotency": (0, 1),
    "timeout_retry": (0, 1),
    "assignment": (0, 1),
    "remediation": (0, 1),
    "uat": (0, 1),
    "risks_assumptions": (0, 1),
    "practical_usability": (0, 1),
}
PACKAGE_ROOT: Final = Path(__file__).resolve().parents[3] / "experiments" / "gpt56_terra_sol"
DEFAULT_CONFIG: Final = PACKAGE_ROOT / "config.example.toml"
DEFAULT_RUN_ROOT: Final = Path(".track-a/gpt56-terra-sol")
DEMO_LABEL: Final = "SYNTHETIC HARNESS DEMO — NOT A MODEL RESULT"

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Controlled GPT-5.6 Terra/Sol evaluation harness.",
)


class EvaluationError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ModelConfig:
    key: str
    model_id: str
    input_rate: Decimal
    output_rate: Decimal

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.model_id,
            "input_usd_per_million": str(self.input_rate),
            "output_usd_per_million": str(self.output_rate),
        }


@dataclass(frozen=True)
class EvaluationConfig:
    schema_version: int
    mode: str
    effort: str
    run_count_per_model: int
    timeout_seconds: float
    max_output_tokens: int
    blind_seed: str
    models: dict[str, ModelConfig]
    pricing_verified_at: str
    pricing_source_url: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "effort": self.effort,
            "run_count_per_model": self.run_count_per_model,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "blind_seed": self.blind_seed,
            "models": {key: self.models[key].as_dict() for key in ("terra", "sol")},
            "pricing": {
                "verified_at": self.pricing_verified_at,
                "source_url": self.pricing_source_url,
                "cached_input_rate_available": False,
                "other_rate_categories_available": False,
            },
        }


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    try:
        return _sha256(path.read_bytes())
    except OSError:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"cannot read {path.name}") from None


def _read_utf8(path: Path, *, max_bytes: int = MAX_FIXTURE_BYTES) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"cannot read {path.name}") from None
    if not data or len(data) > max_bytes:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"invalid size for {path.name}")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeError:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"{path.name} is not UTF-8") from None


def _write_once(path: Path, data: bytes) -> bool:
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError:
            raise EvaluationError("WORKSPACE_CONFLICT", f"cannot read existing {path}") from None
        if existing == data:
            return False
        raise EvaluationError("WORKSPACE_CONFLICT", f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            if path.read_bytes() == data:
                Path(temp_name).unlink(missing_ok=True)
                return False
            raise EvaluationError("WORKSPACE_CONFLICT", f"refusing to overwrite {path}")
        os.replace(temp_name, path)
        return True
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _replace_status(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise EvaluationError("WORKSPACE_CONFLICT", f"invalid JSON file: {path}") from None
    if not isinstance(value, dict):
        raise EvaluationError("WORKSPACE_CONFLICT", f"invalid JSON object: {path}")
    return value


def _parse_decimal(value: object, field: str) -> Decimal:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise EvaluationError("CONFIG_INVALID", f"{field} must be a decimal value")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise EvaluationError("CONFIG_INVALID", f"{field} is not a decimal") from None
    if result < 0:
        raise EvaluationError("CONFIG_INVALID", f"{field} cannot be negative")
    return result


def load_config(path: Path) -> EvaluationConfig:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        raise EvaluationError(
            "CONFIG_INVALID", "configuration is missing or invalid TOML"
        ) from None
    try:
        schema_version = raw["schema_version"]
        mode = raw["mode"]
        effort = raw["effort"]
        run_count = raw["run_count_per_model"]
        timeout = raw["timeout_seconds"]
        max_tokens = raw["max_output_tokens"]
        blind_seed = raw["blind_seed"]
        models_raw = raw["models"]
        pricing = raw["pricing"]
    except KeyError as error:
        raise EvaluationError("CONFIG_INVALID", f"missing config field {error.args[0]}") from None
    if schema_version != SCHEMA_VERSION:
        raise EvaluationError("CONFIG_INVALID", "schema_version must be 1")
    if mode not in {"api", "chatgpt-work"}:
        raise EvaluationError("CONFIG_INVALID", "mode must be api or chatgpt-work")
    if effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
        raise EvaluationError("CONFIG_INVALID", "unsupported reasoning effort")
    if run_count != 3:
        raise EvaluationError("CONFIG_INVALID", "run_count_per_model must be exactly 3")
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not 1 <= timeout <= 600
    ):
        raise EvaluationError("CONFIG_INVALID", "timeout_seconds must be between 1 and 600")
    if (
        not isinstance(max_tokens, int)
        or isinstance(max_tokens, bool)
        or not 1 <= max_tokens <= 128_000
    ):
        raise EvaluationError("CONFIG_INVALID", "max_output_tokens is outside the allowed range")
    if not isinstance(blind_seed, str) or not blind_seed.strip() or len(blind_seed) > 200:
        raise EvaluationError("CONFIG_INVALID", "blind_seed is missing or too long")
    if not isinstance(models_raw, dict) or set(models_raw) != {"terra", "sol"}:
        raise EvaluationError("CONFIG_INVALID", "configuration must define exactly terra and sol")
    models: dict[str, ModelConfig] = {}
    for key in ("terra", "sol"):
        model_raw = models_raw[key]
        if not isinstance(model_raw, dict):
            raise EvaluationError("CONFIG_INVALID", f"models.{key} must be a table")
        model_id = model_raw.get("id")
        if not isinstance(model_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", model_id):
            raise EvaluationError("CONFIG_INVALID", f"models.{key}.id is not live-safe")
        models[key] = ModelConfig(
            key=key,
            model_id=model_id,
            input_rate=_parse_decimal(
                model_raw.get("input_usd_per_million"),
                f"models.{key}.input_usd_per_million",
            ),
            output_rate=_parse_decimal(
                model_raw.get("output_usd_per_million"),
                f"models.{key}.output_usd_per_million",
            ),
        )
    if not isinstance(pricing, dict):
        raise EvaluationError("CONFIG_INVALID", "pricing must be a table")
    verified_at = pricing.get("verified_at")
    source_url = pricing.get("source_url")
    if not isinstance(verified_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_at):
        raise EvaluationError("CONFIG_INVALID", "pricing.verified_at must be YYYY-MM-DD")
    if not isinstance(source_url, str) or not source_url.startswith("https://openai.com/"):
        raise EvaluationError("CONFIG_INVALID", "pricing.source_url must be official OpenAI HTTPS")
    return EvaluationConfig(
        schema_version=schema_version,
        mode=mode,
        effort=effort,
        run_count_per_model=run_count,
        timeout_seconds=float(timeout),
        max_output_tokens=max_tokens,
        blind_seed=blind_seed,
        models=models,
        pricing_verified_at=verified_at,
        pricing_source_url=source_url,
    )


def validate_fixtures(package_root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    fixture_root = package_root / "fixtures"
    required = (*VISIBLE_FIXTURES, REFERENCE_FILE, PROMPT_FILE, RUBRIC_FILE)
    texts: dict[str, str] = {}
    entries: list[dict[str, Any]] = []
    for name in required:
        path = fixture_root / name
        if not path.is_file():
            raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"missing fixture {name}")
        text = _read_utf8(path)
        texts[name] = text
        data = text.encode("utf-8")
        entries.append({"path": f"fixtures/{name}", "sha256": _sha256(data), "bytes": len(data)})
    csv_path = fixture_root / "02_event_log.csv"
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != CSV_HEADER:
                raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "event log header is not exact")
            rows = list(reader)
    except OSError:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "cannot read event log") from None
    if len(rows) < 24:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "event log needs at least 24 rows")
    lead_ids = {row["external_lead_id"] for row in rows}
    if len(lead_ids) != 10:
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "event log needs exactly 10 lead IDs")
    event_ids = [row["event_id"] for row in rows]
    if len(set(event_ids)) != len(event_ids):
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "event IDs must be unique")
    for row in rows:
        for field in ("http_status", "response_time_ms", "retry_number"):
            try:
                number = int(row[field])
            except ValueError:
                raise EvaluationError(
                    "FIXTURE_INTEGRITY_FAILED", f"{field} is not numeric at {row['event_id']}"
                ) from None
            if field == "retry_number" and number < 0:
                raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "retry number cannot be negative")
    mentioned = set(re.findall(r"\bE\d{3}\b", texts[REFERENCE_FILE]))
    unknown = mentioned - set(event_ids)
    if unknown:
        raise EvaluationError(
            "FIXTURE_INTEGRITY_FAILED", f"reference mentions unknown events: {sorted(unknown)}"
        )
    prompt_lower = texts[PROMPT_FILE].casefold()
    if re.search(r"gpt|terra|sol|модел[ьи]", prompt_lower):
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "master prompt contains model identity")
    if re.search(r"\breference\b|\bприват\w*\b|\bключ\b", prompt_lower):  # noqa: RUF001
        raise EvaluationError(
            "FIXTURE_INTEGRITY_FAILED", "master prompt mentions private reference"
        )
    request_input_set = [*VISIBLE_FIXTURES, PROMPT_FILE]
    core = {
        "schema_version": SCHEMA_VERSION,
        "files": sorted(entries, key=lambda entry: str(entry["path"])),
        "request_input_set": request_input_set,
        "prompt_sha256": next(
            str(entry["sha256"]) for entry in entries if entry["path"] == f"fixtures/{PROMPT_FILE}"
        ),
        "reference_sha256": next(
            str(entry["sha256"])
            for entry in entries
            if entry["path"] == f"fixtures/{REFERENCE_FILE}"
        ),
        "event_row_count": len(rows),
        "external_lead_id_count": len(lead_ids),
    }
    return {**core, "manifest_digest": _sha256(_canonical_json(core))}


def _experiment_identity(config: EvaluationConfig, fixture_manifest: Mapping[str, Any]) -> str:
    identity = {
        "schema_version": config.schema_version,
        "fixture_manifest_digest": fixture_manifest["manifest_digest"],
        "prompt_digest": fixture_manifest["prompt_sha256"],
        "models": {key: config.models[key].model_id for key in ("terra", "sol")},
        "effort": config.effort,
        "run_count_per_model": config.run_count_per_model,
        "blind_seed": config.blind_seed,
        "pricing": {
            "verified_at": config.pricing_verified_at,
            "source_url": config.pricing_source_url,
            "terra_input": str(config.models["terra"].input_rate),
            "terra_output": str(config.models["terra"].output_rate),
            "sol_input": str(config.models["sol"].input_rate),
            "sol_output": str(config.models["sol"].output_rate),
        },
    }
    return f"gpt56-ts-{_sha256(_canonical_json(identity))[:24]}"


def _workspace_dirs(run_root: Path) -> tuple[Path, ...]:
    return tuple(
        run_root / name
        for name in (
            "00_setup",
            "01_fixture",
            "02_private_reference",
            "03_raw_runs",
            "04_recordings",
            "05_blind_review",
            "06_corrections",
            "07_results",
            "08_video",
            "08_video/capcut_project",
        )
    )


def prepare_workspace(
    config_path: Path = DEFAULT_CONFIG,
    run_root: Path = DEFAULT_RUN_ROOT,
    package_root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    config = load_config(config_path.resolve())
    fixture = validate_fixtures(package_root.resolve())
    root = run_root.resolve()
    manifest_path = root / "00_setup" / "experiment_manifest.json"
    experiment_id = _experiment_identity(config, fixture)
    if manifest_path.exists():
        existing = _load_json(manifest_path)
        if existing.get("experiment_id") != experiment_id:
            raise EvaluationError("WORKSPACE_CONFLICT", "prepared workspace has another identity")
        _verify_workspace(root)
        return {"experiment_id": experiment_id, "created": False, "run_root": str(root)}
    if root.exists() and any(root.iterdir()):
        raise EvaluationError("WORKSPACE_CONFLICT", "non-empty workspace is not prepared")
    for directory in _workspace_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)
    fixture_manifest = {**fixture, "created_at": _utc_now()}
    run_order = {
        "schema_version": SCHEMA_VERSION,
        "slots": [
            {"run_id": run_id, "position": position, "model_key": model_key}
            for position, (run_id, model_key) in enumerate(zip(RUN_IDS, RUN_ORDER, strict=True), 1)
        ],
    }
    frozen_config = config.as_dict()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "created_at": fixture_manifest["created_at"],
        "mode": config.mode,
        "identity_frozen": True,
        "fixture_manifest_digest": fixture["manifest_digest"],
        "config_digest": _sha256(_canonical_json(frozen_config)),
        "run_order_digest": _sha256(_canonical_json(run_order)),
        "request_input_set": [*VISIBLE_FIXTURES, PROMPT_FILE],
        "private_reference_excluded": True,
        "demo_label": None,
    }
    setup = root / "00_setup"
    _write_once(setup / "test_config.json", _pretty_json(frozen_config))
    _write_once(setup / "run_order.json", _pretty_json(run_order))
    _write_once(setup / "fixture_manifest.json", _pretty_json(fixture_manifest))
    _write_once(setup / "experiment_manifest.json", _pretty_json(manifest))
    _write_once(
        setup / "access_check.md",
        (package_root / "templates" / "access_check.md").read_bytes(),
    )
    source_fixture = package_root / "fixtures"
    for name in (*VISIBLE_FIXTURES, PROMPT_FILE, RUBRIC_FILE):
        _write_once(root / "01_fixture" / name, (source_fixture / name).read_bytes())
    _write_once(
        root / "02_private_reference" / REFERENCE_FILE,
        (source_fixture / REFERENCE_FILE).read_bytes(),
    )
    _write_once(
        root / "05_blind_review" / "scores.csv",
        (package_root / "templates" / "scores.csv").read_bytes(),
    )
    _write_once(
        root / "06_corrections" / "correction_log.csv",
        (package_root / "templates" / "correction_log.csv").read_bytes(),
    )
    _write_once(
        root / "08_video" / "capcut_assembly_checklist.md",
        (package_root / "templates" / "capcut_assembly_checklist.md").read_bytes(),
    )
    status = workspace_status(root, write_file=False)
    _replace_status(root / "STATUS.md", _status_markdown(status).encode("utf-8"))
    return {"experiment_id": experiment_id, "created": True, "run_root": str(root)}


def _config_from_workspace(run_root: Path) -> EvaluationConfig:
    raw = _load_json(run_root / "00_setup" / "test_config.json")
    models_raw = raw.get("models")
    pricing = raw.get("pricing")
    if not isinstance(models_raw, dict) or not isinstance(pricing, dict):
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen config has invalid structure")
    models: dict[str, ModelConfig] = {}
    for key in ("terra", "sol"):
        value = models_raw.get(key)
        if not isinstance(value, dict):
            raise EvaluationError("WORKSPACE_CONFLICT", f"missing frozen model {key}")
        model_id = value.get("id")
        if not isinstance(model_id, str):
            raise EvaluationError("WORKSPACE_CONFLICT", f"invalid frozen model {key}")
        models[key] = ModelConfig(
            key,
            model_id,
            _parse_decimal(value.get("input_usd_per_million"), f"models.{key}.input"),
            _parse_decimal(value.get("output_usd_per_million"), f"models.{key}.output"),
        )
    try:
        return EvaluationConfig(
            schema_version=int(raw["schema_version"]),
            mode=str(raw["mode"]),
            effort=str(raw["effort"]),
            run_count_per_model=int(raw["run_count_per_model"]),
            timeout_seconds=float(raw["timeout_seconds"]),
            max_output_tokens=int(raw["max_output_tokens"]),
            blind_seed=str(raw["blind_seed"]),
            models=models,
            pricing_verified_at=str(pricing["verified_at"]),
            pricing_source_url=str(pricing["source_url"]),
        )
    except (KeyError, TypeError, ValueError):
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen config is incomplete") from None


def _verify_workspace(run_root: Path) -> tuple[EvaluationConfig, dict[str, Any], dict[str, Any]]:
    root = run_root.resolve()
    manifest = _load_json(root / "00_setup" / "experiment_manifest.json")
    fixture = _load_json(root / "00_setup" / "fixture_manifest.json")
    config = _config_from_workspace(root)
    if _sha256(_canonical_json(config.as_dict())) != manifest.get("config_digest"):
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen configuration digest changed")
    order = _load_json(root / "00_setup" / "run_order.json")
    if _sha256(_canonical_json(order)) != manifest.get("run_order_digest"):
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen run order changed")
    slots = order.get("slots")
    if not isinstance(slots, list) or len(slots) != 6:
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen run order is invalid")
    keys = [slot.get("model_key") for slot in slots if isinstance(slot, dict)]
    ids = [slot.get("run_id") for slot in slots if isinstance(slot, dict)]
    if (
        keys != list(RUN_ORDER)
        or ids != list(RUN_IDS)
        or keys.count("terra") != 3
        or keys.count("sol") != 3
    ):
        raise EvaluationError("WORKSPACE_CONFLICT", "frozen run order is not the approved order")
    entries = fixture.get("files")
    if not isinstance(entries, list):
        raise EvaluationError("WORKSPACE_CONFLICT", "fixture manifest is invalid")
    runtime_paths = {
        **{
            name: root / "01_fixture" / name
            for name in (*VISIBLE_FIXTURES, PROMPT_FILE, RUBRIC_FILE)
        },
        REFERENCE_FILE: root / "02_private_reference" / REFERENCE_FILE,
    }
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise EvaluationError("WORKSPACE_CONFLICT", "fixture entry is invalid")
        name = Path(entry["path"]).name
        if name not in runtime_paths or _file_sha256(runtime_paths[name]) != entry.get("sha256"):
            raise EvaluationError("FIXTURE_INTEGRITY_FAILED", f"frozen fixture changed: {name}")
    fixture_core = {
        key: value for key, value in fixture.items() if key not in {"created_at", "manifest_digest"}
    }
    if _sha256(_canonical_json(fixture_core)) != fixture.get("manifest_digest"):
        raise EvaluationError("FIXTURE_INTEGRITY_FAILED", "fixture manifest digest changed")
    if _experiment_identity(config, fixture) != manifest.get("experiment_id"):
        raise EvaluationError("WORKSPACE_CONFLICT", "experiment identity changed")
    return config, fixture, manifest


def _validate_run_id(run_id: str) -> None:
    if run_id not in RUN_IDS or not re.fullmatch(r"run_0[1-6]", run_id):
        raise EvaluationError("PATH_UNSAFE", "run_id must be run_01 through run_06")


def _slot(run_root: Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    order = _load_json(run_root / "00_setup" / "run_order.json")
    slots = order.get("slots")
    if not isinstance(slots, list):
        raise EvaluationError("WORKSPACE_CONFLICT", "run order is invalid")
    for slot in slots:
        if isinstance(slot, dict) and slot.get("run_id") == run_id:
            return slot
    raise EvaluationError("WORKSPACE_CONFLICT", "run slot is missing")


def _request_input(run_root: Path) -> str:
    prompt = _read_utf8(run_root / "01_fixture" / PROMPT_FILE)
    sections = [f"=== {PROMPT_FILE} ===\n{prompt.strip()}"]
    for name in VISIBLE_FIXTURES:
        sections.append(f"=== {name} ===\n{_read_utf8(run_root / '01_fixture' / name).strip()}")
    return "\n\n".join(sections) + "\n"


def request_preview(run_root: Path, run_id: str) -> dict[str, Any]:
    root = run_root.resolve()
    config, fixture, _ = _verify_workspace(root)
    slot = _slot(root, run_id)
    model_key = str(slot["model_key"])
    request_input = _request_input(root)
    fixture_hashes = {
        Path(str(entry["path"])).name: str(entry["sha256"])
        for entry in fixture["files"]
        if Path(str(entry["path"])).name in VISIBLE_FIXTURES
    }
    preview = {
        "run_id": run_id,
        "model_id": config.models[model_key].model_id,
        "effort": config.effort,
        "fixture_hashes": fixture_hashes,
        "prompt_hash": fixture["prompt_sha256"],
        "character_count": len(request_input),
        "tools": [],
        "tool_choice": "none",
        "web_enabled": False,
        "store": False,
        "private_reference_excluded": True,
        "request_input_set": [*VISIBLE_FIXTURES, PROMPT_FILE],
        "input_sha256": _sha256(request_input.encode("utf-8")),
    }
    preview["request_digest"] = _sha256(_canonical_json(preview))
    return preview


def _raw_paths(run_root: Path, run_id: str) -> tuple[Path, Path]:
    _validate_run_id(run_id)
    raw_root = run_root / "03_raw_runs"
    return raw_root / f"{run_id}_raw.md", raw_root / f"{run_id}_metadata.json"


def _completed_runs(run_root: Path) -> list[str]:
    completed: list[str] = []
    for run_id in RUN_IDS:
        raw_path, metadata_path = _raw_paths(run_root, run_id)
        if raw_path.is_file() and metadata_path.is_file():
            metadata = _load_json(metadata_path)
            if metadata.get("valid") is True and _file_sha256(raw_path) == metadata.get(
                "output_sha256"
            ):
                completed.append(run_id)
    return completed


def _next_run_id(run_root: Path) -> str:
    completed = set(_completed_runs(run_root))
    for run_id in RUN_IDS:
        if run_id not in completed:
            raw_path, metadata_path = _raw_paths(run_root, run_id)
            if raw_path.exists() or metadata_path.exists():
                raise EvaluationError(
                    "WORKSPACE_CONFLICT", f"partial run artifacts exist for {run_id}"
                )
            return run_id
    raise EvaluationError("ALL_RUNS_COMPLETE", "all six valid runs already exist")


def _usage_value(usage: object, name: str) -> int | None:
    value = getattr(usage, name, None)
    if value is None and isinstance(usage, Mapping):
        value = usage.get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _nested_usage_value(usage: object, parent: str, name: str) -> int | None:
    value = getattr(usage, parent, None)
    if value is None and isinstance(usage, Mapping):
        value = usage.get(parent)
    return _usage_value(value, name)


def _response_output_text(response: object) -> str:
    value = getattr(response, "output_text", None)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError("PROVIDER_OUTPUT_INVALID", "provider returned no visible output text")
    return value.strip() + "\n"


def _lineage_for_replacement(run_root: Path, run_id: str) -> dict[str, Any] | None:
    path = run_root / "00_setup" / "invalid_replacement.json"
    if not path.exists():
        return None
    record = _load_json(path)
    return record if record.get("run_id") == run_id else None


def execute_api_run(run_root: Path, client: Any) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    if config.mode != "api":
        raise EvaluationError("MODE_MISMATCH", "run-next is available only in api mode")
    run_id = _next_run_id(root)
    preview = request_preview(root, run_id)
    slot = _slot(root, run_id)
    model_key = str(slot["model_key"])
    model = config.models[model_key]
    request_input = _request_input(root)
    started = time.monotonic()
    try:
        response = client.responses.create(
            model=model.model_id,
            input=request_input,
            reasoning={"effort": config.effort},
            max_output_tokens=config.max_output_tokens,
            tools=[],
            tool_choice="none",
            store=False,
            stream=False,
        )
    except EvaluationError:
        raise
    except Exception as error:
        status_code = getattr(error, "status_code", None)
        category = f"HTTP {status_code}" if isinstance(status_code, int) else type(error).__name__
        raise EvaluationError("PROVIDER_FAILURE", f"OpenAI request failed ({category})") from None
    latency = time.monotonic() - started
    output = _response_output_text(response)
    usage_obj = getattr(response, "usage", None)
    input_tokens = _usage_value(usage_obj, "input_tokens")
    output_tokens = _usage_value(usage_obj, "output_tokens")
    total_tokens = _usage_value(usage_obj, "total_tokens")
    cached_tokens = _nested_usage_value(usage_obj, "input_tokens_details", "cached_tokens")
    reasoning_tokens = _nested_usage_value(usage_obj, "output_tokens_details", "reasoning_tokens")
    cost_available = input_tokens is not None and output_tokens is not None and not cached_tokens
    direct_cost: Decimal | None = None
    if cost_available and input_tokens is not None and output_tokens is not None:
        direct_cost = (
            Decimal(input_tokens) * model.input_rate + Decimal(output_tokens) * model.output_rate
        ) / Decimal(1_000_000)
    raw_path, metadata_path = _raw_paths(root, run_id)
    if raw_path.exists() or metadata_path.exists():
        raise EvaluationError("WORKSPACE_CONFLICT", f"run artifacts already exist for {run_id}")
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "run_id": run_id,
        "slot_position": slot["position"],
        "model_key": model_key,
        "model_id": model.model_id,
        "effort": config.effort,
        "source": "openai-api",
        "valid": True,
        "completed_at": _utc_now(),
        "latency_seconds": round(latency, 6),
        "request_digest": preview["request_digest"],
        "output_sha256": _sha256(output.encode("utf-8")),
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "reasoning_tokens": reasoning_tokens,
        },
        "cost_available": cost_available,
        "direct_cost_usd": str(direct_cost) if direct_cost is not None else None,
        "cached_input_pricing_available": False,
        "other_pricing_categories_available": False,
        "hidden_reasoning_persisted": False,
        "tools_enabled": False,
        "store": False,
        "replacement_lineage": _lineage_for_replacement(root, run_id),
    }
    _write_once(raw_path, output.encode("utf-8"))
    try:
        _write_once(metadata_path, _pretty_json(metadata))
    except Exception:
        raw_path.unlink(missing_ok=True)
        raise
    return metadata


def _live_guard(confirm_live: bool, confirm_cost: bool) -> str:
    if not confirm_live or not confirm_cost:
        raise EvaluationError(
            "LIVE_COST_GUARD_FAILED", "both live and cost confirmations are required"
        )
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key.strip():
        raise EvaluationError("OPENAI_API_KEY_MISSING", "OPENAI_API_KEY is not configured")
    if os.environ.get("AI_NEWSROOM_ALLOW_OPENAI_SMOKE") != "1":
        raise EvaluationError(
            "LIVE_COST_GUARD_FAILED", "AI_NEWSROOM_ALLOW_OPENAI_SMOKE must equal 1"
        )
    return key


def access_check_live(
    run_root: Path,
    *,
    confirm_live: bool,
    confirm_cost: bool,
    client: Any | None = None,
) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    key = _live_guard(confirm_live, confirm_cost)
    result_path = root / "00_setup" / "access_check_results.json"
    if result_path.exists():
        raise EvaluationError("WORKSPACE_CONFLICT", "access check already recorded")
    api_client = client or OpenAI(
        api_key=key,
        max_retries=0,
        timeout=config.timeout_seconds,
    )
    results: list[dict[str, Any]] = []
    for model_key in ("terra", "sol"):
        started = time.monotonic()
        try:
            response = api_client.responses.create(
                model=config.models[model_key].model_id,
                input="Reply with exactly: ACCESS OK",
                reasoning={"effort": "none"},
                max_output_tokens=16,
                tools=[],
                tool_choice="none",
                store=False,
                stream=False,
            )
            usage = getattr(response, "usage", None)
            results.append(
                {
                    "model_key": model_key,
                    "model_id": config.models[model_key].model_id,
                    "accessible": True,
                    "latency_seconds": round(time.monotonic() - started, 6),
                    "input_tokens": _usage_value(usage, "input_tokens"),
                    "output_tokens": _usage_value(usage, "output_tokens"),
                    "may_incur_small_cost": True,
                }
            )
        except Exception as error:
            status_code = getattr(error, "status_code", None)
            results.append(
                {
                    "model_key": model_key,
                    "model_id": config.models[model_key].model_id,
                    "accessible": False,
                    "latency_seconds": round(time.monotonic() - started, 6),
                    "sanitized_error": (
                        f"HTTP {status_code}"
                        if isinstance(status_code, int)
                        else type(error).__name__
                    ),
                    "may_incur_small_cost": True,
                }
            )
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "checked_at": _utc_now(),
        "neutral_prompt": True,
        "part_of_six_runs": False,
        "sdk_retries": 0,
        "results": results,
    }
    _write_once(result_path, _pretty_json(result))
    return result


def import_run(
    run_root: Path,
    run_id: str,
    raw_output: Path,
    latency_seconds: float,
    model_id: str,
    effort: str,
    recording_path: Path | None = None,
) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    if config.mode != "chatgpt-work":
        raise EvaluationError("MODE_MISMATCH", "import-run requires chatgpt-work mode")
    expected = _next_run_id(root)
    if run_id != expected:
        raise EvaluationError("RUN_ORDER_VIOLATION", f"next frozen slot is {expected}")
    slot = _slot(root, run_id)
    model_key = str(slot["model_key"])
    if model_id != config.models[model_key].model_id or effort != config.effort:
        raise EvaluationError("RUN_IDENTITY_MISMATCH", "model or effort differs from frozen slot")
    if not 0 <= latency_seconds <= 86_400:
        raise EvaluationError("HUMAN_INPUT_INVALID", "latency must be between 0 and 86400 seconds")
    source = raw_output.resolve()
    if not source.is_file():
        raise EvaluationError("PATH_UNSAFE", "raw output must be an existing file")
    text = _read_utf8(source, max_bytes=2_000_000)
    if not text.strip():
        raise EvaluationError("HUMAN_INPUT_INVALID", "raw output is empty")
    output = text.rstrip() + "\n"
    raw_path, metadata_path = _raw_paths(root, run_id)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "run_id": run_id,
        "slot_position": slot["position"],
        "model_key": model_key,
        "model_id": model_id,
        "effort": effort,
        "source": "chatgpt-work-import",
        "source_sha256": _file_sha256(source),
        "valid": True,
        "completed_at": _utc_now(),
        "latency_seconds": latency_seconds,
        "output_sha256": _sha256(output.encode("utf-8")),
        "usage": None,
        "cost_available": False,
        "direct_cost_usd": None,
        "recording_path": str(recording_path.resolve()) if recording_path else None,
        "hidden_reasoning_persisted": False,
        "replacement_lineage": _lineage_for_replacement(root, run_id),
    }
    _write_once(raw_path, output.encode("utf-8"))
    try:
        _write_once(metadata_path, _pretty_json(metadata))
    except Exception:
        raw_path.unlink(missing_ok=True)
        raise
    return metadata


def mark_invalid(run_root: Path, run_id: str, reason: str) -> dict[str, Any]:
    root = run_root.resolve()
    _verify_workspace(root)
    _validate_run_id(run_id)
    if not reason.strip() or len(reason) > 500:
        raise EvaluationError("HUMAN_INPUT_INVALID", "technical failure reason is required")
    record_path = root / "00_setup" / "invalid_replacement.json"
    if record_path.exists():
        raise EvaluationError(
            "MORE_THAN_ONE_INVALID_REPLACEMENT", "only one replacement is allowed"
        )
    raw_path, metadata_path = _raw_paths(root, run_id)
    if not raw_path.is_file() or not metadata_path.is_file():
        raise EvaluationError("RUN_NOT_COMPLETE", f"valid artifacts are missing for {run_id}")
    archive = root / "03_raw_runs" / "invalid"
    archive.mkdir(parents=True, exist_ok=True)
    archived_raw = archive / f"{run_id}_attempt_1_raw.md"
    archived_metadata = archive / f"{run_id}_attempt_1_metadata.json"
    if archived_raw.exists() or archived_metadata.exists():
        raise EvaluationError("WORKSPACE_CONFLICT", "invalid archive already exists")
    os.replace(raw_path, archived_raw)
    os.replace(metadata_path, archived_metadata)
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "invalidated_at": _utc_now(),
        "technical_failure_reason": reason.strip(),
        "archived_raw": str(archived_raw.relative_to(root)).replace("\\", "/"),
        "archived_metadata": str(archived_metadata.relative_to(root)).replace("\\", "/"),
        "replacement_limit": 1,
    }
    _write_once(record_path, _pretty_json(record))
    return record


def _blind_mapping(config: EvaluationConfig) -> list[dict[str, str]]:
    shuffled = list(RUN_IDS)
    random.Random(config.blind_seed).shuffle(shuffled)
    mapping: list[dict[str, str]] = []
    for output_id, run_id in zip(OUTPUT_IDS, shuffled, strict=True):
        model_key = RUN_ORDER[RUN_IDS.index(run_id)]
        mapping.append(
            {
                "output_id": output_id,
                "run_id": run_id,
                "model_key": model_key,
                "model_id": config.models[model_key].model_id,
            }
        )
    return mapping


def _csv_bytes(fields: Iterable[str], rows: Iterable[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    field_list = list(fields)
    writer = csv.DictWriter(
        stream, fieldnames=field_list, lineterminator="\n", extrasaction="ignore"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in field_list})
    return stream.getvalue().encode("utf-8")


def _blind_text(text: str, model_ids: Iterable[str]) -> tuple[str, int]:
    kept_lines: list[str] = []
    removed = 0
    for line in text.splitlines():
        if re.match(r"^\s*(?:model|модель|run[ _-]?id)\s*:", line, flags=re.IGNORECASE):
            removed += 1
            continue
        kept_lines.append(line)
    blinded = "\n".join(kept_lines).rstrip() + "\n"
    identity_patterns = [
        *(re.compile(re.escape(identity), flags=re.IGNORECASE) for identity in model_ids),
        re.compile(re.escape("GPT-5.6 Terra"), flags=re.IGNORECASE),
        re.compile(re.escape("GPT-5.6 Sol"), flags=re.IGNORECASE),
        re.compile(r"\b(?:terra|sol)\b", flags=re.IGNORECASE),
    ]
    for pattern in identity_patterns:
        blinded, count = pattern.subn("[MODEL]", blinded)
        removed += count
    if any(pattern.search(blinded) for pattern in identity_patterns):
        raise EvaluationError("BLINDING_FAILED", "model identity remains after exact redaction")
    return blinded, removed


def blind_runs(run_root: Path) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    if _completed_runs(root) != list(RUN_IDS):
        raise EvaluationError("BLINDING_FAILED", "six valid frozen runs are required")
    mapping = _blind_mapping(config)
    mapping_rows: list[dict[str, object]] = []
    blind_files: dict[str, bytes] = {}
    for row in mapping:
        raw_path, _ = _raw_paths(root, row["run_id"])
        blinded, redactions = _blind_text(
            _read_utf8(raw_path, max_bytes=2_000_000),
            (config.models["terra"].model_id, config.models["sol"].model_id),
        )
        blind_files[row["output_id"]] = blinded.encode("utf-8")
        mapping_rows.append(
            {**row, "redaction_count": redactions, "source_sha256": _file_sha256(raw_path)}
        )
    mapping_bytes = _csv_bytes(
        ("output_id", "run_id", "model_key", "model_id", "redaction_count", "source_sha256"),
        mapping_rows,
    )
    blind_root = root / "05_blind_review"
    existing_mapping = blind_root / "blind_mapping_PRIVATE.csv"
    if existing_mapping.exists() and existing_mapping.read_bytes() != mapping_bytes:
        raise EvaluationError("BLINDING_FAILED", "conflicting blind mapping exists")
    for output_id, data in blind_files.items():
        _write_once(blind_root / f"{output_id}.md", data)
    _write_once(existing_mapping, mapping_bytes)
    manifest_data = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "mapping_sha256": _sha256(mapping_bytes),
        "outputs": [
            {
                "output_id": row["output_id"],
                "sha256": _sha256(blind_files[str(row["output_id"])]),
                "redaction_count": row["redaction_count"],
            }
            for row in mapping_rows
        ],
        "originals_preserved": True,
    }
    _write_once(blind_root / "blind_manifest.json", _pretty_json(manifest_data))
    return manifest_data


def _read_csv(path: Path, expected_fields: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != expected_fields:
                raise EvaluationError("HUMAN_INPUT_INVALID", f"invalid header in {path.name}")
            rows = [dict(row) for row in reader]
    except OSError:
        raise EvaluationError("HUMAN_INPUT_INVALID", f"cannot read {path.name}") from None
    if len(rows) != 6 or {row["output_id"] for row in rows} != set(OUTPUT_IDS):
        raise EvaluationError("HUMAN_INPUT_INVALID", f"{path.name} must contain A-F exactly once")
    return rows


def _parse_bool(value: str, field: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise EvaluationError("HUMAN_INPUT_INVALID", f"{field} must be true or false")


def validate_human_input(run_root: Path) -> dict[str, list[dict[str, Any]]]:
    root = run_root.resolve()
    config, _, _ = _verify_workspace(root)
    _validated_mapping_rows(root, config)
    score_path = root / "05_blind_review" / "scores.csv"
    correction_path = root / "06_corrections" / "correction_log.csv"
    combined = score_path.read_text(encoding="utf-8") + correction_path.read_text(encoding="utf-8")
    identities = [
        config.models["terra"].model_id,
        config.models["sol"].model_id,
        "GPT-5.6 Terra",
        "GPT-5.6 Sol",
    ]
    if any(
        re.search(re.escape(identity), combined, flags=re.IGNORECASE) for identity in identities
    ) or re.search(r"\b(?:terra|sol)\b", combined, flags=re.IGNORECASE):
        raise EvaluationError(
            "HUMAN_INPUT_INVALID", "model identity appears in blinded human input"
        )
    scores_raw = _read_csv(score_path, SCORE_FIELDS)
    corrections_raw = _read_csv(correction_path, CORRECTION_FIELDS)
    scores: list[dict[str, Any]] = []
    for row in scores_raw:
        parsed: dict[str, Any] = {"output_id": row["output_id"]}
        total = 0
        for field, (lower, upper) in SCORE_RANGES.items():
            try:
                value = int(row[field])
            except ValueError:
                raise EvaluationError(
                    "HUMAN_INPUT_INVALID", f"{field} must be an integer"
                ) from None
            if not lower <= value <= upper:
                raise EvaluationError("HUMAN_INPUT_INVALID", f"{field} is outside rubric range")
            parsed[field] = value
            total += value
        try:
            critical_count = int(row["critical_error_count"])
        except ValueError:
            raise EvaluationError(
                "HUMAN_INPUT_INVALID", "critical_error_count must be integer"
            ) from None
        if critical_count < 0:
            raise EvaluationError("HUMAN_INPUT_INVALID", "critical_error_count cannot be negative")
        if critical_count and not row["critical_error_notes"].strip():
            raise EvaluationError("HUMAN_INPUT_INVALID", "critical error notes are required")
        if not _parse_bool(row["review_complete"], "review_complete"):
            raise EvaluationError("HUMAN_INPUT_INVALID", "all reviews must be complete")
        parsed.update(
            {
                "critical_error_count": critical_count,
                "critical_error_notes": row["critical_error_notes"],
                "review_complete": True,
                "total_score": total,
            }
        )
        scores.append(parsed)
    corrections: list[dict[str, Any]] = []
    for row in corrections_raw:
        try:
            minutes = Decimal(row["minutes"])
        except InvalidOperation:
            raise EvaluationError("HUMAN_INPUT_INVALID", "minutes must be decimal") from None
        if not Decimal(0) <= minutes <= Decimal(20):
            raise EvaluationError("HUMAN_INPUT_INVALID", "minutes must be between 0 and 20")
        accepted = _parse_bool(row["accepted"], "accepted")
        if not _parse_bool(row["timer_complete"], "timer_complete"):
            raise EvaluationError("HUMAN_INPUT_INVALID", "all timers must be complete")
        if not accepted and not any(
            row[field].strip()
            for field in ("critical_fixes", "major_additions", "minor_edits", "notes")
        ):
            raise EvaluationError("HUMAN_INPUT_INVALID", "non-acceptance needs an explicit note")
        corrections.append(
            {
                "output_id": row["output_id"],
                "minutes": minutes,
                "accepted": accepted,
                "critical_fixes": row["critical_fixes"],
                "major_additions": row["major_additions"],
                "minor_edits": row["minor_edits"],
                "notes": row["notes"],
                "timer_complete": True,
            }
        )
    return {"scores": scores, "corrections": corrections}


def choose_verdict(metrics: Mapping[str, Mapping[str, Any]]) -> str:
    if set(metrics) != {"terra", "sol"} or any(metrics[key].get("n") != 3 for key in metrics):
        return "INCONCLUSIVE"
    terra = metrics["terra"]
    sol = metrics["sol"]
    score_delta = Decimal(str(sol["median_score"])) - Decimal(str(terra["median_score"]))
    critical_delta = int(sol["critical_error_total"]) - int(terra["critical_error_total"])
    correction_delta = Decimal(str(sol["median_correction_minutes"])) - Decimal(
        str(terra["median_correction_minutes"])
    )
    accepted_delta = int(sol["accepted_within_20"]) - int(terra["accepted_within_20"])
    if score_delta >= 1 and critical_delta <= 0 and correction_delta <= 5:
        return "SOL"
    if score_delta <= -1 and critical_delta >= 0 and correction_delta >= -5:
        return "TERRA"
    if critical_delta <= -2 and score_delta >= Decimal("-1.5"):
        return "SOL"
    if critical_delta >= 2 and score_delta <= Decimal("1.5"):
        return "TERRA"
    if accepted_delta >= 2 and critical_delta <= 0:
        return "SOL"
    if accepted_delta <= -2 and critical_delta >= 0:
        return "TERRA"
    return "MIXED"


def _median_decimal(values: list[Decimal]) -> Decimal:
    return Decimal(str(median(values)))


def _range_text(values: Sequence[Decimal | float | int]) -> str:
    return f"{min(values)}-{max(values)}"


def _mapping_rows(path: Path) -> list[dict[str, str]]:
    return _read_csv(path, MAPPING_FIELDS)


def _validated_mapping_rows(root: Path, config: EvaluationConfig) -> list[dict[str, str]]:
    blind_root = root / "05_blind_review"
    mapping_path = blind_root / "blind_mapping_PRIVATE.csv"
    manifest_path = blind_root / "blind_manifest.json"
    if not mapping_path.is_file() or not manifest_path.is_file():
        raise EvaluationError("HUMAN_INPUT_INVALID", "blind mapping or manifest is missing")
    try:
        mapping_bytes = mapping_path.read_bytes()
    except OSError:
        raise EvaluationError("HUMAN_INPUT_INVALID", "cannot read blind mapping") from None
    blind_manifest = _load_json(manifest_path)
    if blind_manifest.get("mapping_sha256") != _sha256(mapping_bytes):
        raise EvaluationError("HUMAN_INPUT_INVALID", "blind mapping digest mismatch")

    rows = _mapping_rows(mapping_path)
    expected = {row["output_id"]: row for row in _blind_mapping(config)}
    for row in rows:
        expected_row = expected[row["output_id"]]
        if any(row[field] != expected_row[field] for field in ("run_id", "model_key", "model_id")):
            raise EvaluationError("HUMAN_INPUT_INVALID", "blind mapping identity mismatch")
        try:
            redaction_count = int(row["redaction_count"])
        except ValueError:
            raise EvaluationError(
                "HUMAN_INPUT_INVALID", "blind mapping redaction count is invalid"
            ) from None
        if redaction_count < 0:
            raise EvaluationError("HUMAN_INPUT_INVALID", "blind mapping redaction count is invalid")
        raw_path, _ = _raw_paths(root, row["run_id"])
        if not raw_path.is_file() or row["source_sha256"] != _file_sha256(raw_path):
            raise EvaluationError("HUMAN_INPUT_INVALID", "blind mapping source digest mismatch")
    return rows


def _chart_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _result_chart(metrics: Mapping[str, Mapping[str, Any]], verdict: str) -> bytes:
    image = Image.new("RGB", (1920, 1080), "#0b1020")
    draw = ImageDraw.Draw(image)
    title_font = _chart_font(62, bold=True)
    body_font = _chart_font(38)
    metric_font = _chart_font(46, bold=True)
    small_font = _chart_font(30)
    draw.text((170, 70), "GPT-5.6 Terra vs Sol", font=title_font, fill="#f8fafc")
    draw.text(
        (170, 150),
        "Контролируемое слепое сравнение · n=3 на модель",
        font=body_font,
        fill="#a5b4fc",
    )
    colors = {"terra": "#34d399", "sol": "#60a5fa"}
    for index, key in enumerate(("terra", "sol")):
        x = 170 + index * 800
        y = 260
        draw.rounded_rectangle(
            (x, y, x + 700, y + 520), radius=28, fill="#151d33", outline=colors[key], width=4
        )
        label = "TERRA" if key == "terra" else "SOL"
        draw.text((x + 45, y + 35), label, font=title_font, fill=colors[key])
        values = metrics[key]
        lines = (
            ("Медиана оценки", f"{values['median_score']} / 10"),
            ("Критические ошибки", str(values["critical_error_total"])),
            ("Медиана правок", f"{values['median_correction_minutes']} мин"),
            ("Принято ≤20 мин", f"{values['accepted_within_20']} / 3"),
        )
        for line_index, (label_text, value_text) in enumerate(lines):
            line_y = y + 140 + line_index * 88
            draw.text((x + 45, line_y), label_text, font=small_font, fill="#cbd5e1")
            draw.text((x + 430, line_y - 7), value_text, font=metric_font, fill="#f8fafc")
        if values.get("direct_cost_total_usd") is not None:
            draw.text(
                (x + 45, y + 485),
                f"API cost: ${values['direct_cost_total_usd']}",
                font=small_font,
                fill="#fde68a",
            )
    verdict_color = "#fbbf24" if verdict in {"MIXED", "INCONCLUSIVE"} else "#f8fafc"
    draw.text((170, 825), f"Вердикт: {verdict}", font=title_font, fill=verdict_color)
    draw.text(
        (170, 940),
        "Один синтетический CRM-инцидент; не универсальный рейтинг",
        font=body_font,
        fill="#cbd5e1",
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def analyze_results(run_root: Path) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    human = validate_human_input(root)
    mapping = _validated_mapping_rows(root, config)
    score_by_id = {str(row["output_id"]): row for row in human["scores"]}
    correction_by_id = {str(row["output_id"]): row for row in human["corrections"]}
    run_rows: list[dict[str, Any]] = []
    for map_row in mapping:
        metadata = _load_json(root / "03_raw_runs" / f"{map_row['run_id']}_metadata.json")
        score = score_by_id[map_row["output_id"]]
        correction = correction_by_id[map_row["output_id"]]
        run_rows.append(
            {
                "output_id": map_row["output_id"],
                "run_id": map_row["run_id"],
                "model_key": map_row["model_key"],
                "model_id": map_row["model_id"],
                "total_score": score["total_score"],
                "critical_error_count": score["critical_error_count"],
                "correction_minutes": str(correction["minutes"]),
                "accepted": correction["accepted"],
                "latency_seconds": metadata["latency_seconds"],
                "input_tokens": (metadata.get("usage") or {}).get("input_tokens"),
                "output_tokens": (metadata.get("usage") or {}).get("output_tokens"),
                "cost_available": metadata.get("cost_available") is True,
                "direct_cost_usd": metadata.get("direct_cost_usd"),
            }
        )
    metrics: dict[str, dict[str, Any]] = {}
    for key in ("terra", "sol"):
        selected = [row for row in run_rows if row["model_key"] == key]
        scores = [int(row["total_score"]) for row in selected]
        corrections = [Decimal(str(row["correction_minutes"])) for row in selected]
        latencies = [float(row["latency_seconds"]) for row in selected]
        costs_available = all(row["cost_available"] for row in selected)
        costs = [Decimal(str(row["direct_cost_usd"])) for row in selected if row["cost_available"]]
        metrics[key] = {
            "n": len(selected),
            "individual_scores": scores,
            "median_score": str(median(scores)),
            "score_range": _range_text(scores),
            "critical_error_total": sum(int(row["critical_error_count"]) for row in selected),
            "outputs_with_critical_errors": sum(
                int(row["critical_error_count"]) > 0 for row in selected
            ),
            "median_correction_minutes": str(_median_decimal(corrections)),
            "correction_range": _range_text(corrections),
            "accepted_within_20": sum(bool(row["accepted"]) for row in selected),
            "median_latency_seconds": str(median(latencies)),
            "latency_range": _range_text(latencies),
            "direct_cost_available": costs_available and config.mode == "api",
            "direct_cost_total_usd": str(sum(costs, Decimal(0)))
            if costs_available and config.mode == "api"
            else None,
            "input_tokens_total": sum(
                int(row["input_tokens"]) for row in selected if row["input_tokens"] is not None
            )
            if all(row["input_tokens"] is not None for row in selected)
            else None,
            "output_tokens_total": sum(
                int(row["output_tokens"]) for row in selected if row["output_tokens"] is not None
            )
            if all(row["output_tokens"] is not None for row in selected)
            else None,
        }
    verdict = choose_verdict(metrics)
    result_root = root / "07_results"
    summary_rows = [{"model": key.upper(), **metrics[key]} for key in ("terra", "sol")]
    summary_fields = (
        "model",
        "n",
        "individual_scores",
        "median_score",
        "score_range",
        "critical_error_total",
        "outputs_with_critical_errors",
        "median_correction_minutes",
        "correction_range",
        "accepted_within_20",
        "median_latency_seconds",
        "latency_range",
        "input_tokens_total",
        "output_tokens_total",
        "direct_cost_available",
        "direct_cost_total_usd",
    )
    run_fields = (
        "output_id",
        "run_id",
        "model_key",
        "model_id",
        "total_score",
        "critical_error_count",
        "correction_minutes",
        "accepted",
        "latency_seconds",
        "input_tokens",
        "output_tokens",
        "cost_available",
        "direct_cost_usd",
    )
    summary_bytes = _csv_bytes(summary_fields, summary_rows)
    run_bytes = _csv_bytes(run_fields, run_rows)
    conclusion = (
        "# Editorial conclusion\n\n"
        f"Verdict: **{verdict}**\n\n"
        "This result covers one synthetic CRM incident and three runs per model. It is not a "
        "universal ranking or publication approval. Critical errors, correction time, and rubric "
        "scores are reported separately; API rates are not converted into labor cost.\n\n"
        + (
            "ChatGPT Work mode provides no measured direct API cost.\n"
            if config.mode == "chatgpt-work"
            else "Direct API cost uses only frozen verified input/output token rates.\n"
        )
    ).encode("utf-8")
    chart = _result_chart(metrics, verdict)
    artifacts = {
        "results_summary.csv": summary_bytes,
        "run_results.csv": run_bytes,
        "editorial_conclusion.md": conclusion,
        "result_chart.png": chart,
    }
    for name, data in artifacts.items():
        _write_once(result_root / name, data)
    result_manifest = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "verdict": verdict,
        "n_per_model": 3,
        "mode": config.mode,
        "synthetic_single_task_limitation": True,
        "artifacts": {name: _sha256(data) for name, data in artifacts.items()},
    }
    _write_once(result_root / "result_manifest.json", _pretty_json(result_manifest))
    return {"verdict": verdict, "metrics": metrics, "result_manifest": result_manifest}


def evidence_manifest(run_root: Path) -> dict[str, Any]:
    root = run_root.resolve()
    _, _, manifest = _verify_workspace(root)
    expected: list[Path] = []
    expected.extend((root / "00_setup").glob("*"))
    expected.extend((root / "01_fixture").glob("*"))
    expected.extend((root / "02_private_reference").glob("*"))
    for run_id in RUN_IDS:
        expected.extend(_raw_paths(root, run_id))
    expected.extend((root / "05_blind_review").glob("*"))
    expected.extend((root / "06_corrections").glob("*"))
    expected.extend((root / "07_results").glob("*"))
    expected.append(root / "08_video" / "capcut_assembly_checklist.md")
    inventory: list[dict[str, Any]] = []
    missing: list[str] = []
    seen: set[Path] = set()
    for path in expected:
        if path.name == "evidence_manifest.json" or path in seen:
            continue
        seen.add(path)
        relative = str(path.relative_to(root)).replace("\\", "/")
        if path.is_file():
            inventory.append(
                {"path": relative, "bytes": path.stat().st_size, "sha256": _file_sha256(path)}
            )
        else:
            missing.append(relative)
    recordings: list[str] = []
    for run_id in RUN_IDS:
        _, metadata_path = _raw_paths(root, run_id)
        if metadata_path.is_file():
            recording = _load_json(metadata_path).get("recording_path")
            if isinstance(recording, str) and recording:
                recordings.append(recording)
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": manifest["experiment_id"],
        "inventory": sorted(inventory, key=lambda item: str(item["path"])),
        "recording_paths": recordings,
        "missing_assets": sorted(set(missing)),
        "api_key_included": False,
        "scope": [
            "setup",
            "fixtures",
            "raw_runs",
            "recording_paths",
            "blind_review",
            "human_inputs",
            "results",
            "chart",
        ],
    }
    encoded = _pretty_json(result)
    forbidden = os.environ.get("OPENAI_API_KEY", "")
    if forbidden and forbidden.encode("utf-8") in encoded:
        raise EvaluationError("SECRET_BOUNDARY_FAILED", "API key entered evidence manifest")
    _write_once(root / "07_results" / "evidence_manifest.json", encoded)
    return result


def workspace_status(run_root: Path, *, write_file: bool = True) -> dict[str, Any]:
    root = run_root.resolve()
    config, _, manifest = _verify_workspace(root)
    completed = _completed_runs(root)
    invalid_path = root / "00_setup" / "invalid_replacement.json"
    invalid_unresolved = False
    if invalid_path.exists():
        invalid_run_id = _load_json(invalid_path).get("run_id")
        invalid_unresolved = invalid_run_id not in completed
    blind_ready = len(completed) == 6 and not invalid_unresolved
    blind_files_ready = all(
        (root / "05_blind_review" / f"{label}.md").is_file() for label in OUTPUT_IDS
    )
    human_ready = False
    if blind_files_ready:
        try:
            validate_human_input(root)
            human_ready = True
        except EvaluationError:
            human_ready = False
    analysis_ready = human_ready and len(completed) == 6
    analyzed = (root / "07_results" / "result_manifest.json").is_file()
    if len(completed) < 6:
        next_action = f"execute or import {_next_run_id(root)}"
    elif not blind_files_ready:
        next_action = "run blind"
    elif not human_ready:
        next_action = "complete scores.csv and correction_log.csv, then validate-human-input"
    elif not analyzed:
        next_action = "run analyze"
    else:
        next_action = "run evidence-manifest and complete owner QA"
    status = {
        "experiment_id": manifest["experiment_id"],
        "mode": config.mode,
        "completed_runs": completed,
        "invalid_replacements": 1 if invalid_path.exists() else 0,
        "blind_readiness": blind_ready,
        "blind_files_ready": blind_files_ready,
        "scores_readiness": human_ready,
        "correction_readiness": human_ready,
        "analysis_readiness": analysis_ready,
        "analyzed": analyzed,
        "next_action": next_action,
    }
    if write_file:
        _replace_status(root / "STATUS.md", _status_markdown(status).encode("utf-8"))
    return status


def _status_markdown(status: Mapping[str, Any]) -> str:
    completed = ", ".join(str(value) for value in status["completed_runs"]) or "none"
    return (
        "# Track A status\n\n"
        f"- Experiment ID: `{status['experiment_id']}`\n"
        f"- Mode: `{status['mode']}`\n"
        f"- Completed runs: {completed}\n"
        f"- Invalid replacements: {status['invalid_replacements']}\n"
        f"- Blind readiness: {status['blind_readiness']}\n"
        f"- Scores readiness: {status['scores_readiness']}\n"
        f"- Correction readiness: {status['correction_readiness']}\n"
        f"- Analysis readiness: {status['analysis_readiness']}\n"
        f"- Next action: {status['next_action']}\n"
    )


def _emit(value: Any) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _terminal_safe_text(value: str) -> str:
    safe: list[str] = []
    for character in value:
        codepoint = ord(character)
        if character in "\n\r\t" or not (codepoint < 32 or 127 <= codepoint <= 159):
            safe.append(character)
        else:
            safe.append(f"\\u{codepoint:04x}")
    return "".join(safe)


def _command_error(error: EvaluationError) -> None:
    typer.echo(f"{error.code}: {error.message}", err=True)
    raise typer.Exit(code=1)


@app.command("prepare")
def prepare_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        _emit(prepare_workspace(config, run_root))
    except EvaluationError as error:
        _command_error(error)


@app.command("status")
def status_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        _emit(workspace_status(run_root))
    except EvaluationError as error:
        _command_error(error)


@app.command("request-preview")
def request_preview_command(
    run_id: Annotated[str, typer.Option("--run-id")],
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        _emit(request_preview(run_root, run_id))
    except EvaluationError as error:
        _command_error(error)


@app.command("access-check")
def access_check_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
    confirm_live: Annotated[bool, typer.Option("--confirm-live")] = False,
    confirm_cost: Annotated[bool, typer.Option("--confirm-cost")] = False,
) -> None:
    try:
        _emit(
            access_check_live(
                run_root,
                confirm_live=confirm_live,
                confirm_cost=confirm_cost,
            )
        )
    except EvaluationError as error:
        _command_error(error)


@app.command("run-next")
def run_next_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
    confirm_live: Annotated[bool, typer.Option("--confirm-live")] = False,
    confirm_cost: Annotated[bool, typer.Option("--confirm-cost")] = False,
    show_output: Annotated[bool, typer.Option("--show-output")] = False,
) -> None:
    try:
        root = run_root.resolve()
        config, _, _ = _verify_workspace(root)
        key = _live_guard(confirm_live, confirm_cost)
        client = OpenAI(api_key=key, max_retries=0, timeout=config.timeout_seconds)
        metadata = execute_api_run(root, client)
        concise = {
            "run_id": metadata["run_id"],
            "model_id": metadata["model_id"],
            "latency_seconds": metadata["latency_seconds"],
            "cost_available": metadata["cost_available"],
            "direct_cost_usd": metadata["direct_cost_usd"],
        }
        _emit(concise)
        if show_output:
            raw_path, _ = _raw_paths(root, str(metadata["run_id"]))
            typer.echo(_terminal_safe_text(raw_path.read_text(encoding="utf-8")))
    except EvaluationError as error:
        _command_error(error)


@app.command("mark-invalid")
def mark_invalid_command(
    run_id: Annotated[str, typer.Option("--run-id")],
    reason: Annotated[str, typer.Option("--reason")],
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        _emit(mark_invalid(run_root, run_id, reason))
    except EvaluationError as error:
        _command_error(error)


@app.command("import-run")
def import_run_command(
    run_id: Annotated[str, typer.Option("--run-id")],
    raw_output: Annotated[Path, typer.Option("--raw-output")],
    latency_seconds: Annotated[float, typer.Option("--latency-seconds")],
    model_id: Annotated[str, typer.Option("--model-id")],
    effort: Annotated[str, typer.Option("--effort")],
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
    recording_path: Annotated[Path | None, typer.Option("--recording-path")] = None,
) -> None:
    try:
        _emit(
            import_run(
                run_root,
                run_id,
                raw_output,
                latency_seconds,
                model_id,
                effort,
                recording_path,
            )
        )
    except EvaluationError as error:
        _command_error(error)


@app.command("blind")
def blind_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        _emit(blind_runs(run_root))
    except EvaluationError as error:
        _command_error(error)


@app.command("validate-human-input")
def validate_human_input_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        validated = validate_human_input(run_root)
        _emit({"scores": len(validated["scores"]), "corrections": len(validated["corrections"])})
    except EvaluationError as error:
        _command_error(error)


@app.command("analyze")
def analyze_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        result = analyze_results(run_root)
        _emit({"verdict": result["verdict"], "metrics": result["metrics"]})
    except EvaluationError as error:
        _command_error(error)


@app.command("evidence-manifest")
def evidence_manifest_command(
    run_root: Annotated[Path, typer.Option("--run-root")] = DEFAULT_RUN_ROOT,
) -> None:
    try:
        result = evidence_manifest(run_root)
        _emit({"files": len(result["inventory"]), "missing_assets": result["missing_assets"]})
    except EvaluationError as error:
        _command_error(error)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
