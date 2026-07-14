from __future__ import annotations

import asyncio
import hashlib
import json
import math
import struct
import subprocess
import wave
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import edge_tts
import pytest
from PIL import Image
from typer.testing import CliRunner

import ai_newsroom.video_renderer as video_renderer
from ai_newsroom.cli import app
from ai_newsroom.database import harvest_snapshots, init_database, load_story_source
from ai_newsroom.models import (
    EVIDENCE_LIMITATION,
    BuildGenerator,
    F0Error,
    RealStoryPackagePayload,
    SourceReference,
)
from ai_newsroom.normalization import story_id
from ai_newsroom.package_builder import build_package, load_validated_package
from ai_newsroom.rss import parse_live_feed_bytes
from ai_newsroom.script_builder import (
    GENERATOR_VERSION,
    TEMPLATE_VERSION,
    build_script,
    expected_script_identity,
    load_script,
)
from ai_newsroom.script_models import ProductionScript, ScriptScene, count_spoken_words
from ai_newsroom.tts import choose_russian_voice, synthesize_tts
from ai_newsroom.video_renderer import (
    VideoInfo,
    assemble_video,
    build_timed_cards,
    find_cyrillic_font,
    render_scene_card,
    render_video,
    validate_cover_text,
)

NOW = "2026-07-14T12:00:00Z"
SECRET = "test-key"
URL = "https://openai.com/news/f3-pilot"
runner = CliRunner()


class FakeCompletions:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def completion(value: dict[str, Any] | str) -> Any:
    content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    choice = SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=content))
    return SimpleNamespace(choices=[choice], usage=SimpleNamespace())


def prepare_story(data_dir: Path) -> str:
    init_database(data_dir)
    feed = (
        "<rss><channel><item><title>Новый AI-инструмент</title>"
        f"<link>{URL}</link>"
        "<description>Поставщик заявил о новой функции для рабочих процессов.</description>"
        "</item></channel></rss>"
    ).encode()
    snapshot = parse_live_feed_bytes(feed, NOW, "openai-news", 5)[0]
    harvest_snapshots(data_dir, [snapshot])
    return story_id(snapshot.id)


def package_draft(
    data_dir: Path, selected_story: str, verdict: str, *, allow_claims: bool = True
) -> dict[str, Any]:
    _story, source = load_story_source(data_dir, selected_story)
    return {
        "story_id": selected_story,
        "source_id": source.id,
        "working_title": "Что меняет новый AI-инструмент",
        "editorial_format": "AI_SIGNAL",
        "one_sentence_fact": "Поставщик опубликовал анонс AI-инструмента.",
        "why_it_matters": "Анонс относится к рабочим процессам специалистов.",
        "editorial_angle": "Отделить заявление поставщика от результата проверки.",
        "claims": [
            {
                "claim_id": "claim_allowed",
                "text": "Поставщик заявляет о новой функции для рабочих процессов.",
                "status": "VENDOR_CLAIM",
                "confidence": "MEDIUM",
                "evidence_source_id": source.id,
                "use_in_script": allow_claims,
                "qualification": "По данным официальной ленты поставщика.",
            },
            {
                "claim_id": "claim_unverified",
                "text": "Функция гарантированно удваивает производительность.",
                "status": "UNVERIFIED",
                "confidence": "LOW",
                "evidence_source_id": source.id,
                "use_in_script": False,
                "qualification": "Нет подтверждения.",
            },
            {
                "claim_id": "claim_verified",
                "text": "В официальной ленте опубликован анонс новой AI-функции.",
                "status": "VERIFIED",
                "confidence": "HIGH",
                "evidence_source_id": source.id,
                "use_in_script": allow_claims,
                "qualification": ("Подтверждено только фактом публикации в указанной ленте."),
            },
        ],
        "limitations": [EVIDENCE_LIMITATION],
        "demonstration_plan": ["Проверить функцию отдельно."],
        "publication_verdict": verdict,
        "source_references": [{"source_id": source.id, "canonical_url": URL}],
    }


def prepare_real_package(
    data_dir: Path,
    verdict: str = "READY_WITH_QUALIFICATION",
    *,
    allow_claims: bool = True,
) -> tuple[str, str, RealStoryPackagePayload]:
    selected_story = prepare_story(data_dir)
    package_client = FakeClient(
        [completion(package_draft(data_dir, selected_story, verdict, allow_claims=allow_claims))]
    )
    package_id, _created = build_package(
        data_dir,
        selected_story,
        NOW,
        BuildGenerator.DEEPSEEK,
        api_key=SECRET,
        client=package_client,
    )
    _snapshot, package = load_validated_package(data_dir, selected_story, package_id=package_id)
    assert isinstance(package, RealStoryPackagePayload)
    return selected_story, package_id, package


