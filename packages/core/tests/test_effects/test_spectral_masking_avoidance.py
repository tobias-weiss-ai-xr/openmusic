"""Tests for SpectralMaskingAvoidance effect."""

import numpy as np
import pytest

from openmusic.effects.spectral_masking_avoidance import (
    SpectralMaskingAvoidance,
)


class TestSpectralMaskingAvoidance:

    def setup_method(self):
        self.effect = SpectralMaskingAvoidance()

    def test_initialization(self):
        assert self.effect.name == "spectral_masking_avoidance"

    def test_process_mono_audio(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_process_stereo_audio(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right], axis=0)
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert output.shape[0] == 2

    def test_high_sensitivity_carves_more(self):
        np.random.seed(42)
        audio = np.random.randn(48000) * 0.5
        params_low = {"sensitivity": 0, "sample_rate": 48000}
        params_high = {"sensitivity": 100, "sample_rate": 48000}
        out_low = self.effect.process(audio, params_low)
        out_high = self.effect.process(audio, params_high)
        rms_low = np.sqrt(np.mean(out_low**2))
        rms_high = np.sqrt(np.mean(out_high**2))
        assert rms_high < rms_low, (
            "Higher sensitivity should produce more spectral carving"
        )

    def test_max_cut_db_limits_reduction(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params = {
            "sensitivity": 100,
            "max_cut_db": 3,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        max_gain_reduction = 10.0 ** (-3.0 / 20.0)
        rms_in = np.sqrt(np.mean(audio**2))
        rms_out = np.sqrt(np.mean(output**2))
        if rms_in > 1e-10:
            ratio = rms_out / rms_in
            assert ratio >= max_gain_reduction * 0.9, (
                f"RMS ratio {ratio:.4f} below expected {max_gain_reduction:.4f}"
            )

    def test_frequency_range_limits_processing(self):
        t = np.linspace(0, 1, 48000, endpoint=False)
        audio = np.sin(2 * np.pi * 200 * t)
        params_high = {
            "frequency_range": [5000, 20000],
            "sensitivity": 100,
            "max_cut_db": 12,
            "sample_rate": 48000,
        }
        output_high = self.effect.process(audio, params_high)
        rms_in = np.sqrt(np.mean(audio**2))
        rms_out_high = np.sqrt(np.mean(output_high**2))
        assert rms_out_high > rms_in * 0.95, (
            "Signal outside frequency range should be mostly preserved"
        )

    def test_auto_detect_true(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params = {"auto_detect": True, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_auto_detect_false(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params = {"auto_detect": False, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_empty_audio(self):
        audio = np.zeros((0,))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_zero_input(self):
        audio = np.zeros(48000)
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape
        assert np.allclose(output, 0)

    def test_default_parameters(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_different_sample_rates(self):
        for sr in [44100, 48000, 96000]:
            audio = np.sin(np.linspace(0, 2 * np.pi, sr))
            params = {"sample_rate": sr}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_stereo_independent_processing(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        right = np.cos(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        audio = np.stack([left, right], axis=0)
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert not np.allclose(output[0, :], output[1, :])

    def test_notch_width_factor(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params_narrow = {
            "notch_width_factor": 0.1,
            "sensitivity": 100,
            "sample_rate": 48000,
        }
        params_wide = {
            "notch_width_factor": 1.0,
            "sensitivity": 100,
            "sample_rate": 48000,
        }
        out_narrow = self.effect.process(audio, params_narrow)
        out_wide = self.effect.process(audio, params_wide)
        assert not np.allclose(out_narrow, out_wide), (
            "Different notch widths should produce different results"
        )

    def test_process_preserves_finite(self):
        audio = np.random.randn(48000) * 0.5
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert np.all(np.isfinite(output))

    def test_very_short_audio(self):
        audio = np.sin(np.linspace(0, np.pi, 256))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_very_long_audio(self):
        audio = np.sin(np.linspace(0, 16 * np.pi, 96000))
        params = {
            "window_size": 2048,
            "hop_size": 512,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_custom_window_and_hop_size(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "window_size": 1024,
            "hop_size": 256,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_parameter_clamping_sensitivity(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "sensitivity": 200,
            "max_cut_db": 50,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert np.all(np.isfinite(output))
        assert output.shape == audio.shape

    def test_different_dtype_preserved(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000)).astype(np.float32)
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.dtype == np.float32
