"""edge-tts provider — free French TTS with word-level timestamps."""

from __future__ import annotations

import json
from pathlib import Path

import edge_tts

from backend.config import settings


async def synthesize(
    text: str,
    output_path: Path,
    voice: str | None = None,
) -> tuple[Path, list[dict]]:
    """Generate audio + word-level timestamps.

    Returns (audio_path, [{"word": str, "start": float, "end": float}, ...])
    """
    voice = voice or settings.tts_voice
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")

    word_timestamps: list[dict] = []

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timestamps.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 1e7,  # 100ns units → seconds
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"TTS produced no audio at {output_path}")

    return output_path, word_timestamps