def test_script_rejects_mock_package(tmp_path: Path) -> None:
    selected_story = prepare_story(tmp_path)
    package_id, _created = build_package(tmp_path, selected_story, NOW)
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
        )
    assert error.value.code == "E_SCRIPT_PACKAGE"


@pytest.mark.parametrize("verdict", ["HOLD", "REJECT"])
def test_script_rejects_blocked_verdicts(tmp_path: Path, verdict: str) -> None:
    selected_story, package_id, _package = prepare_real_package(tmp_path, verdict)
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
        )
    assert error.value.code == "E_SCRIPT_VERDICT"


def test_valid_script_filters_unverified_and_reuses_stable_pair(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    script, created, json_path, markdown_path = build_script(
        tmp_path,
        selected_story,
        package_id,
    )
    assert created is True
    assert isinstance(script, ProductionScript)
    assert 90 <= script.word_count <= 170
    assert script.spoken_text == " ".join(scene.narration for scene in script.scenes)
    assert [scene.order for scene in script.scenes] == list(range(1, len(script.scenes) + 1))
    assert 5 <= len(script.scenes) <= 8
    assert {scene.visual_kind for scene in script.scenes} == {"TEXT_CARD"}
    assert {scene.source_label for scene in script.scenes} == {"Источник: openai.com"}
    assert script.generator == GENERATOR_VERSION == "safe-local-v1"
    assert script.template_version == TEMPLATE_VERSION == "claim-safe-script-v1"
    referenced = {claim_id for scene in script.scenes for claim_id in scene.claim_ids}
    assert referenced == {"claim_allowed", "claim_verified"}
    assert "claim_unverified" not in referenced
    assert package.claims[0].text in script.spoken_text
    assert package.claims[0].qualification in script.spoken_text
    assert package.claims[1].text not in script.spoken_text
    assert package.claims[2].text in script.spoken_text
    assert package.claims[2].qualification in script.spoken_text
    assert package.limitations[0] in script.spoken_text
    assert script.hook == f"Главный факт: {package.claims[2].text}"
    original = (json_path.read_bytes(), markdown_path.read_bytes())

    repeated = build_script(
        tmp_path,
        selected_story,
        package_id,
    )
    assert repeated[1] is False
    assert (json_path.read_bytes(), markdown_path.read_bytes()) == original


def test_script_build_cli_composes_real_package_offline_and_reuses_pair(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    expected_fingerprint, expected_script_id = expected_script_identity(package)
    command = [
        "--data-dir",
        str(tmp_path),
        "script",
        "build",
        selected_story,
        "--package-id",
        package_id,
    ]

    built = runner.invoke(app, command)
    assert built.exit_code == 0
    assert f"script_id={expected_script_id} created" in built.stdout
    assert "provider_called" not in built.stdout

    script_dir = tmp_path / "scripts" / selected_story
    (json_path,) = script_dir.glob("script_*.json")
    (markdown_path,) = script_dir.glob("script_*.md")
    script = ProductionScript.model_validate_json(json_path.read_bytes())
    assert script.script_id == expected_script_id
    assert script.input_fingerprint == expected_fingerprint
    assert script.story_id == selected_story
    assert script.package_id == package_id
    assert script.source_references == package.source_references
    assert script.limitations == package.limitations
    original = (json_path.read_bytes(), markdown_path.read_bytes())

    repeated = runner.invoke(app, command)
    assert repeated.exit_code == 0
    assert f"script_id={script.script_id} unchanged" in repeated.stdout
    assert (json_path.read_bytes(), markdown_path.read_bytes()) == original


def test_script_rejects_package_without_allowed_claims(tmp_path: Path) -> None:
    selected_story, package_id, _package = prepare_real_package(tmp_path, allow_claims=False)
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
        )
    assert error.value.code == "E_SCRIPT_PACKAGE"
    assert not (tmp_path / "scripts").exists()


def test_script_identity_is_deterministic_and_package_bound(tmp_path: Path) -> None:
    _story, _package_id, package = prepare_real_package(tmp_path)
    first = expected_script_identity(package)
    second = expected_script_identity(package)
    assert first == second
    changed = package.model_copy(update={"working_title": package.working_title + "!"})
    assert expected_script_identity(changed) != first


def test_partial_script_pair_is_a_conflict(tmp_path: Path) -> None:
    selected_story, package_id, _package = prepare_real_package(tmp_path)
    script, _created, json_path, markdown_path = build_script(
        tmp_path,
        selected_story,
        package_id,
    )
    assert script.script_id in json_path.name
    markdown_path.unlink()
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
        )
    assert error.value.code == "E_SCRIPT_PARTIAL"


