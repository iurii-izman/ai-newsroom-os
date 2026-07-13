from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_newsroom.cli import app

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
    for arguments in (["--help"], ["unknown"], ["db", "init", "--unknown"]):
        result = runner.invoke(app, arguments)
        if arguments == ["--help"]:
            assert result.exit_code == 0
        else:
            assert result.exit_code != 0
        assert "Traceback" not in result.output
