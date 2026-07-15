from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image
from typer.testing import CliRunner

from ai_newsroom.experiments import gpt56_eval as evaluation


@dataclass
class FakeUsage:
    input_tokens: int = 1_000
    output_tokens: int = 500
    total_tokens: int = 1_500
    input_tokens_details: object = None
    output_tokens_details: object = None

    def __post_init__(self) -> None:
        self.input_tokens_details = SimpleNamespace(cached_tokens=0)
        self.output_tokens_details = SimpleNamespace(reasoning_tokens=100)


@dataclass
class FakeResponse:
    output_text: str
    usage: FakeUsage


class FakeResponsesClient:
    def __init__(self, *, self_identify: bool = False, bare_identity: bool = False) -> None:
        self.responses = self
        self.calls: list[dict[str, Any]] = []
        self.self_identify = self_identify
        self.bare_identity = bare_identity

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        suffix = f"\nModel: {kwargs['model']}" if self.self_identify else ""
        if self.bare_identity:
            alias = "Terra" if str(kwargs["model"]).endswith("terra") else "Sol"
            suffix = f"\nI am {alias}."
        return FakeResponse(
            f"# Синтетический анализ {len(self.calls)}\n\nФакт E001.{suffix}",
            FakeUsage(),
        )


@pytest.fixture
def prepared(tmp_path: Path) -> Path:
    root = tmp_path / "run-root"
    evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, root)
    return root


def _work_config(tmp_path: Path) -> Path:
    source = evaluation.DEFAULT_CONFIG.read_text(encoding="utf-8")
    path = tmp_path / "work.toml"
    path.write_text(source.replace('mode = "api"', 'mode = "chatgpt-work"'), encoding="utf-8")
    return path


def _prepare_all_runs(root: Path, *, self_identify: bool = False) -> FakeResponsesClient:
    client = FakeResponsesClient(self_identify=self_identify)
    for _ in evaluation.RUN_IDS:
        evaluation.execute_api_run(root, client)
    return client


def _write_human_inputs(root: Path, *, model_specific: bool = False) -> None:
    mapping_path = root / "05_blind_review" / "blind_mapping_PRIVATE.csv"
    with mapping_path.open("r", encoding="utf-8", newline="") as stream:
        mapping = {row["output_id"]: row for row in csv.DictReader(stream)}
    scores_path = root / "05_blind_review" / "scores.csv"
    with scores_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=evaluation.SCORE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for output_id in evaluation.OUTPUT_IDS:
            high = not model_specific or mapping[output_id]["model_key"] == "sol"
            writer.writerow(
                {
                    "output_id": output_id,
                    "factual_accuracy": 2 if high else 1,
                    "root_cause_reasoning": 1,
                    "idempotency": 1,
                    "timeout_retry": 1,
                    "assignment": 1,
                    "remediation": 1,
                    "uat": 1,
                    "risks_assumptions": 1,
                    "practical_usability": 1 if high else 0,
                    "critical_error_count": 0 if high else 1,
                    "critical_error_notes": "" if high else "Пропущен безопасный rollback",
                    "review_complete": "true",
                }
            )
    correction_path = root / "06_corrections" / "correction_log.csv"
    with correction_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=evaluation.CORRECTION_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        for output_id in evaluation.OUTPUT_IDS:
            high = not model_specific or mapping[output_id]["model_key"] == "sol"
            writer.writerow(
                {
                    "output_id": output_id,
                    "minutes": "4.5" if high else "12",
                    "accepted": "true" if high else "false",
                    "critical_fixes": "" if high else "Добавлен rollback",
                    "major_additions": "",
                    "minor_edits": "Стиль",
                    "notes": "",
                    "timer_complete": "true",
                }
            )


def _complete_workflow(root: Path) -> dict[str, Any]:
    _prepare_all_runs(root, self_identify=True)
    evaluation.blind_runs(root)
    _write_human_inputs(root, model_specific=True)
    evaluation.validate_human_input(root)
    result = evaluation.analyze_results(root)
    evaluation.evidence_manifest(root)
    return result


