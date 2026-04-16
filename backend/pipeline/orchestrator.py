from __future__ import annotations

import logging
import time
from typing import Callable, Awaitable
from uuid import uuid4

from backend.config import settings
from backend.pipeline.context import PipelineContext
from backend.pipeline.steps import (
    generate_script,
    generate_voice,
    generate_timestamps,
    prepare_visuals,
    build_subtitles,
    compose_video,
)

logger = logging.getLogger(__name__)

Step = Callable[[PipelineContext, type(settings)], Awaitable[PipelineContext]]

STEPS: list[tuple[str, Step]] = [
    ("generate_script", generate_script.run),
    ("generate_voice", generate_voice.run),
    ("generate_timestamps", generate_timestamps.run),
    ("prepare_visuals", prepare_visuals.run),
    ("build_subtitles", build_subtitles.run),
    ("compose_video", compose_video.run),
]

STEP_NAMES = [name for name, _ in STEPS]

# In-memory run tracking
_runs: dict[str, PipelineContext] = {}


def get_run(run_id: str) -> PipelineContext | None:
    return _runs.get(run_id)


def start_run(prompt: str) -> str:
    """Create a run entry and return its ID."""
    run_id = uuid4().hex[:12]
    settings.ensure_dirs()
    ctx = PipelineContext(run_id=run_id, prompt=prompt)
    _runs[run_id] = ctx
    return run_id


async def run_pipeline(
    run_id: str,
    on_progress: Callable[[str, str], None] | None = None,
    from_step: str | None = None,
) -> PipelineContext:
    ctx = _runs.get(run_id)
    if not ctx:
        raise RuntimeError(f"Run {run_id} not found")

    ctx.status = "running"

    # Determine starting step
    start_idx = 0
    if from_step:
        if from_step not in STEP_NAMES:
            raise ValueError(f"Unknown step: {from_step}. Valid: {STEP_NAMES}")
        start_idx = STEP_NAMES.index(from_step)
        logger.info(f"[{run_id}] Resuming from step: {from_step}")

    total = len(STEPS)
    for i, (step_name, step_fn) in enumerate(STEPS):
        if i < start_idx:
            continue

        ctx.current_step = step_name
        if on_progress:
            on_progress(run_id, step_name)

        logger.info(f"[{run_id}] [{i+1}/{total}] Starting: {step_name}")
        t0 = time.perf_counter()

        try:
            ctx = await step_fn(ctx, settings)
        except Exception as e:
            ctx.status = "failed"
            ctx.error = f"{step_name}: {e}"
            logger.error(f"[{run_id}] Failed at {step_name}: {e}", exc_info=True)
            return ctx

        elapsed = time.perf_counter() - t0
        logger.info(f"[{run_id}] [{i+1}/{total}] Finished: {step_name} ({elapsed:.1f}s)")

    ctx.status = "completed"
    ctx.current_step = "done"
    if on_progress:
        on_progress(run_id, "done")

    logger.info(f"[{run_id}] Pipeline completed")
    return ctx
