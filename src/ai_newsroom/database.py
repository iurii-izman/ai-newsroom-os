from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ai_newsroom.models import F0Error, SourceSnapshot, Story
from ai_newsroom.normalization import content_hash, source_id, story_id

DATABASE_NAME = "newsroom.db"

DDL = {
    "schema_meta": """
        CREATE TABLE schema_meta(
          singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
          version INTEGER NOT NULL CHECK(version = 1)
        )
    """,
    "sources": """
        CREATE TABLE sources(
          id TEXT PRIMARY KEY NOT NULL
            CHECK(length(id)=28 AND substr(id,1,4)='src_'
                  AND substr(id,5) NOT GLOB '*[^0-9a-f]*'),
          original_url TEXT NOT NULL CHECK(length(original_url)>0),
          canonical_url TEXT NOT NULL CHECK(length(canonical_url)>0),
          title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 500),
          summary_text TEXT NOT NULL CHECK(length(summary_text)<=10000),
          published_at TEXT NULL CHECK(published_at IS NULL OR length(published_at)>0),
          published_at_raw TEXT NULL
            CHECK(published_at_raw IS NULL OR length(published_at_raw)>0),
          discovered_at TEXT NOT NULL CHECK(length(discovered_at)>0),
          content_hash TEXT NOT NULL
            CHECK(length(content_hash)=64 AND content_hash NOT GLOB '*[^0-9a-f]*'),
          UNIQUE(canonical_url, content_hash)
        )
    """,
    "stories": """
        CREATE TABLE stories(
          id TEXT PRIMARY KEY NOT NULL
            CHECK(length(id)=30 AND substr(id,1,6)='story_'
                  AND substr(id,7) NOT GLOB '*[^0-9a-f]*'),
          primary_source_id TEXT UNIQUE NOT NULL REFERENCES sources(id)
        )
    """,
    "story_packages": """
        CREATE TABLE story_packages(
          package_id TEXT PRIMARY KEY NOT NULL
            CHECK(length(package_id)=28 AND substr(package_id,1,4)='pkg_'
                  AND substr(package_id,5) NOT GLOB '*[^0-9a-f]*'),
          story_id TEXT UNIQUE NOT NULL REFERENCES stories(id),
          schema_version INTEGER NOT NULL CHECK(schema_version=1),
          generator_name TEXT NOT NULL CHECK(generator_name='mock'),
          generator_version TEXT NOT NULL CHECK(generator_version='mock-v1'),
          input_fingerprint TEXT NOT NULL
            CHECK(length(input_fingerprint)=64
                  AND input_fingerprint NOT GLOB '*[^0-9a-f]*'),
          payload_json TEXT NOT NULL CHECK(length(payload_json) BETWEEN 2 AND 1000000),
          built_at TEXT NOT NULL CHECK(length(built_at)>0)
        )
    """,
}

EXPECTED_COLUMNS = {
    "schema_meta": ("singleton", "version"),
    "sources": (
        "id",
        "original_url",
        "canonical_url",
        "title",
        "summary_text",
        "published_at",
        "published_at_raw",
        "discovered_at",
        "content_hash",
    ),
    "stories": ("id", "primary_source_id"),
    "story_packages": (
        "package_id",
        "story_id",
        "schema_version",
        "generator_name",
        "generator_version",
        "input_fingerprint",
        "payload_json",
        "built_at",
    ),
}


def database_path(data_dir: Path) -> Path:
    return data_dir / DATABASE_NAME


def _map_sqlite_error(error: sqlite3.Error) -> F0Error:
    message = str(error).casefold()
    if "locked" in message or "busy" in message:
        return F0Error("E_DB_LOCKED", "database is locked; close the other writer and retry")
    if "malformed" in message or "not a database" in message or "disk image" in message:
        return F0Error("E_DB_CORRUPT", "database is corrupt; preserve it and diagnose a copy")
    return F0Error("E_DB_SCHEMA", "database schema or data is incompatible with F0")


def _connect(path: Path) -> sqlite3.Connection:
    try:
        connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection
    except sqlite3.Error as error:
        raise _map_sqlite_error(error) from None


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _normalized_ddl(value: str) -> str:
    return "".join(value.split()).casefold()