def test_fixture_structure_cardinality_and_unique_events() -> None:
    manifest = evaluation.validate_fixtures()
    assert manifest["event_row_count"] == 24
    assert manifest["external_lead_id_count"] == 10
    assert manifest["request_input_set"] == [
        "01_incident_brief.md",
        "02_event_log.csv",
        "03_acceptance_criteria.md",
        "master_prompt.md",
    ]


def test_reference_key_uses_only_valid_event_ids() -> None:
    manifest = evaluation.validate_fixtures()
    assert len(manifest["reference_sha256"]) == 64


def test_private_reference_is_excluded_from_payload(prepared: Path) -> None:
    preview = evaluation.request_preview(prepared, "run_01")
    assert preview["private_reference_excluded"] is True
    assert evaluation.REFERENCE_FILE not in preview["request_input_set"]
    assert evaluation.REFERENCE_FILE not in evaluation._request_input(prepared)


def test_canonical_identities_are_stable(tmp_path: Path) -> None:
    first = evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, tmp_path / "a")
    second = evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, tmp_path / "b")
    assert first["experiment_id"] == second["experiment_id"]
    assert (
        evaluation.request_preview(tmp_path / "a", "run_01")["request_digest"]
        == (evaluation.request_preview(tmp_path / "b", "run_01")["request_digest"])
    )


def test_prepare_is_idempotent(prepared: Path) -> None:
    before = (prepared / "00_setup" / "experiment_manifest.json").read_bytes()
    result = evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, prepared)
    assert result["created"] is False
    assert (prepared / "00_setup" / "experiment_manifest.json").read_bytes() == before


def test_prepare_rejects_conflicting_workspace(tmp_path: Path) -> None:
    root = tmp_path / "conflict"
    root.mkdir()
    (root / "owner.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(evaluation.EvaluationError, match="non-empty"):
        evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, root)


def test_run_order_is_frozen_three_per_model(prepared: Path) -> None:
    order = json.loads((prepared / "00_setup" / "run_order.json").read_text(encoding="utf-8"))
    keys = [slot["model_key"] for slot in order["slots"]]
    assert keys == ["terra", "sol", "sol", "terra", "terra", "sol"]
    assert keys.count("terra") == keys.count("sol") == 3


def test_request_preview_has_same_effort_and_no_tools_or_web(prepared: Path) -> None:
    terra = evaluation.request_preview(prepared, "run_01")
    sol = evaluation.request_preview(prepared, "run_02")
    assert terra["effort"] == sol["effort"] == "medium"
    assert terra["tools"] == []
    assert terra["tool_choice"] == "none"
    assert terra["web_enabled"] is False


def test_missing_key_blocks_live_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AI_NEWSROOM_ALLOW_OPENAI_SMOKE", "1")
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation._live_guard(True, True)
    assert error.value.code == "OPENAI_API_KEY_MISSING"


@pytest.mark.parametrize(
    "confirm_live,confirm_cost", [(False, False), (True, False), (False, True)]
)
def test_both_confirmation_flags_are_required(
    monkeypatch: pytest.MonkeyPatch, confirm_live: bool, confirm_cost: bool
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "local-test-key")
    monkeypatch.setenv("AI_NEWSROOM_ALLOW_OPENAI_SMOKE", "1")
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation._live_guard(confirm_live, confirm_cost)
    assert error.value.code == "LIVE_COST_GUARD_FAILED"


def test_fake_api_run_stores_visible_output_usage_and_no_reasoning(prepared: Path) -> None:
    client = FakeResponsesClient()
    metadata = evaluation.execute_api_run(prepared, client)
    assert metadata["usage"]["input_tokens"] == 1_000
    assert metadata["usage"]["reasoning_tokens"] == 100
    assert metadata["hidden_reasoning_persisted"] is False
    assert "reasoning_content" not in json.dumps(metadata)
    assert client.calls[0]["tools"] == []
    assert client.calls[0]["tool_choice"] == "none"
    assert client.calls[0]["store"] is False


