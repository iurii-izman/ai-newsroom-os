from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import imageio_ffmpeg  # type: ignore[import-untyped]
from PIL import Image, ImageDraw, ImageFont

from ai_newsroom.models import F0Error
from ai_newsroom.script_builder import load_script
from ai_newsroom.script_models import ProductionScript, ScriptScene
from ai_newsroom.tts import synthesize_tts

WIDTH: Final = 1080
HEIGHT: Final = 1920
FRAME_RATE: Final = 30
TEMPLATE: Final = "TEXT_CARD_V1_1"
MIN_PILOT_DURATION: Final = 38
MAX_PILOT_DURATION: Final = 55
MIN_CARD_DURATION: Final = 1.5
TARGET_MAX_CARD_DURATION: Final = 5.5
MAX_CARD_DURATION: Final = 6.5
MAX_CARD_WORDS: Final = 10
LOUDNESS_TARGET: Final = -16.0
# AAC can introduce roughly 2 dB of inter-sample overshoot for this speech track.
# The encoder-side headroom keeps the measured final MP4 below the -1.0 dBTP contract.
TRUE_PEAK_TARGET: Final = -4.0
BACKGROUND: Final = "#111318"
FOREGROUND: Final = "#F4F6F8"
SECONDARY: Final = "#AAB2BE"
ACCENT: Final = "#5EE1B2"
_SRT_TIMING: Final = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration_seconds: float
    has_video: bool
    has_audio: bool
    frame_rate: float = FRAME_RATE
    video_codec: str = "h264"
    audio_codec: str = "aac-lc"
    pixel_format: str = "yuv420p"
    faststart: bool = True
    integrated_loudness: float = 0.0
    true_peak: float = 0.0
    tts_fallback_used: bool = False
    visual_card_count: int = 0


@dataclass(frozen=True)
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class TimedCard:
    scene_order: int
    section_label: str
    narration_text: str
    source_label: str
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True)
class _TimedWord:
    text: str
    start_seconds: float
    end_seconds: float


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
    preferred = [fonts / "segoeui.ttf", fonts / "arial.ttf", fonts / "calibri.ttf"]
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


