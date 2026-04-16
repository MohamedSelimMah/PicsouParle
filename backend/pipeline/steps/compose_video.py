"""Step 6: Frame-by-frame video composition with Pillow + FFmpeg.

Renders each frame individually for full control over:
- Mouth animation (open/closed based on audio amplitude)
- Word-highlighted subtitles
- Ken Burns zoom effect on background
- Character entry/exit transitions
- Optional background music mixing
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from PIL import Image

from backend.pipeline.context import PipelineContext
from backend.utils.rendering import (
    apply_ken_burns,
    get_transition_alpha,
    render_subtitle_overlay,
    WIDTH,
    HEIGHT,
    FPS,
)
from backend.utils.fonts import load_font

logger = logging.getLogger(__name__)

# Character positioning
CHAR_TARGET_H = int(HEIGHT * 0.42)  # ~42% of canvas height
CHAR_Y_OFFSET = 350  # pixels from top
SUB_Y = 1480  # subtitle overlay Y position


def _load_image(path: Path) -> Image.Image | None:
    if path.exists():
        return Image.open(path).convert("RGBA")
    return None


def _scale_character(img: Image.Image, target_h: int) -> Image.Image:
    ratio = target_h / img.height
    new_w = int(img.width * ratio)
    return img.resize((new_w, target_h), Image.LANCZOS)


def _apply_alpha(img: Image.Image, alpha: float) -> Image.Image:
    """Apply global opacity to RGBA image."""
    if alpha >= 1.0:
        return img
    r, g, b, a = img.split()
    a = a.point(lambda x: int(x * alpha))
    return Image.merge("RGBA", (r, g, b, a))


def _find_music(assets_dir: Path) -> Path | None:
    """Look for background music in assets/music/."""
    music_dir = assets_dir / "music"
    if not music_dir.exists():
        return None
    for ext in ["mp3", "wav", "ogg", "m4a"]:
        candidates = list(music_dir.glob(f"*.{ext}"))
        if candidates:
            return candidates[0]
    return None


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    if not ctx.visuals_dir or not ctx.audio_path:
        raise RuntimeError("Missing visuals or audio for composition")

    output_path = settings.output_dir / f"{ctx.run_id}.mp4"
    fps = settings.video_fps
    duration = ctx.audio_duration or 30.0
    total_frames = int(duration * fps) + 1

    # Load assets
    bg = Image.open(ctx.visuals_dir / "background.png").convert("RGB")
    char_closed = _load_image(ctx.visuals_dir / "character_closed.png")
    char_open = _load_image(ctx.visuals_dir / "character_open.png")
    has_char = char_closed is not None

    if has_char:
        char_closed = _scale_character(char_closed, CHAR_TARGET_H)
        char_open = _scale_character(char_open, CHAR_TARGET_H) if char_open else char_closed

    font = load_font(52)
    music_path = _find_music(settings.assets_dir)

    logger.info(f"Rendering {total_frames} frames at {fps}fps ({duration:.1f}s)")
    if music_path:
        logger.info(f"Background music: {music_path.name}")

    # Build FFmpeg command — pipe raw RGB frames in, get MP4 out
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        # Video input: raw frames from stdin
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(fps),
        "-i", "pipe:0",
        # Audio input
        "-i", str(ctx.audio_path),
    ]

    # Optional background music
    if music_path:
        ffmpeg_cmd += ["-i", str(music_path)]
        ffmpeg_cmd += [
            "-filter_complex",
            f"[1:a]volume=1[voice];[2:a]volume={settings.music_volume}[music];"
            f"[voice][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
        ]
    else:
        ffmpeg_cmd += ["-map", "0:v", "-map", "1:a"]

    ffmpeg_cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-t", str(duration + 0.3),
        "-shortest",
        str(output_path),
    ]

    process = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Render frames
    amplitudes = ctx.amplitudes
    threshold = ctx.amplitude_threshold

    broken = False
    try:
        for frame_idx in range(total_frames):
            t = frame_idx / fps

            # 1. Background with Ken Burns zoom
            frame = apply_ken_burns(bg, t, duration)

            # 2. Character overlay with mouth animation
            if has_char:
                # Pick mouth state based on amplitude
                mouth_open = False
                if frame_idx < len(amplitudes):
                    mouth_open = amplitudes[frame_idx] > threshold

                char_img = char_open if mouth_open else char_closed

                # Apply entry/exit fade
                alpha = get_transition_alpha(t, duration, fade_in=0.6, fade_out=0.4)
                if alpha < 1.0:
                    char_img = _apply_alpha(char_img, alpha)

                # Center character horizontally
                char_x = (WIDTH - char_img.width) // 2
                frame.paste(char_img, (char_x, CHAR_Y_OFFSET), char_img)

            # 3. Subtitle overlay with word highlight
            sub_overlay = render_subtitle_overlay(t, ctx.subtitle_groups, font)
            if sub_overlay:
                frame.paste(sub_overlay, (0, SUB_Y), sub_overlay)

            # Write frame to FFmpeg
            try:
                process.stdin.write(frame.convert("RGB").tobytes())
            except BrokenPipeError:
                broken = True
                break

            if frame_idx % 100 == 0:
                logger.debug(f"Frame {frame_idx}/{total_frames}")

    finally:
        if process.stdin and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass

    # Wait for FFmpeg to finish (don't use communicate — stdin is already closed)
    stderr_data = process.stderr.read() if process.stderr else b""
    try:
        process.wait(timeout=120)
    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError("FFmpeg timed out")

    if process.returncode != 0 or broken:
        raise RuntimeError(f"FFmpeg failed (rc={process.returncode}):\n{stderr_data.decode()[-1000:]}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg produced no output")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Video composed: {output_path} ({size_mb:.1f} MB)")

    # Cleanup temp files if not keeping
    if not settings.keep_temp:
        import shutil
        tmp_run_dir = settings.tmp_dir / ctx.run_id
        if tmp_run_dir.exists():
            shutil.rmtree(tmp_run_dir)
            logger.info(f"Cleaned temp files: {tmp_run_dir}")

    ctx.video_path = output_path
    return ctx