def test_api_key_never_enters_files_or_terminal_result(
    prepared: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "sk-do-not-persist-123"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    metadata = evaluation.execute_api_run(prepared, FakeResponsesClient())
    assert secret not in json.dumps(metadata)
    for path in prepared.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()


def test_show_output_escapes_terminal_controls_but_preserves_raw_evidence(
    prepared: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = FakeResponsesClient()
    control_text = "# Ответ\n\nДо\x1b[2Jпосле\x1b]52;c;ZmFrZQ==\x07"

    def create(**kwargs: Any) -> FakeResponse:
        client.calls.append(kwargs)
        return FakeResponse(control_text, FakeUsage())

    client.create = create  # type: ignore[method-assign]
    monkeypatch.setattr(evaluation, "OpenAI", lambda **_: client)
    monkeypatch.setenv("OPENAI_API_KEY", "local-test-key")
    monkeypatch.setenv("AI_NEWSROOM_ALLOW_OPENAI_SMOKE", "1")
    result = CliRunner().invoke(
        evaluation.app,
        [
            "run-next",
            "--run-root",
            str(prepared),
            "--confirm-live",
            "--confirm-cost",
            "--show-output",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "\x1b" not in result.output
    assert "\\u001b[2J" in result.output
    raw = (prepared / "03_raw_runs" / "run_01_raw.md").read_text(encoding="utf-8")
    assert "\x1b[2J" in raw
    assert "\x1b]52;" in raw


def test_completed_run_cannot_be_overwritten(tmp_path: Path) -> None:
    root = tmp_path / "work"
    config = _work_config(tmp_path)
    evaluation.prepare_workspace(config, root)
    output = tmp_path / "answer.md"
    output.write_text("# Ответ\n\nE001", encoding="utf-8")
    evaluation.import_run(root, "run_01", output, 3.0, "gpt-5.6-terra", "medium")
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation.import_run(root, "run_01", output, 3.0, "gpt-5.6-terra", "medium")
    assert error.value.code == "RUN_ORDER_VIOLATION"


def test_only_one_invalid_replacement_is_permitted(prepared: Path) -> None:
    evaluation.execute_api_run(prepared, FakeResponsesClient())
    evaluation.mark_invalid(prepared, "run_01", "transport truncated the visible output")
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation.mark_invalid(prepared, "run_01", "another technical issue")
    assert error.value.code == "MORE_THAN_ONE_INVALID_REPLACEMENT"
    assert (prepared / "03_raw_runs" / "invalid" / "run_01_attempt_1_raw.md").is_file()


@pytest.mark.parametrize(
    "run_id,model_id,effort,code",
    [
        ("run_02", "gpt-5.6-sol", "medium", "RUN_ORDER_VIOLATION"),
        ("run_01", "gpt-5.6-sol", "medium", "RUN_IDENTITY_MISMATCH"),
        ("run_01", "gpt-5.6-terra", "high", "RUN_IDENTITY_MISMATCH"),
    ],
)
def test_manual_import_validates_slot_model_and_effort(
    tmp_path: Path, run_id: str, model_id: str, effort: str, code: str
) -> None:
    root = tmp_path / "work"
    evaluation.prepare_workspace(_work_config(tmp_path), root)
    output = tmp_path / "answer.md"
    output.write_text("# Ответ\n\nE001", encoding="utf-8")
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation.import_run(root, run_id, output, 4.0, model_id, effort)
    assert error.value.code == code


def test_blind_mapping_is_deterministic_and_originals_preserved(tmp_path: Path) -> None:
    roots = [tmp_path / "first", tmp_path / "second"]
    mappings: list[bytes] = []
    for root in roots:
        evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, root)
        _prepare_all_runs(root)
        original = (root / "03_raw_runs" / "run_01_raw.md").read_bytes()
        evaluation.blind_runs(root)
        assert (root / "03_raw_runs" / "run_01_raw.md").read_bytes() == original
        mappings.append((root / "05_blind_review" / "blind_mapping_PRIVATE.csv").read_bytes())
    assert mappings[0] == mappings[1]


def test_blind_copies_preserve_content_and_record_redactions(prepared: Path) -> None:
    _prepare_all_runs(prepared, self_identify=True)
    result = evaluation.blind_runs(prepared)
    blind_text = (prepared / "05_blind_review" / "A.md").read_text(encoding="utf-8")
    assert "Факт E001" in blind_text
    assert "gpt-5.6-" not in blind_text.casefold()
    assert sum(int(item["redaction_count"]) for item in result["outputs"]) == 6


def test_blind_copies_redact_standalone_model_aliases(prepared: Path) -> None:
    client = FakeResponsesClient(bare_identity=True)
    for _ in evaluation.RUN_IDS:
        evaluation.execute_api_run(prepared, client)
    result = evaluation.blind_runs(prepared)
    for output_id in evaluation.OUTPUT_IDS:
        text = (prepared / "05_blind_review" / f"{output_id}.md").read_text(encoding="utf-8")
        assert "[MODEL]" in text
        assert re.search(r"\b(?:terra|sol)\b", text, flags=re.IGNORECASE) is None
    assert sum(int(item["redaction_count"]) for item in result["outputs"]) == 6


@pytest.mark.parametrize("reseal_manifest", [False, True])
def test_modified_blind_mapping_is_rejected(
    prepared: Path, reseal_manifest: bool
) -> None:
    _prepare_all_runs(prepared)
    evaluation.blind_runs(prepared)
    _write_human_inputs(prepared, model_specific=True)
    evaluation.validate_human_input(prepared)

    mapping_path = prepared / "05_blind_review" / "blind_mapping_PRIVATE.csv"
    with mapping_path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    row = rows[0]
    replacement_key = "sol" if row["model_key"] == "terra" else "terra"
    row["model_key"] = replacement_key
    row["model_id"] = f"gpt-5.6-{replacement_key}"
    with mapping_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=evaluation.MAPPING_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    if reseal_manifest:
        manifest_path = prepared / "05_blind_review" / "blind_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["mapping_sha256"] = evaluation._sha256(mapping_path.read_bytes())
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    expected = "identity mismatch" if reseal_manifest else "digest mismatch"
    with pytest.raises(evaluation.EvaluationError, match=expected):
        evaluation.validate_human_input(prepared)


def test_malformed_scores_are_rejected(prepared: Path) -> None:
    _prepare_all_runs(prepared)
    evaluation.blind_runs(prepared)
    _write_human_inputs(prepared)
    score_path = prepared / "05_blind_review" / "scores.csv"
    score_path.write_text(
        score_path.read_text(encoding="utf-8").replace("A,2,", "A,9,"), encoding="utf-8"
    )
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation.validate_human_input(prepared)
    assert error.value.code == "HUMAN_INPUT_INVALID"


def test_totals_are_computed_not_entered(prepared: Path) -> None:
    _prepare_all_runs(prepared)
    evaluation.blind_runs(prepared)
    _write_human_inputs(prepared)
    validated = evaluation.validate_human_input(prepared)
    assert {row["total_score"] for row in validated["scores"]} == {10}
    assert "total_score" not in evaluation.SCORE_FIELDS


def test_correction_time_is_capped_at_twenty(prepared: Path) -> None:
    _prepare_all_runs(prepared)
    evaluation.blind_runs(prepared)
    _write_human_inputs(prepared)
    path = prepared / "06_corrections" / "correction_log.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("A,4.5", "A,20.1"), encoding="utf-8")
    with pytest.raises(evaluation.EvaluationError, match="between 0 and 20"):
        evaluation.validate_human_input(prepared)


def test_medians_ranges_and_decimal_pricing_are_correct(prepared: Path) -> None:
    result = _complete_workflow(prepared)
    assert result["metrics"]["sol"]["median_score"] == "10"
    assert result["metrics"]["terra"]["median_score"] == "8"
    assert result["metrics"]["sol"]["direct_cost_total_usd"] == "0.06"
    metadata = json.loads(
        (prepared / "03_raw_runs" / "run_01_metadata.json").read_text(encoding="utf-8")
    )
    assert Decimal(metadata["direct_cost_usd"]) == Decimal("0.0100")


def test_work_mode_never_fabricates_cost(tmp_path: Path) -> None:
    root = tmp_path / "work"
    evaluation.prepare_workspace(_work_config(tmp_path), root)
    for run_id, model_key in zip(evaluation.RUN_IDS, evaluation.RUN_ORDER, strict=True):
        output = tmp_path / f"{run_id}.md"
        output.write_text(f"# Ответ {run_id}\n\nE001", encoding="utf-8")
        metadata = evaluation.import_run(
            root,
            run_id,
            output,
            5.0,
            f"gpt-5.6-{model_key}",
            "medium",
        )
        assert metadata["cost_available"] is False
        assert metadata["direct_cost_usd"] is None
    evaluation.blind_runs(root)
    _write_human_inputs(root, model_specific=True)
    result = evaluation.analyze_results(root)
    assert result["metrics"]["terra"]["direct_cost_total_usd"] is None
    assert result["metrics"]["sol"]["direct_cost_total_usd"] is None


@pytest.mark.parametrize(
    "metrics,expected",
    [
        ({"terra": {"n": 2}, "sol": {"n": 3}}, "INCONCLUSIVE"),
        (
            {
                "terra": {
                    "n": 3,
                    "median_score": 8,
                    "critical_error_total": 1,
                    "median_correction_minutes": 8,
                    "accepted_within_20": 2,
                },
                "sol": {
                    "n": 3,
                    "median_score": 10,
                    "critical_error_total": 0,
                    "median_correction_minutes": 5,
                    "accepted_within_20": 3,
                },
            },
            "SOL",
        ),
        (
            {
                "terra": {
                    "n": 3,
                    "median_score": 10,
                    "critical_error_total": 0,
                    "median_correction_minutes": 5,
                    "accepted_within_20": 3,
                },
                "sol": {
                    "n": 3,
                    "median_score": 8,
                    "critical_error_total": 1,
                    "median_correction_minutes": 8,
                    "accepted_within_20": 2,
                },
            },
            "TERRA",
        ),
        (
            {
                "terra": {
                    "n": 3,
                    "median_score": 9,
                    "critical_error_total": 0,
                    "median_correction_minutes": 8,
                    "accepted_within_20": 3,
                },
                "sol": {
                    "n": 3,
                    "median_score": 9,
                    "critical_error_total": 0,
                    "median_correction_minutes": 8,
                    "accepted_within_20": 3,
                },
            },
            "MIXED",
        ),
    ],
)
def test_all_verdicts_follow_declared_rules(
    metrics: dict[str, dict[str, Any]], expected: str
) -> None:
    assert evaluation.choose_verdict(metrics) == expected


def test_pillow_chart_decodes_at_full_hd(prepared: Path) -> None:
    _complete_workflow(prepared)
    path = prepared / "07_results" / "result_chart.png"
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        assert image.size == (1920, 1080)


def test_evidence_manifest_excludes_secrets(
    prepared: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "sk-evidence-must-not-contain"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    _complete_workflow(prepared)
    data = (prepared / "07_results" / "evidence_manifest.json").read_text(encoding="utf-8")
    assert secret not in data
    assert "api_key" not in data.casefold() or '"api_key_included": false' in data


@pytest.mark.parametrize("run_id", ["../run_01", "run_01/../../secret", "run_07", "RUN_01"])
def test_path_traversal_and_invalid_run_ids_are_rejected(prepared: Path, run_id: str) -> None:
    with pytest.raises(evaluation.EvaluationError) as error:
        evaluation.request_preview(prepared, run_id)
    assert error.value.code == "PATH_UNSAFE"


def test_cli_prepare_and_preview_are_offline(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / "cli"
    prepared = runner.invoke(
        evaluation.app,
        ["prepare", "--config", str(evaluation.DEFAULT_CONFIG), "--run-root", str(root)],
    )
    assert prepared.exit_code == 0, prepared.output
    preview = runner.invoke(
        evaluation.app,
        ["request-preview", "--run-root", str(root), "--run-id", "run_01"],
    )
    assert preview.exit_code == 0, preview.output
    assert '"private_reference_excluded": true' in preview.output


def test_offline_e2e_smoke_is_stable_and_labeled(tmp_path: Path) -> None:
    root = tmp_path / "offline-e2e"
    evaluation.prepare_workspace(evaluation.DEFAULT_CONFIG, root)
    manifest_path = root / "00_setup" / "experiment_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["demo_label"] = evaluation.DEMO_LABEL
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    result = _complete_workflow(root)
    assert result["verdict"] in {"SOL", "TERRA", "MIXED", "INCONCLUSIVE"}
    first_status = evaluation.workspace_status(root)
    second_status = evaluation.workspace_status(root)
    assert first_status == second_status
    assert (root / "07_results" / "result_chart.png").is_file()
    assert (root / "07_results" / "evidence_manifest.json").is_file()
