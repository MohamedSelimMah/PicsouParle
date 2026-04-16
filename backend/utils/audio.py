"""Audio amplitude analysis for mouth animation."""

from __future__ import annotations

import logging
import math
import struct
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000  # 16kHz mono — sufficient for voice amplitude


def extract_amplitudes(audio_path: Path, fps: int = 30) -> list[float]:
    """Extract RMS amplitude per video frame from audio.

    Uses FFmpeg to decode to raw PCM, then computes RMS per frame interval.
    Returns normalized amplitudes (0.0 to 1.0).
    """
    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE),
        "-v", "quiet", "pipe:1",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio decode failed: {result.stderr.decode()[-500:]}")

    pcm = result.stdout
    samples_per_frame = SAMPLE_RATE // fps
    bytes_per_frame = samples_per_frame * 2  # 16-bit = 2 bytes/sample

    amplitudes: list[float] = []
    for i in range(0, len(pcm) - bytes_per_frame + 1, bytes_per_frame):
        chunk = pcm[i:i + bytes_per_frame]
        n_samples = len(chunk) // 2
        if n_samples == 0:
            break
        samples = struct.unpack(f"<{n_samples}h", chunk)
        rms = math.sqrt(sum(s * s for s in samples) / n_samples)
        amplitudes.append(rms)

    # Normalize to 0–1
    if amplitudes:
        peak = max(amplitudes)
        if peak > 0:
            amplitudes = [a / peak for a in amplitudes]

    logger.info(f"Extracted {len(amplitudes)} amplitude values at {fps}fps")
    return amplitudes


def compute_adaptive_threshold(amplitudes: list[float], factor: float = 0.6) -> float:
    """Adaptive threshold for mouth open/close detection.

    Uses mean * factor so it adapts to different voice volumes.
    """
    if not amplitudes:
        return 0.3
    mean_amp = sum(amplitudes) / len(amplitudes)
    threshold = mean_amp * factor
    logger.info(f"Adaptive threshold: {threshold:.3f} (mean={mean_amp:.3f}, factor={factor})")
    return threshold
