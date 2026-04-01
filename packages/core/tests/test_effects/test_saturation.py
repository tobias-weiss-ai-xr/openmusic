"""Tests for TapeSaturation effect."""

import numpy as np
import pytest

from openmusic.effects.saturation import TapeSaturation


class TestTapeSaturation:
    """Test suite for TapeSaturation effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = TapeSaturation()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "tape_saturation"

    def test_process_mono_audio(self):
        """Test processing mono audio signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000))
        params = {"drive": 50, "wet_dry_mix": 50}

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.dtype == audio.dtype

    def test_process_stereo_audio(self):
        """Test processing stereo audio signal."""
        left = np.sin(np.linspace(0, 4 * np.pi, 1000))
        right = np.cos(np.linspace(0, 4 * np.pi, 1000))
        audio = np.stack([left, right])

        params = {"drive": 50, "wet_dry_mix": 50}
        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[0] == 2  # Stereo channels

    def test_drive_parameter_affects_output(self):
        """Test that drive parameter changes output saturation."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000)) * 0.8

        # Low drive
        output_low = self.effect.process(
            audio.copy(), {"drive": 10, "wet_dry_mix": 100}
        )
        # High drive
        output_high = self.effect.process(
            audio.copy(), {"drive": 90, "wet_dry_mix": 100}
        )

        # Higher drive should produce more saturation (different output)
        assert not np.allclose(output_low, output_high)

        # High drive should produce more harmonic distortion (higher RMS for same input)
        # or simply verify the waveforms are different in shape
        assert np.mean(np.abs(output_high - output_low)) > 0.001

    def test_wet_dry_mix_zero(self):
        """Test wet_dry_mix=0 returns original signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000))
        params = {"drive": 100, "wet_dry_mix": 0}

        output = self.effect.process(audio, params)

        # Should be nearly identical to input
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_wet_dry_mix_full(self):
        """Test wet_dry_mix=100 returns fully saturated signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000)) * 0.5
        params = {"drive": 50, "wet_dry_mix": 100}

        output = self.effect.process(audio, params)

        # Output should be different from input (saturated)
        assert not np.allclose(output, audio)

    def test_wet_dry_mix_partial(self):
        """Test partial wet/dry mix produces blended output."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000)) * 0.5

        # Dry signal
        dry_params = {"drive": 50, "wet_dry_mix": 0}
        dry = self.effect.process(audio.copy(), dry_params)

        # Wet signal
        wet_params = {"drive": 50, "wet_dry_mix": 100}
        wet = self.effect.process(audio.copy(), wet_params)

        # 50% mix
        mixed_params = {"drive": 50, "wet_dry_mix": 50}
        mixed = self.effect.process(audio.copy(), mixed_params)

        # Mixed should be approximately average of dry and wet
        expected = (dry + wet) / 2
        np.testing.assert_allclose(mixed, expected, rtol=0.1)

    def test_bias_tone_added(self):
        """Test that bias tone is added when configured."""
        audio = np.zeros(48000)  # 1 second of silence
        params = {
            "drive": 0,
            "wet_dry_mix": 0,
            "bias_tone": {"frequency": 100, "amplitude": 0.1},
        }

        output = self.effect.process(audio, params)

        # Output should not be all zeros
        assert not np.allclose(output, 0)

        # Should have some energy
        assert np.std(output) > 0.01

    def test_bias_tone_without_config(self):
        """Test that no bias tone is added when not configured."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 1000))
        params = {"drive": 50, "wet_dry_mix": 50}

        output = self.effect.process(audio, params)

        # Should process normally without bias
        assert output.shape == audio.shape

    def test_output_clipped_properly(self):
        """Test that output doesn't exceed reasonable bounds."""
        # Use large input that would normally clip
        audio = np.ones(1000) * 10.0
        params = {"drive": 100, "wet_dry_mix": 100}

        output = self.effect.process(audio, params)

        # Output should be bounded (tanh saturates to ~1)
        assert np.max(np.abs(output)) < 2.0

    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        audio = np.random.randn(1000)

        # Call with empty params - should use defaults
        output = self.effect.process(audio, {})

        assert output.shape == audio.shape
        assert not np.allclose(output, 0)

    def test_stereo_independence(self):
        """Test that stereo channels are processed independently."""
        left = np.sin(np.linspace(0, 4 * np.pi, 1000))
        right = np.cos(np.linspace(0, 4 * np.pi, 1000)) * 0.5
        audio = np.stack([left, right])

        params = {"drive": 50, "wet_dry_mix": 100}
        output = self.effect.process(audio, params)

        # Channels should remain different
        assert not np.allclose(output[0], output[1])

    def test_zero_input(self):
        """Test processing zero input."""
        audio = np.zeros(1000)
        params = {"drive": 50, "wet_dry_mix": 50}

        output = self.effect.process(audio, params)

        # Zero input should produce zero output
        assert np.allclose(output, 0)
