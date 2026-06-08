"""Tests for export.loudness module."""

import numpy as np
import pytest

from openmusic.export.loudness import (
    measure_integrated_loudness,
    normalize_loudness,
    LUFS_TARGET,
)


class TestMeasureIntegratedLoudness:
    def test_returns_float(self):
        audio = np.random.randn(48000, 2).astype(np.float64)
        result = measure_integrated_loudness(audio, 48000)
        assert isinstance(result, float)

    def test_silence_returns_low_value(self):
        audio = np.zeros((48000, 2), dtype=np.float64)
        result = measure_integrated_loudness(audio, 48000)
        assert result < -40.0

    def test_full_scale_sine_measurement(self):
        t = np.linspace(0, 1, 48000, endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        audio = np.column_stack([audio, audio])
        result = measure_integrated_loudness(audio, 48000)
        assert -10.0 < result < -3.0

    def test_mono_input_raises(self):
        audio = np.random.randn(48000).astype(np.float64)
        with pytest.raises(ValueError, match="2D array with shape"):
            measure_integrated_loudness(audio, 48000)

    def test_single_channel_raises(self):
        audio = np.random.randn(48000, 1).astype(np.float64)
        with pytest.raises(ValueError, match="at least 2 channels"):
            measure_integrated_loudness(audio, 48000)

    def test_3plus_channels_raises(self):
        audio = np.random.randn(48000, 4).astype(np.float64)
        with pytest.raises(ValueError, match="Expected 2 channels"):
            measure_integrated_loudness(audio, 48000)


class TestNormalizeLoudness:
    def test_returns_same_shape(self):
        audio = np.random.randn(48000, 2).astype(np.float64)
        result = normalize_loudness(audio, 48000, target=-16.0)
        assert result.shape == audio.shape
        assert result.dtype == np.float64

    def test_normalizes_to_target(self):
        import pyloudnorm

        audio = (np.random.randn(48000, 2) * 0.01).astype(np.float64)
        result = normalize_loudness(audio, 48000, target=-23.0)
        measured = pyloudnorm.Meter(48000).integrated_loudness(result)
        assert abs(measured - (-23.0)) < 1.0

    def test_default_target_is_neg_14(self):
        import pyloudnorm

        audio = (np.random.randn(48000, 2) * 0.01).astype(np.float64)
        result = normalize_loudness(audio, 48000)
        measured = pyloudnorm.Meter(48000).integrated_loudness(result)
        assert abs(measured - (-14.0)) < 1.0

    def test_silence_returns_unchanged(self):
        audio = np.zeros((48000, 2), dtype=np.float64)
        result = normalize_loudness(audio, 48000, target=-14.0)
        assert np.all(result == 0.0)
        assert not np.any(np.isnan(result))

    def test_clips_properly(self):
        rng = np.random.default_rng(42)
        audio = rng.normal(0, 0.1, (48000, 2)).astype(np.float64)
        result = normalize_loudness(audio, 48000, target=0.0)
        assert np.max(np.abs(result)) <= 1.0
        assert np.any(np.abs(result) >= 0.999)

    def test_identity_at_target(self):
        t = np.linspace(0, 1, 48000, endpoint=False)
        audio = 0.25 * np.sin(2 * np.pi * 440 * t)
        audio = np.column_stack([audio, audio])
        normalized = normalize_loudness(audio, 48000, target=-20.0)
        normalized2 = normalize_loudness(normalized, 48000, target=-20.0)
        assert np.max(np.abs(normalized - normalized2)) < 0.01
