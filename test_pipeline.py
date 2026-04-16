"""Quick end-to-end pipeline test."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config import settings
from backend.pipeline.orchestrator import start_run, run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


def on_progress(run_id: str, step: str):
    print(f"  → [{run_id}] {step}")


async def main():
    prompt = "Pourquoi il ne faut jamais prêter d'argent à ses amis"

    print(f"\n🎬 Starting pipeline with prompt: {prompt}\n")

    run_id = start_run(prompt)
    ctx = await run_pipeline(run_id, on_progress=on_progress)

    print(f"\n{'='*50}")
    print(f"Status: {ctx.status}")

    if ctx.error:
        print(f"Error: {ctx.error}")
        return

    if ctx.script:
        print(f"Title: {ctx.script.title}")
        print(f"Lines: {len(ctx.script.lines)}")
        print(f"Mood: {ctx.script.mood}")
        for i, line in enumerate(ctx.script.lines, 1):
            print(f"  {i}. [{line.emotion}] {line.text}")

    print(f"Audio: {ctx.audio_path}")
    print(f"Duration: {ctx.audio_duration:.1f}s")
    print(f"Timestamps: {len(ctx.timestamps)} words")
    print(f"Subtitle groups: {len(ctx.subtitle_groups)}")
    print(f"Video: {ctx.video_path}")

    if ctx.video_path and Path(ctx.video_path).exists():
        size_mb = Path(ctx.video_path).stat().st_size / (1024 * 1024)
        print(f"Video size: {size_mb:.1f} MB")
        print(f"\n✅ Pipeline completed successfully!")
    else:
        print(f"\n❌ No video file produced")


if __name__ == "__main__":
    asyncio.run(main())
