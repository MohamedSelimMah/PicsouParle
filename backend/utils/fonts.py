"""Font discovery and loading for subtitle rendering."""

from __future__ import annotations

import logging
from pathlib import Path
from functools import lru_cache

from PIL import ImageFont

logger = logging.getLogger(__name__)

# Font search paths (system + project)
_FONT_CANDIDATES = [
    "assets/fonts/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


@lru_cache(maxsize=8)
def load_font(size: int = 68) -> ImageFont.FreeTypeFont:
    """Load the best available bold font for subtitles."""
    for candidate in _FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            logger.info(f"Using font: {path}")
            return ImageFont.truetype(str(path), size)

    logger.warning("No bold font found, using Pillow default")
    return ImageFont.load_default(size=size)
