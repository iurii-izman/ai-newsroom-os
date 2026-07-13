from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ai_newsroom.database import (
    database_path,
    harvest_snapshots,
    init_database,
    list_stories,
    open_database,
)
from ai_newsroom.models import F0Error
from ai_newsroom.rss import parse_rss_bytes

NOW = "2026-07-14T12:00:00Z"


def source(title: str = "A", url: str = "https://example.com/a") -> bytes:
    return (
        f"<rss><channel><item><title>{title}</title><link>{url}</link>"
        "<description>summary</description></item></channel></rss>"
    ).encode()


def counts(path: Path) -> tuple[int, int, int]:
    with sqlite3.connect(database_path(path)) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("sources", "stories", "story_packages")
        )


def test_init_is_exact_idempotent_and_configures_connections(tmp_path: Path) -> None:
    assert init_database(tmp_path) is True
    assert init_database(tmp_path) is False
    with sqlite3.connect(database_path(tmp_path)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        assert tables == {"schema_meta", "sources", "stories", "story_packages"}
        assert connection.execute("SELECT * FROM schema_meta").fetchall() == [(1, 1)]
    with open_database(tmp_path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA busy_timeout").fetchone() == (5000,)


def test_incompatible_database_is_not_repaired(tmp_path: Path) -> None:
    init_database(tmp_path)
    path = database_path(tmp_path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute("UPDATE schema_meta SET version=2")
    before = path.read_bytes()
    with pytest.raises(F0Error) as error:
        init_database(tmp_path)
    assert error.value.code == "E_DB_SCHEMA"
    assert path.read_bytes() == before


def test_harvest_is_atomic_idempotent_and_preserves_revisions(tmp_path: Path) -> None:
    init_database(tmp_path)
    first = parse_rss_bytes(source(), NOW)
    assert harvest_snapshots(tmp_path, first) == (1, 0)
    assert harvest_snapshots(tmp_path, first) == (0, 1)
    assert counts(tmp_path) == (1, 1, 0)

    changed = parse_rss_bytes(source(title="Changed"), NOW)
    assert harvest_snapshots(tmp_path, changed) == (1, 0)
    same_content_other_url = parse_rss_bytes(source(title="A", url="https://other.example/a"), NOW)
    assert harvest_snapshots(tmp_path, same_content_other_url) == (1, 0)
    assert counts(tmp_path) == (3, 3, 0)
    listed = list_stories(tmp_path)
    assert [story.id for story, _title in listed] == sorted(story.id for story, _title in listed)


def test_write_failure_rolls_back_source_and_story(tmp_path: Path) -> None:
    init_database(tmp_path)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        connection.execute(
            "CREATE TRIGGER fail_story BEFORE INSERT ON stories "
            "BEGIN SELECT RAISE(ABORT, 'fail'); END"
        )
    with pytest.raises(F0Error):
        harvest_snapshots(tmp_path, parse_rss_bytes(source(), NOW))
    assert counts(tmp_path) == (0, 0, 0)


def test_corrupt_database_is_preserved(tmp_path: Path) -> None:
    path = database_path(tmp_path)
    path.write_bytes(b"not a sqlite database")
    before = path.read_bytes()
    with pytest.raises(F0Error) as error:
        init_database(tmp_path)
    assert error.value.code == "E_DB_CORRUPT"
    assert path.read_bytes() == before


def test_harvest_requires_initialized_database(tmp_path: Path) -> None:
    with pytest.raises(F0Error) as error:
        harvest_snapshots(tmp_path, parse_rss_bytes(source(), NOW))
    assert error.value.code == "E_DB_SCHEMA"


def test_missing_story_is_not_repaired(tmp_path: Path) -> None:
    init_database(tmp_path)
    snapshot = parse_rss_bytes(source(), NOW)
    harvest_snapshots(tmp_path, snapshot)
    with sqlite3.connect(database_path(tmp_path)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DELETE FROM stories")
    with pytest.raises(F0Error) as error:
        harvest_snapshots(tmp_path, snapshot)
    assert error.value.code == "E_DB_SCHEMA"
    assert counts(tmp_path) == (1, 0, 0)


def test_database_lock_maps_to_stable_error(tmp_path: Path) -> None:
    init_database(tmp_path)
    locker = sqlite3.connect(database_path(tmp_path), isolation_level=None)
    try:
        locker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(F0Error) as error:
            harvest_snapshots(tmp_path, parse_rss_bytes(source(), NOW))
        assert error.value.code == "E_DB_LOCKED"
    finally:
        locker.execute("ROLLBACK")
        locker.close()


def test_mixed_validity_fixture_leaves_existing_rows_unchanged(tmp_path: Path) -> None:
    init_database(tmp_path)
    initial = parse_rss_bytes(source(), NOW)
    harvest_snapshots(tmp_path, initial)
    before = counts(tmp_path)
    mixed = (
        "<rss><channel>"
        + source().decode().removeprefix("<rss><channel>").removesuffix("</channel></rss>")
        + "<item><title>Invalid</title><link>file:///not-allowed</link></item>"
        + "</channel></rss>"
    ).encode()
    with pytest.raises(F0Error) as error:
        parse_rss_bytes(mixed, NOW)
    assert error.value.code == "E_FIXTURE_INVALID"
    assert counts(tmp_path) == before