def _fit_dominant_text(
    draw: ImageDraw.ImageDraw, value: str, font_path: Path, max_width: int, scale: float
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for nominal_size in range(72, 50, -2):
        font = ImageFont.truetype(str(font_path), max(24, round(nominal_size * scale)))
        try:
            return font, _wrap_text(draw, value, font, max_width, 3)
        except F0Error as error:
            if error.code != "E_VIDEO_LAYOUT":
                raise
    raise F0Error("E_VIDEO_LAYOUT", "dominant narration cannot fit the text-card safe area")


def render_timed_card(
    card: TimedCard,
    path: Path,
    *,
    total_scenes: int,
    total_duration: float,
    font_path: Path | None = None,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> None:
    selected_font = font_path if font_path is not None else find_cyrillic_font()
    scale = width / WIDTH
    label_font = ImageFont.truetype(str(selected_font), max(16, round(40 * scale)))
    meta_font = ImageFont.truetype(str(selected_font), max(16, round(32 * scale)))
    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = round(96 * scale)
    max_width = width - 2 * margin

    label_y = round(210 * height / HEIGHT)
    draw.rounded_rectangle(
        (margin, label_y, margin + round(110 * scale), label_y + round(10 * scale)),
        radius=round(5 * scale),
        fill=ACCENT,
    )
    section_lines = _wrap_text(draw, card.section_label, label_font, max_width, 2)
    _draw_lines(
        draw,
        section_lines,
        (margin, round(265 * height / HEIGHT)),
        label_font,
        fill=SECONDARY,
        spacing=round(10 * scale),
    )

    dominant_font, narration_lines = _fit_dominant_text(
        draw, card.narration_text, selected_font, max_width, scale
    )
    line_height = dominant_font.getbbox("Hg")[3] - dominant_font.getbbox("Hg")[1]
    text_height = (
        len(narration_lines) * line_height
        + (len(narration_lines) - 1) * round(24 * scale)
    )
    text_y = round((900 * height / HEIGHT) - text_height / 2)
    end_y = _draw_lines(
        draw,
        narration_lines,
        (margin, text_y),
        dominant_font,
        fill=FOREGROUND,
        spacing=round(24 * scale),
    )
    if text_y < round(480 * height / HEIGHT) or end_y > round(1310 * height / HEIGHT):
        raise F0Error("E_VIDEO_LAYOUT", "dominant narration exceeds the vertical safe area")

    source_lines = _wrap_text(draw, card.source_label, meta_font, max_width, 2)
    _draw_lines(
        draw,
        source_lines,
        (margin, round(1450 * height / HEIGHT)),
        meta_font,
        fill=SECONDARY,
        spacing=round(10 * scale),
    )
    counter = f"{card.scene_order:02d} / {total_scenes:02d}"
    draw.text(
        (margin, round(1570 * height / HEIGHT)), counter, font=meta_font, fill=SECONDARY
    )
    progress_y = round(1640 * height / HEIGHT)
    draw.rectangle((margin, progress_y, width - margin, progress_y + 8), fill="#303640")
    progress = min(1.0, max(0.0, card.end_seconds / total_duration))
    draw.rectangle(
        (margin, progress_y, margin + round(max_width * progress), progress_y + 8), fill=ACCENT
    )
    image.save(path, format="PNG", optimize=True)


def render_scene_card(
    scene: ScriptScene,
    path: Path,
    *,
    total_scenes: int,
    font_path: Path | None = None,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> None:
    """Compatibility helper that renders one narration-bearing V1.1 card."""
    render_timed_card(
        TimedCard(scene.order, scene.on_screen_text, scene.narration, scene.source_label, 0.0, 1.0),
        path,
        total_scenes=total_scenes,
        total_duration=1.0,
        font_path=font_path,
        width=width,
        height=height,
    )


def validate_cover_text(value: str, *, name: str, maximum: int) -> str:
    if not value or not value.strip():
        raise F0Error("E_VIDEO_COVER", f"{name} must be non-empty plain text")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise F0Error("E_VIDEO_COVER", f"{name} contains a control character")
    normalized = " ".join(value.split())
    if len(normalized) > maximum:
        raise F0Error("E_VIDEO_COVER", f"{name} exceeds {maximum} characters")
    return normalized


def render_cover(
    script: ProductionScript,
    path: Path,
    *,
    title: str | None = None,
    kicker: str | None = None,
    font_path: Path | None = None,
) -> None:
    selected_font = font_path if font_path is not None else find_cyrillic_font()
    selected_title = validate_cover_text(
        script.working_title if title is None else title, name="cover title", maximum=120
    )
    selected_kicker = (
        None
        if kicker is None
        else validate_cover_text(kicker, name="cover kicker", maximum=80)
    )
    title_font = ImageFont.truetype(str(selected_font), 72)
    label_font = ImageFont.truetype(str(selected_font), 34)
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = 96
    if selected_kicker is not None:
        kicker_lines = _wrap_text(draw, selected_kicker, label_font, WIDTH - 2 * margin, 2)
        _draw_lines(draw, kicker_lines, (margin, 260), label_font, fill=ACCENT, spacing=12)
    draw.rectangle((margin, 390, margin + 18, 1340), fill=ACCENT)
    lines = _wrap_text(draw, selected_title, title_font, WIDTH - 2 * margin - 70, 7)
    end_y = _draw_lines(
        draw, lines, (margin + 70, 470), title_font, fill=FOREGROUND, spacing=24
    )
    if end_y > 1340:
        raise F0Error("E_VIDEO_LAYOUT", "cover title exceeds the vertical safe area")
    draw.text(
        (margin + 70, 1550),
        "AI NEWSROOM • РУЧНАЯ ПРОВЕРКА",
        font=label_font,
        fill=SECONDARY,
    )
    image.save(path, format="PNG", optimize=True)


def _timestamp_seconds(values: tuple[str, ...]) -> float:
    hours, minutes, seconds, milliseconds = (int(value) for value in values)
    return ((hours * 60 + minutes) * 60 + seconds) + milliseconds / 1_000


def parse_srt(path: Path) -> list[SubtitleCue]:
    try:
        value = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing could not be read") from None
    cues: list[SubtitleCue] = []
    previous_end = 0.0
    for expected_index, block in enumerate(re.split(r"\r?\n\r?\n", value), start=1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0] != str(expected_index):
            raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing is invalid")
        match = _SRT_TIMING.fullmatch(lines[1])
        text = " ".join(line.strip() for line in lines[2:] if line.strip())
        if match is None or not text:
            raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing is invalid")
        groups = match.groups()
        start = _timestamp_seconds(groups[:4])
        end = _timestamp_seconds(groups[4:])
        if start < previous_end - 0.001 or end <= start:
            raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing overlaps or is reversed")
        cues.append(SubtitleCue(start, end, text))
        previous_end = end
    if not cues:
        raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing is empty")
    return cues


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _timed_words(cues: list[SubtitleCue]) -> list[_TimedWord]:
    words: list[_TimedWord] = []
    for cue in cues:
        tokens = cue.text.split()
        step = (cue.end_seconds - cue.start_seconds) / len(tokens)
        words.extend(
            _TimedWord(
                token,
                cue.start_seconds + step * index,
                cue.start_seconds + step * (index + 1),
            )
            for index, token in enumerate(tokens)
        )
    return words


def _boundary_rank(value: str) -> int:
    if re.search(r"[.!?][\"»)]*$", value):
        return 0
    if re.search(r"[,;:][\"»)]*$", value):
        return 1
    return 2


def _partition_scene(words: list[_TimedWord]) -> list[list[_TimedWord]]:
    duration = words[-1].end_seconds - words[0].start_seconds
    count = max(
        1,
        math.ceil(duration / TARGET_MAX_CARD_DURATION),
        math.ceil(len(words) / MAX_CARD_WORDS),
    )
    count = min(count, max(1, math.floor(duration / MIN_CARD_DURATION)))
    groups: list[list[_TimedWord]] = []
    start = 0
    for group_number in range(count - 1):
        remaining_groups = count - group_number
        remaining_words = len(words) - start
        target_index = start + round(remaining_words / remaining_groups)
        target_time = words[start].start_seconds + (
            words[-1].end_seconds - words[start].start_seconds
        ) / remaining_groups
        candidates: list[tuple[float, int]] = []
        for end in range(start + 1, len(words)):
            group_duration = words[end - 1].end_seconds - words[start].start_seconds
            words_left = len(words) - end
            groups_left = remaining_groups - 1
            duration_left = words[-1].end_seconds - words[end].start_seconds
            if len(words[start:end]) > MAX_CARD_WORDS or group_duration > MAX_CARD_DURATION:
                break
            if group_duration < MIN_CARD_DURATION:
                continue
            if words_left < groups_left or words_left > MAX_CARD_WORDS * groups_left:
                continue
            if duration_left > MAX_CARD_DURATION * groups_left + 0.01:
                continue
            rank = _boundary_rank(words[end - 1].text)
            score = rank * 10 + abs(words[end - 1].end_seconds - target_time) + abs(
                end - target_index
            ) * 0.2
            candidates.append((score, end))
        if not candidates:
            raise F0Error("E_VIDEO_CAPTIONS", "narration cannot be split within timing bounds")
        end = min(candidates)[1]
        groups.append(words[start:end])
        start = end
    groups.append(words[start:])
    return groups


def build_timed_cards(
    script: ProductionScript, subtitle_path: Path, audio_duration: float
) -> list[TimedCard]:
    cues = parse_srt(subtitle_path)
    subtitle_text = _normalize_text(" ".join(cue.text for cue in cues))
    if subtitle_text != _normalize_text(script.spoken_text):
        raise F0Error("E_VIDEO_CAPTIONS", "subtitle text does not reconstruct spoken_text")
    words = _timed_words(cues)
    expected_words = script.spoken_text.split()
    if [word.text for word in words] != expected_words:
        raise F0Error("E_VIDEO_CAPTIONS", "subtitle words do not match spoken_text")

    cards: list[TimedCard] = []
    offset = 0
    for scene in script.scenes:
        scene_words = scene.narration.split()
        timed_scene_words = words[offset : offset + len(scene_words)]
        if [word.text for word in timed_scene_words] != scene_words:
            raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing crosses a logical scene incorrectly")
        for group in _partition_scene(timed_scene_words):
            cards.append(
                TimedCard(
                    scene.order,
                    scene.on_screen_text,
                    " ".join(word.text for word in group),
                    scene.source_label,
                    group[0].start_seconds,
                    group[-1].end_seconds,
                )
            )
        offset += len(scene_words)
    if offset != len(words):
        raise F0Error("E_VIDEO_CAPTIONS", "subtitle timing contains extra narration")

    contiguous: list[TimedCard] = []
    for index, card in enumerate(cards):
        start = 0.0 if index == 0 else contiguous[-1].end_seconds
        end = audio_duration if index == len(cards) - 1 else card.end_seconds
        contiguous.append(replace(card, start_seconds=start, end_seconds=end))
    if _normalize_text(" ".join(card.narration_text for card in contiguous)) != _normalize_text(
        script.spoken_text
    ):
        raise F0Error("E_VIDEO_CAPTIONS", "timed cards do not reconstruct spoken_text")
    for index, card in enumerate(contiguous):
        if card.duration_seconds > MAX_CARD_DURATION + 0.01:
            raise F0Error("E_VIDEO_CAPTIONS", "a timed card exceeds the maximum duration")
        if index < len(contiguous) - 1 and card.duration_seconds < MIN_CARD_DURATION - 0.01:
            raise F0Error("E_VIDEO_CAPTIONS", "a timed card is shorter than the minimum duration")
    return contiguous


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
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise F0Error("E_VIDEO_RENDER", "FFmpeg execution failed") from None


def media_duration(path: Path) -> float:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg([ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"])
    if result.returncode != 0:
        raise F0Error("E_VIDEO_RENDER", "FFmpeg could not decode the audio track")
    return _duration_from_output(result.stderr)


def _measure_loudness(path: Path) -> tuple[float, float]:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            f"loudnorm=I={LOUDNESS_TARGET:g}:TP={TRUE_PEAK_TARGET:g}:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    loudness = re.search(r'"input_i"\s*:\s*"(-?\d+(?:\.\d+)?)"', result.stderr)
    peak = re.search(r'"input_tp"\s*:\s*"(-?\d+(?:\.\d+)?)"', result.stderr)
    if result.returncode != 0 or loudness is None or peak is None:
        raise F0Error("E_VIDEO_VERIFY", "final audio loudness could not be measured")
    integrated = float(loudness.group(1))
    true_peak = float(peak.group(1))
    if not -17.5 <= integrated <= -14.5 or true_peak > -1.0:
        raise F0Error("E_VIDEO_VERIFY", "final audio loudness is outside the accepted bound")
    return integrated, true_peak


def _loudnorm_filter(audio_path: Path) -> str:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = _run_ffmpeg(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(audio_path),
            "-af",
            f"loudnorm=I={LOUDNESS_TARGET:g}:TP={TRUE_PEAK_TARGET:g}:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    fields: dict[str, str] = {}
    for field in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
        match = re.search(rf'"{field}"\s*:\s*"(-?\d+(?:\.\d+)?)"', result.stderr)
        if match is None:
            raise F0Error("E_VIDEO_RENDER", "FFmpeg loudness analysis was incomplete")
        fields[field] = match.group(1)
    if result.returncode != 0:
        raise F0Error("E_VIDEO_RENDER", "FFmpeg loudness analysis failed")
    return (
        f"loudnorm=I={LOUDNESS_TARGET:g}:TP={TRUE_PEAK_TARGET:g}:LRA=11:"
        f"measured_I={fields['input_i']}:measured_TP={fields['input_tp']}:"
        f"measured_LRA={fields['input_lra']}:measured_thresh={fields['input_thresh']}:"
        f"offset={fields['target_offset']}:linear=true"
    )


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
    video_match = re.search(r"Video:\s*h264.*?(\d{2,5})x(\d{2,5})", output)
    audio_match = re.search(r"Audio:\s*aac\s*\(LC\)", output)
    pixel_match = re.search(r"Video:\s*h264.*?\b(yuv420p)\b", output)
    fps_match = re.search(r"(\d+(?:\.\d+)?)\s+fps", output)
    if result.returncode != 0 or video_match is None or audio_match is None or pixel_match is None:
        raise F0Error("E_VIDEO_VERIFY", "MP4 must decode as H.264/yuv420p with AAC-LC audio")
    width, height = (int(video_match.group(1)), int(video_match.group(2)))
    if (width, height) != expected_dimensions:
        raise F0Error("E_VIDEO_VERIFY", "MP4 dimensions do not match the requested frame")
    frame_rate = float(fps_match.group(1)) if fps_match is not None else 0.0
    if abs(frame_rate - FRAME_RATE) > 0.1:
        raise F0Error("E_VIDEO_VERIFY", "MP4 frame rate is not approximately 30 fps")
    duration = _duration_from_output(output)
    if duration_bounds is not None and not duration_bounds[0] <= duration <= duration_bounds[1]:
        raise F0Error("E_VIDEO_VERIFY", "MP4 duration is outside the accepted pilot bound")
    prefix = path.read_bytes()[: 5 * 1024 * 1024]
    moov = prefix.find(b"moov")
    mdat = prefix.find(b"mdat")
    if moov < 0 or mdat < 0 or moov > mdat:
        raise F0Error("E_VIDEO_VERIFY", "MP4 is not fast-start optimized")
    integrated, true_peak = _measure_loudness(path)
    return VideoInfo(
        width,
        height,
        duration,
        True,
        True,
        frame_rate=frame_rate,
        integrated_loudness=integrated,
        true_peak=true_peak,
    )


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
    concat_path = output_path.parent / "cards.ffconcat"
    lines = ["ffconcat version 1.0"]
    for scene_path, duration in zip(scene_paths, durations, strict=True):
        if re.fullmatch(r"(?:card-\d{3}|scene-\d{2})\.png", scene_path.name) is None:
            raise F0Error("E_VIDEO_RENDER", "generated card filename is invalid")
        lines.extend([f"file '{scene_path.name}'", f"duration {duration:.6f}"])
    lines.append(f"file '{scene_paths[-1].name}'")
    concat_path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    loudnorm_filter = _loudnorm_filter(audio_path)
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
            "-profile:a",
            "aac_low",
            "-af",
            loudnorm_filter,
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
        output_path, expected_dimensions=expected_dimensions, duration_bounds=duration_bounds
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_validated_fallback(
    script_path: Path,
    script: ProductionScript,
    audio_path: Path,
    subtitle_path: Path,
) -> str:
    fallback = script_path.parent / "video-final"
    manifest_path = fallback / "manifest.json"
    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise F0Error("E_TTS_FALLBACK", "validated fallback manifest is unavailable") from None
    expected_lineage = {
        "script_id": script.script_id,
        "package_id": script.package_id,
        "story_id": script.story_id,
    }
    if any(manifest.get(key) != value for key, value in expected_lineage.items()):
        raise F0Error("E_TTS_FALLBACK", "fallback lineage does not match the script")
    hashes = manifest.get("artifact_sha256")
    if not isinstance(hashes, dict):
        raise F0Error("E_TTS_FALLBACK", "fallback hashes are unavailable")
    source_audio = fallback / "voice.mp3"
    source_subtitles = fallback / "subtitles.srt"
    if hashes.get("voice.mp3") != _sha256(source_audio) or hashes.get("subtitles.srt") != _sha256(
        source_subtitles
    ):
        raise F0Error("E_TTS_FALLBACK", "fallback audio or subtitles failed hash validation")
    audio_path.unlink(missing_ok=True)
    subtitle_path.unlink(missing_ok=True)
    shutil.copyfile(source_audio, audio_path)
    shutil.copyfile(source_subtitles, subtitle_path)
    voice = manifest.get("voice")
    if not isinstance(voice, str) or not voice.startswith("ru-RU-"):
        raise F0Error("E_TTS_FALLBACK", "fallback voice is not a validated Russian voice")
    return voice


def _validate_output_path(script_path: Path, selected_output: Path) -> None:
    protected = (script_path.parent / "video-final").resolve()
    resolved = selected_output.resolve()
    if resolved == protected or resolved.is_relative_to(protected):
        raise F0Error("E_VIDEO_OUTPUT", "the validated video-final directory is read-only")


def render_video(
    script_path: Path,
    *,
    output_dir: Path | None = None,
    requested_voice: str | None = None,
    cover_title: str | None = None,
    cover_kicker: str | None = None,
) -> tuple[Path, VideoInfo, str]:
    script = load_script(script_path)
    selected_output = output_dir if output_dir is not None else script_path.parent / "video"
    _validate_output_path(script_path, selected_output)
    if cover_title is not None:
        cover_title = validate_cover_text(cover_title, name="cover title", maximum=120)
    if cover_kicker is not None:
        cover_kicker = validate_cover_text(cover_kicker, name="cover kicker", maximum=80)
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
        tts_fallback_used = False
        try:
            voice = synthesize_tts(
                script.spoken_text, audio_path, subtitles_path, requested_voice=requested_voice
            )
        except F0Error as error:
            if error.code not in {"E_TTS_VOICE", "E_TTS_SYNTHESIS"}:
                raise
            voice = _copy_validated_fallback(script_path, script, audio_path, subtitles_path)
            tts_fallback_used = True

        audio_seconds = media_duration(audio_path)
        if not MIN_PILOT_DURATION <= audio_seconds <= MAX_PILOT_DURATION:
            raise F0Error("E_VIDEO_RENDER", "TTS duration is outside the accepted polished bound")
        cards = build_timed_cards(script, subtitles_path, audio_seconds)
        if not 9 <= len(cards) <= 16:
            raise F0Error("E_VIDEO_CAPTIONS", "polished render must contain 9 to 16 timed cards")

        font_path = find_cyrillic_font()
        cover_path = work / "cover.png"
        render_cover(
            script,
            cover_path,
            title=cover_title,
            kicker=cover_kicker,
            font_path=font_path,
        )
        card_paths: list[Path] = []
        for index, card in enumerate(cards, start=1):
            card_path = work / f"card-{index:03d}.png"
            render_timed_card(
                card,
                card_path,
                total_scenes=len(script.scenes),
                total_duration=audio_seconds,
                font_path=font_path,
            )
            card_paths.append(card_path)

        video_path = work / "video.mp4"
        info = assemble_video(
            card_paths,
            [card.duration_seconds for card in cards],
            audio_path,
            video_path,
            expected_dimensions=(WIDTH, HEIGHT),
            duration_bounds=(MIN_PILOT_DURATION, MAX_PILOT_DURATION),
        )
        info = replace(
            info,
            tts_fallback_used=tts_fallback_used,
            visual_card_count=len(cards),
        )

        artifact_paths = [audio_path, subtitles_path, cover_path, *card_paths, video_path]
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
            "integrated_loudness_lufs": info.integrated_loudness,
            "true_peak_dbtp": info.true_peak,
            "visual_card_count": len(cards),
            "tts_fallback_used": tts_fallback_used,
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
