from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import imageio_ffmpeg  # type: ignore[import-untyped]
from PIL import Image, ImageDraw, ImageFont

from ai_newsroom.models import F0Error
from ai_newsroom.script_builder import load_script
from ai_newsroom.script_models import ProductionScript, ScriptScene, count_spoken_words
from ai_newsroom.tts import synthesize_tts

WIDTH: Final = 1080
HEIGHT: Final = 1920
FRAME_RATE: Final = 30
TEMPLATE: Final = "TEXT_CARD_V1"
MIN_PILOT_DURATION: Final = 25
MAX_PILOT_DURATION: Final = 85
BACKGROUND: Final = "#111318"
FOREGROUND: Final = "#F4F6F8"
SECONDARY: Final = "#AAB2BE"
ACCENT: Final = "#5EE1B2"


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration_seconds: float
    has_video: bool
    has_audio: bool


def _font_supports_cyrillic(path: Path) -> bool:
    try:
        font = ImageFont.truetype(str(path), 48)
        return bool(font.getbbox("Привет")) and bytes(font.getmask("Ж")) != bytes(
            font.getmask("Я")
        )
    except (OSError, ValueError):
        return False


def find_cyrillic_font() -> Path:
    fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    preferred = [
        fonts / "segoeui.ttf",
        fonts / "arial.ttf",
        fonts / "calibri.ttf",
    ]
    for path in preferred:
        if path.is_file() and _font_supports_cyrillic(path):
            return path
    if fonts.is_dir():
        for pattern in ("*.ttf", "*.otf"):
            for path in sorted(fonts.glob(pattern)):
                if _font_supports_cyrillic(path):
                    return path
    raise F0Error("FONT_REQUIRED", "no installed Cyrillic-capable system font was found")


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = value.replace("\n", " ").split()
    if not words:
        raise F0Error("E_VIDEO_LAYOUT", "text card contains empty display text")
    lines: list[str] = []
    current = ""
    for word in words:
        if draw.textlength(word, font=font) > max_width:
            raise F0Error("E_VIDEO_LAYOUT", "one text-card word is too wide to fit")
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    if len(lines) > max_lines:
        raise F0Error("E_VIDEO_LAYOUT", "text card exceeds the maximum line count")
    return lines


def _draw_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    position: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    *,
    fill: str,
    spacing: int,
) -> int:
    x = position[0]
    y: float = position[1]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line, font=font)
        y = box[3] + spacing
    return round(y)