def test_renderer_rejects_invalid_script_without_tts(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}\n", encoding="utf-8")
    with pytest.raises(F0Error) as error:
        load_script(invalid)
    assert error.value.code == "E_SCRIPT_INVALID"
    result = runner.invoke(app, ["video", "render", str(invalid)])
    assert result.exit_code != 0
    assert "E_SCRIPT_INVALID" in result.stderr
    assert "Traceback" not in result.output


def test_cyrillic_scene_card_renders_inside_safe_layout(tmp_path: Path) -> None:
    scene = ScriptScene(
        order=1,
        narration="Краткая русская фраза для озвучивания.",
        on_screen_text="Как AI меняет рабочий процесс без выдуманных обещаний",
        source_label="Источник: официальная лента поставщика",
        claim_ids=[],
        visual_kind="TEXT_CARD",
    )
    output = tmp_path / "scene.png"
    render_scene_card(scene, output, total_scenes=5, font_path=find_cyrillic_font())
    with Image.open(output) as image:
        assert image.size == (1080, 1920)
        assert image.getbbox() == (0, 0, 1080, 1920)


def _write_wav(path: Path, duration: float = 1.2) -> None:
    sample_rate = 44_100
    frames = int(sample_rate * duration)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        values = (
            struct.pack("<h", round(2_000 * math.sin(2 * math.pi * 440 * index / sample_rate)))
            for index in range(frames)
        )
        output.writeframes(b"".join(values))


def test_short_offline_mp4_contains_video_and_audio(tmp_path: Path) -> None:
    scenes = []
    for index, color in enumerate(((20, 30, 40), (40, 30, 20)), start=1):
        path = tmp_path / f"scene-{index:02d}.png"
        Image.new("RGB", (320, 568), color).save(path)
        scenes.append(path)
    audio = tmp_path / "audio.wav"
    _write_wav(audio)
    output = tmp_path / "video.mp4"
    info = assemble_video(
        scenes,
        [0.6, 0.6],
        audio,
        output,
        expected_dimensions=(320, 568),
        duration_bounds=None,
    )
    assert output.stat().st_size > 0
    assert info.has_video is True
    assert info.has_audio is True
    assert info.width == 320
    assert info.height == 568


def test_tts_selects_preferred_voice_and_sends_only_narration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    voices = [
        {"ShortName": "ru-RU-SvetlanaNeural", "Locale": "ru-RU"},
        {"ShortName": "ru-RU-DmitryNeural", "Locale": "ru-RU"},
        {"ShortName": "en-US-TestNeural", "Locale": "en-US"},
    ]
    assert choose_russian_voice(voices, None) == "ru-RU-DmitryNeural"
    calls: list[tuple[str, str, dict[str, Any]]] = []

    class FakeManager:
        def __init__(self) -> None:
            self.voices = voices

        @classmethod
        async def create(cls) -> FakeManager:
            return cls()

    class FakeCommunication:
        def __init__(self, text: str, voice: str, **kwargs: Any) -> None:
            calls.append((text, voice, kwargs))

        async def stream(self) -> Any:
            yield {"type": "audio", "data": b"fake-mp3"}
            yield {
                "type": "SentenceBoundary",
                "offset": 0,
                "duration": 10_000_000,
                "text": "Первая фраза.",
            }
            yield {
                "type": "SentenceBoundary",
                "offset": 9_500_000,
                "duration": 10_000_000,
                "text": "Вторая фраза.",
            }

    monkeypatch.setattr(edge_tts, "VoicesManager", FakeManager)
    monkeypatch.setattr(edge_tts, "Communicate", FakeCommunication)

    def run_immediate(coroutine: Any) -> str:
        try:
            coroutine.send(None)
        except StopIteration as finished:
            return str(finished.value)
        raise AssertionError("offline TTS fake unexpectedly suspended")

    monkeypatch.setattr(asyncio, "run", run_immediate)
    audio = tmp_path / "voice.mp3"
    subtitles = tmp_path / "subtitles.srt"
    spoken_text = "Первая фраза. Вторая фраза."
    voice = synthesize_tts(spoken_text, audio, subtitles)
    assert voice == "ru-RU-DmitryNeural"
    assert calls[0][0] == spoken_text
    assert calls[0][1] == voice
    assert calls[0][2] == {
        "rate": "+12%",
        "volume": "+0%",
        "pitch": "+0Hz",
        "boundary": "SentenceBoundary",
    }
    assert audio.read_bytes() == b"fake-mp3"
    subtitle_text = subtitles.read_text(encoding="utf-8-sig")
    assert "Первая фраза." in subtitle_text
    assert "Вторая фраза." in subtitle_text
    assert "00:00:01,000 --> 00:00:01,950" in subtitle_text


