from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

import edge_tts

from ai_newsroom.models import F0Error

PREFERRED_VOICES: Final = ("ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural")
RATE: Final = "+5%"
VOLUME: Final = "+0%"
PITCH: Final = "+0Hz"


def choose_russian_voice(
    voices: Sequence[Mapping[str, Any]], requested: str | None
) -> str:
    russian = sorted(
        (
            voice
            for voice in voices
            if voice.get("Locale") == "ru-RU"
            and isinstance(voice.get("ShortName"), str)
            and str(voice["ShortName"]).endswith("Neural")
        ),
        key=lambda voice: str(voice["ShortName"]),
    )
    names = {str(voice["ShortName"]) for voice in russian}
    if requested is not None:
        if requested not in names:
            raise F0Error("E_TTS_VOICE", "requested voice is not a current Russian neural voice")
        return requested
    for preferred in PREFERRED_VOICES:
        if preferred in names:
            return preferred
    if russian:
        return str(russian[0]["ShortName"])
    raise F0Error("E_TTS_VOICE", "no current ru-RU neural voice is available")


async def _synthesize(
    spoken_text: str,
    audio_path: Path,
    subtitle_path: Path,
    requested_voice: str | None,
) -> str:
    try:
        manager = await edge_tts.VoicesManager.create()
        voice = choose_russian_voice(manager.voices, requested_voice)
    except F0Error:
        raise
    except Exception:
        raise F0Error("E_TTS_VOICE", "current Edge voice list could not be queried") from None

    submaker = edge_tts.SubMaker()
    audio_bytes = 0
    try:
        communication = edge_tts.Communicate(
            spoken_text,
            voice,
            rate=RATE,
            volume=VOLUME,
            pitch=PITCH,
            boundary="SentenceBoundary",
        )
        with audio_path.open("xb") as audio:
            async for chunk in communication.stream():
                if chunk["type"] == "audio":
                    data = chunk["data"]
                    audio.write(data)
                    audio_bytes += len(data)
                elif chunk["type"] in {"WordBoundary", "SentenceBoundary"}:
                    submaker.feed(chunk)
        subtitles = submaker.get_srt()
        if audio_bytes == 0 or not subtitles.strip():
            raise F0Error("E_TTS_SYNTHESIS", "Edge TTS returned incomplete audio or timing")
        subtitle_path.write_text(subtitles, encoding="utf-8", newline="\n")
    except F0Error:
        raise
    except Exception:
        raise F0Error("E_TTS_SYNTHESIS", "Edge TTS synthesis failed") from None
    return voice


def synthesize_tts(
    spoken_text: str,
    audio_path: Path,
    subtitle_path: Path,
    requested_voice: str | None = None,
) -> str:
    return asyncio.run(_synthesize(spoken_text, audio_path, subtitle_path, requested_voice))
