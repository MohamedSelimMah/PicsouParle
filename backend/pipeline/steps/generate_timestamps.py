"""Step 3: Validate and normalize timestamps from TTS.

edge-tts provides word-level timestamps directly. This step validates them
and could fall back to estimation if they're missing (e.g., switching TTS provider).
"""

from __future__ import annotations

import logging

from backend.pipeline.context import PipelineContext
from backend.pipeline.models import TimestampedWord

logger = logging.getLogger(__name__)


def _estimate_timestamps(text: str, duration: float) -> list[TimestampedWord]:
    """Fallback: evenly distribute timestamps when TTS doesn't provide them."""
    words = text.split()
    if not words or duration <= 0:
        return []
    avg_duration = duration / len(words)
    return [
        TimestampedWord(word=w, start=i * avg_duration, end=(i + 1) * avg_duration)
        for i, w in enumerate(words)
    ]


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    if not ctx.timestamps and ctx.full_text and ctx.audio_duration > 0:
        logger.warning("No TTS timestamps — using estimation fallback")
        ctx.timestamps = _estimate_timestamps(ctx.full_text, ctx.audio_duration)

    if not ctx.timestamps:
        raise RuntimeError("No timestamps available")

    # Ensure duration is set
    if ctx.timestamps and not ctx.audio_duration:
        ctx.audio_duration = ctx.timestamps[-1].end

    logger.info(f"Timestamps: {len(ctx.timestamps)} words, {ctx.audio_duration:.1f}s")
    return ctx
