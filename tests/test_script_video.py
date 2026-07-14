from __future__ import annotations

import asyncio
import hashlib
import json
import math
import struct
import wave
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import edge_tts
import pytest
from PIL import Image
from typer.testing import CliRunner

from ai_newsroom.cli import app
from ai_newsroom.database import harvest_snapshots, init_database, load_story_source
from ai_newsroom.models import EVIDENCE_LIMITATION, BuildGenerator, F0Error, RealStoryPackagePayload
from ai_newsroom.normalization import canonical_json, story_id
from ai_newsroom.package_builder import build_package, load_validated_package
from ai_newsroom.rss import parse_live_feed_bytes
from ai_newsroom.script_builder import (
    PROMPT_SHA256,
    PROMPT_VERSION,
    build_script,
    expected_script_identity,
    load_script,
)
from ai_newsroom.script_models import ProductionScript, ProviderScriptDraft, ScriptScene
from ai_newsroom.tts import choose_russian_voice, synthesize_tts
from ai_newsroom.video_renderer import assemble_video, find_cyrillic_font, render_scene_card

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


def package_draft(data_dir: Path, selected_story: str, verdict: str) -> dict[str, Any]:
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
                "use_in_script": True,
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
        ],
        "limitations": [EVIDENCE_LIMITATION],
        "demonstration_plan": ["Проверить функцию отдельно."],
        "publication_verdict": verdict,
        "source_references": [{"source_id": source.id, "canonical_url": URL}],
    }


def prepare_real_package(
    data_dir: Path, verdict: str = "READY_WITH_QUALIFICATION"
) -> tuple[str, str, RealStoryPackagePayload]:
    selected_story = prepare_story(data_dir)
    package_client = FakeClient(
        [completion(package_draft(data_dir, selected_story, verdict))]
    )
    package_id, _created = build_package(
        data_dir,
        selected_story,
        NOW,
        BuildGenerator.DEEPSEEK,
        api_key=SECRET,
        client=package_client,
    )
    _snapshot, package = load_validated_package(
        data_dir, selected_story, package_id=package_id
    )
    assert isinstance(package, RealStoryPackagePayload)
    return selected_story, package_id, package


def valid_script_draft(_package: RealStoryPackagePayload) -> dict[str, Any]:
    seed = [
        "По",
        "данным",
        "официальной",
        "ленты",
        "поставщика.",
        "Новая",
        "функция",
        "относится",
        "к",
        "рабочим",
        "процессам",
        "специалистов",
        "и",
        "требует",
        "внимательной",
        "ручной",
        "оценки",
        "перед",
        "любым",
        "практическим",
        "решением",
        "в",
        "команде",
        "сейчас",
    ]
    tokens = (seed * 5)[:120]
    narrations = [" ".join(tokens[index : index + 24]) for index in range(0, 120, 24)]
    narrations = [f"{value}." if not value.endswith(".") else value for value in narrations]
    scenes = [
        {
            "narration": narration,
            "on_screen_text": f"Ключевой тезис {index + 1}",
            "claim_ids": ["claim_allowed"],
        }
        for index, narration in enumerate(narrations)
    ]
    return {
        "working_title": "Новый AI-инструмент: что известно",
        "hook": narrations[0],
        "scenes": scenes,
        "caption": "Пилотный сценарий требует ручной проверки перед публикацией.",
    }


def test_script_rejects_mock_package(tmp_path: Path) -> None:
    selected_story = prepare_story(tmp_path)
    package_id, _created = build_package(tmp_path, selected_story, NOW)
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
            api_key=SECRET,
            client=FakeClient([]),
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
            api_key=SECRET,
            client=FakeClient([]),
        )
    assert error.value.code == "E_SCRIPT_VERDICT"


def test_valid_script_filters_unverified_and_reuses_stable_pair(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    client = FakeClient([completion(valid_script_draft(package))])
    script, created, json_path, markdown_path, repair_used = build_script(
        tmp_path,
        selected_story,
        package_id,
        api_key=SECRET,
        client=client,
    )
    assert created is True
    assert repair_used is False
    assert isinstance(script, ProductionScript)
    assert script.word_count == 120
    assert script.spoken_text == " ".join(scene.narration for scene in script.scenes)
    assert [scene.order for scene in script.scenes] == [1, 2, 3, 4, 5]
    assert {scene.visual_kind for scene in script.scenes} == {"TEXT_CARD"}
    assert {scene.source_label for scene in script.scenes} == {"Источник: openai.com"}
    assert script.prompt_version == "short-video-script-v2"
    assert set(valid_script_draft(package)) == {"working_title", "hook", "scenes", "caption"}
    request = json.loads(client.completions.calls[0]["messages"][1]["content"])
    assert [claim["claim_id"] for claim in request["allowed_claims"]] == ["claim_allowed"]
    assert "claim_unverified" not in client.completions.calls[0]["messages"][1]["content"]
    assert set(request) == {"publication_verdict", "allowed_claims", "limitations"}
    original = (json_path.read_bytes(), markdown_path.read_bytes())

    unused = FakeClient([])
    repeated = build_script(
        tmp_path,
        selected_story,
        package_id,
        api_key=None,
        client=unused,
    )
    assert repeated[1] is False
    assert unused.completions.calls == []
    assert (json_path.read_bytes(), markdown_path.read_bytes()) == original


def test_invalid_script_output_persists_nothing(tmp_path: Path) -> None:
    selected_story, package_id, _package = prepare_real_package(tmp_path)
    client = FakeClient([completion({}), completion({})])
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
            api_key=SECRET,
            client=client,
        )
    assert error.value.code == "E_SCRIPT_OUTPUT"
    assert len(client.completions.calls) == 2
    assert not (tmp_path / "scripts").exists()


