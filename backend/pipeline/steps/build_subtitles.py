"""Step 5: Build subtitle groups from word-level timestamps."""

from __future__ import annotations

import logging

from backend.pipeline.context import PipelineContext
from backend.pipeline.models import SubtitleGroup, TimestampedWord

logger = logging.getLogger(__name__)

# Subtitle grouping config
MAX_WORDS_PER_GROUP = 5
MAX_DURATION_PER_GROUP = 2.5  # seconds


def _group_words(words: list[TimestampedWord]) -> list[SubtitleGroup]:
    """Split word-level timestamps into readable subtitle groups."""
    groups: list[SubtitleGroup] = []
    current: list[TimestampedWord] = []

    for word in words:
        current.append(word)

        duration = current[-1].end - current[0].start
        if len(current) >= MAX_WORDS_PER_GROUP or duration >= MAX_DURATION_PER_GROUP:
            groups.append(SubtitleGroup(
                text=" ".join(w.word for w in current),
                words=list(current),
                start=current[0].start,
                end=current[-1].end,
            ))
            current = []

    # Flush remaining words
    if current:
        groups.append(SubtitleGroup(
            text=" ".join(w.word for w in current),
            words=list(current),
            start=current[0].start,
            end=current[-1].end,
        ))

    return groups


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    if not ctx.timestamps:
        raise RuntimeError("No timestamps to build subtitles from")

    ctx.subtitle_groups = _group_words(ctx.timestamps)
    logger.info(f"Built {len(ctx.subtitle_groups)} subtitle groups from {len(ctx.timestamps)} words")
    return ctx
