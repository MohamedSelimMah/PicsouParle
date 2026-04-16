"""Generate static background assets for each preset mode.

Usage:
    python scripts/generate_backgrounds.py

Outputs:
    assets/backgrounds/luxury_car.png   (1080×1920)
    assets/backgrounds/seaside.png      (1080×1920)
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
OUT = Path(__file__).resolve().parents[1] / "assets" / "backgrounds"


def _gradient(draw: ImageDraw.Draw, w: int, h: int, top: tuple, bot: tuple):
    for y in range(h):
        r = y / h
        c = tuple(int(a + (b - a) * r) for a, b in zip(top, bot))
        draw.line([(0, y), (w, y)], fill=c)


def _ellipse_glow(img: Image.Image, cx: int, cy: int, rx: int, ry: int, color: tuple, alpha: int):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(*color, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(rx // 2))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _bokeh_circles(img: Image.Image, count: int, colors: list[tuple], y_range: tuple, size_range: tuple, alpha_range: tuple):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(count):
        x = random.randint(0, W)
        y = random.randint(*y_range)
        r = random.randint(*size_range)
        a = random.randint(*alpha_range)
        color = random.choice(colors)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(8))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _vignette(img: Image.Image, strength: float = 0.7) -> Image.Image:
    vig = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(vig)
    for i in range(50):
        opacity = int(255 * (1 - i / 50))
        margin_x = i * (W // 100)
        margin_y = i * (H // 80)
        d.rectangle([margin_x, margin_y, W - margin_x, H - margin_y], fill=opacity)
    vig = vig.filter(ImageFilter.GaussianBlur(80))
    black = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(img.convert("RGB"), black, vig)


# ───────────────────────────────────────────
#  LUXURY CAR
# ───────────────────────────────────────────

def generate_luxury_car() -> Path:
    random.seed(42)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark gradient base
    _gradient(draw, W, H, (12, 10, 6), (22, 18, 10))

    img = img.convert("RGBA")

    # Warm gold ambient glow from center-bottom (dashboard light)
    img = _ellipse_glow(img, W // 2, int(H * 0.7), 600, 400, (180, 140, 40), 30)
    img = _ellipse_glow(img, W // 2, int(H * 0.55), 400, 300, (200, 160, 50), 20)

    # Steering wheel — dark circle with gold rim highlight
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = W // 2, int(H * 0.72)
    # Outer rim
    for t in range(8):
        offset = t * 2
        alpha = 55 - t * 6
        d.ellipse([cx - 220 - offset, cy - 220 - offset, cx + 220 + offset, cy + 220 + offset],
                  outline=(180, 150, 50, max(alpha, 0)), width=3)
    # Inner dark
    d.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], fill=(15, 12, 8, 200))
    # Center hub
    d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(30, 25, 15, 220))
    d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], outline=(160, 130, 40, 100), width=2)
    # Spokes (3 spokes)
    for angle_deg in [90, 210, 330]:
        a = math.radians(angle_deg)
        x1, y1 = cx + int(55 * math.cos(a)), cy + int(55 * math.sin(a))
        x2, y2 = cx + int(175 * math.cos(a)), cy + int(175 * math.sin(a))
        d.line([(x1, y1), (x2, y2)], fill=(40, 35, 20, 180), width=18)
        d.line([(x1, y1), (x2, y2)], fill=(80, 65, 30, 80), width=6)
    overlay = overlay.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, overlay)

    # Dashboard — horizontal gold accent lines
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    dash_y = int(H * 0.52)
    d.rectangle([80, dash_y, W - 80, dash_y + 3], fill=(180, 150, 50, 60))
    d.rectangle([120, dash_y + 40, W - 120, dash_y + 42], fill=(140, 110, 35, 40))
    # Small instrument cluster circles
    for ix in range(3):
        gx = 250 + ix * 200
        gy = dash_y - 60
        d.ellipse([gx - 35, gy - 35, gx + 35, gy + 35], outline=(160, 130, 45, 50), width=2)
        d.ellipse([gx - 25, gy - 25, gx + 25, gy + 25], outline=(100, 80, 30, 35), width=1)
    overlay = overlay.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, overlay)

    # City bokeh lights in upper third (through windshield)
    bokeh_colors = [
        (255, 200, 80), (255, 170, 50), (255, 220, 120),
        (200, 160, 255), (100, 180, 255), (255, 120, 80),
        (255, 255, 200), (180, 220, 255),
    ]
    img = _bokeh_circles(img, 80, bokeh_colors, (40, int(H * 0.35)), (8, 35), (15, 60))
    img = _bokeh_circles(img, 30, bokeh_colors, (40, int(H * 0.25)), (35, 70), (8, 30))

    # Windshield frame — subtle dark bars at edges
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, 30, int(H * 0.45)], fill=(5, 4, 2, 120))
    d.rectangle([W - 30, 0, W, int(H * 0.45)], fill=(5, 4, 2, 120))
    d.rectangle([0, 0, W, 15], fill=(5, 4, 2, 100))
    img = Image.alpha_composite(img, overlay)

    # Gold accent line at very top
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, W, 4], fill=(212, 164, 24, 180))
    img = Image.alpha_composite(img, overlay)

    # Leather texture — subtle noise
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(3000):
        x = random.randint(0, W - 1)
        y = random.randint(int(H * 0.5), H - 1)
        v = random.randint(20, 50)
        a = random.randint(8, 25)
        d.point((x, y), fill=(v, v - 5, v - 10, a))
    img = Image.alpha_composite(img, overlay)

    # Final vignette + convert
    result = _vignette(img.convert("RGB"), 0.8)

    out = OUT / "luxury_car.png"
    result.save(out, quality=95)
    print(f"✓ {out} ({W}×{H})")
    return out


# ───────────────────────────────────────────
#  SEASIDE
# ───────────────────────────────────────────

def generate_seaside() -> Path:
    random.seed(77)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Sky gradient — deep blue to warm orange
    horizon_y = int(H * 0.38)
    for y in range(horizon_y):
        r = y / horizon_y
        # Deep blue → orange at horizon
        c = (
            int(10 + 220 * r),
            int(20 + 120 * r),
            int(80 + 20 * r * r),
        )
        draw.line([(0, y), (W, y)], fill=c)

    # Sun glow near horizon
    img = img.convert("RGBA")
    img = _ellipse_glow(img, W // 2 + 100, horizon_y - 20, 300, 200, (255, 180, 60), 80)
    img = _ellipse_glow(img, W // 2 + 100, horizon_y - 40, 150, 100, (255, 220, 120), 50)

    # Sun disc
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    sx, sy = W // 2 + 100, horizon_y - 60
    d.ellipse([sx - 55, sy - 55, sx + 55, sy + 55], fill=(255, 200, 80, 200))
    d.ellipse([sx - 45, sy - 45, sx + 45, sy + 45], fill=(255, 230, 150, 220))
    overlay = overlay.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img, overlay)

    # Ocean — dark blue-teal below horizon
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    ocean_bottom = int(H * 0.62)
    for y in range(horizon_y, ocean_bottom):
        r = (y - horizon_y) / (ocean_bottom - horizon_y)
        c = (
            int(20 + 30 * (1 - r)),
            int(60 + 40 * (1 - r)),
            int(100 + 30 * (1 - r)),
        )
        d.line([(0, y), (W, y)], fill=(*c, 240))
    img = Image.alpha_composite(img, overlay)

    # Ocean sun reflection
    img = _ellipse_glow(img, W // 2 + 100, horizon_y + 80, 80, 200, (255, 180, 80), 35)

    # Water shimmer lines
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(60):
        y = random.randint(horizon_y + 10, ocean_bottom - 10)
        x = random.randint(50, W - 50)
        length = random.randint(30, 120)
        a = random.randint(15, 45)
        d.line([(x, y), (x + length, y)], fill=(200, 220, 255, a), width=1)
    img = Image.alpha_composite(img, overlay)

    # Beach / terrace area — warm sandy tones
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(ocean_bottom, H):
        r = (y - ocean_bottom) / (H - ocean_bottom)
        c = (
            int(60 - 35 * r),
            int(45 - 25 * r),
            int(30 - 15 * r),
        )
        d.line([(0, y), (W, y)], fill=(*c, 250))
    img = Image.alpha_composite(img, overlay)

    # Villa silhouette on the right
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    villa_base = ocean_bottom - 20
    # Main building
    d.rectangle([W - 350, villa_base - 280, W - 60, villa_base + 40], fill=(25, 22, 18, 180))
    # Roof
    d.polygon([(W - 370, villa_base - 280), (W - 200, villa_base - 380), (W - 40, villa_base - 280)],
              fill=(30, 25, 18, 190))
    # Windows — warm light
    for wy in range(3):
        for wx in range(3):
            wx1 = W - 330 + wx * 90
            wy1 = villa_base - 260 + wy * 80
            d.rectangle([wx1, wy1, wx1 + 45, wy1 + 40], fill=(255, 210, 120, 80))
    # Terrace pillars
    for px in range(4):
        px1 = W - 360 + px * 80
        d.rectangle([px1, villa_base - 20, px1 + 8, villa_base + 40], fill=(35, 30, 22, 160))
    # Terrace railing
    d.rectangle([W - 370, villa_base - 20, W - 40, villa_base - 16], fill=(40, 35, 25, 150))
    overlay = overlay.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, overlay)

    # Palm tree silhouette on left
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    trunk_x = 120
    trunk_base = ocean_bottom + 60
    trunk_top = horizon_y - 100
    # Curved trunk
    for t in range(50):
        r = t / 50
        x = trunk_x + int(30 * math.sin(r * 1.2))
        y = int(trunk_base + (trunk_top - trunk_base) * r)
        w = int(14 - 8 * r)
        d.ellipse([x - w, y - 3, x + w, y + 3], fill=(20, 18, 12, 200))
    # Palm fronds
    frond_cx = trunk_x + 28
    frond_cy = trunk_top
    for angle_deg in [-60, -30, 0, 20, 50, 80, 120, 160]:
        a = math.radians(angle_deg - 90)
        points = []
        for t in range(20):
            r = t / 19
            droop = r * r * 60
            fx = frond_cx + int(r * 140 * math.cos(a))
            fy = frond_cy + int(r * 140 * math.sin(a)) + int(droop)
            points.append((fx, fy))
        if len(points) > 1:
            d.line(points, fill=(18, 30, 12, 170), width=4)
            # Leaf width
            for i, (fx, fy) in enumerate(points[3:], 3):
                leaf_w = int(12 * (1 - i / len(points)))
                if leaf_w > 1:
                    d.ellipse([fx - leaf_w, fy - 2, fx + leaf_w, fy + 2], fill=(15, 28, 10, 130))
    overlay = overlay.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, overlay)

    # Clouds
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(8):
        cx = random.randint(50, W - 50)
        cy = random.randint(30, horizon_y - 120)
        for _ in range(5):
            ox = random.randint(-60, 60)
            oy = random.randint(-15, 15)
            rx = random.randint(40, 90)
            ry = random.randint(15, 30)
            d.ellipse([cx + ox - rx, cy + oy - ry, cx + ox + rx, cy + oy + ry],
                      fill=(255, 200, 150, random.randint(8, 22)))
    overlay = overlay.filter(ImageFilter.GaussianBlur(15))
    img = Image.alpha_composite(img, overlay)

    # Gold accent line at top
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, W, 4], fill=(212, 164, 24, 150))
    img = Image.alpha_composite(img, overlay)

    result = _vignette(img.convert("RGB"), 0.7)

    out = OUT / "seaside.png"
    result.save(out, quality=95)
    print(f"✓ {out} ({W}×{H})")
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    generate_luxury_car()
    generate_seaside()
    print("\nDone — backgrounds ready in assets/backgrounds/")
