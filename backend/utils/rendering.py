"""Frame rendering helpers — Ken Burns, subtitle overlay, transitions."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from backend.pipeline.models import SubtitleGroup

WIDTH, HEIGHT = 1080, 1920
FPS = 30


def apply_ken_burns(
    bg: Image.Image, t: float, duration: float, zoom_factor: float = 1.06,
) -> Image.Image:
    """Slow zoom-in (Ken Burns) on background image."""
    progress = t / max(duration, 0.1)
    scale = 1.0 + (zoom_factor - 1.0) * progress

    new_w = int(WIDTH * scale)
    new_h = int(HEIGHT * scale)
    resized = bg.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - WIDTH) // 2
    top = (new_h - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def get_transition_alpha(
    t: float, duration: float, fade_in: float = 0.5, fade_out: float = 0.5,
) -> float:
    """Character entry/exit fade opacity (0.0–1.0)."""
    if t < fade_in:
        return t / fade_in
    if t > duration - fade_out:
        return max(0.0, (duration - t) / fade_out)
    return 1.0


def render_subtitle_overlay(
    t: float,
    groups: list[SubtitleGroup],
    font: ImageFont.FreeTypeFont,
    highlight_color: str = "#FFD700",
    text_color: str = "#FFFFFF",
) -> Image.Image | None:
    """Render subtitle overlay with highlighted current word.

    Returns RGBA image (WIDTH x 200) or None if no subtitle active.
    """
    # Find active group
    active = None
    for group in groups:
        if group.start <= t <= group.end:
            active = group
            break
    if not active:
        return None

    # Find current word index
    current_idx = -1
    for i, word in enumerate(active.words):
        if word.start <= t <= word.end:
            current_idx = i
            break

    MAX_TEXT_W = WIDTH - 120  # leave 60px margin each side
    overlay = Image.new("RGBA", (WIDTH, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    words = [w.word.upper() for w in active.words]

    # Split into lines that fit within MAX_TEXT_W
    lines: list[list[tuple[str, int]]] = []  # list of [(word, original_index), ...]
    current_line: list[tuple[str, int]] = []
    for i, word in enumerate(words):
        test_text = " ".join(w for w, _ in current_line + [(word, i)])
        tw = draw.textlength(test_text, font=font)
        if tw > MAX_TEXT_W and current_line:
            lines.append(current_line)
            current_line = [(word, i)]
        else:
            current_line.append((word, i))
    if current_line:
        lines.append(current_line)

    # Measure total height
    line_h = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
    line_gap = 10
    total_h = line_h * len(lines) + line_gap * (len(lines) - 1)
    y = (260 - total_h) // 2

    # Draw each line centered
    for line in lines:
        line_text = " ".join(w for w, _ in line)
        lw = draw.textlength(line_text, font=font)
        x = (WIDTH - int(lw)) // 2

        for word, idx in line:
            color = highlight_color if idx == current_idx else text_color
            draw.text((x, y), word, fill=color, font=font, stroke_width=4, stroke_fill="#000000")
            word_w = draw.textlength(word + " ", font=font)
            x += int(word_w)
        y += line_h + line_gap

    return overlay
