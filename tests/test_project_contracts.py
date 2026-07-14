from __future__ import annotations

import ast
import subprocess
import tomllib
from pathlib import Path

from ai_newsroom.cli import (
    app,
    db_app,
    harvest_app,
    package_app,
    script_app,
    stories_app,
    video_app,
)


def test_direct_dependency_declarations() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == [
        "edge-tts>=7.2,<8",
        "imageio-ffmpeg>=0.6,<1",
        "openai>=2,<3",
        "pillow>=12.3,<13",
        "pydantic>=2.12,<3",
        "typer>=0.20,<1",
    ]
    assert project["dependency-groups"]["dev"] == [
        "mypy>=1.19,<2",
        "pytest>=9,<10",
        "ruff>=0.14,<1",
    ]
    assert project["build-system"] == {
        "requires": ["uv_build>=0.9.30,<0.10.0"],
        "build-backend": "uv_build",
    }


def test_domain_modules_do_not_import_typer_or_sqlite() -> None:
    for filename in ("models.py", "normalization.py", "rss.py", "script_models.py"):
        tree = ast.parse(Path("src/ai_newsroom", filename).read_text(encoding="utf-8"))
        imports = {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert imports.isdisjoint({"typer", "sqlite3"})


def test_exact_cli_surface_and_entry_point() -> None:
    groups = {group.name for group in app.registered_groups}
    assert groups == {"db", "harvest", "stories", "package", "script", "video"}
    assert {command.name for command in db_app.registered_commands} == {"init"}
    assert {command.name for command in harvest_app.registered_commands} == {"live", "run"}
    assert {command.name for command in stories_app.registered_commands} == {"list"}
    assert {command.name for command in package_app.registered_commands} == {"build", "export"}
    assert {command.name for command in script_app.registered_commands} == {"build"}
    assert {command.name for command in video_app.registered_commands} == {"render"}
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"] == {"ai-newsroom": "ai_newsroom.cli:main"}


def test_only_concrete_vertical_modules_and_bounded_network_imports() -> None:
    modules = {path.name for path in Path("src/ai_newsroom").glob("*.py")}
    assert modules == {
        "__init__.py",
        "cli.py",
        "database.py",
        "deepseek.py",
        "exporters.py",
        "live_sources.py",
        "models.py",
        "normalization.py",
        "package_builder.py",
        "rss.py",
        "script_builder.py",
        "script_models.py",
        "tts.py",
        "video_renderer.py",
    }
    forbidden_imports = {"requests", "aiohttp", "socket"}
    for path in Path("src/ai_newsroom").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert imports.isdisjoint(forbidden_imports)
        if path.name != "live_sources.py":
            assert "urllib.request" not in imports
        if path.name != "deepseek.py":
            assert "openai" not in imports


def test_no_runtime_artifacts_are_tracked() -> None:
    result = subprocess.run(
        ["git", "ls-files"], check=True, capture_output=True, text=True, encoding="utf-8"
    )
    tracked = result.stdout.splitlines()
    forbidden_suffixes = (
        ".db",
        ".sqlite",
        ".sqlite3",
        ".log",
        ".pyc",
        ".mp3",
        ".srt",
        ".mp4",
    )
    normalized = [path.replace("\\", "/") for path in tracked]
    assert not [path for path in tracked if path.endswith(forbidden_suffixes)]
    assert not [path for path in normalized if "/exports/" in f"/{path}/"]


def test_only_approved_provider_credential_is_referenced() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src/ai_newsroom").glob("*.py")
    )
    assert "DEEPSEEK_API_KEY" in source
    assert "OPENAI_API_KEY" not in source
