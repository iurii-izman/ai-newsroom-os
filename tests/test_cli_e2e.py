from __future__ import annotations

import hashlib
import socket
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

import ai_newsroom.cli as cli_module
from ai_newsroom.cli import app
from ai_newsroom.database import database_path

runner = CliRunner()


def test_init_harvest_and_list_with_unicode_space_paths(tmp_path: Path) -> None:
    data_dir = tmp_path / "данные с пробелом"
    fixture_dir = tmp_path / "вход с пробелом"
    fixture_dir.mkdir()
    fixture = fixture_dir / "лента.xml"
    fixture.write_bytes(Path("tests/fixtures/feeds/sample.xml").read_bytes())

    init = runner.invoke(app, ["--data-dir", str(data_dir), "db", "init"])
    assert init.exit_code == 0
    assert "created" in init.stdout
    assert runner.invoke(app, ["--data-dir", str(data_dir), "db", "init"]).exit_code == 0

    harvest = runner.invoke(
        app, ["--data-dir", str(data_dir), "harvest", "run", "--fixture", str(fixture)]
    )
    assert harvest.exit_code == 0
    assert "sources created=1 unchanged=0" in harvest.stdout
    repeated = runner.invoke(
        app, ["--data-dir", str(data_dir), "harvest", "run", "--fixture", str(fixture)]
    )
    assert repeated.exit_code == 0
    assert "sources created=0 unchanged=1" in repeated.stdout

    listed = runner.invoke(app, ["--data-dir", str(data_dir), "stories", "list", "--ids-only"])
    assert listed.exit_code == 0
    assert listed.stdout == "story_55c2bc7f60628d20cb9acd4c\n"


def test_empty_list_and_project_error_are_concise(tmp_path: Path) -> None:
    assert runner.invoke(app, ["--data-dir", str(tmp_path), "db", "init"]).exit_code == 0
    empty = runner.invoke(app, ["--data-dir", str(tmp_path), "stories", "list", "--ids-only"])
    assert empty.exit_code == 0
    assert empty.stdout == ""
    missing = runner.invoke(
        app,
        ["--data-dir", str(tmp_path), "harvest", "run", "--fixture", str(tmp_path / "x")],
    )
    assert missing.exit_code != 0
    assert "E_FIXTURE_INVALID" in missing.stderr
    assert "Traceback" not in missing.stderr


def test_framework_usage_and_help() -> None:
    for arguments in (
        ["--help"],
        ["unknown"],
        ["db", "init", "--unknown"],
        ["package", "build"],
    ):
        result = runner.invoke(app, arguments)
        if arguments == ["--help"]:
            assert result.exit_code == 0
        else:
            assert result.exit_code != 0
        assert "Traceback" not in result.output


def test_package_build_cli(tmp_path: Path) -> None:
    arguments = ["--data-dir", str(tmp_path)]
    assert runner.invoke(app, [*arguments, "db", "init"]).exit_code == 0
    assert (
        runner.invoke(
            app,
            [
                *arguments,
                "harvest",
                "run",
                "--fixture",
                "tests/fixtures/feeds/sample.xml",
            ],
        ).exit_code
        == 0
    )
    built = runner.invoke(app, [*arguments, "package", "build", "story_55c2bc7f60628d20cb9acd4c"])
    assert built.exit_code == 0
    assert built.stdout == "package_id=pkg_17e9b7502f7bc00db437b993 created\n"
    repeated = runner.invoke(
        app, [*arguments, "package", "build", "story_55c2bc7f60628d20cb9acd4c"]
    )
    assert repeated.exit_code == 0
    assert repeated.stdout.endswith(" unchanged\n")
    exported = runner.invoke(
        app,
        [
            *arguments,
            "package",
            "export",
            "story_55c2bc7f60628d20cb9acd4c",
            "--format",
            "all",
        ],
    )
    assert exported.exit_code == 0
    assert exported.stdout == "exported=2 unchanged=0\n"
    assert (
        tmp_path
        / "exports"
        / "story_55c2bc7f60628d20cb9acd4c"
        / "story-package.json"
    ).is_file()


