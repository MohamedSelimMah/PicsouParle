from __future__ import annotations

import dataclasses
from pathlib import Path

from backend.pipeline.models import Script, TimestampedWord, SubtitleGroup


@dataclasses.dataclass
class PipelineContext:
    """Mutable state passed through each pipeline step."""

    run_id: str
    prompt: str

    # Step outputs — filled progressively
    script: Script | None = None
    full_text: str = ""

    audio_path: Path | None = None
    audio_duration: float = 0.0

    timestamps: list[TimestampedWord] = dataclasses.field(default_factory=list)
    subtitle_groups: list[SubtitleGroup] = dataclasses.field(default_factory=list)

    # Audio analysis for mouth animation
    amplitudes: list[float] = dataclasses.field(default_factory=list)
    amplitude_threshold: float = 0.3

    visuals_dir: Path | None = None
    video_path: Path | None = None

    # Run metadata
    status: str = "pending"
    current_step: str = ""
    error: str | None = None
