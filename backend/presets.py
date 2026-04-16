"""Background visual presets — single source of truth."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackgroundPreset:
    label: str
    description: str
    gradient_top: str
    gradient_bottom: str
    ai_prompt: str


BACKGROUND_PRESETS: dict[str, BackgroundPreset] = {
    "luxury_car": BackgroundPreset(
        label="Luxury Car",
        description="Gold interior, city lights, wealthy night-drive mood.",
        gradient_top="#0D0A04",
        gradient_bottom="#1A1408",
        ai_prompt=(
            "luxury car interior, rich gold leather seats, steering wheel visible, "
            "night city bokeh lights through windshield, premium cinematic mood, "
            "black and gold palette, warm ambient lighting"
        ),
    ),
    "seaside": BackgroundPreset(
        label="Seaside",
        description="Sunset ocean view, calm luxury, villa lifestyle mood.",
        gradient_top="#0A1628",
        gradient_bottom="#1A2A3A",
        ai_prompt=(
            "luxury seaside villa terrace, panoramic ocean view, golden sunset sky, "
            "blue and orange tones, calm wealthy lifestyle, elegant warm atmosphere, "
            "mediterranean architecture"
        ),
    ),
}

DEFAULT_BACKGROUND_MODE = "luxury_car"

VALID_BACKGROUND_MODES = list(BACKGROUND_PRESETS.keys())
