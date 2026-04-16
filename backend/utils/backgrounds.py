"""Animated background renderers — one function per preset.

Each renderer returns a full 1080×1920 RGB frame for time `t`.
Elements move across frames to create a living, cinematic feel.
"""

from __future__ import annotations

import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1080, 1920


# ─── Shared helpers ──────────────────────────────────────

def _gradient_img(w: int, h: int, top: tuple[int, ...], bot: tuple[int, ...]) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = y / h
        c = tuple(int(a + (b - a) * r) for a, b in zip(top, bot))
        draw.line([(0, y), (w, y)], fill=c)
    return img


def _vignette(img: Image.Image) -> Image.Image:
    w, h = img.size
    vig = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(vig)
    steps = 40
    for i in range(steps):
        mx = i * (w // 80)
        my = i * (h // 60)
        x1, y1 = mx, my
        x2, y2 = w - mx, h - my
        if x2 <= x1 or y2 <= y1:
            break
        opacity = int(255 * (1 - i / steps))
        d.rectangle([x1, y1, x2, y2], fill=opacity)
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, black, vig)


# ═══════════════════════════════════════════════════════════
#  LUXURY CAR — Rolls-Royce exterior, night street, Picsou in front
# ═══════════════════════════════════════════════════════════

# Geometry constants — all derived from HEIGHT so nothing is magic
CAR_GROUND_Y   = int(HEIGHT * 0.695)   # pavement / tyre contact line
_CAR_BOTTOM    = CAR_GROUND_Y          # alias
_CAR_ROOF_Y    = int(HEIGHT * 0.435)   # top of roof
_CAR_HOOD_Y    = int(HEIGHT * 0.515)   # front/rear hood height
_CAR_BODY_TOP  = int(HEIGHT * 0.545)   # shoulder line
_CAR_LEFT      = 55                    # front bumper x
_CAR_RIGHT     = WIDTH - 55            # rear bumper x
_WHEEL_R       = 88                    # tyre radius
_FRONT_WHEEL_X = _CAR_LEFT  + 230
_REAR_WHEEL_X  = _CAR_RIGHT - 200

_CAR_RNG = random.Random(42)
_BOKEH_LIGHTS: list[dict] = []
for _ in range(80):
    _BOKEH_LIGHTS.append({
        "x": _CAR_RNG.randint(0, WIDTH),
        "y": _CAR_RNG.randint(20, int(HEIGHT * 0.38)),
        "r": _CAR_RNG.randint(8, 50),
        "alpha": _CAR_RNG.randint(12, 55),
        "color": _CAR_RNG.choice([
            (255, 200, 80), (255, 170, 50), (255, 220, 120),
            (200, 160, 255), (100, 190, 255), (255, 130, 80),
            (255, 255, 200), (180, 220, 255), (255, 210, 140),
        ]),
        "pulse_phase": _CAR_RNG.uniform(0, math.tau),
        "pulse_speed": _CAR_RNG.uniform(1.0, 3.5),
    })


@lru_cache(maxsize=1)
def _car_base() -> Image.Image:
    """Static base: Rolls-Royce style exterior on a rain-wet night street."""
    # ── Sky gradient: deep indigo → near-black ──
    img = _gradient_img(WIDTH, HEIGHT, (7, 6, 12), (12, 10, 18))
    img = img.convert("RGBA")

    def composite(layer: Image.Image) -> Image.Image:
        return Image.alpha_composite(img, layer)

    # ── Far background: fog glow across city ──
    fog = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    sky_base = int(HEIGHT * 0.26)
    for gy in range(sky_base - 60, sky_base + 20):
        a = max(0, 18 - abs(gy - sky_base) // 2)
        fd.line([(0, gy), (WIDTH, gy)], fill=(80, 100, 160, a))
    fog = fog.filter(ImageFilter.GaussianBlur(30))
    img = composite(fog)

    # ── City skyline — two depth layers ──
    rng2 = random.Random(17)
    for depth, color, alpha, y_frac, h_range in [
        ("far",  (16, 14, 22), 140, 0.26, (60, 220)),
        ("near", (22, 19, 30), 200, 0.28, (100, 320)),
    ]:
        sky = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sky)
        sky_y = int(HEIGHT * y_frac)
        x = 0
        while x < WIDTH:
            bw = rng2.randint(35, 90)
            bh = rng2.randint(*h_range)
            bx1, bx2 = x, min(x + bw, WIDTH)
            by1, by2 = sky_y - bh, sky_y
            sd.rectangle([bx1, by1, bx2, by2], fill=(*color, alpha))
            # windows
            for _ in range(rng2.randint(3, 9)):
                wx = rng2.randint(bx1 + 3, max(bx1 + 4, bx2 - 8))
                wy = rng2.randint(by1 + 8, max(by1 + 9, by2 - 12))
                wa = rng2.randint(20, 65)
                sd.rectangle([wx, wy, wx + 5, wy + 7], fill=(255, 220, 140, wa))
            x += bw + rng2.randint(0, 4)
        img = composite(sky)

    # ── Street: rain-wet asphalt with perspective lanes ──
    road = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    rd = ImageDraw.Draw(road)
    horizon_y = int(HEIGHT * 0.285)
    for y in range(horizon_y, HEIGHT):
        r = (y - horizon_y) / max(HEIGHT - horizon_y, 1)
        bv = int(18 + 10 * r)
        rd.line([(0, y), (WIDTH, y)], fill=(bv, bv, bv + 4, 240))
    # Wet reflection: mirror of sky glow on road surface
    for y in range(horizon_y, min(horizon_y + 200, HEIGHT)):
        a = max(0, 30 - (y - horizon_y) // 4)
        rd.line([(0, y), (WIDTH, y)], fill=(60, 80, 130, a))
    # Lane markings (perspective)
    for lane_x_top, lane_x_bot in [(WIDTH // 2 - 30, WIDTH // 2 - 120),
                                    (WIDTH // 2 + 30, WIDTH // 2 + 120)]:
        for seg in range(8):
            r1 = seg / 8
            r2 = (seg + 0.4) / 8
            y1 = int(horizon_y + r1 * (HEIGHT - horizon_y))
            y2 = int(horizon_y + r2 * (HEIGHT - horizon_y))
            x1 = int(lane_x_top + (lane_x_bot - lane_x_top) * r1)
            x2 = int(lane_x_top + (lane_x_bot - lane_x_top) * r2)
            a = int(25 + 20 * r1)
            rd.line([(x1, y1), (x2, y2)], fill=(180, 160, 80, a), width=max(1, int(3 * r1)))
    img = composite(road)

    # ── Rolls-Royce silhouette ──
    G = CAR_GROUND_Y      # tyre contact
    ROOF  = _CAR_ROOF_Y
    HOOD  = _CAR_HOOD_Y
    BODY  = _CAR_BODY_TOP
    L     = _CAR_LEFT
    R     = _CAR_RIGHT
    FWX   = _FRONT_WHEEL_X
    RWX   = _REAR_WHEEL_X
    WR    = _WHEEL_R

    # ── Underbody shadow ──
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shadow)
    shd.ellipse([L + 60, G - 15, R - 60, G + 45], fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img = composite(shadow)

    car = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    cd = ImageDraw.Draw(car)

    # Body fill — deep black with slight blue tint (Phantom style)
    BODY_COLOR = (18, 17, 24)

    # Main lower body (sill to shoulder)
    cd.polygon([
        (L + 10,  G),             # front-bottom
        (L,       G - 70),        # front-lower
        (L + 30,  BODY + 30),     # front-shoulder
        (R - 30,  BODY + 30),     # rear-shoulder
        (R,       G - 70),        # rear-lower
        (R - 10,  G),             # rear-bottom
    ], fill=(*BODY_COLOR, 235))

    # Upper body (shoulder to roof)
    cd.polygon([
        (L + 30,  BODY + 30),     # front-shoulder
        (L + 60,  BODY - 10),     # front-upper
        (L + 160, HOOD),          # front hood base
        (L + 310, ROOF + 40),     # A-pillar base
        (L + 390, ROOF),          # A-pillar top
        (R - 340, ROOF),          # C-pillar top
        (R - 260, ROOF + 40),     # C-pillar base
        (R - 130, HOOD + 15),     # rear deck
        (R - 50,  BODY - 10),     # rear-upper
        (R - 30,  BODY + 30),     # rear-shoulder
    ], fill=(*BODY_COLOR, 235))

    # ── Body highlight: slim chrome shoulder line ──
    for thickness, a in [(6, 55), (3, 90), (1, 130)]:
        cd.line([
            (L + 60,  BODY - 8),
            (L + 200, BODY - 22),
            (R - 200, BODY - 22),
            (R - 60,  BODY - 8),
        ], fill=(210, 200, 180, a), width=thickness)

    # ── Gold chrome trim strip (waistline) ──
    trim_y = BODY + 14
    cd.polygon([
        (L + 55,  trim_y + 12),
        (L + 75,  trim_y),
        (R - 75,  trim_y),
        (R - 55,  trim_y + 12),
    ], fill=(190, 158, 45, 110))
    # bright edge
    cd.line([(L + 75, trim_y), (R - 75, trim_y)], fill=(240, 210, 80, 70), width=1)

    # ── Windshield & rear glass ──
    # Windshield
    ws_pts = [
        (L + 316, ROOF + 36), (L + 396, ROOF + 2),
        (L + 530, ROOF + 2),  (L + 490, ROOF + 36),
    ]
    cd.polygon(ws_pts, fill=(20, 30, 45, 195))
    # Windshield glare
    cd.polygon([
        (L + 320, ROOF + 33), (L + 400, ROOF + 5),
        (L + 440, ROOF + 5),  (L + 400, ROOF + 33),
    ], fill=(60, 100, 140, 40))

    # Side window (single large pane — Phantom style)
    sw_pts = [
        (L + 495, ROOF + 38), (L + 530, ROOF + 4),
        (R - 340, ROOF + 4),  (R - 265, ROOF + 38),
    ]
    cd.polygon(sw_pts, fill=(20, 30, 45, 185))
    # Window glare streak
    cd.line([
        (L + 510, ROOF + 28), (L + 560, ROOF + 8),
    ], fill=(80, 130, 180, 45), width=4)

    # Rear glass
    rg_pts = [
        (R - 260, ROOF + 38), (R - 338, ROOF + 4),
        (R - 420, ROOF + 4),  (R - 370, ROOF + 38),
    ]
    cd.polygon(rg_pts, fill=(20, 30, 45, 185))

    # B-pillar (dark divider between windows)
    cd.polygon([
        (L + 490, ROOF + 38), (L + 497, ROOF + 4),
        (L + 510, ROOF + 4),  (L + 503, ROOF + 38),
    ], fill=(10, 10, 14, 220))

    # ── Roof chrome rail ──
    cd.line([(L + 390, ROOF - 1), (R - 340, ROOF - 1)],
            fill=(200, 190, 170, 80), width=3)
    cd.line([(L + 390, ROOF + 1), (R - 340, ROOF + 1)],
            fill=(160, 140, 100, 50), width=1)

    # ── A/C pillars (dark posts) ──
    for pts in [
        [(L + 308, ROOF + 38), (L + 392, ROOF),    (L + 396, ROOF),    (L + 315, ROOF + 38)],
        [(R - 315, ROOF + 38), (R - 396, ROOF),    (R - 392, ROOF),    (R - 308, ROOF + 38)],
    ]:
        cd.polygon(pts, fill=(12, 11, 16, 230))

    # ── Front end: Rolls Spirit grille ──
    grille_cx = L + 95
    grille_top = HOOD + 5
    grille_bot = G - WR * 2 - 8
    grille_w   = 70
    # Frame
    cd.rectangle([grille_cx - grille_w // 2, grille_top,
                  grille_cx + grille_w // 2, grille_bot],
                 outline=(160, 140, 60, 100), width=3,
                 fill=(10, 9, 13, 200))
    # Vertical slats
    n_slats = 7
    for si in range(n_slats):
        sx = grille_cx - grille_w // 2 + 5 + si * ((grille_w - 10) // n_slats)
        cd.line([(sx, grille_top + 4), (sx, grille_bot - 4)],
                fill=(140, 120, 50, 70), width=2)
    # Horizontal bar (Spirit of Ecstasy mount)
    cd.line([(grille_cx - grille_w // 2 + 4, grille_top + 18),
             (grille_cx + grille_w // 2 - 4, grille_top + 18)],
            fill=(180, 160, 60, 90), width=3)

    # ── Front headlights: dual DRL strips ──
    hl_top = grille_top - 4
    hl_bot = grille_top + 28
    for hly_off, ha in [(0, 180), (18, 130)]:
        cd.rounded_rectangle(
            [L + 18, hl_top + hly_off, L + 148, hl_top + hly_off + 14],
            radius=4, fill=(220, 235, 255, ha)
        )
    # DRL inner bright strip
    cd.rectangle([L + 25, hl_top + 3, L + 140, hl_top + 7],
                 fill=(240, 250, 255, 200))

    # ── Rear lights: full-width LED strip ──
    rl_y = BODY - 5
    cd.rounded_rectangle(
        [R - 160, rl_y - 5, R - 18, rl_y + 22],
        radius=3, fill=(160, 25, 18, 180)
    )
    # Bright inner strip
    cd.rectangle([R - 155, rl_y - 2, R - 24, rl_y + 4],
                 fill=(230, 60, 45, 200))

    # ── Door lines (etched panels) ──
    for dx in [L + 290, L + 290 + 290]:
        cd.line([(dx, BODY + 10), (dx, G - 30)],
                fill=(35, 33, 42, 160), width=3)

    # ── Door handles (chrome bars) ──
    for hx in [L + 360, L + 360 + 290]:
        hy = BODY + 60
        cd.rounded_rectangle([hx, hy, hx + 52, hy + 12],
                             radius=3, fill=(160, 150, 130, 120))
        cd.line([(hx + 2, hy + 4), (hx + 50, hy + 4)],
                fill=(220, 210, 180, 70), width=1)

    # ── Wheels — 22" multi-spoke rims ──
    for wc_x in [FWX, RWX]:
        wc_y = G - 2
        # Tyre (wide, low-profile)
        cd.ellipse([wc_x - WR, wc_y - WR, wc_x + WR, wc_y + WR],
                   fill=(12, 11, 14, 245))
        # Tyre sidewall highlight
        cd.arc([wc_x - WR, wc_y - WR, wc_x + WR, wc_y + WR],
               start=200, end=320, fill=(30, 28, 35, 120), width=6)
        # Rim outer ring
        cd.ellipse([wc_x - WR + 10, wc_y - WR + 10,
                    wc_x + WR - 10, wc_y + WR - 10],
                   outline=(130, 108, 38, 120), width=4)
        # 10-spoke design
        for spoke_i in range(10):
            sa = math.radians(spoke_i * 36)
            # Two thin blades per spoke
            for blade in [-0.06, 0.06]:
                ab = sa + blade
                d0, d1 = WR * 0.24, WR * 0.88
                x0 = wc_x + int(d0 * math.cos(ab))
                y0 = wc_y + int(d0 * math.sin(ab))
                x1 = wc_x + int(d1 * math.cos(ab))
                y1 = wc_y + int(d1 * math.sin(ab))
                cd.line([(x0, y0), (x1, y1)],
                        fill=(155, 130, 45, 130), width=3)
        # Centre cap
        cd.ellipse([wc_x - 18, wc_y - 18, wc_x + 18, wc_y + 18],
                   fill=(20, 18, 12, 230))
        cd.ellipse([wc_x - 12, wc_y - 12, wc_x + 12, wc_y + 12],
                   outline=(170, 145, 50, 100), width=2)
        # Brake caliper (red, visible through spokes)
        cd.arc([wc_x - 44, wc_y - 44, wc_x + 44, wc_y + 44],
               start=30, end=100, fill=(160, 35, 25, 150), width=10)

    # ── Spirit of Ecstasy hood ornament ──
    ox, oy = L + 170, HOOD - 18
    cd.line([(ox, oy + 18), (ox, oy)], fill=(200, 185, 150, 120), width=2)
    # Wing silhouette (simplified)
    cd.polygon([(ox, oy), (ox - 14, oy + 10), (ox, oy + 6)],
               fill=(190, 175, 140, 100))
    cd.polygon([(ox, oy), (ox + 14, oy + 10), (ox, oy + 6)],
               fill=(190, 175, 140, 100))

    # ── Gold accent line at very top ──
    cd.rectangle([0, 0, WIDTH, 4], fill=(212, 164, 24, 160))

    car = car.filter(ImageFilter.GaussianBlur(0))   # keep crisp
    img = composite(car)
    return img


def render_luxury_car(t: float, duration: float) -> Image.Image:
    """Animated frame: bokeh city lights, headlight beams, tail-light pulse, wet road reflection."""
    base = _car_base().copy()

    # ── Headlight beam fans ──
    beam = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    beam_a = int(14 + 7 * math.sin(t * 0.7))
    hl_x, hl_y = _CAR_LEFT + 83, _CAR_HOOD_Y + 14
    for spread in [(-160, -20), (-20, 20), (20, 80)]:
        pts = [
            (hl_x + 4, hl_y),
            (hl_x + spread[0], CAR_GROUND_Y + 30),
            (hl_x + spread[1], CAR_GROUND_Y + 30),
        ]
        bd.polygon(pts, fill=(210, 230, 255, beam_a))
    beam = beam.filter(ImageFilter.GaussianBlur(28))
    base = Image.alpha_composite(base, beam)

    # ── Wet road: headlight reflection pool ──
    ref = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    refd = ImageDraw.Draw(ref)
    ref_a = int(20 + 10 * math.sin(t * 1.3))
    refd.ellipse([_CAR_LEFT - 60, CAR_GROUND_Y, _CAR_LEFT + 300, CAR_GROUND_Y + 80],
                 fill=(180, 200, 255, ref_a))
    # Tail-light red pool
    refd.ellipse([_CAR_RIGHT - 260, CAR_GROUND_Y, _CAR_RIGHT + 60, CAR_GROUND_Y + 70],
                 fill=(160, 20, 15, int(ref_a * 0.8)))
    ref = ref.filter(ImageFilter.GaussianBlur(22))
    base = Image.alpha_composite(base, ref)

    # ── Pulsing bokeh city lights ──
    bokeh = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bd2 = ImageDraw.Draw(bokeh)
    for light in _BOKEH_LIGHTS:
        pulse = 0.62 + 0.38 * math.sin(t * light["pulse_speed"] + light["pulse_phase"])
        alpha = int(light["alpha"] * pulse)
        r = int(light["r"] * (0.88 + 0.12 * pulse))
        cr, cg, cb = light["color"]
        ix, iy = light["x"], light["y"]
        bd2.ellipse([ix - r, iy - r, ix + r, iy + r], fill=(cr, cg, cb, alpha))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(11))
    base = Image.alpha_composite(base, bokeh)

    # ── Tail-light ambient glow (rear, pulsing red) ──
    tl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    tld = ImageDraw.Draw(tl)
    tl_a = int(28 + 16 * math.sin(t * 2.2))
    tld.ellipse([_CAR_RIGHT - 200, _CAR_BODY_TOP - 40,
                 _CAR_RIGHT + 60, CAR_GROUND_Y],
                fill=(170, 22, 14, tl_a))
    tl = tl.filter(ImageFilter.GaussianBlur(30))
    base = Image.alpha_composite(base, tl)

    # ── DRL flicker (very subtle, front) ──
    drl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    drl_d = ImageDraw.Draw(drl)
    drl_a = int(35 + 20 * math.sin(t * 3.0 + 0.4))
    drl_d.rectangle([_CAR_LEFT + 15, _CAR_HOOD_Y + 3,
                     _CAR_LEFT + 148, _CAR_HOOD_Y + 10],
                    fill=(240, 248, 255, drl_a))
    drl = drl.filter(ImageFilter.GaussianBlur(6))
    base = Image.alpha_composite(base, drl)

    result = _vignette(base.convert("RGB"))
    return result


# ═══════════════════════════════════════════════════════════
#  SEASIDE — animated waves, drifting clouds, flying birds
# ═══════════════════════════════════════════════════════════

_SEA_RNG = random.Random(77)

# Pre-generate cloud positions
_CLOUDS: list[dict] = []
for _ in range(7):
    _CLOUDS.append({
        "cx": _SEA_RNG.randint(-100, WIDTH + 100),
        "cy": _SEA_RNG.randint(40, int(HEIGHT * 0.28)),
        "blobs": [(
            _SEA_RNG.randint(-70, 70),
            _SEA_RNG.randint(-20, 20),
            _SEA_RNG.randint(50, 100),
            _SEA_RNG.randint(18, 35),
            _SEA_RNG.randint(10, 25),
        ) for _ in range(5)],
        "speed": _SEA_RNG.uniform(8, 20),
    })

# Pre-generate bird paths
_BIRDS: list[dict] = []
for _ in range(5):
    _BIRDS.append({
        "start_x": _SEA_RNG.randint(WIDTH + 50, WIDTH + 400),
        "y": _SEA_RNG.randint(60, int(HEIGHT * 0.30)),
        "speed": _SEA_RNG.uniform(40, 80),
        "wing_speed": _SEA_RNG.uniform(5, 9),
        "wing_phase": _SEA_RNG.uniform(0, math.tau),
        "size": _SEA_RNG.randint(6, 14),
    })

# Pre-generate wave shimmer lines
_WAVE_LINES: list[dict] = []
for _ in range(50):
    _WAVE_LINES.append({
        "base_y": _SEA_RNG.uniform(0, 1),  # 0-1 within ocean band
        "base_x": _SEA_RNG.randint(30, WIDTH - 30),
        "length": _SEA_RNG.randint(40, 140),
        "speed": _SEA_RNG.uniform(1.0, 3.0),
        "phase": _SEA_RNG.uniform(0, math.tau),
        "alpha": _SEA_RNG.randint(18, 50),
    })

HORIZON_Y = int(HEIGHT * 0.38)
OCEAN_BOTTOM = int(HEIGHT * 0.62)


@lru_cache(maxsize=1)
def _sea_base() -> Image.Image:
    """Static base for seaside — sky gradient, sun, villa, palm tree."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Sky gradient — deep blue to warm orange at horizon
    for y in range(HORIZON_Y):
        r = y / HORIZON_Y
        c = (int(10 + 220 * r), int(20 + 120 * r), int(80 + 20 * r * r))
        draw.line([(0, y), (WIDTH, y)], fill=c)

    # Horizon to ocean bottom — static base ocean color
    for y in range(HORIZON_Y, OCEAN_BOTTOM):
        r = (y - HORIZON_Y) / (OCEAN_BOTTOM - HORIZON_Y)
        c = (int(20 + 30 * (1 - r)), int(60 + 40 * (1 - r)), int(100 + 30 * (1 - r)))
        draw.line([(0, y), (WIDTH, y)], fill=c)

    # Beach / terrace area below ocean
    for y in range(OCEAN_BOTTOM, HEIGHT):
        r = (y - OCEAN_BOTTOM) / max(HEIGHT - OCEAN_BOTTOM, 1)
        c = (int(60 - 35 * r), int(45 - 25 * r), int(30 - 15 * r))
        draw.line([(0, y), (WIDTH, y)], fill=c)

    img = img.convert("RGBA")

    # Sun disc
    sun = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    sx, sy = WIDTH // 2 + 100, HORIZON_Y - 60
    # Glow
    for ring in range(10):
        gr = 120 + ring * 30
        a = max(25 - ring * 3, 2)
        sd.ellipse([sx - gr, sy - gr, sx + gr, sy + gr], fill=(255, 180, 60, a))
    # Disc
    sd.ellipse([sx - 55, sy - 55, sx + 55, sy + 55], fill=(255, 200, 80, 190))
    sd.ellipse([sx - 42, sy - 42, sx + 42, sy + 42], fill=(255, 230, 150, 210))
    sun = sun.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, sun)

    # Sun reflection on water (static base)
    ref = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ref)
    for ry in range(10):
        a = max(30 - ry * 3, 3)
        w = 60 + ry * 10
        yy = HORIZON_Y + 20 + ry * 18
        rd.ellipse([sx - w, yy - 6, sx + w, yy + 6], fill=(255, 180, 80, a))
    ref = ref.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img, ref)

    # Villa silhouette
    villa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    vd = ImageDraw.Draw(villa)
    vb = OCEAN_BOTTOM - 20
    vd.rectangle([WIDTH - 350, vb - 280, WIDTH - 60, vb + 40], fill=(25, 22, 18, 170))
    vd.polygon([(WIDTH - 370, vb - 280), (WIDTH - 200, vb - 380), (WIDTH - 40, vb - 280)],
               fill=(30, 25, 18, 180))
    for wy in range(3):
        for wx in range(3):
            wx1 = WIDTH - 330 + wx * 90
            wy1 = vb - 260 + wy * 80
            vd.rectangle([wx1, wy1, wx1 + 45, wy1 + 40], fill=(255, 210, 120, 70))
    for px in range(4):
        px1 = WIDTH - 360 + px * 80
        vd.rectangle([px1, vb - 20, px1 + 8, vb + 40], fill=(35, 30, 22, 150))
    vd.rectangle([WIDTH - 370, vb - 20, WIDTH - 40, vb - 16], fill=(40, 35, 25, 140))
    villa = villa.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, villa)

    # Palm tree silhouette
    palm = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(palm)
    trunk_x = 120
    trunk_base = OCEAN_BOTTOM + 60
    trunk_top = HORIZON_Y - 100
    for step in range(50):
        r = step / 50
        x = trunk_x + int(30 * math.sin(r * 1.2))
        y = int(trunk_base + (trunk_top - trunk_base) * r)
        w = int(14 - 8 * r)
        if w > 0:
            pd.ellipse([x - w, y - 3, x + w, y + 3], fill=(20, 18, 12, 190))
    # Fronds (static — they'll sway in animated layer)
    # Just the trunk in base, fronds rendered per-frame for sway
    palm = palm.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, palm)

    # Gold accent at top
    top_bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(top_bar)
    td.rectangle([0, 0, WIDTH, 4], fill=(212, 164, 24, 140))
    img = Image.alpha_composite(img, top_bar)

    return img


def render_seaside(t: float, duration: float) -> Image.Image:
    """Render one frame of the seaside background at time t."""
    base = _sea_base().copy()
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # ── Animated ocean waves ──
    for wl in _WAVE_LINES:
        wave_y_norm = wl["base_y"]
        y = int(HORIZON_Y + wave_y_norm * (OCEAN_BOTTOM - HORIZON_Y))
        # Vertical bob
        y_offset = int(4 * math.sin(t * wl["speed"] + wl["phase"]))
        y = y + y_offset
        # Horizontal drift
        x = int((wl["base_x"] + t * 15 * wl["speed"]) % (WIDTH + 100) - 50)
        length = wl["length"]
        # Shimmer alpha
        pulse = 0.5 + 0.5 * math.sin(t * wl["speed"] * 2 + wl["phase"])
        alpha = int(wl["alpha"] * pulse)
        d.line([(x, y), (x + length, y)], fill=(200, 220, 255, alpha), width=1)

    # Gentle wave edge along horizon (undulating line)
    for x in range(0, WIDTH, 2):
        wave_h = int(3 * math.sin(x * 0.015 + t * 2.5) + 2 * math.sin(x * 0.025 + t * 1.8))
        wy = HORIZON_Y + wave_h
        d.line([(x, wy), (x, wy + 4)], fill=(30, 70, 110, 60))

    # ── Palm fronds swaying ──
    frond_cx = 120 + 28
    frond_cy = HORIZON_Y - 100
    sway = 8 * math.sin(t * 1.5)  # gentle wind sway
    for angle_deg in [-60, -30, 0, 20, 50, 80, 120, 160]:
        a = math.radians(angle_deg - 90 + sway)
        points = []
        for step in range(20):
            r = step / 19
            droop = r * r * 60
            fx = frond_cx + int(r * 140 * math.cos(a))
            fy = frond_cy + int(r * 140 * math.sin(a)) + int(droop)
            points.append((fx, fy))
        if len(points) > 1:
            d.line(points, fill=(18, 30, 12, 160), width=4)
            for i, (fx, fy) in enumerate(points[3:], 3):
                lw = int(12 * (1 - i / len(points)))
                if lw > 1:
                    d.ellipse([fx - lw, fy - 2, fx + lw, fy + 2], fill=(15, 28, 10, 120))

    # ── Drifting clouds ──
    for cloud in _CLOUDS:
        cx = (cloud["cx"] + cloud["speed"] * t) % (WIDTH + 300) - 150
        cy = cloud["cy"] + int(5 * math.sin(t * 0.3))
        for ox, oy, rx, ry, ca in cloud["blobs"]:
            d.ellipse([int(cx + ox - rx), int(cy + oy - ry),
                        int(cx + ox + rx), int(cy + oy + ry)],
                       fill=(255, 200, 150, ca))

    # ── Flying birds ──
    for bird in _BIRDS:
        # Birds fly from right to left, loop
        bx = (bird["start_x"] - bird["speed"] * t) % (WIDTH + 500) - 50
        by = bird["y"] + int(10 * math.sin(t * 0.7 + bird["wing_phase"]))
        sz = bird["size"]

        # Wing flap
        wing_angle = math.sin(t * bird["wing_speed"] + bird["wing_phase"])
        wing_dy = int(sz * 0.8 * wing_angle)

        # Draw bird as a simple V shape
        d.line([(bx - sz, by + wing_dy), (bx, by), (bx + sz, by + wing_dy)],
               fill=(20, 18, 15, 130), width=2)

    # ── Villa window flicker (warm light) ──
    vb = OCEAN_BOTTOM - 20
    flicker = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flicker)
    for wy in range(3):
        for wx in range(3):
            wx1 = WIDTH - 330 + wx * 90
            wy1 = vb - 260 + wy * 80
            # Subtle brightness variation per window
            phase = wx * 1.7 + wy * 2.3
            brightness = int(15 + 10 * math.sin(t * 2.0 + phase))
            fd.rectangle([wx1 + 2, wy1 + 2, wx1 + 43, wy1 + 38],
                          fill=(255, 210, 120, brightness))
    img_with_flicker = Image.alpha_composite(base, flicker)
    base = img_with_flicker

    # Blur the dynamic elements slightly for soft look
    overlay = overlay.filter(ImageFilter.GaussianBlur(3))
    base = Image.alpha_composite(base, overlay)

    result = _vignette(base.convert("RGB"))
    return result


# ─── Public dispatch ─────────────────────────────────────

RENDERERS: dict[str, callable] = {
    "luxury_car": render_luxury_car,
    "seaside": render_seaside,
}


def render_background_frame(mode: str, t: float, duration: float) -> Image.Image:
    """Render an animated background frame for the given mode and time."""
    renderer = RENDERERS.get(mode)
    if renderer:
        return renderer(t, duration)
    # Fallback — should not happen, but return black
    return Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
