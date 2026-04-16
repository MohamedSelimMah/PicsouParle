"""Tests for audio amplitude analysis utilities."""

import math
import pytest

from backend.utils.audio import compute_adaptive_threshold


def test_threshold_empty_returns_default():
    assert compute_adaptive_threshold([]) == pytest.approx(0.3)


def test_threshold_scales_with_mean():
    amps = [0.2, 0.4, 0.6, 0.8]
    mean = sum(amps) / len(amps)  # 0.5
    threshold = compute_adaptive_threshold(amps, factor=0.6)
    assert threshold == pytest.approx(mean * 0.6, rel=1e-5)


def test_threshold_custom_factor():
    amps = [0.5, 0.5, 0.5, 0.5]
    threshold = compute_adaptive_threshold(amps, factor=1.0)
    assert threshold == pytest.approx(0.5, rel=1e-5)


def test_threshold_all_zeros():
    # All-zero amplitudes → mean = 0 → threshold = 0
    threshold = compute_adaptive_threshold([0.0, 0.0, 0.0])
    assert threshold == pytest.approx(0.0)


def test_threshold_single_value():
    threshold = compute_adaptive_threshold([0.8], factor=0.6)
    assert threshold == pytest.approx(0.8 * 0.6, rel=1e-5)
