"""Tests for MidSideStereoWidener effect."""

import numpy as np
import pytest

from openmusic.effects.stereo import MidSideStereoWidener


class TestMidSideStereoWidener:

    def setup_method(self):
        self.effect = MidSideStereoWidener()

    def test_initialization(self):
        assert self.effect.name == "mid_side_widener"

    def _make_stereo(self, left, right):
        return np.column_stack([left, right])

    def test_process_stereo_audio(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = self._make_stereo(left, right)

        params = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": {},
            "side_compression": {},
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[1] == 2

    def test_mono_audio_passed_through(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        np.testing.assert_allclose(output, audio)

    def test_stereo_width_normal(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = self._make_stereo(left, right)
        params = {"stereo_width": 1.0, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        np.testing.assert_allclose(output, audio, rtol=1e-3, atol=1e-15)

    def test_stereo_width_narrow(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = -left
        audio = self._make_stereo(left, right)

        output_normal = self.effect.process(audio.copy(), {"stereo_width": 1.0, "sample_rate": 48000})
        output_narrow = self.effect.process(audio.copy(), {"stereo_width": 0.5, "sample_rate": 48000})

        diff_normal = np.mean(np.abs(output_normal[:, 0] - output_normal[:, 1]))
        diff_narrow = np.mean(np.abs(output_narrow[:, 0] - output_narrow[:, 1]))
        assert diff_narrow < diff_normal

    def test_stereo_width_wide(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = left * 0.98
        audio = self._make_stereo(left, right)

        output_normal = self.effect.process(audio.copy(), {"stereo_width": 1.0, "sample_rate": 48000})
        output_wide = self.effect.process(audio.copy(), {"stereo_width": 1.5, "sample_rate": 48000})

        diff_normal = np.mean(np.abs(output_normal[:, 0] - output_normal[:, 1]))
        diff_wide = np.mean(np.abs(output_wide[:, 0] - output_wide[:, 1]))
        assert diff_wide > diff_normal

    def test_stereo_width_clamped_to_range(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = self._make_stereo(left, right)

        output_min = self.effect.process(audio.copy(), {"stereo_width": -1.0, "sample_rate": 48000})
        output_max = self.effect.process(audio.copy(), {"stereo_width": 3.0, "sample_rate": 48000})
        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_mid_eq_affects_mid_channel(self):
        left = np.ones(48000) * 0.5
        right = np.ones(48000) * 0.5
        audio = self._make_stereo(left, right)

        mid_eq = {"frequency": 1000, "gain_db": -20, "Q": 1.0}
        params_with = {"stereo_width": 1.0, "mid_eq": mid_eq, "side_eq": {}, "side_compression": {}, "sample_rate": 48000}
        params_without = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with = self.effect.process(audio.copy(), params_with)
        output_without = self.effect.process(audio.copy(), params_without)
        assert not np.allclose(output_with, output_without)

    def test_side_eq_affects_side_channel(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = -left
        audio = self._make_stereo(left, right)

        side_eq = {"frequency": 1000, "gain_db": -20, "Q": 1.0}
        params_with = {"stereo_width": 1.0, "mid_eq": {}, "side_eq": side_eq, "side_compression": {}, "sample_rate": 48000}
        params_without = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with = self.effect.process(audio.copy(), params_with)
        output_without = self.effect.process(audio.copy(), params_without)
        assert not np.allclose(output_with, output_without)

    def test_side_compression_affects_side_channel(self):
        audio = np.zeros((48000, 2))
        audio[12000:24000, 0] = 0.8
        audio[12000:24000, 1] = -0.8
        audio += np.random.randn(48000, 2) * 0.1

        side_comp = {"threshold_db": -6, "ratio": 4, "attack_ms": 10, "release_ms": 200}
        params_with = {"stereo_width": 1.0, "mid_eq": {}, "side_eq": {}, "side_compression": side_comp, "sample_rate": 48000}
        params_without = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with = self.effect.process(audio.copy(), params_with)
        output_without = self.effect.process(audio.copy(), params_without)
        assert not np.allclose(output_with, output_without)

    def test_default_parameters(self):
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = self._make_stereo(left, right)
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_zero_input(self):
        audio = np.zeros((48000, 2))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert np.allclose(output, 0)

    def test_empty_audio(self):
        audio = np.zeros((0, 2))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_equivalent_mono_to_stereo_conversion(self):
        mono = np.sin(np.linspace(0, 4 * np.pi, 48000))
        stereo = self._make_stereo(mono, mono)
        output = self.effect.process(stereo, {"stereo_width": 1.0, "sample_rate": 48000})
        np.testing.assert_allclose(output[:, 0], output[:, 1])

    def test_mid_side_decode_reversibility(self):
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = self._make_stereo(left, right)
        output = self.effect.process(audio, {"stereo_width": 1.0, "sample_rate": 48000})
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_mid_eq_parameters_clamped(self):
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = self._make_stereo(left, right)

        eq = {"frequency": 1000, "gain_db": 0, "Q": 1.0}
        params = {"stereo_width": 1.0, "mid_eq": eq, "side_eq": eq, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_compression_parameters_clamped(self):
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = self._make_stereo(left, right)

        comp = {"threshold_db": -20, "ratio": 4, "attack_ms": 10, "release_ms": 200}
        params = {"stereo_width": 1.0, "mid_eq": {}, "side_eq": {}, "side_compression": comp, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_different_sample_rates(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = self._make_stereo(left, right)

        audio_44k = audio[:44100]
        audio_96k = np.random.randn(96000, 2) * 0.1

        output_48k = self.effect.process(audio.copy(), {"stereo_width": 1.0, "sample_rate": 48000})
        output_44k = self.effect.process(audio_44k, {"stereo_width": 1.0, "sample_rate": 44100})
        output_96k = self.effect.process(audio_96k, {"stereo_width": 1.0, "sample_rate": 96000})

        assert output_48k.shape == audio.shape
        assert output_44k.shape == audio_44k.shape
        assert output_96k.shape == audio_96k.shape

    def test_width_zero_creates_mono(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = self._make_stereo(left, right)
        output = self.effect.process(audio, {"stereo_width": 0.0, "sample_rate": 48000})
        np.testing.assert_allclose(output[:, 0], output[:, 1])

    def test_width_two_extreme_stereo(self):
        mid = np.ones(48000) * 0.3
        side = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.3
        left = (mid + side) / np.sqrt(2)
        right = (mid - side) / np.sqrt(2)
        audio = self._make_stereo(left, right)

        output_normal = self.effect.process(audio.copy(), {"stereo_width": 1.0, "sample_rate": 48000})
        output_wide = self.effect.process(audio.copy(), {"stereo_width": 2.0, "sample_rate": 48000})

        diff_normal = np.mean(np.abs(output_normal[:, 0] - output_normal[:, 1]))
        diff_wide = np.mean(np.abs(output_wide[:, 0] - output_wide[:, 1]))
        assert diff_wide > diff_normal

    def test_invalid_channel_count_raises_error(self):
        audio = np.random.randn(48000, 3)
        params = {"sample_rate": 48000}
        with pytest.raises(ValueError, match="stereo audio"):
            self.effect.process(audio, params)

    def test_mid_and_side_eq_independent(self):
        mid_content = np.ones(48000) * 0.5
        side_content = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        left = (mid_content + side_content) / np.sqrt(2)
        right = (mid_content - side_content) / np.sqrt(2)
        audio = self._make_stereo(left, right)

        params = {
            "stereo_width": 1.0,
            "mid_eq": {"frequency": 100, "gain_db": -10, "Q": 1.0},
            "side_eq": {"frequency": 5000, "gain_db": -10, "Q": 1.0},
            "side_compression": {},
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert not np.allclose(output, audio)

    def test_side_compression_does_not_affect_mid(self):
        left = np.ones(48000) * 0.5
        right = np.ones(48000) * 0.5
        audio = self._make_stereo(left, right)

        comp = {"threshold_db": -20, "ratio": 4, "attack_ms": 10, "release_ms": 200}
        params_no_comp = {"stereo_width": 1.0, "sample_rate": 48000}
        params_with_comp = {"stereo_width": 1.0, "mid_eq": {}, "side_eq": {}, "side_compression": comp, "sample_rate": 48000}

        output_no_comp = self.effect.process(audio.copy(), params_no_comp)
        output_with_comp = self.effect.process(audio.copy(), params_with_comp)
        np.testing.assert_allclose(output_no_comp, output_with_comp, rtol=1e-5)
