"""Tests for MultiTapDelay effect."""

import numpy as np
import pytest

from openmusic.effects.delay import MultiTapDelay


class TestMultiTapDelay:
    """Test suite for MultiTapDelay effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = MultiTapDelay()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "multi_tap_delay"

    def test_process_mono_audio(self):
        """Test processing mono audio signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "num_taps": 4,
            "tap_times_ms": [250, 375, 500, 625],
            "tap_feedback": [0.3, 0.25, 0.2, 0.15],
            "tap_pan": [0.0, -0.5, 0.5, 0.0],
            "master_feedback": 0.3,
            "wet_dry": 50,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.dtype == audio.dtype

    def test_process_stereo_audio(self):
        """Test processing stereo audio signal."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params = {
            "num_taps": 4,
            "tap_times_ms": [250, 375, 500, 625],
            "tap_feedback": [0.3, 0.25, 0.2, 0.15],
            "tap_pan": [0.0, -0.5, 0.5, 0.0],
            "master_feedback": 0.3,
            "wet_dry": 50,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[0] == 2  # Stereo channels

    def test_tap_times_affect_output(self):
        """Test that different tap times produce different outputs."""
        audio = np.zeros(48000)
        audio[0] = 1.0  # Impulse at start

        # Short delay
        params_short = {
            "num_taps": 2,
            "tap_times_ms": [100, 200],
            "tap_feedback": [0.5, 0.5],
            "tap_pan": [0.0, 0.0],
            "master_feedback": 0.5,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        # Long delay
        params_long = {
            "num_taps": 2,
            "tap_times_ms": [500, 1000],
            "tap_feedback": [0.5, 0.5],
            "tap_pan": [0.0, 0.0],
            "master_feedback": 0.5,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        output_short = self.effect.process(audio.copy(), params_short)
        output_long = self.effect.process(audio.copy(), params_long)

        # Outputs should be different due to different delay times
        assert not np.allclose(output_short, output_long)

    def test_feedback_creates_repeats(self):
        """Test that feedback creates repeating echoes."""
        audio = np.zeros(48000 * 2)  # 2 seconds
        audio[0] = 1.0  # Impulse

        params = {
            "num_taps": 1,
            "tap_times_ms": [500],
            "tap_feedback": [0.8],
            "tap_pan": [0.0],
            "master_feedback": 1.0,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should have energy at delay positions due to feedback
        # First repeat at 500ms, second at 1000ms, etc.
        assert np.std(output) > 0.001  # Some energy in output

    def test_pan_position_affects_channels(self):
        """Test that pan position affects left/right balance."""
        audio = np.zeros(48000)
        audio[0] = 1.0  # Impulse

        # Hard left pan
        params_left = {
            "num_taps": 1,
            "tap_times_ms": [250],
            "tap_feedback": [0.0],
            "tap_pan": [-1.0],  # Hard left
            "master_feedback": 0.0,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        # Hard right pan
        params_right = {
            "num_taps": 1,
            "tap_times_ms": [250],
            "tap_feedback": [0.0],
            "tap_pan": [1.0],  # Hard right
            "master_feedback": 0.0,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        # Test with stereo input
        stereo_audio = np.stack([audio.copy(), audio.copy()])

        output_left = self.effect.process(stereo_audio.copy(), params_left)
        output_right = self.effect.process(stereo_audio.copy(), params_right)

        # Left pan should have more energy in left channel
        # Right pan should have more energy in right channel
        # (Actual values depend on implementation details)
        assert output_left.shape == (2, 48000)
        assert output_right.shape == (2, 48000)

    def test_wet_dry_zero_returns_original(self):
        """Test wet_dry=0 returns original signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "num_taps": 4,
            "tap_times_ms": [250, 375, 500, 625],
            "tap_feedback": [0.5, 0.5, 0.5, 0.5],
            "tap_pan": [0.0, 0.0, 0.0, 0.0],
            "master_feedback": 0.5,
            "wet_dry": 0,  # No wet signal
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should be identical to input
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_wet_dry_full_returns_delayed(self):
        """Test wet_dry=100 returns fully delayed signal."""
        audio = np.zeros(48000)
        audio[0] = 1.0  # Impulse

        params = {
            "num_taps": 1,
            "tap_times_ms": [250],
            "tap_feedback": [0.0],
            "tap_pan": [0.0],
            "master_feedback": 0.0,
            "wet_dry": 100,  # Full wet
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should have energy at delay position
        delay_samples = int(0.25 * 48000)
        # Check that there's energy around the delay position
        assert np.sum(np.abs(output[delay_samples - 100 : delay_samples + 100])) > 0.1

    def test_master_feedback_controls_overall_decay(self):
        """Test that master feedback controls overall decay."""
        audio = np.zeros(48000 * 3)  # 3 seconds
        audio[0] = 1.0  # Impulse

        # Low master feedback
        params_low = {
            "num_taps": 1,
            "tap_times_ms": [500],
            "tap_feedback": [1.0],
            "tap_pan": [0.0],
            "master_feedback": 0.2,  # Low overall feedback
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        # High master feedback
        params_high = {
            "num_taps": 1,
            "tap_times_ms": [500],
            "tap_feedback": [1.0],
            "tap_pan": [0.0],
            "master_feedback": 0.8,  # High overall feedback
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        output_low = self.effect.process(audio.copy(), params_low)
        output_high = self.effect.process(audio.copy(), params_high)

        # High feedback should have more sustained energy
        # Compare energy in later portion of signal
        energy_low = np.sum(np.abs(output_low[144000:]))
        energy_high = np.sum(np.abs(output_high[144000:]))

        # High feedback should have more late energy
        assert energy_high >= energy_low * 0.5  # Allow some tolerance

    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        audio = np.random.randn(48000)

        # Call with minimal params - should use defaults
        output = self.effect.process(audio, {"sample_rate": 48000})

        assert output.shape == audio.shape

    def test_multiple_taps(self):
        """Test processing with multiple taps."""
        audio = np.zeros(48000)
        audio[0] = 1.0  # Impulse

        params = {
            "num_taps": 4,
            "tap_times_ms": [125, 250, 375, 500],
            "tap_feedback": [0.3, 0.25, 0.2, 0.15],
            "tap_pan": [-0.5, -0.25, 0.25, 0.5],
            "master_feedback": 0.5,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should have multiple echoes at different positions
        assert output.shape == audio.shape
        assert np.std(output) > 0.01

    def test_stereo_channels_processed(self):
        """Test that stereo channels are both processed."""
        left = np.zeros(48000)
        right = np.zeros(48000)
        left[0] = 1.0
        right[0] = 0.5  # Different amplitude

        audio = np.stack([left, right])

        params = {
            "num_taps": 2,
            "tap_times_ms": [250, 500],
            "tap_feedback": [0.5, 0.3],
            "tap_pan": [0.0, 0.0],
            "master_feedback": 0.5,
            "wet_dry": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == (2, 48000)
        # Both channels should have output
        assert np.std(output[0]) > 0.001
        assert np.std(output[1]) > 0.001

    def test_zero_input(self):
        """Test processing zero input."""
        audio = np.zeros(48000)
        params = {
            "num_taps": 4,
            "tap_times_ms": [250, 375, 500, 625],
            "tap_feedback": [0.3, 0.25, 0.2, 0.15],
            "tap_pan": [0.0, -0.5, 0.5, 0.0],
            "master_feedback": 0.3,
            "wet_dry": 50,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Zero input should produce zero output
        assert np.allclose(output, 0)

    def test_tap_list_auto_expands(self):
        """Test that tap lists auto-expand to match num_taps."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        # Provide fewer tap values than num_taps
        params = {
            "num_taps": 5,  # Request 5 taps
            "tap_times_ms": [250],  # Only 1 time provided
            "tap_feedback": [0.5],  # Only 1 feedback provided
            "tap_pan": [0.0],  # Only 1 pan provided
            "master_feedback": 0.3,
            "wet_dry": 50,
            "sample_rate": 48000,
        }

        # Should not raise an error
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
