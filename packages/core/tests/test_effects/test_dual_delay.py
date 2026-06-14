"""Tests for DualDelay effect."""

import numpy as np
import pytest

from openmusic.effects.dual_delay import DualDelay


class TestDualDelay:
    """Test suite for DualDelay effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = DualDelay()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "dual_delay"

    def test_process_stereo(self):
        """Test processing stereo audio signal."""
        audio = np.random.randn(2, 48000) * 0.5
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_mono_passthrough(self):
        """Test processing mono audio signal."""
        audio = np.random.randn(48000) * 0.5
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_detune_changes_signal(self):
        """Test that detune parameter actually alters the output."""
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params_no = {"sample_rate": 48000, "detune_cents": 0.0}
        params_yes = {"sample_rate": 48000, "detune_cents": 5.0}
        out_no = self.effect.process(audio.copy(), params_no)
        out_yes = self.effect.process(audio.copy(), params_yes)
        assert not np.allclose(out_no, out_yes, atol=1e-6)

    def test_zero_mix_identity(self):
        """Test that zero mix returns original audio."""
        audio = np.random.randn(2, 48000) * 0.5
        params = {"sample_rate": 48000, "mix": 0.0}
        output = self.effect.process(audio, params)
        np.testing.assert_allclose(output, audio, atol=1e-10)
