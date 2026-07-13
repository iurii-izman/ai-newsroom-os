from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ai_newsroom.database import database_path, harvest_snapshots, init_database
from ai_newsroom.models import F0Error
from ai_newsroom.package_builder import build_package, load_validated_package
from ai_newsroom.rss import parse_rss_bytes, read_rss_fixture

NOW = "2026-07-14T12:00:00Z"
STORY_ID = "story_55c2bc7f60628d20cb9acd4c"


def prepare(data_dir: Path) -> None:
    init_database(data_dir)
    harvest_snapshots(
        data_dir, read_rss_fixture(Path("tests/fixtures/feeds/sample.xml"), NOW)
    )


def test_build_exact_package_and_repeat(tmp_path: Path) -> None:
    prepare(tmp_path)
    package_id, created = build_package(tmp_path, STORY_ID, NOW)
    assert (package_id, created) == ("pkg_17e9b7502f7bc00db437b993", True)
    assert build_package(tmp_path, STORY_ID, "2026-07-14T13:00:00Z") == (package_id, False)
    snapshot, payload = load_validated_package(tmp_path, STORY_ID)
    assert snapshot.package_id == package_id
    assert "built_at" not in snapshot.payload_json
    assert payload.publishable is False
    assert payload.story.title == "Тест AI"
    assert payload.sources[0].id == "src_58343a9a5ffae3037a3f73bf"
    assert payload.claims[0].id == "claim_11806810946d69ba4de2ccd4"
    assert payload.claims[0].source_ids == [payload.sources[0].id]


def test_missing_story(tmp_path: Path) -> None:
    init_database(tmp_path)
    with pytest.raises(F0Error) as error:
        build_package(tmp_path, "story_000000000000000000000000", NOW)
    assert error.value.code == "E_STORY_NOT_FOUND"


def test_source_content_tamper_is_rejected(tmp_path: Path) -> None:
    prepare(tmp_path)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        connection.execute("UPDATE sources SET title='tampered'")
    with pytest.raises(F0Error) as error:
        build_package(tmp_path, STORY_ID, NOW)
    assert error.value.code == "E_DB_SCHEMA"


def test_story_source_relation_tamper_is_rejected(tmp_path: Path) -> None:
    init_database(tmp_path)
    second = parse_rss_bytes(
        b"<rss><channel><item><title>Other</title>"
        b"<link>https://other.example/x</link></item></channel></rss>",
        NOW,
    )
    first = read_rss_fixture(Path("tests/fixtures/feeds/sample.xml"), NOW)
    harvest_snapshots(tmp_path, first + second)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("DELETE FROM stories WHERE primary_source_id=?", (second[0].id,))
        connection.execute(
            "UPDATE stories SET primary_source_id=? WHERE id=?", (second[0].id, STORY_ID)
        )
    with pytest.raises(F0Error) as error:
        build_package(tmp_path, STORY_ID, NOW)
    assert error.value.code == "E_DB_SCHEMA"


@pytest.mark.parametrize("tamper", ["input_fingerprint", "modified_claim", "extra_claim"])
def test_existing_package_tamper_is_rejected(tmp_path: Path, tamper: str) -> None:
    prepare(tmp_path)
    build_package(tmp_path, STORY_ID, NOW)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        if tamper == "input_fingerprint":
            connection.execute(
                "UPDATE story_packages SET input_fingerprint=?", ("0" * 64,)
            )
        else:
            payload = json.loads(
                connection.execute("SELECT payload_json FROM story_packages").fetchone()[0]
            )
            if tamper == "modified_claim":
                payload["claims"][0]["text"] = "tampered"
            else:
                payload["claims"].append(payload["claims"][0])
            connection.execute(
                "UPDATE story_packages SET payload_json=?",
                (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),),
            )
    with pytest.raises(F0Error) as error:
        build_package(tmp_path, STORY_ID, NOW)
    assert error.value.code == "E_DB_SCHEMA"
