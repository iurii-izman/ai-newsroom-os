from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

import ai_newsroom.exporters as exporters
from ai_newsroom.database import database_path, harvest_snapshots, init_database
from ai_newsroom.exporters import ExportFormat, export_package
from ai_newsroom.models import F0Error
from ai_newsroom.normalization import story_id
from ai_newsroom.package_builder import build_package
from ai_newsroom.rss import parse_rss_bytes, read_rss_fixture

NOW = "2026-07-14T12:00:00Z"
STORY_ID = "story_55c2bc7f60628d20cb9acd4c"


def prepare(data_dir: Path) -> None:
    init_database(data_dir)
    harvest_snapshots(
        data_dir, read_rss_fixture(Path("tests/fixtures/feeds/sample.xml"), NOW)
    )
    build_package(data_dir, STORY_ID, NOW)


def exported_paths(data_dir: Path) -> tuple[Path, Path]:
    directory = data_dir / "exports" / STORY_ID
    return directory / "story-package.json", directory / "story-package.md"


def test_json_and_markdown_match_exact_goldens(tmp_path: Path) -> None:
    prepare(tmp_path)
    assert export_package(tmp_path, STORY_ID, ExportFormat.ALL)[:2] == (2, 0)
    json_path, markdown_path = exported_paths(tmp_path)
    assert json_path.read_bytes() == Path("tests/golden/story-package.json").read_bytes()
    assert markdown_path.read_bytes() == Path("tests/golden/story-package.md").read_bytes()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["sources"][0]["canonical_url"] == "https://example.com/news"
    assert "url" not in payload["sources"][0]
    assert payload["sources"][0]["published_at_raw"] == "2026-07-13 10:00"
    assert b"\r" not in json_path.read_bytes() + markdown_path.read_bytes()


def test_identical_export_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(tmp_path)
    export_package(tmp_path, STORY_ID, ExportFormat.ALL)

    def unexpected_replace(*_args: object) -> None:
        raise AssertionError("identical files must not be replaced")

    monkeypatch.setattr(os, "replace", unexpected_replace)
    assert export_package(tmp_path, STORY_ID, ExportFormat.ALL)[:2] == (0, 2)


def test_conflict_and_explicit_force(tmp_path: Path) -> None:
    prepare(tmp_path)
    export_package(tmp_path, STORY_ID, ExportFormat.JSON)
    json_path, _markdown_path = exported_paths(tmp_path)
    json_path.write_bytes(b"manual edit\n")
    with pytest.raises(F0Error) as error:
        export_package(tmp_path, STORY_ID, ExportFormat.JSON)
    assert error.value.code == "E_EXPORT_CONFLICT"
    assert json_path.read_bytes() == b"manual edit\n"
    assert export_package(tmp_path, STORY_ID, ExportFormat.JSON, force=True)[:2] == (1, 0)
    assert json_path.read_bytes() == Path("tests/golden/story-package.json").read_bytes()


def test_pre_replace_failure_preserves_existing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(tmp_path)
    json_path, markdown_path = exported_paths(tmp_path)
    json_path.parent.mkdir(parents=True)
    json_path.write_bytes(b"old json")
    markdown_path.write_bytes(b"old markdown")
    original_write = exporters._write_temp
    calls = 0

    def fail_second(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected")
        original_write(path, content)

    monkeypatch.setattr(exporters, "_write_temp", fail_second)
    with pytest.raises(F0Error) as error:
        export_package(tmp_path, STORY_ID, ExportFormat.ALL, force=True)
    assert error.value.code == "E_EXPORT_PARTIAL"
    assert (json_path.read_bytes(), markdown_path.read_bytes()) == (b"old json", b"old markdown")


def test_interrupted_pair_is_detected_and_force_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(tmp_path)
    json_path, markdown_path = exported_paths(tmp_path)
    json_path.parent.mkdir(parents=True)
    json_path.write_bytes(b"old json")
    markdown_path.write_bytes(b"old markdown")
    original_replace = os.replace
    calls = 0

    def fail_second(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected")
        original_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second)
    with pytest.raises(F0Error):
        export_package(tmp_path, STORY_ID, ExportFormat.ALL, force=True)
    assert json_path.read_bytes() == Path("tests/golden/story-package.json").read_bytes()
    assert markdown_path.read_bytes() == b"old markdown"
    monkeypatch.setattr(os, "replace", original_replace)
    with pytest.raises(F0Error) as error:
        export_package(tmp_path, STORY_ID, ExportFormat.ALL)
    assert error.value.code == "E_EXPORT_PARTIAL"
    assert export_package(tmp_path, STORY_ID, ExportFormat.ALL, force=True)[:2] == (1, 1)


def test_export_revalidates_tampered_claim_without_writing(tmp_path: Path) -> None:
    prepare(tmp_path)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        payload = json.loads(
            connection.execute("SELECT payload_json FROM story_packages").fetchone()[0]
        )
        payload["claims"].append(payload["claims"][0])
        connection.execute(
            "UPDATE story_packages SET payload_json=?",
            (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),),
        )
    with pytest.raises(F0Error) as error:
        export_package(tmp_path, STORY_ID, ExportFormat.ALL)
    assert error.value.code == "E_DB_SCHEMA"
    assert not (tmp_path / "exports").exists()


def test_markdown_escapes_untrusted_labels(tmp_path: Path) -> None:
    init_database(tmp_path)
    snapshots = parse_rss_bytes(
        b"<rss><channel><item><title>A [x] *z*</title>"
        b"<link>https://example.com/a_(b)</link></item></channel></rss>",
        NOW,
    )
    harvest_snapshots(tmp_path, snapshots)
    selected_story_id = story_id(snapshots[0].id)
    build_package(tmp_path, selected_story_id, NOW)
    export_package(tmp_path, selected_story_id, ExportFormat.MARKDOWN)
    markdown = (
        tmp_path / "exports" / selected_story_id / "story-package.md"
    ).read_text(encoding="utf-8")
    assert "A \\[x\\] \\*z\\*" in markdown
    assert "a\\_\\(b\\)" in markdown
    assert "Published at raw:" not in markdown
