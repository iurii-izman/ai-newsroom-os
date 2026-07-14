from __future__ import annotations

import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from ai_newsroom.database import harvest_snapshots, init_database, list_stories
from ai_newsroom.exporters import ExportFormat, export_package
from ai_newsroom.live_sources import SOURCE_NAMES, fetch_feed, load_live_sources
from ai_newsroom.models import BuildGenerator, F0Error, RealStoryPackagePayload
from ai_newsroom.package_builder import build_package, load_validated_package
from ai_newsroom.rss import parse_live_feed_bytes, read_rss_fixture
from ai_newsroom.script_builder import build_script
from ai_newsroom.video_renderer import render_video

app = typer.Typer(no_args_is_help=True, add_completion=False)
db_app = typer.Typer(no_args_is_help=True)
harvest_app = typer.Typer(no_args_is_help=True)
stories_app = typer.Typer(no_args_is_help=True)
package_app = typer.Typer(no_args_is_help=True)
script_app = typer.Typer(no_args_is_help=True)
video_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(harvest_app, name="harvest")
app.add_typer(stories_app, name="stories")
app.add_typer(package_app, name="package")
app.add_typer(script_app, name="script")
app.add_typer(video_app, name="video")


class LiveSourceSelection(StrEnum):
    OPENAI_NEWS = "openai-news"
    GOOGLE_AI = "google-ai"
    MICROSOFT_AI = "microsoft-ai"
    ALL = "all"


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
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


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
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


@harvest_app.command("live")
def harvest_live(
    ctx: typer.Context,
    source: Annotated[LiveSourceSelection, typer.Option("--source")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=50)] = 20,
) -> None:
    try:
        configured = load_live_sources()
        selected = SOURCE_NAMES if source is LiveSourceSelection.ALL else (source.value,)
        failures = 0
        for source_name in selected:
            try:
                data = fetch_feed(configured[source_name])
                snapshots = parse_live_feed_bytes(data, _now(), source_name, limit)
                created, unchanged = harvest_snapshots(ctx.obj["data_dir"], snapshots)
                typer.echo(
                    f"source={source_name} items={len(snapshots)} "
                    f"created={created} unchanged={unchanged}"
                )
            except F0Error as error:
                failures += 1
                typer.echo(f"source={source_name} error={error.code}", err=True)
        if failures:
            raise F0Error(
                "E_LIVE_HARVEST", f"{failures} selected live source request(s) failed"
            )
    except F0Error as error:
        _fail(error)
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


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
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


@package_app.command("build")
def package_build(
    ctx: typer.Context,
    story_id: str,
    generator: Annotated[BuildGenerator, typer.Option("--generator")] = BuildGenerator.MOCK,
) -> None:
    try:
        api_key = (
            os.environ.get("DEEPSEEK_API_KEY")
            if generator is BuildGenerator.DEEPSEEK
            else None
        )
        package_id, created = build_package(
            ctx.obj["data_dir"], story_id, _now(), generator, api_key=api_key
        )
        suffix = ""
        if generator is BuildGenerator.DEEPSEEK:
            _snapshot, payload = load_validated_package(
                ctx.obj["data_dir"], story_id, package_id=package_id
            )
            if isinstance(payload, RealStoryPackagePayload):
                suffix = f" repair_used={str(payload.usage_metadata.repair_used).lower()}"
        typer.echo(
            f"package_id={package_id} {'created' if created else 'unchanged'}{suffix}"
        )
    except F0Error as error:
        _fail(error)
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


@package_app.command("export")
def package_export(
    ctx: typer.Context,
    story_id: str,
    export_format: Annotated[ExportFormat, typer.Option("--format")],
    force: Annotated[bool, typer.Option("--force")] = False,
    package_id: Annotated[str | None, typer.Option("--package-id")] = None,
) -> None:
    try:
        replaced, unchanged, _paths = export_package(
            ctx.obj["data_dir"],
            story_id,
            export_format,
            force=force,
            package_id=package_id,
        )
        typer.echo(f"exported={replaced} unchanged={unchanged}")
    except F0Error as error:
        _fail(error)
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


@script_app.command("build")
def script_build(
    ctx: typer.Context,
    story_id: str,
    package_id: Annotated[str, typer.Option("--package-id")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
) -> None:
    try:
        script, created, json_path, markdown_path = build_script(
            ctx.obj["data_dir"],
            story_id,
            package_id,
            output_dir=output_dir,
        )
        typer.echo(
            f"script_id={script.script_id} {'created' if created else 'unchanged'} "
            f"json={json_path} markdown={markdown_path}"
        )
    except F0Error as error:
        _fail(error)
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


@video_app.command("render")
def video_render(
    script_json: Path,
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    voice: Annotated[str | None, typer.Option("--voice")] = None,
) -> None:
    try:
        rendered, info, selected_voice = render_video(
            script_json, output_dir=output_dir, requested_voice=voice
        )
        typer.echo(
            f"video={rendered / 'video.mp4'} voice={selected_voice} "
            f"dimensions={info.width}x{info.height} duration={info.duration_seconds:.3f}s"
        )
    except F0Error as error:
        _fail(error)
    except Exception:
        _fail(F0Error("E_UNEXPECTED", "unexpected failure; preserve data and inspect diagnostics"))


def main() -> None:
    app()
