from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from ai_newsroom.database import harvest_snapshots, init_database, list_stories
from ai_newsroom.models import F0Error
from ai_newsroom.rss import read_rss_fixture

app = typer.Typer(no_args_is_help=True, add_completion=False)
db_app = typer.Typer(no_args_is_help=True)
harvest_app = typer.Typer(no_args_is_help=True)
stories_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(harvest_app, name="harvest")
app.add_typer(stories_app, name="stories")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(error: F0Error) -> None:
    typer.echo(f"{error.code}: {error.message}", err=True)
    raise typer.Exit(code=1)


@app.callback()
def root(
    ctx: typer.Context,
    data_dir: Annotated[Path, typer.Option("--data-dir")] = Path("data"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["data_dir"] = data_dir


@db_app.command("init")
def db_init(ctx: typer.Context) -> None:
    try:
        created = init_database(ctx.obj["data_dir"])
        typer.echo(f"database: {'created' if created else 'unchanged'}")
    except F0Error as error:
        _fail(error)


@harvest_app.command("run")
def harvest_run(
    ctx: typer.Context,
    fixture: Annotated[Path, typer.Option("--fixture")],
) -> None:
    try:
        snapshots = read_rss_fixture(fixture, _now())
        created, unchanged = harvest_snapshots(ctx.obj["data_dir"], snapshots)
        typer.echo(
            f"sources created={created} unchanged={unchanged}; "
            f"stories created={created} unchanged={unchanged}"
        )
    except F0Error as error:
        _fail(error)


@stories_app.command("list")
def stories_list(
    ctx: typer.Context,
    ids_only: Annotated[bool, typer.Option("--ids-only")] = False,
) -> None:
    try:
        for story, title in list_stories(ctx.obj["data_dir"]):
            typer.echo(story.id if ids_only else f"{story.id}\t{title}")
    except F0Error as error:
        _fail(error)


def main() -> None:
    app()