def _timed_card_script() -> ProductionScript:
    scene_texts = [
        f"Сцена {index} сообщает только проверенный текст и сохраняет точную последовательность "
        "всех русских слов для карточки сейчас без каких-либо изменений."
        for index in range(1, 6)
    ]
    spoken_text = " ".join(scene_texts)
    return ProductionScript(
        schema_version=1,
        script_id="script_" + "a" * 24,
        story_id="story_" + "b" * 24,
        package_id="pkg_" + "c" * 24,
        input_fingerprint="d" * 64,
        generator="safe-local-v1",
        template_version="claim-safe-script-v1",
        language="ru",
        target_duration_seconds=45,
        working_title="Проверенный заголовок",
        hook=scene_texts[0],
        spoken_text=spoken_text,
        word_count=count_spoken_words(spoken_text),
        scenes=[
            ScriptScene(
                order=index,
                narration=text,
                on_screen_text=f"Раздел {index}",
                source_label="Источник: example.com",
                claim_ids=[],
                visual_kind="TEXT_CARD",
            )
            for index, text in enumerate(scene_texts, start=1)
        ],
        source_references=[
            SourceReference(
                source_id="src_" + "e" * 24,
                canonical_url="https://example.com/source",
            )
        ],
        limitations=["Тестовое ограничение."],
        caption="Тестовая подпись.",
        manual_approval_required=True,
    )


def _write_scene_srt(path: Path, script: ProductionScript) -> None:
    blocks = []
    for index, scene in enumerate(script.scenes, start=1):
        start = (index - 1) * 9
        end = index * 9
        blocks.append(
            f"{index}\n00:00:{start:02d},000 --> 00:00:{end:02d},000\n{scene.narration}\n"
        )
    path.write_text("\n".join(blocks), encoding="utf-8")


def test_timed_caption_segmentation_preserves_narration_and_scene_metadata(
    tmp_path: Path,
) -> None:
    script = _timed_card_script()
    subtitles = tmp_path / "subtitles.srt"
    _write_scene_srt(subtitles, script)

    cards = build_timed_cards(script, subtitles, 45.0)

    assert 9 <= len(cards) <= 16
    assert len(cards) > len(script.scenes)
    assert " ".join(card.narration_text for card in cards) == script.spoken_text
    assert max(card.duration_seconds for card in cards) <= 6.5
    assert min(card.duration_seconds for card in cards[:-1]) >= 1.5
    for card in cards:
        scene = script.scenes[card.scene_order - 1]
        assert card.section_label == scene.on_screen_text
        assert card.source_label == scene.source_label
        assert card.narration_text in scene.narration


@pytest.mark.parametrize(
    ("value", "maximum"),
    [("строка\nс переносом", 120), ("д" * 121, 120), ("\x00", 80)],
)
def test_cover_override_validation_rejects_controls_and_excessive_length(
    value: str, maximum: int
) -> None:
    with pytest.raises(F0Error) as error:
        validate_cover_text(value, name="cover", maximum=maximum)
    assert error.value.code == "E_VIDEO_COVER"


