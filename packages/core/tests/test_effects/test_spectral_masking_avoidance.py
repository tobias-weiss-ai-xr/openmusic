"""Tests for FrequencyMaskingAvoidance effect."""

import numpy as np
import pytest

from openmusic.effects.spectral_masking_avoidance import FrequencyMaskingAvoidance


class TestFrequencyMaskingAvoidance:

    def setup_method(self):
        self.effect = FrequencyMaskingAvoidance()

    def test_initialization(self):
        assert self.effect.name == "frequency_masking_avoidance"

    def test_process_mono_audio(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_process_stereo_audio(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.column_stack([left, right])
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert output.shape[1] == 2

    def test_default_parameters(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_sensitivity_zero_has_minimal_effect(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sensitivity": 0, "sample_rate": 48000}
        output = self.effect.process(audio.copy(), params)
        assert np.allclose(output, audio, rtol=1e-3)

    def test_sensitivity_max_applies_notching(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sensitivity": 100, "sample_rate": 48000}
        output = self.effect.process(audio.copy(), params)
        assert output.shape == audio.shape

    def test_with_conflict_frequencies(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "conflict_frequencies": [200, 500, 2000],
            "auto_detect": False,
            "max_cut_db": 6,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_auto_detect_true_without_conflict_frequencies(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "auto_detect": True,
            "num_peaks": 3,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_empty_audio(self):
        audio = np.zeros((0,))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_zero_input(self):
        audio = np.zeros(48000)
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape
        assert np.allclose(output, 0, atol=1e-6)

    def test_different_sample_rates(self):
        for sr in [44100, 48000, 96000]:
            audio = np.sin(np.linspace(0, 2 * np.pi, sr))
            params = {"sample_rate": sr}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_window_and_hop_size(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "window_size": 1024,
            "hop_size": 256,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_max_cut_db_limits(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        for cut in [0, 3, 12, 24]:
            params = {"max_cut_db": cut, "sample_rate": 48000}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape
            assert np.all(np.isfinite(output))

    def test_sensitivity_range(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        for sens in [0, 25, 50, 75, 100]:
            params = {"sensitivity": sens, "sample_rate": 48000}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_frequency_range_limits(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "frequency_range": (100, 8000),
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_stereo_processing_preserves_shape(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        right = np.cos(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        audio = np.column_stack([left, right])
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_short_audio_handling(self):
        audio = np.sin(np.linspace(0, np.pi, 256))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_very_long_audio_handling(self):
        audio = np.sin(np.linspace(0, 16 * np.pi, 96000))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_num_peaks_parameter(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        for peaks in [1, 3, 5]:
            params = {
                "num_peaks": peaks,
                "auto_detect": True,
                "sample_rate": 48000,
            }
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_bandwidth_parameter(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        for bw in [10, 50, 200]:
            params = {
                "bandwidth": bw,
                "conflict_frequencies": [500],
                "auto_detect": False,
                "sample_rate": 48000,
            }
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_output_clipped_to_valid_range(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params = {
            "sensitivity": 100,
            "max_cut_db": 12,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert np.all(output >= -1.0)
        assert np.all(output <= 1.0)

    def test_detect_peaks_no_frequencies_in_range(self):
        audio = np.zeros(48000)
        audio[10000:11000] = np.sin(np.linspace(0, 2 * np.pi, 1000))
        params = {
            "frequency_range": (20000, 22000),
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_default_center_frequencies(self):
        centers = FrequencyMaskingAvoidance._default_center_frequencies(20, 16000)
        assert len(centers) > 0
        assert all(20 <= f <= 16000 for f in centers)
        assert centers == sorted(centers)
