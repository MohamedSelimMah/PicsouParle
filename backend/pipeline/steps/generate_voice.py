"""Step 2: Generate voice audio via edge-tts."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.pipeline.context import PipelineContext
from backend.pipeline.models import TimestampedWord
from backend.providers import tts

logger = logging.getLogger(__name__)


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    if not ctx.full_text:
        raise RuntimeError("No script text to synthesize")

    output_path = settings.tmp_dir / f"{ctx.run_id}_voice.mp3"

    audio_path, word_timestamps = await tts.synthesize(
        text=ctx.full_text,
        output_path=output_path,
    )

    ctx.audio_path = audio_path

    # Convert raw timestamps to typed models immediately
    ctx.timestamps = [
        TimestampedWord(word=w["word"], start=w["start"], end=w["end"])
        for w in word_timestamps
    ]
    if ctx.timestamps:
        ctx.audio_duration = ctx.timestamps[-1].end

    logger.info(f"Voice: {audio_path} ({len(ctx.timestamps)} words, {ctx.audio_duration:.1f}s)")

    # Save timestamps JSON for debugging/resume
    ts_path = settings.tmp_dir / f"{ctx.run_id}_timestamps.json"
    ts_path.write_text(json.dumps(word_timestamps, ensure_ascii=False, indent=2))

    return ctx