def render_scene_card(
    scene: ScriptScene,
    path: Path,
    *,
    total_scenes: int,
    font_path: Path | None = None,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> None:
    selected_font = font_path if font_path is not None else find_cyrillic_font()
    scale = width / WIDTH
    title_font = ImageFont.truetype(str(selected_font), max(24, round(76 * scale)))
    label_font = ImageFont.truetype(str(selected_font), max(16, round(36 * scale)))
    counter_font = ImageFont.truetype(str(selected_font), max(16, round(32 * scale)))
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = round(96 * scale)
    max_width = width - 2 * margin
    accent_y = round(310 * height / HEIGHT)
    draw.rounded_rectangle(
        (margin, accent_y, margin + round(170 * scale), accent_y + round(18 * scale)),
        radius=round(9 * scale),
        fill=ACCENT,
    )
    lines = _wrap_text(draw, scene.on_screen_text, title_font, max_width, 6)
    text_y = round(430 * height / HEIGHT)
    end_y = _draw_lines(
        draw, lines, (margin, text_y), title_font, fill=FOREGROUND, spacing=round(24 * scale)
    )
    if end_y > round(1370 * height / HEIGHT):
        raise F0Error("E_VIDEO_LAYOUT", "main text exceeds the vertical safe area")
    source_lines = _wrap_text(draw, scene.source_label, label_font, max_width, 2)
    _draw_lines(
        draw,
        source_lines,
        (margin, round(1510 * height / HEIGHT)),
        label_font,
        fill=SECONDARY,
        spacing=round(12 * scale),
    )
    counter = f"{scene.order:02d} / {total_scenes:02d}"
    draw.text(
        (margin, round(1760 * height / HEIGHT)),
        counter,
        font=counter_font,
        fill=SECONDARY,
    )
    progress_width = max_width * scene.order // total_scenes
    progress_y = round(1830 * height / HEIGHT)
    draw.rectangle((margin, progress_y, width - margin, progress_y + 6), fill="#303640")
    draw.rectangle((margin, progress_y, margin + progress_width, progress_y + 6), fill=ACCENT)
    image.save(path, format="PNG", optimize=True)


def render_cover(
    script: ProductionScript, path: Path, *, font_path: Path | None = None
) -> None:
    selected_font = font_path if font_path is not None else find_cyrillic_font()
    title_font = ImageFont.truetype(str(selected_font), 72)
    label_font = ImageFont.truetype(str(selected_font), 34)
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = 96
    draw.rectangle((margin, 300, margin + 18, 1420), fill=ACCENT)
    lines = _wrap_text(draw, script.working_title, title_font, WIDTH - 2 * margin - 70, 7)
    end_y = _draw_lines(
        draw, lines, (margin + 70, 410), title_font, fill=FOREGROUND, spacing=24
    )
    if end_y > 1400:
        raise F0Error("E_VIDEO_LAYOUT", "cover title exceeds the vertical safe area")
    draw.text((margin + 70, 1510), "AI NEWS • РУЧНАЯ ПРОВЕРКА", font=label_font, fill=SECONDARY)
    image.save(path, format="PNG", optimize=True)


def _duration_from_output(output: str) -> float:
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if match is None:
        raise F0Error("E_VIDEO_VERIFY", "FFmpeg did not report media duration")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _run_ffmpeg(
    arguments: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise F0Error("E_VIDEO_RENDER", "FFmpeg execution failed") from None


def media_duration(path: Path) -> float:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg([ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"])
    if result.returncode != 0:
        raise F0Error("E_VIDEO_RENDER", "FFmpeg could not decode the audio track")
    return _duration_from_output(result.stderr)


def verify_video(
    path: Path,
    *,
    expected_dimensions: tuple[int, int],
    duration_bounds: tuple[float, float] | None,
) -> VideoInfo:
    if not path.is_file() or path.stat().st_size == 0:
        raise F0Error("E_VIDEO_VERIFY", "encoded MP4 is missing or empty")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg(
        [
            ffmpeg,
            "-hide_banner",
            "-v",
            "info",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ]
    )
    output = result.stderr
    video_match = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", output)
    has_video = video_match is not None
    has_audio = re.search(r"Audio:", output) is not None
    if result.returncode != 0 or not has_video or not has_audio or video_match is None:
        raise F0Error("E_VIDEO_VERIFY", "MP4 must decode with both video and audio streams")
    width, height = (int(video_match.group(1)), int(video_match.group(2)))
    if (width, height) != expected_dimensions:
        raise F0Error("E_VIDEO_VERIFY", "MP4 dimensions do not match the requested frame")
    duration = _duration_from_output(output)
    if duration_bounds is not None and not duration_bounds[0] <= duration <= duration_bounds[1]:
        raise F0Error("E_VIDEO_VERIFY", "MP4 duration is outside the accepted pilot bound")
    return VideoInfo(width, height, duration, True, True)


def assemble_video(
    scene_paths: list[Path],
    durations: list[float],
    audio_path: Path,
    output_path: Path,
    *,
    expected_dimensions: tuple[int, int],
    duration_bounds: tuple[float, float] | None,
) -> VideoInfo:
    if (
        not scene_paths
        or len(scene_paths) != len(durations)
        or any(value <= 0 for value in durations)
    ):
        raise F0Error("E_VIDEO_RENDER", "scene timeline is invalid")
    if any(path.parent != output_path.parent for path in scene_paths):
        raise F0Error("E_VIDEO_RENDER", "scene images must be in the render workspace")
    concat_path = output_path.parent / "scenes.ffconcat"
    lines = ["ffconcat version 1.0"]
    for scene_path, duration in zip(scene_paths, durations, strict=True):
        if re.fullmatch(r"scene-\d{2}\.png", scene_path.name) is None:
            raise F0Error("E_VIDEO_RENDER", "generated scene filename is invalid")
        lines.extend([f"file '{scene_path.name}'", f"duration {duration:.6f}"])
    lines.append(f"file '{scene_paths[-1].name}'")
    concat_path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg(
        [
            ffmpeg,
            "-hide_banner",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path.name,
            "-i",
            str(audio_path.resolve()),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FRAME_RATE),
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            output_path.name,
        ],
        cwd=output_path.parent,
    )
    concat_path.unlink(missing_ok=True)
    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        raise F0Error("E_VIDEO_RENDER", "FFmpeg could not encode the MP4")
    return verify_video(
        output_path,
        expected_dimensions=expected_dimensions,
        duration_bounds=duration_bounds,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_video(
    script_path: Path,
    *,
    output_dir: Path | None = None,
    requested_voice: str | None = None,
) -> tuple[Path, VideoInfo, str]:
    script = load_script(script_path)
    selected_output = output_dir if output_dir is not None else script_path.parent / "video"
    if selected_output.exists():
        raise F0Error("E_VIDEO_CONFLICT", "video output directory already exists")
    try:
        selected_output.parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=".video-", dir=selected_output.parent))
    except OSError:
        raise F0Error("E_VIDEO_RENDER", "video workspace cannot be created") from None

    try:
        audio_path = work / "voice.mp3"
        subtitles_path = work / "subtitles.srt"
        voice = synthesize_tts(
            script.spoken_text, audio_path, subtitles_path, requested_voice=requested_voice
        )
        font_path = find_cyrillic_font()
        cover_path = work / "cover.png"
        render_cover(script, cover_path, font_path=font_path)
        scene_paths: list[Path] = []
        for scene in script.scenes:
            scene_path = work / f"scene-{scene.order:02d}.png"
            render_scene_card(
                scene,
                scene_path,
                total_scenes=len(script.scenes),
                font_path=font_path,
            )
            scene_paths.append(scene_path)

        audio_seconds = media_duration(audio_path)
        if not MIN_PILOT_DURATION <= audio_seconds <= MAX_PILOT_DURATION:
            raise F0Error("E_VIDEO_RENDER", "TTS duration is outside the accepted pilot bound")
        weights = [max(1, count_spoken_words(scene.narration)) for scene in script.scenes]
        total_weight = sum(weights)
        durations = [audio_seconds * weight / total_weight for weight in weights]
        video_path = work / "video.mp4"
        info = assemble_video(
            scene_paths,
            durations,
            audio_path,
            video_path,
            expected_dimensions=(WIDTH, HEIGHT),
            duration_bounds=(MIN_PILOT_DURATION, MAX_PILOT_DURATION),
        )

        artifact_paths = [audio_path, subtitles_path, cover_path, *scene_paths, video_path]
        artifacts = [path.name for path in artifact_paths]
        manifest = {
            "schema_version": 1,
            "script_id": script.script_id,
            "package_id": script.package_id,
            "story_id": script.story_id,
            "template": TEMPLATE,
            "voice": voice,
            "dimensions": [WIDTH, HEIGHT],
            "frame_rate": FRAME_RATE,
            "duration_seconds": round(info.duration_seconds, 3),
            "created_at": datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "manual_approval_required": True,
            "artifacts": artifacts,
            "artifact_sha256": {path.name: _sha256(path) for path in artifact_paths},
        }
        (work / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(work, selected_output)
        return selected_output, info, voice
    except F0Error:
        raise
    except OSError:
        raise F0Error("E_VIDEO_RENDER", "video artifacts could not be finalized") from None
    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)