def test_ffmpeg_invocation_is_argument_based_and_normalizes_audio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    card = tmp_path / "card-001.png"
    Image.new("RGB", (16, 16)).save(card)
    audio = tmp_path / "audio.wav"
    _write_wav(audio)
    output = tmp_path / "video.mp4"
    calls: list[list[str]] = []
    original_run_ffmpeg = video_renderer._run_ffmpeg

    def fake_ffmpeg(arguments: list[str], *, cwd: Path | None = None) -> Any:
        calls.append(arguments)
        output.write_bytes(b"video")
        analysis = """
        {"input_i":"-20.0","input_tp":"-4.0","input_lra":"2.0",
         "input_thresh":"-30.0","target_offset":"0.0"}
        """
        return SimpleNamespace(returncode=0, stderr=analysis, stdout="")

    monkeypatch.setattr(video_renderer, "_run_ffmpeg", fake_ffmpeg)
    monkeypatch.setattr(
        video_renderer,
        "verify_video",
        lambda *_args, **_kwargs: VideoInfo(16, 16, 1.2, True, True),
    )
    assemble_video(
        [card],
        [1.2],
        audio,
        output,
        expected_dimensions=(16, 16),
        duration_bounds=None,
    )
    assert any(any("loudnorm=I=-16:TP=-4:LRA=11" in item for item in call) for call in calls)

    subprocess_kwargs: dict[str, Any] = {}

    def fake_run(arguments: list[str], **kwargs: Any) -> Any:
        subprocess_kwargs.update(kwargs)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(video_renderer, "_run_ffmpeg", original_run_ffmpeg)
    monkeypatch.setattr(subprocess, "run", fake_run)
    video_renderer._run_ffmpeg(["ffmpeg", "-version"])
    assert subprocess_kwargs["shell"] is False


def test_polished_manifest_preserves_lineage_hashes_and_protects_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _timed_card_script()
    script_path = tmp_path / f"{script.script_id}.json"
    script_path.write_text(
        json.dumps(script.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )
    protected = tmp_path / "video-final"
    protected.mkdir()
    marker = protected / "marker.bin"
    marker.write_bytes(b"preserve")
    monkeypatch.setattr(video_renderer, "load_script", lambda _path: script)

    with pytest.raises(F0Error) as error:
        render_video(script_path, output_dir=protected)
    assert error.value.code == "E_VIDEO_OUTPUT"
    assert marker.read_bytes() == b"preserve"

    def fake_tts(text: str, audio: Path, subtitles: Path, requested_voice: str | None) -> str:
        assert text == script.spoken_text
        audio.write_bytes(b"audio")
        _write_scene_srt(subtitles, script)
        return "ru-RU-DmitryNeural"

    def fake_cover(_script: ProductionScript, path: Path, **_kwargs: Any) -> None:
        path.write_bytes(b"cover")

    def fake_card(_card: Any, path: Path, **_kwargs: Any) -> None:
        path.write_bytes(b"card")

    def fake_assemble(
        _cards: list[Path],
        _durations: list[float],
        _audio: Path,
        output: Path,
        **_kwargs: Any,
    ) -> VideoInfo:
        output.write_bytes(b"video")
        return VideoInfo(
            1080,
            1920,
            45.0,
            True,
            True,
            integrated_loudness=-16.0,
            true_peak=-1.5,
        )

    monkeypatch.setattr(video_renderer, "synthesize_tts", fake_tts)
    monkeypatch.setattr(video_renderer, "media_duration", lambda _path: 45.0)
    monkeypatch.setattr(video_renderer, "find_cyrillic_font", lambda: Path("font.ttf"))
    monkeypatch.setattr(video_renderer, "render_cover", fake_cover)
    monkeypatch.setattr(video_renderer, "render_timed_card", fake_card)
    monkeypatch.setattr(video_renderer, "assemble_video", fake_assemble)

    output_dir = tmp_path / "video-polished"
    rendered, info, voice = render_video(
        script_path,
        output_dir=output_dir,
        cover_title="Безопасный заголовок",
        cover_kicker="Заявление источника",
    )
    manifest = json.loads((rendered / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["template"] == "TEXT_CARD_V1_1"
    assert manifest["script_id"] == script.script_id
    assert manifest["package_id"] == script.package_id
    assert manifest["story_id"] == script.story_id
    assert manifest["manual_approval_required"] is True
    assert manifest["visual_card_count"] == info.visual_card_count == 10
    assert voice == "ru-RU-DmitryNeural"
    assert set(manifest["artifacts"]) == set(manifest["artifact_sha256"])
    for name, digest in manifest["artifact_sha256"].items():
        assert hashlib.sha256((rendered / name).read_bytes()).hexdigest() == digest
    assert marker.read_bytes() == b"preserve"
