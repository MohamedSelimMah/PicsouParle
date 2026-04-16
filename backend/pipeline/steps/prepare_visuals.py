"""Step 4: Prepare visual assets + analyze audio amplitude for animation."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from backend.pipeline.context import PipelineContext
from backend.presets import BACKGROUND_PRESETS, DEFAULT_BACKGROUND_MODE
from backend.utils.audio import extract_amplitudes, compute_adaptive_threshold

logger = logging.getLogger(__name__)

WIDTH, HEIGHT = 1080, 1920

MOOD_GRADIENTS: dict[str, tuple[str, str]] = {
    "cynique": ("#0F1923", "#1A2A3A"),
    "sarcastique": ("#0F1923", "#1A2A3A"),
    "furieux": ("#1F0F0F", "#2A1A1A"),
    "nostalgique": ("#0F1520", "#1A2540"),
    "fier": ("#0F1F0F", "#1A2A1A"),
    "default": ("#0C1017", "#141C26"),
}


def _create_background(top_color: str, bottom_color: str, output: Path) -> Path:
    """Vertical gradient background with subtle vignette."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = Image.new("RGB", (1, 1), top_color).getpixel((0, 0))
    r2, g2, b2 = Image.new("RGB", (1, 1), bottom_color).getpixel((0, 0))

    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Gold accent line at top
    for y in range(3):
        draw.line([(0, y), (WIDTH, y)], fill="#D4A017")

    # Vignette
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    for i in range(40):
        opacity = int(255 * (1 - i / 40))
        vdraw.rectangle([i * 8, i * 14, WIDTH - i * 8, HEIGHT - i * 14], fill=opacity)
    vignette = vignette.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(img, Image.new("RGB", (WIDTH, HEIGHT), "#000000"), vignette)

    img.save(output, quality=95)
    return output


def _load_character_assets(assets_dir: Path, visuals_dir: Path) -> tuple[Path | None, Path | None]:
    """Load character mouth-open and mouth-closed PNGs."""
    char_dir = assets_dir / "character"
    closed_src = char_dir / "picsou_mouth_closed.png"
    open_src = char_dir / "picsou_mouth_open.png"

    closed_dst = visuals_dir / "character_closed.png"
    open_dst = visuals_dir / "character_open.png"

    if closed_src.exists():
        shutil.copy2(closed_src, closed_dst)
    else:
        logger.warning(f"Missing: {closed_src}")
        return None, None

    if open_src.exists():
        shutil.copy2(open_src, open_dst)
    else:
        shutil.copy2(closed_src, open_dst)
        logger.warning(f"Missing: {open_src} — using closed for both states")

    return closed_dst, open_dst


def _get_cached_background(mood: str, assets_dir: Path) -> Path | None:
    """Return cached background path if it exists for this mood."""
    cache_path = assets_dir / "cache" / f"background_{mood}.png"
    if cache_path.exists():
        logger.info(f"Background cache hit (mood={mood})")
        return cache_path
    return None


def _save_background_cache(src: Path, mood: str, assets_dir: Path) -> None:
    """Save a generated background to the cache."""
    cache_dir = assets_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(src, cache_dir / f"background_{mood}.png")
    logger.info(f"Background cached (mood={mood})")


async def run(ctx: PipelineContext, settings) -> PipelineContext:
    visuals_dir = settings.tmp_dir / ctx.run_id / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create (or restore from cache) background
    preset = BACKGROUND_PRESETS.get(ctx.background_mode, BACKGROUND_PRESETS[DEFAULT_BACKGROUND_MODE])
    cache_key = ctx.background_mode
    bg_dest = visuals_dir / "background.png"
    cached = _get_cached_background(cache_key, settings.assets_dir)
    if cached:
        import shutil
        shutil.copy2(cached, bg_dest)
    else:
        generated = False
        # Always attempt AI generation for presets (FLUX.1 is free)
        if settings.openrouter_api_key:
            from backend.providers.image import generate_background
            generated = await generate_background(preset.ai_prompt, bg_dest)

        if not generated:
            _create_background(preset.gradient_top, preset.gradient_bottom, bg_dest)

        _save_background_cache(bg_dest, cache_key, settings.assets_dir)
    logger.info(f"Background ready (mode={ctx.background_mode})")

    # 2. Load character assets (mouth open/closed)
    closed, opened = _load_character_assets(settings.assets_dir, visuals_dir)
    if closed:
        logger.info("Character assets: 2 states (mouth open/closed)")
    else:
        logger.warning("No character assets — subtitles only")

    # 3. Analyze audio amplitude for mouth animation
    if ctx.audio_path and ctx.audio_path.exists():
        ctx.amplitudes = extract_amplitudes(ctx.audio_path, fps=settings.video_fps)
        ctx.amplitude_threshold = compute_adaptive_threshold(ctx.amplitudes)
        logger.info(f"Audio amplitude: {len(ctx.amplitudes)} frames, threshold={ctx.amplitude_threshold:.3f}")

    ctx.visuals_dir = visuals_dir

    ctx.visuals_dir = visuals_dir
    logger.info(f"Visuals prepared in {visuals_dir}")
    return ctx
