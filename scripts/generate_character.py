"""Generate placeholder Picsou character assets (mouth open / closed).

Run once to create assets/character/picsou_mouth_closed.png and picsou_mouth_open.png.
These are stylized placeholders — replace with actual character art for production.
"""

from pathlib import Path
from PIL import Image, ImageDraw

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "character"
CHAR_W, CHAR_H = 600, 900


def draw_character(mouth_open: bool = False) -> Image.Image:
    img = Image.new("RGBA", (CHAR_W, CHAR_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = CHAR_W // 2  # center x

    # === Body (blue coat) ===
    draw.rounded_rectangle([160, 450, 440, 850], radius=50, fill="#1B3A5C", outline="#14304D", width=2)
    # Coat buttons
    for by in [530, 600, 670]:
        draw.ellipse([cx - 8, by, cx + 8, by + 16], fill="#D4A017")
    # Collar
    draw.polygon([(200, 450), (cx, 510), (400, 450)], fill="#244B75")

    # === Head (duck skin) ===
    draw.ellipse([175, 130, 425, 400], fill="#F5D6A0", outline="#D4A574", width=3)

    # === Top hat ===
    draw.rectangle([210, 10, 390, 130], fill="#1A1A1A", outline="#333", width=2)
    draw.rectangle([180, 120, 420, 160], fill="#1A1A1A", outline="#333", width=2)
    # Hat band
    draw.rectangle([210, 100, 390, 118], fill="#8B0000")

    # === Glasses ===
    # Left lens
    draw.ellipse([210, 195, 290, 270], outline="#333", width=4)
    draw.ellipse([215, 200, 285, 265], fill=(255, 255, 255, 180))
    # Right lens
    draw.ellipse([310, 195, 390, 270], outline="#333", width=4)
    draw.ellipse([315, 200, 385, 265], fill=(255, 255, 255, 180))
    # Bridge
    draw.line([290, 230, 310, 230], fill="#333", width=4)
    # Temple arms
    draw.line([210, 230, 180, 215], fill="#333", width=3)
    draw.line([390, 230, 420, 215], fill="#333", width=3)

    # === Eyes (pupils) ===
    draw.ellipse([240, 215, 265, 250], fill="#1A1A1A")
    draw.ellipse([340, 215, 365, 250], fill="#1A1A1A")
    # Eye shine
    draw.ellipse([250, 220, 258, 230], fill="white")
    draw.ellipse([350, 220, 358, 230], fill="white")

    # === Eyebrows ===
    draw.arc([220, 185, 280, 215], 190, 350, fill="#8B6914", width=4)
    draw.arc([320, 185, 380, 215], 190, 350, fill="#8B6914", width=4)

    # === Bill (duck beak) ===
    if mouth_open:
        # Upper bill
        draw.polygon([(240, 300), (360, 300), (400, 330), (cx, 340), (200, 330)], fill="#E67E22")
        draw.polygon([(240, 300), (360, 300), (400, 330), (cx, 340), (200, 330)],
                      outline="#D35400", width=2)
        # Lower bill (dropped for open mouth)
        draw.polygon([(250, 345), (350, 345), (385, 370), (cx, 380), (215, 370)], fill="#D35400")
        draw.polygon([(250, 345), (350, 345), (385, 370), (cx, 380), (215, 370)],
                      outline="#C0392B", width=2)
        # Dark inside mouth
        draw.polygon([(260, 335), (340, 335), (360, 348), (cx, 352), (240, 348)], fill="#4A1A1A")
    else:
        # Closed bill
        draw.polygon([(240, 310), (360, 310), (400, 340), (cx, 348), (200, 340)], fill="#E67E22")
        draw.polygon([(240, 310), (360, 310), (400, 340), (cx, 348), (200, 340)],
                      outline="#D35400", width=2)
        # Mouth line
        draw.line([(230, 330), (370, 330)], fill="#D35400", width=2)

    # === Sideburns ===
    draw.arc([170, 310, 240, 400], 130, 250, fill="#D4A574", width=4)
    draw.arc([360, 310, 430, 400], 290, 50, fill="#D4A574", width=4)

    # === Monocle chain (optional flair) ===
    draw.arc([380, 250, 440, 450], 0, 90, fill="#D4A017", width=2)

    return img


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    closed = draw_character(mouth_open=False)
    closed.save(ASSET_DIR / "picsou_mouth_closed.png")

    opened = draw_character(mouth_open=True)
    opened.save(ASSET_DIR / "picsou_mouth_open.png")

    print(f"✓ Character assets generated in {ASSET_DIR}")


if __name__ == "__main__":
    main()
