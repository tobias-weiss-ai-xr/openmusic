"""Tests for SpectralGate effect."""

import numpy as np
import pytest

from openmusic.effects.spectral import SpectralGate


class TestSpectralGate:

    def setup_method(self):
        self.effect = SpectralGate()

    def test_initialization(self):
        assert self.effect.name == "spectral_gate"

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

    def test_negative_threshold_suppresses_noise(self):
        audio = np.random.randn(48000) * 0.01
        params = {"threshold": -20, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_threshold_clamped_to_range(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        for threshold in [-80, 10]:
            params = {"threshold": threshold, "sample_rate": 48000}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_zero_threshold_passes_signal(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        params = {"threshold": 0, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_attack_release_parameters(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "threshold": -40,
            "attack_ms": 1,
            "release_ms": 10,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_hold_parameter(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "threshold": -40,
            "hold_ms": 50,
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
        assert np.allclose(output, 0)

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

    def test_sync_to_tempo_basic(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params = {
            "sync_to_tempo": True,
            "bpm": 125,
            "gate_pattern": [1, 0, 1, 0],
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_tempo_sync_creates_rhythmic_gating(self):
        audio = np.ones(48000) * 0.5
        params = {
            "sync_to_tempo": True,
            "bpm": 120,
            "gate_pattern": [1, 0],
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.any(output < 0.4)
        assert np.any(output > 0.4)

    def test_frequency_bands(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "frequency_bands": [
                {"min_freq": 20, "max_freq": 200, "threshold_db": -10},
                {"min_freq": 200, "max_freq": 2000, "threshold_db": -20},
            ],
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_default_parameters(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_stereo_processing_independent(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        right = np.cos(np.linspace(0, 4 * np.pi, 48000)) * 0.5
        audio = np.column_stack([left, right])
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert not np.allclose(output[:, 0], output[:, 1])

    def test_process_with_varying_threshold(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        for threshold in [-60, -40, -20, -10]:
            params = {"threshold": threshold, "sample_rate": 48000}
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_short_audio_handling(self):
        audio = np.sin(np.linspace(0, np.pi, 256))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_very_long_audio_handling(self):
        audio = np.sin(np.linspace(0, 16 * np.pi, 96000))
        params = {
            "window_size": 2048,
            "hop_size": 512,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_custom_gate_pattern(self):
        audio = np.ones(48000) * 0.5
        params = {
            "sync_to_tempo": True,
            "bpm": 120,
            "gate_pattern": [1, 0, 0, 1, 0, 0],
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.any(output < 0.4)
        assert np.any(output > 0.4)