def validate_schema(connection: sqlite3.Connection) -> None:
    try:
        if _table_names(connection) != set(DDL):
            raise F0Error("E_DB_SCHEMA", "database does not contain the exact F0 tables")
        for table, expected in EXPECTED_COLUMNS.items():
            actual = tuple(str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})"))
            if actual != expected:
                raise F0Error("E_DB_SCHEMA", "database table shape is incompatible with F0")
            stored = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if stored is None or _normalized_ddl(str(stored[0])) != _normalized_ddl(DDL[table]):
                raise F0Error("E_DB_SCHEMA", "database table definition is incompatible with F0")
        rows = connection.execute("SELECT singleton, version FROM schema_meta").fetchall()
        if rows != [(1, 1)]:
            raise F0Error("E_DB_SCHEMA", "database schema version metadata is incompatible")
    except F0Error:
        raise
    except sqlite3.Error as error:
        raise _map_sqlite_error(error) from None


@contextmanager
def open_database(data_dir: Path) -> Iterator[sqlite3.Connection]:
    path = database_path(data_dir)
    if not path.is_file():
        raise F0Error("E_DB_SCHEMA", "database is not initialized; run db init")
    connection = _connect(path)
    try:
        validate_schema(connection)
        yield connection
    finally:
        connection.close()


def init_database(data_dir: Path) -> bool:
    path = database_path(data_dir)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise F0Error("E_DB_SCHEMA", "data directory cannot be created") from None
    existed = path.exists()
    connection = _connect(path)
    try:
        tables = _table_names(connection)
        if tables:
            validate_schema(connection)
            return False
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in DDL.values():
                connection.execute(statement)
            connection.execute("INSERT INTO schema_meta(singleton, version) VALUES (1, 1)")
            connection.execute("COMMIT")
        except sqlite3.Error:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        validate_schema(connection)
        return not existed or not tables
    except F0Error:
        raise
    except sqlite3.Error as error:
        raise _map_sqlite_error(error) from None
    finally:
        connection.close()


def _validate_snapshot(snapshot: SourceSnapshot) -> None:
    digest = content_hash(
        snapshot.title,
        snapshot.summary_text,
        snapshot.published_at,
        snapshot.published_at_raw,
    )
    if digest != snapshot.content_hash or source_id(snapshot.canonical_url, digest) != snapshot.id:
        raise F0Error("E_DB_SCHEMA", "source snapshot identity is invalid")


def harvest_snapshots(data_dir: Path, snapshots: list[SourceSnapshot]) -> tuple[int, int]:
    for snapshot in snapshots:
        _validate_snapshot(snapshot)
    with open_database(data_dir) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            created = 0
            for snapshot in snapshots:
                before = connection.total_changes
                connection.execute(
                    """
                    INSERT OR IGNORE INTO sources(
                      id, original_url, canonical_url, title, summary_text, published_at,
                      published_at_raw, discovered_at, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot.id,
                        snapshot.original_url,
                        snapshot.canonical_url,
                        snapshot.title,
                        snapshot.summary_text,
                        snapshot.published_at,
                        snapshot.published_at_raw,
                        snapshot.discovered_at,
                        snapshot.content_hash,
                    ),
                )
                source_created = connection.total_changes - before
                created += source_created
                existing = connection.execute(
                    """
                    SELECT canonical_url, title, summary_text, published_at,
                           published_at_raw, content_hash
                    FROM sources WHERE id = ?
                    """,
                    (snapshot.id,),
                ).fetchone()
                expected = (
                    snapshot.canonical_url,
                    snapshot.title,
                    snapshot.summary_text,
                    snapshot.published_at,
                    snapshot.published_at_raw,
                    snapshot.content_hash,
                )
                if existing != expected:
                    raise F0Error("E_DB_SCHEMA", "existing source conflicts with its identity")
                expected_story_id = story_id(snapshot.id)
                if source_created:
                    connection.execute(
                        "INSERT INTO stories(id, primary_source_id) VALUES (?, ?)",
                        (expected_story_id, snapshot.id),
                    )
                story_row = connection.execute(
                    "SELECT id, primary_source_id FROM stories WHERE primary_source_id = ?",
                    (snapshot.id,),
                ).fetchone()
                if story_row != (expected_story_id, snapshot.id):
                    raise F0Error("E_DB_SCHEMA", "existing Story conflicts with its source")
            connection.execute("COMMIT")
            return created, len(snapshots) - created
        except F0Error:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as error:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise _map_sqlite_error(error) from None


def list_stories(data_dir: Path) -> list[tuple[Story, str]]:
    with open_database(data_dir) as connection:
        try:
            rows = connection.execute(
                """
                SELECT stories.id, stories.primary_source_id, sources.title
                FROM stories
                JOIN sources ON sources.id = stories.primary_source_id
                ORDER BY stories.id
                """
            ).fetchall()
        except sqlite3.Error as error:
            raise _map_sqlite_error(error) from None
    return [(Story(id=str(row[0]), primary_source_id=str(row[1])), str(row[2])) for row in rows]