@pytest.mark.parametrize("claim_id", ["claim_missing", "claim_unverified"])
def test_invalid_or_unverified_claim_reference_is_rejected(
    tmp_path: Path, claim_id: str
) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    draft = valid_script_draft(package)
    draft["scenes"][0]["claim_ids"] = [claim_id]
    client = FakeClient([completion(draft), completion(draft)])
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
            api_key=SECRET,
            client=client,
        )
    assert error.value.code == "E_SCRIPT_OUTPUT"
    assert len(client.completions.calls) == 2
    assert not (tmp_path / "scripts").exists()


def test_required_qualification_is_enforced(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    draft = valid_script_draft(package)
    for scene in draft["scenes"]:
        scene["narration"] = scene["narration"].replace(
            "По данным официальной ленты поставщика.", "Согласно сообщению поставщика"
        )
    draft["hook"] = draft["scenes"][0]["narration"]
    client = FakeClient([completion(draft), completion(draft)])
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
            api_key=SECRET,
            client=client,
        )
    assert error.value.code == "E_SCRIPT_OUTPUT"
    assert len(client.completions.calls) == 2


def test_v2_identity_differs_from_v1(tmp_path: Path) -> None:
    _story, _package_id, package = prepare_real_package(tmp_path)
    v2_fingerprint, v2_script_id = expected_script_identity(package)
    package_digest = hashlib.sha256(
        canonical_json(package.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()
    v1_identity = {
        "package_json_sha256": package_digest,
        "package_id": package.package_id,
        "generator": {
            "provider": "deepseek",
            "model": "deepseek-v4-flash",
            "api_format": "openai-chat-completions",
            "thinking": "disabled",
            "temperature": 0.2,
        },
        "prompt_version": "short-video-script-v1",
        "prompt_sha256": "8d31bff7ad6cd9b70c027518dc2c90ef1506ce3c970c5018a8508053ed488d83",
        "script_schema_version": 1,
    }
    v1_fingerprint = hashlib.sha256(canonical_json(v1_identity).encode("utf-8")).hexdigest()
    v1_script_id = "script_" + hashlib.sha256(
        f"f3-script:{v1_fingerprint}".encode()
    ).hexdigest()[:24]
    assert PROMPT_VERSION == "short-video-script-v2"
    assert len(PROMPT_SHA256) == 64
    assert v2_fingerprint != v1_fingerprint
    assert v2_script_id != v1_script_id


def test_one_repair_can_produce_valid_v2_script(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    client = FakeClient([completion({}), completion(valid_script_draft(package))])
    script, created, _json, _markdown, repair_used = build_script(
        tmp_path,
        selected_story,
        package_id,
        api_key=SECRET,
        client=client,
    )
    assert created is True
    assert repair_used is True
    assert script.word_count == 120
    assert len(client.completions.calls) == 2
    repair = json.loads(client.completions.calls[1]["messages"][1]["content"])["repair"]
    assert "validation_errors" in repair
    assert "на замену" in repair["instruction"]


def test_partial_script_pair_is_a_conflict(tmp_path: Path) -> None:
    selected_story, package_id, package = prepare_real_package(tmp_path)
    script, _created, json_path, markdown_path, _repair_used = build_script(
        tmp_path,
        selected_story,
        package_id,
        api_key=SECRET,
        client=FakeClient([completion(valid_script_draft(package))]),
    )
    assert script.script_id in json_path.name
    markdown_path.unlink()
    with pytest.raises(F0Error) as error:
        build_script(
            tmp_path,
            selected_story,
            package_id,
            api_key=None,
            client=FakeClient([]),
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
                "text": "Только narration.",
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
    voice = synthesize_tts("Только narration.", audio, subtitles)
    assert voice == "ru-RU-DmitryNeural"
    assert calls[0][0] == "Только narration."
    assert calls[0][1] == voice
    assert calls[0][2] == {
        "rate": "+5%",
        "volume": "+0%",
        "pitch": "+0Hz",
        "boundary": "SentenceBoundary",
    }
    assert audio.read_bytes() == b"fake-mp3"
    assert "Только narration." in subtitles.read_text(encoding="utf-8-sig")


def test_provider_script_draft_cannot_control_deterministic_metadata() -> None:
    value = {
        "working_title": "Заголовок",
        "hook": "Короткий hook.",
        "scenes": [
            {
                "narration": "Короткий hook.",
                "on_screen_text": "Hook",
                "claim_ids": ["claim_allowed"],
            }
        ]
        * 5,
        "caption": "Подпись",
        "word_count": 110,
    }
    with pytest.raises(ValueError):
        ProviderScriptDraft.model_validate(value)
