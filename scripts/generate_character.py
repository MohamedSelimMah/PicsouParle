"""Generate high-quality 2D Picsou character assets via SVG → PNG.

Uses cairosvg for crisp anti-aliased vector rendering with bezier curves,
gradients, and proper cartoon shading.

Run: python scripts/generate_character.py
"""

from pathlib import Path
import cairosvg

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "character"
OUT_W, OUT_H = 600, 900


def _svg_character(mouth_open: bool = False) -> str:
    """Build an SVG string of Uncle Scrooge / Picsou."""

    # Mouth-specific paths
    if mouth_open:
        beak_upper = """
          <path d="M 245,410 Q 300,400 340,410 Q 380,420 395,440
                   Q 370,445 300,448 Q 230,445 205,440 Q 220,420 245,410 Z"
                fill="#E8841A" stroke="#B56010" stroke-width="2.5"/>
        """
        beak_lower = """
          <path d="M 220,448 Q 260,465 300,470 Q 340,465 380,448
                   Q 370,480 300,490 Q 230,480 220,448 Z"
                fill="#D06818" stroke="#A04808" stroke-width="2"/>
        """
        mouth_interior = """
          <ellipse cx="300" cy="455" rx="55" ry="14" fill="#2A0505"/>
          <ellipse cx="300" cy="462" rx="28" ry="10" fill="#CC4040" opacity="0.7"/>
        """
    else:
        beak_upper = """
          <path d="M 245,410 Q 300,400 340,410 Q 385,425 395,445
                   Q 370,450 300,455 Q 230,450 205,445 Q 215,425 245,410 Z"
                fill="#E8841A" stroke="#B56010" stroke-width="2.5"/>
        """
        beak_lower = ""
        mouth_interior = """
          <path d="M 230,440 Q 265,450 300,448 Q 335,450 370,440"
                fill="none" stroke="#B56010" stroke-width="2.5" stroke-linecap="round"/>
        """

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 900" width="600" height="900">
  <defs>
    <!-- Head gradient -->
    <radialGradient id="headGrad" cx="50%" cy="40%" r="55%">
      <stop offset="0%"  stop-color="#FDE8C0"/>
      <stop offset="60%" stop-color="#F5D6A0"/>
      <stop offset="100%" stop-color="#D4A574"/>
    </radialGradient>

    <!-- Coat gradient -->
    <linearGradient id="coatGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="#24507A"/>
      <stop offset="50%" stop-color="#1B3A5C"/>
      <stop offset="100%" stop-color="#0F2540"/>
    </linearGradient>

    <!-- Hat gradient -->
    <linearGradient id="hatGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#2A2A2A"/>
      <stop offset="40%" stop-color="#1A1A1A"/>
      <stop offset="100%" stop-color="#080808"/>
    </linearGradient>

    <!-- Gold gradient -->
    <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#F0D040"/>
      <stop offset="50%" stop-color="#D4A017"/>
      <stop offset="100%" stop-color="#8B6914"/>
    </linearGradient>

    <!-- Lens gradient -->
    <radialGradient id="lensGrad" cx="35%" cy="35%" r="60%">
      <stop offset="0%"  stop-color="white" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#DDEEFF" stop-opacity="0.3"/>
    </radialGradient>

    <!-- Shirt gradient -->
    <linearGradient id="shirtGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E8E4DA"/>
    </linearGradient>

    <!-- Body shadow filter -->
    <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="3" dy="5" stdDeviation="8" flood-color="#000" flood-opacity="0.25"/>
    </filter>

    <filter id="softShadow">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000" flood-opacity="0.15"/>
    </filter>
  </defs>

  <!-- ═══ Ground shadow ═══ -->
  <ellipse cx="300" cy="870" rx="160" ry="25" fill="#000" opacity="0.12"
           filter="url(#softShadow)"/>

  <!-- ═══ Legs ═══ -->
  <g filter="url(#softShadow)">
    <!-- Left leg -->
    <path d="M 240,700 Q 238,760 235,790 Q 233,810 240,820"
          fill="none" stroke="url(#headGrad)" stroke-width="30" stroke-linecap="round"/>
    <!-- Right leg -->
    <path d="M 355,700 Q 357,760 360,790 Q 362,810 355,820"
          fill="none" stroke="url(#headGrad)" stroke-width="30" stroke-linecap="round"/>
    <!-- Left spat -->
    <rect x="222" y="808" width="40" height="30" rx="8" fill="white" stroke="#CCC" stroke-width="1.5"/>
    <rect x="222" y="830" width="42" height="15" rx="6" fill="#3A3A3A"/>
    <!-- Right spat -->
    <rect x="338" y="808" width="40" height="30" rx="8" fill="white" stroke="#CCC" stroke-width="1.5"/>
    <rect x="337" y="830" width="42" height="15" rx="6" fill="#3A3A3A"/>
  </g>

  <!-- ═══ Cane ═══ -->
  <g filter="url(#softShadow)">
    <line x1="175" y1="590" x2="165" y2="850" stroke="#6B4C18" stroke-width="7"
          stroke-linecap="round"/>
    <line x1="176" y1="592" x2="166" y2="848" stroke="#8B6914" stroke-width="4"
          stroke-linecap="round"/>
    <!-- Cane top (gold knob) -->
    <ellipse cx="176" cy="585" rx="12" ry="11" fill="url(#goldGrad)" stroke="#6B4C18"
             stroke-width="2"/>
    <ellipse cx="173" cy="582" rx="4" ry="3" fill="#F0D040" opacity="0.6"/>
  </g>

  <!-- ═══ Body / Tailcoat ═══ -->
  <g filter="url(#shadow)">
    <!-- Coat tails -->
    <path d="M 210,700 Q 195,750 190,790 Q 188,810 200,800 Q 240,760 260,700"
          fill="#162F4A" stroke="#0F2540" stroke-width="2"/>
    <path d="M 390,700 Q 405,750 410,790 Q 412,810 400,800 Q 360,760 340,700"
          fill="#162F4A" stroke="#0F2540" stroke-width="2"/>

    <!-- Main coat -->
    <path d="M 210,480 Q 200,530 198,580 Q 195,650 210,730
             Q 240,740 300,745 Q 360,740 390,730
             Q 405,650 402,580 Q 400,530 390,480
             Q 345,470 300,468 Q 255,470 210,480 Z"
          fill="url(#coatGrad)" stroke="#0F2540" stroke-width="2.5"/>

    <!-- Coat highlight (left edge) -->
    <path d="M 213,490 Q 205,550 203,600 Q 200,660 214,725"
          fill="none" stroke="#2A5A8A" stroke-width="3" opacity="0.4" stroke-linecap="round"/>

    <!-- Left arm -->
    <path d="M 210,490 Q 175,520 160,570 Q 148,615 155,660 Q 160,680 175,688"
          fill="none" stroke="url(#coatGrad)" stroke-width="42" stroke-linecap="round"/>
    <path d="M 210,490 Q 175,520 160,570 Q 148,615 155,660 Q 160,680 175,688"
          fill="none" stroke="#0F2540" stroke-width="44" stroke-linecap="round" opacity="0.15"/>
    <!-- Left hand -->
    <ellipse cx="176" cy="594" rx="18" ry="16"
             fill="#F5D6A0" stroke="#C4A870" stroke-width="2"/>

    <!-- Right arm -->
    <path d="M 390,490 Q 425,520 440,570 Q 452,615 445,660 Q 440,680 425,688"
          fill="none" stroke="url(#coatGrad)" stroke-width="42" stroke-linecap="round"/>
    <path d="M 390,490 Q 425,520 440,570 Q 452,615 445,660 Q 440,680 425,688"
          fill="none" stroke="#0F2540" stroke-width="44" stroke-linecap="round" opacity="0.15"/>
    <!-- Right hand -->
    <ellipse cx="424" cy="594" rx="18" ry="16"
             fill="#F5D6A0" stroke="#C4A870" stroke-width="2"/>

    <!-- Gold coins in right hand -->
    <circle cx="418" cy="588" r="8" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
    <circle cx="430" cy="594" r="7" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
    <circle cx="422" cy="600" r="7" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
  </g>

  <!-- ═══ Shirt front ═══ -->
  <path d="M 270,480 Q 300,475 330,480 L 325,600 Q 300,610 275,600 Z"
        fill="url(#shirtGrad)" stroke="#D0CCB8" stroke-width="1"/>

  <!-- ═══ Bow tie ═══ -->
  <g>
    <path d="M 275,490 Q 285,500 300,505 Q 285,510 275,520 Z" fill="#8B0000"/>
    <path d="M 325,490 Q 315,500 300,505 Q 315,510 325,520 Z" fill="#8B0000"/>
    <circle cx="300" cy="505" r="6" fill="#AA0000"/>
    <circle cx="298" cy="503" r="2" fill="#CC2020" opacity="0.5"/>
  </g>

  <!-- ═══ Buttons ═══ -->
  <g>
    <circle cx="300" cy="545" r="7" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
    <circle cx="298" cy="543" r="2.5" fill="#F0D040" opacity="0.4"/>
    <circle cx="300" cy="595" r="7" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
    <circle cx="298" cy="593" r="2.5" fill="#F0D040" opacity="0.4"/>
    <circle cx="300" cy="645" r="7" fill="url(#goldGrad)" stroke="#6B4C18" stroke-width="1.5"/>
    <circle cx="298" cy="643" r="2.5" fill="#F0D040" opacity="0.4"/>
  </g>

  <!-- ═══ Lapels ═══ -->
  <path d="M 270,480 Q 265,510 250,540 Q 270,520 300,505"
        fill="#244B75" stroke="#1A3A5A" stroke-width="1.5"/>
  <path d="M 330,480 Q 335,510 350,540 Q 330,520 300,505"
        fill="#244B75" stroke="#1A3A5A" stroke-width="1.5"/>

  <!-- ═══ Neck ═══ -->
  <rect x="272" y="440" width="56" height="55" rx="20"
        fill="url(#headGrad)" stroke="none"/>

  <!-- ═══ Head ═══ -->
  <g filter="url(#softShadow)">
    <ellipse cx="300" cy="320" rx="125" ry="145"
             fill="url(#headGrad)" stroke="#C4A068" stroke-width="3"/>
    <!-- Cheek blush -->
    <ellipse cx="220" cy="380" rx="30" ry="18" fill="#E8A080" opacity="0.25"/>
    <ellipse cx="380" cy="380" rx="30" ry="18" fill="#E8A080" opacity="0.25"/>
    <!-- Head highlight -->
    <ellipse cx="280" cy="260" rx="50" ry="30" fill="white" opacity="0.08"/>
  </g>

  <!-- ═══ Sideburns ═══ -->
  <path d="M 185,400 Q 175,420 180,445 Q 185,455 195,450"
        fill="none" stroke="#C4A068" stroke-width="5" stroke-linecap="round"/>
  <path d="M 415,400 Q 425,420 420,445 Q 415,455 405,450"
        fill="none" stroke="#C4A068" stroke-width="5" stroke-linecap="round"/>

  <!-- ═══ Top hat ═══ -->
  <g filter="url(#softShadow)">
    <!-- Brim -->
    <ellipse cx="300" cy="195" rx="140" ry="28"
             fill="url(#hatGrad)" stroke="#000" stroke-width="2.5"/>
    <!-- Crown -->
    <path d="M 225,195 Q 225,60 230,40 Q 260,20 300,15 Q 340,20 370,40
             Q 375,60 375,195"
          fill="url(#hatGrad)" stroke="#000" stroke-width="2.5"/>
    <!-- Hat band -->
    <rect x="227" y="162" width="146" height="28" rx="2"
          fill="#8B0000" stroke="#6A0000" stroke-width="1"/>
    <!-- Band highlight -->
    <line x1="228" y1="165" x2="372" y2="165" stroke="#AA1515" stroke-width="2"/>
    <!-- Crown highlight -->
    <path d="M 240,50 Q 260,38 300,35 Q 310,35 320,38"
          fill="none" stroke="#3A3A3A" stroke-width="4" opacity="0.3" stroke-linecap="round"/>
    <!-- Crown left highlight -->
    <line x1="232" y1="60" x2="228" y2="185" stroke="#2A2A2A" stroke-width="4" opacity="0.4"/>
  </g>

  <!-- ═══ Glasses ═══ -->
  <g>
    <!-- Left lens -->
    <ellipse cx="258" cy="315" rx="42" ry="38"
             fill="url(#lensGrad)" stroke="#2A2A2A" stroke-width="4"/>
    <!-- Right lens -->
    <ellipse cx="342" cy="315" rx="42" ry="38"
             fill="url(#lensGrad)" stroke="#2A2A2A" stroke-width="4"/>
    <!-- Bridge -->
    <path d="M 298,315 Q 300,310 302,315" fill="none"
          stroke="#2A2A2A" stroke-width="4"/>
    <!-- Left temple -->
    <line x1="218" y1="310" x2="185" y2="298" stroke="#2A2A2A" stroke-width="3.5"/>
    <!-- Right temple -->
    <line x1="382" y1="310" x2="415" y2="298" stroke="#2A2A2A" stroke-width="3.5"/>
    <!-- Lens reflections -->
    <ellipse cx="245" cy="305" rx="12" ry="8" fill="white" opacity="0.2"/>
    <ellipse cx="330" cy="305" rx="12" ry="8" fill="white" opacity="0.2"/>
  </g>

  <!-- ═══ Eyes ═══ -->
  <g>
    <!-- Left eye -->
    <ellipse cx="258" cy="315" rx="18" ry="20" fill="white"/>
    <ellipse cx="262" cy="318" rx="10" ry="12" fill="#1A1A1A"/>
    <ellipse cx="258" cy="312" rx="4" ry="5" fill="white" opacity="0.8"/>
    <!-- Right eye -->
    <ellipse cx="342" cy="315" rx="18" ry="20" fill="white"/>
    <ellipse cx="338" cy="318" rx="10" ry="12" fill="#1A1A1A"/>
    <ellipse cx="342" cy="312" rx="4" ry="5" fill="white" opacity="0.8"/>
  </g>

  <!-- ═══ Eyebrows (grumpy / angled inward) ═══ -->
  <g>
    <path d="M 218,275 Q 240,268 275,280"
          fill="none" stroke="#7A5C18" stroke-width="7" stroke-linecap="round"/>
    <path d="M 218,275 Q 240,269 275,280"
          fill="none" stroke="#9A7A28" stroke-width="3.5" stroke-linecap="round"/>
    <path d="M 382,275 Q 360,268 325,280"
          fill="none" stroke="#7A5C18" stroke-width="7" stroke-linecap="round"/>
    <path d="M 382,275 Q 360,269 325,280"
          fill="none" stroke="#9A7A28" stroke-width="3.5" stroke-linecap="round"/>
  </g>

  <!-- ═══ Beak ═══ -->
  {beak_upper}
  {mouth_interior}
  {beak_lower}

  <!-- ═══ Monocle chain ═══ -->
  <path d="M 384,330 Q 400,380 410,440 Q 415,470 408,500"
        fill="none" stroke="#D4A017" stroke-width="2" stroke-dasharray="5,4"
        opacity="0.6"/>

  <!-- ═══ Coin bag at hip ═══ -->
  <g transform="translate(395,650)" filter="url(#softShadow)">
    <ellipse cx="0" cy="0" rx="25" ry="22" fill="#6B3410" stroke="#3A1A00" stroke-width="2"/>
    <path d="M -12,-20 Q 0,-28 12,-20" fill="none" stroke="#3A1A00" stroke-width="3"
          stroke-linecap="round"/>
    <circle cx="0" cy="2" r="10" fill="url(#goldGrad)" opacity="0.7"/>
    <text x="0" y="7" font-family="serif" font-weight="bold" font-size="14"
          fill="#6B4C18" text-anchor="middle">$</text>
  </g>

</svg>"""


def generate(mouth_open: bool, output: Path) -> None:
    svg = _svg_character(mouth_open)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(output),
                     output_width=OUT_W, output_height=OUT_H)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    generate(False, ASSET_DIR / "picsou_mouth_closed.png")
    print("✓ picsou_mouth_closed.png")

    generate(True, ASSET_DIR / "picsou_mouth_open.png")
    print("✓ picsou_mouth_open.png")

    print(f"✓ Saved in {ASSET_DIR}")


if __name__ == "__main__":
    main()
