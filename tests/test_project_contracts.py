from __future__ import annotations

import ast
import tomllib
from pathlib import Path


def test_direct_dependency_declarations() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == ["pydantic>=2.12,<3", "typer>=0.20,<1"]
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
    for filename in ("models.py", "normalization.py", "rss.py"):
        tree = ast.parse(Path("src/ai_newsroom", filename).read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert imports.isdisjoint({"typer", "sqlite3"})
