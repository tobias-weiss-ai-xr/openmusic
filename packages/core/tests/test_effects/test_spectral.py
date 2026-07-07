"""Tests for SpectralGate effect."""

import numpy as np
import pytest

from openmusic.effects.spectral import SpectralGate


class TestSpectralGate:
    """Test suite for SpectralGate effect."""

    def setup_method(self):
        self.effect = SpectralGate()

    def test_initialization(self):
        assert self.effect.name == "spectral_gate"

    def test_process_mono_audio(self):
        audio = np.sin(np.linspace(0, 4 * np.pi, 4096))
        params = {"threshold_db": -40}

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.dtype == audio.dtype

    def test_process_stereo_audio(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 4096))
        right = np.cos(np.linspace(0, 4 * np.pi, 4096))
        audio = np.column_stack([left, right])

        params = {"threshold_db": -40}
        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[1] == 2

    def test_default_parameters(self):
        audio = np.random.randn(4096)
        output = self.effect.process(audio, {})
        assert output.shape == audio.shape

    def test_zero_input(self):
        audio = np.zeros(4096)
        params = {"threshold_db": -40}
        output = self.effect.process(audio, params)
        assert np.allclose(output, 0, atol=1e-6)

    def test_low_threshold_passes_audio(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(4096) * 0.5
        params = {"threshold_db": -100}
        output = self.effect.process(audio.copy(), params)
        assert not np.allclose(output, 0)

    def test_high_threshold_gates_audio(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(4096) * 0.01
        params = {"threshold_db": 0}
        output = self.effect.process(audio.copy(), params)
        total_energy = np.sum(np.abs(output))
        assert total_energy < np.sum(np.abs(audio)) + 1e-3

    def test_attack_parameter_affects_output(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(8192) * 0.5

        fast_attack = self.effect.process(
            audio.copy(), {"threshold_db": -20, "attack_ms": 1, "release_ms": 10, "hold_ms": 0}
        )
        slow_attack = self.effect.process(
            audio.copy(), {"threshold_db": -20, "attack_ms": 200, "release_ms": 10, "hold_ms": 0}
        )

        assert not np.allclose(fast_attack, slow_attack)

    def test_release_parameter_affects_output(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(8192) * 0.5

        fast_release = self.effect.process(
            audio.copy(), {"threshold_db": -20, "attack_ms": 1, "release_ms": 10, "hold_ms": 0}
        )
        slow_release = self.effect.process(
            audio.copy(), {"threshold_db": -20, "attack_ms": 1, "release_ms": 500, "hold_ms": 0}
        )

        assert not np.allclose(fast_release, slow_release)

    def test_tempo_sync_creates_rhythmic_pattern(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(48000) * 0.5

        no_sync = self.effect.process(
            audio.copy(), {"threshold_db": -40, "sync_to_tempo": 0, "attack_ms": 1, "release_ms": 10}
        )
        with_sync = self.effect.process(
            audio.copy(), {"threshold_db": -40, "sync_to_tempo": 120, "attack_ms": 1, "release_ms": 10}
        )

        assert not np.allclose(no_sync, with_sync)

    def test_frequency_bands_processing(self):
        rng = np.random.RandomState(42)
        audio = rng.randn(8192) * 0.5

        full_spectrum = self.effect.process(
            audio.copy(), {"threshold_db": -40}
        )
        per_band = self.effect.process(
            audio.copy(), {"threshold_db": -40, "frequency_bands": [100, 1000, 5000]}
        )

        assert not np.allclose(full_spectrum, per_band)

    def test_empty_audio(self):
        audio = np.array([])
        params = {"threshold_db": -40}
        output = self.effect.process(audio, params)
        assert len(output) == 0

    def test_stereo_channels_independent(self):
        left = np.sin(np.linspace(0, 4 * np.pi, 4096)) * 0.5
        right = np.zeros(4096)
        audio = np.column_stack([left, right])

        params = {"threshold_db": -20, "attack_ms": 1, "release_ms": 10}
        output = self.effect.process(audio, params)

        assert not np.allclose(output[:, 0], output[:, 1])
