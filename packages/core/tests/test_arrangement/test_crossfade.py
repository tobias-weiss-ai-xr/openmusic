"""Tests for crossfade utilities."""

import numpy as np
import pytest

from openmusic.arrangement.crossfade import crossfade_numpy, generate_crossfade_curve


class TestGenerateCrossfadeCurve:
    def test_linear_curve(self):
        samples = 100
        fade_in, fade_out = generate_crossfade_curve(samples, "linear")
        assert len(fade_in) == samples
        assert len(fade_out) == samples
        np.testing.assert_array_almost_equal(fade_in, np.linspace(0.0, 1.0, samples))
        np.testing.assert_array_almost_equal(fade_out, np.linspace(1.0, 0.0, samples))

    def test_equal_power_curve(self):
        samples = 100
        fade_in, fade_out = generate_crossfade_curve(samples, "equal_power")
        assert len(fade_in) == samples
        assert len(fade_out) == samples
        # Equal power: sin^2 for fade in, cos^2 for fade out
        expected_in = np.sin(np.linspace(0, np.pi / 2, samples)) ** 2
        expected_out = np.cos(np.linspace(0, np.pi / 2, samples)) ** 2
        np.testing.assert_array_almost_equal(fade_in, expected_in)
        np.testing.assert_array_almost_equal(fade_out, expected_out)

    def test_sine_curve(self):
        samples = 100
        fade_in, fade_out = generate_crossfade_curve(samples, "sine")
        assert len(fade_in) == samples
        assert len(fade_out) == samples
        expected_in = np.sin(np.linspace(0, np.pi / 2, samples))
        expected_out = np.cos(np.linspace(0, np.pi / 2, samples))
        np.testing.assert_array_almost_equal(fade_in, expected_in)
        np.testing.assert_array_almost_equal(fade_out, expected_out)

    def test_invalid_curve_type_raises(self):
        with pytest.raises(ValueError, match="curve_type"):
            generate_crossfade_curve(100, "invalid")

    def test_curve_boundaries(self):
        """Fade in starts at 0, ends at 1. Fade out starts at 1, ends at 0."""
        samples = 100
        for curve_type in ["linear", "equal_power", "sine"]:
            fade_in, fade_out = generate_crossfade_curve(samples, curve_type)
            assert abs(fade_in[0]) < 1e-10
            assert abs(fade_in[-1] - 1.0) < 1e-10
            assert abs(fade_out[0] - 1.0) < 1e-10
            assert abs(fade_out[-1]) < 1e-10

    def test_single_sample_curve(self):
        fade_in, fade_out = generate_crossfade_curve(1, "linear")
        assert len(fade_in) == 1
        assert len(fade_out) == 1


class TestCrossfadeNumpy:
    def test_crossfade_mono(self):
        sample_rate = 48000
        fade_dur = 0.1
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.ones(fade_samples, dtype=np.float64)
        audio_b = np.ones(fade_samples, dtype=np.float64) * 0.5

        result = crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "linear")
        assert len(result) == fade_samples

    def test_crossfade_stereo(self):
        sample_rate = 48000
        fade_dur = 0.01
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.ones((fade_samples, 2), dtype=np.float64)
        audio_b = np.ones((fade_samples, 2), dtype=np.float64) * 0.5

        result = crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "linear")
        assert result.shape == (fade_samples, 2)

    def test_crossfade_output_within_range(self):
        """Output should not clip beyond input ranges."""
        sample_rate = 48000
        fade_dur = 0.01
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.ones(fade_samples, dtype=np.float64)
        audio_b = np.ones(fade_samples, dtype=np.float64) * 0.5

        result = crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "equal_power")
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_crossfade_starts_with_audio_a(self):
        """First sample should be mostly audio_a."""
        sample_rate = 48000
        fade_dur = 0.01
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.full(fade_samples, 1.0)
        audio_b = np.full(fade_samples, 0.0)

        result = crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "linear")
        np.testing.assert_almost_equal(result[0], 1.0)

    def test_crossfade_ends_with_audio_b(self):
        """Last sample should be mostly audio_b."""
        sample_rate = 48000
        fade_dur = 0.01
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.full(fade_samples, 1.0)
        audio_b = np.full(fade_samples, 0.0)

        result = crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "linear")
        np.testing.assert_almost_equal(result[-1], 0.0)

    def test_crossfade_different_lengths_raises(self):
        sample_rate = 48000
        fade_dur = 0.01
        fade_samples = int(sample_rate * fade_dur)

        audio_a = np.ones(fade_samples, dtype=np.float64)
        audio_b = np.ones(fade_samples + 10, dtype=np.float64)

        with pytest.raises(ValueError, match="same length"):
            crossfade_numpy(audio_a, audio_b, fade_dur, sample_rate, "linear")

    def test_crossfade_fade_too_long_raises(self):
        """fade_duration longer than audio arrays should raise."""
        sample_rate = 48000
        fade_dur = 0.1
        fade_samples = int(sample_rate * fade_dur)

        short_audio = np.ones(100, dtype=np.float64)

        with pytest.raises(ValueError):
            crossfade_numpy(short_audio, short_audio, fade_dur, sample_rate, "linear")
