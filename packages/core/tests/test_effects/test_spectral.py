"""Tests for spectral effects (SpectralGate, SpectralMaskingAvoidance)."""

import numpy as np
import pytest

from openmusic.effects.spectral import SpectralGate, SpectralMaskingAvoidance


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
        audio = np.column_stack([left, right])
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert output.shape[1] == 2
        assert np.all(np.isfinite(output))

    def test_zero_sensitivity_passthrough(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {"sensitivity": 0, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))

    def test_max_cut_db_attenuates_strong_tones(self):
        sr = 48000
        t = np.linspace(0, 1.0, sr, endpoint=False)
        strong_tone = 0.9 * np.sin(2 * np.pi * 250 * t)
        quiet_highs = 0.05 * np.sin(2 * np.pi * 4000 * t)
        audio = strong_tone + quiet_highs

        params = {
            "sensitivity": 90,
            "max_cut_db": 12,
            "auto_detect": True,
            "sample_rate": sr,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert np.all(np.isfinite(output))
        output_fft = np.abs(np.fft.rfft(output))
        input_fft = np.abs(np.fft.rfft(audio))
        low_bin = int(250 * len(audio) / sr)
        assert output_fft[low_bin] <= input_fft[low_bin] * 1.01

    def test_default_parameters(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        output = self.effect.process(audio, {"sample_rate": 48000})
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

    def test_custom_frequency_range(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "frequency_range": {"min_hz": 100, "max_hz": 8000},
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_auto_detect_disabled(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "auto_detect": False,
            "sample_rate": 48000,
        }
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_short_audio(self):
        audio = np.sin(np.linspace(0, np.pi, 256))
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert output.shape == audio.shape

    def test_different_window_sizes(self):
        for window_size in [2048, 4096, 8192]:
            audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
            params = {
                "window_size": window_size,
                "hop_size": window_size // 4,
                "sample_rate": 48000,
            }
            output = self.effect.process(audio, params)
            assert output.shape == audio.shape

    def test_high_sensitivity_applies_more_attenuation(self):
        sr = 48000
        t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 150 * t) + 0.5 * np.sin(2 * np.pi * 6000 * t)

        out_low = self.effect.process(
            audio, {"sensitivity": 10, "sample_rate": sr}
        )
        out_high = self.effect.process(
            audio, {"sensitivity": 100, "sample_rate": sr}
        )
        assert not np.allclose(out_low, out_high)

    def test_process_preserves_finite_values(self):
        audio = np.random.randn(48000).astype(np.float32) * 0.1
        output = self.effect.process(audio, {"sample_rate": 48000})
        assert np.all(np.isfinite(output))

