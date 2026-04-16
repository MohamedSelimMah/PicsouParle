"""OpenRouter image generation — used for AI-generated backgrounds."""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

_STYLE_SUFFIX = (
    "digital art, rich golden tones, cinematic lighting, no text, no characters, "
    "widescreen composition suitable as video background, highly detailed"
)

# Portrait crop: we request a square and will stretch/fill in Pillow
_WIDTH = 1024
_HEIGHT = 1024


async def generate_background(description: str, output_path: Path) -> bool:
    """Generate a background image via OpenRouter image API.

    Returns True on success, False on any failure (caller falls back to gradient).
    """
    if not settings.openrouter_api_key:
        logger.warning("No OPENROUTER_API_KEY — skipping AI background")
        return False

    prompt = f"{description}, {_STYLE_SUFFIX}"

    try:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.image_model,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{_WIDTH}x{_HEIGHT}",
                    "response_format": "b64_json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        b64 = data["data"][0].get("b64_json")
        if not b64:
            # Some models return a URL instead
            url = data["data"][0].get("url")
            if url:
                async with httpx.AsyncClient(timeout=30) as client:
                    img_resp = await client.get(url)
                    img_resp.raise_for_status()
                    raw = img_resp.content
            else:
                logger.warning("Image API returned no image data")
                return False
        else:
            raw = base64.b64decode(b64)

        # Resize to 1080×1920 portrait and save
        from PIL import Image

        img = Image.open(BytesIO(raw)).convert("RGB")
        # Fill portrait: scale so width = 1080, crop height center
        target_w, target_h = 1080, 1920
        ratio = target_w / img.width
        new_h = int(img.height * ratio)
        img = img.resize((target_w, new_h), Image.LANCZOS)
        if new_h >= target_h:
            top = (new_h - target_h) // 2
            img = img.crop((0, top, target_w, top + target_h))
        else:
            # Pad with black
            canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
            canvas.paste(img, (0, (target_h - new_h) // 2))
            img = canvas

        # Darken slightly so text/character stay readable
        from PIL import ImageEnhance
        img = ImageEnhance.Brightness(img).enhance(0.72)

        img.save(output_path, quality=92)
        logger.info(f"AI background saved → {output_path}")
        return True

    except Exception as e:
        logger.warning(f"AI background generation failed: {e} — falling back to gradient")
        return False