def test_export_usage_and_missing_package(tmp_path: Path) -> None:
    arguments = ["--data-dir", str(tmp_path)]
    assert runner.invoke(app, [*arguments, "db", "init"]).exit_code == 0
    invalid = runner.invoke(
        app,
        [
            *arguments,
            "package",
            "export",
            "story_000000000000000000000000",
            "--format",
            "invalid",
        ],
    )
    assert invalid.exit_code != 0
    assert "Traceback" not in invalid.output
    missing = runner.invoke(
        app,
        [
            *arguments,
            "package",
            "export",
            "story_000000000000000000000000",
            "--format",
            "all",
        ],
    )
    assert missing.exit_code != 0
    assert "E_PACKAGE_NOT_BUILT" in missing.stderr
    assert "Traceback" not in missing.output


def _complete_flow(data_dir: Path) -> tuple[str, tuple[int, int, int], str, str]:
    prefix = ["--data-dir", str(data_dir)]
    commands = [
        [*prefix, "db", "init"],
        [*prefix, "harvest", "run", "--fixture", "tests/fixtures/feeds/sample.xml"],
    ]
    for command in commands:
        assert runner.invoke(app, command).exit_code == 0
    story = runner.invoke(app, [*prefix, "stories", "list", "--ids-only"])
    assert story.exit_code == 0
    selected = story.stdout.strip()
    assert runner.invoke(app, [*prefix, "package", "build", selected]).exit_code == 0
    export = [*prefix, "package", "export", selected, "--format", "all"]
    assert runner.invoke(app, export).exit_code == 0
    directory = data_dir / "exports" / selected
    json_hash = hashlib.sha256((directory / "story-package.json").read_bytes()).hexdigest()
    markdown_hash = hashlib.sha256((directory / "story-package.md").read_bytes()).hexdigest()
    with sqlite3.connect(database_path(data_dir)) as connection:
        counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("sources", "stories", "story_packages")
        )
    assert runner.invoke(
        app,
        [*prefix, "harvest", "run", "--fixture", "tests/fixtures/feeds/sample.xml"],
    ).exit_code == 0
    assert runner.invoke(app, [*prefix, "package", "build", selected]).exit_code == 0
    assert runner.invoke(app, export).exit_code == 0
    with sqlite3.connect(database_path(data_dir)) as connection:
        repeated_counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("sources", "stories", "story_packages")
        )
    assert repeated_counts == counts
    assert hashlib.sha256((directory / "story-package.json").read_bytes()).hexdigest() == json_hash
    assert (
        hashlib.sha256((directory / "story-package.md").read_bytes()).hexdigest()
        == markdown_hash
    )
    return selected, counts, json_hash, markdown_hash


def test_two_isolated_repeated_flows_are_deterministic(tmp_path: Path) -> None:
    first = _complete_flow(tmp_path / "first path")
    second = _complete_flow(tmp_path / "второй путь")
    assert first == second
    assert first[1] == (1, 1, 1)


def test_socket_guard_is_active() -> None:
    with pytest.raises(AssertionError, match="network access is forbidden"):
        socket.create_connection(("127.0.0.1", 9))


def test_unexpected_error_is_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_with_sensitive_detail(_data_dir: Path) -> bool:
        raise RuntimeError("secret raw fixture body")

    monkeypatch.setattr(cli_module, "init_database", fail_with_sensitive_detail)
    result = runner.invoke(app, ["--data-dir", str(tmp_path), "db", "init"])
    assert result.exit_code != 0
    assert "E_UNEXPECTED" in result.stderr
    assert "secret" not in result.output
    assert "fixture body" not in result.output
    assert "Traceback" not in result.output
