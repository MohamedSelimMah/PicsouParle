"""CLI entry point — generate a video from a prompt.

Usage:
    python -m backend.cli --prompt "Pourquoi il ne faut jamais prêter d'argent"
    python -m backend.cli --prompt "..." --from-step compose_video --keep-temp
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time

from backend.config import settings
from backend.pipeline.orchestrator import start_run, run_pipeline, STEP_NAMES
from backend.presets import VALID_BACKGROUND_MODES, DEFAULT_BACKGROUND_MODE

STEP_LABELS = {
    "generate_script": "Generating script",
    "generate_voice": "Generating voice",
    "generate_timestamps": "Building timestamps",
    "prepare_visuals": "Preparing visuals",
    "build_subtitles": "Building subtitles",
    "compose_video": "Composing video",
    "done": "Done",
}


def on_progress(run_id: str, step: str):
    label = STEP_LABELS.get(step, step)
    idx = STEP_NAMES.index(step) + 1 if step in STEP_NAMES else len(STEP_NAMES)
    total = len(STEP_NAMES)
    if step == "done":
        return
    print(f"  [{idx}/{total}] {label}...", flush=True)


async def main():
    parser = argparse.ArgumentParser(description="Picsou Parle — prompt-to-video generator")
    parser.add_argument("--prompt", "-p", required=True, help="Video topic (in French)")
    parser.add_argument("--from-step", choices=STEP_NAMES, help="Resume from a specific step")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate files")
    parser.add_argument("--voice", help=f"TTS voice (default: {settings.tts_voice})")
    parser.add_argument("--model", help=f"LLM model (default: {settings.llm_model})")
    parser.add_argument("--ai-background", action="store_true", help="Generate background with AI (requires OPENROUTER_API_KEY)")
    parser.add_argument("--background", choices=VALID_BACKGROUND_MODES, default=DEFAULT_BACKGROUND_MODE, help=f"Background mode (default: {DEFAULT_BACKGROUND_MODE})")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.keep_temp:
        settings.keep_temp = True
    if args.voice:
        settings.tts_voice = args.voice
    if args.model:
        settings.llm_model = args.model
    if args.ai_background:
        settings.ai_background = True

    print(f"\n🎬 Picsou Parle — Video Generator")
    print(f"   Prompt: {args.prompt}")
    print(f"   Model: {settings.llm_model}")
    print(f"   Voice: {settings.tts_voice}")
    print(f"   Background: {args.background}\n")

    t0 = time.perf_counter()
    run_id = start_run(args.prompt, background_mode=args.background)
    ctx = await run_pipeline(run_id, on_progress=on_progress, from_step=args.from_step)

    elapsed = time.perf_counter() - t0
    print()

    if ctx.status == "failed":
        print(f"❌ Failed: {ctx.error}")
        sys.exit(1)

    print(f"✅ Video generated in {elapsed:.1f}s")
    if ctx.script:
        print(f"   Title: {ctx.script.title}")
        print(f"   Lines: {len(ctx.script.lines)} ({sum(len(l.text.split()) for l in ctx.script.lines)} words)")
    print(f"   Duration: {ctx.audio_duration:.1f}s")
    print(f"   Output: {ctx.video_path}")


if __name__ == "__main__":
    asyncio.run(main())
