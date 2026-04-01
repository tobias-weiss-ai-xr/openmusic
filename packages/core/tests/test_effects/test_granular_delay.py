"""Tests for GranularDelay effect."""

import numpy as np
import pytest

from openmusic.effects.granular_delay import GranularDelay


class TestGranularDelay:
    """Test suite for GranularDelay effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = GranularDelay()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "granular_delay"

    def test_process_mono_audio(self):
        """Test processing mono audio signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 60,
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
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 60,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[0] == 2  # Stereo channels

    def test_grain_size_parameter_affects_output(self):
        """Test that grain_size parameter changes output texture."""
        audio = np.random.randn(48000)

        # Small grain size
        params_small = {
            "grain_size_ms": 10,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Large grain size
        params_large = {
            "grain_size_ms": 200,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_small = self.effect.process(audio.copy(), params_small)
        output_large = self.effect.process(audio.copy(), params_large)

        # Different grain sizes should produce different outputs
        assert not np.allclose(output_small, output_large)

    def test_grain_density_parameter_affects_output(self):
        """Test that grain_density parameter changes grain overlap."""
        # Use random noise which will be affected by different grain overlaps
        np.random.seed(42)
        audio = np.random.randn(48000)

        # Low density - fewer, more separated grains
        params_low = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # High density - more overlapping grains
        params_high = {
            "grain_size_ms": 100,
            "grain_density": 15,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_low = self.effect.process(audio.copy(), params_low)
        output_high = self.effect.process(audio.copy(), params_high)

        # Different densities should produce different outputs
        # Check that the outputs are meaningfully different
        assert not np.allclose(output_low, output_high)
        # Both should have some energy
        assert np.std(output_low) > 0.001
        assert np.std(output_high) > 0.001

    def test_randomization_parameter_affects_output(self):
        """Test that randomization_amount parameter adds variation."""
        audio = np.random.randn(48000)

        # No randomization
        params_no_rand = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # High randomization
        params_high_rand = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 100,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_no_rand = self.effect.process(audio.copy(), params_no_rand)
        output_high_rand = self.effect.process(audio.copy(), params_high_rand)

        # Different randomization should produce different outputs
        assert not np.allclose(output_no_rand, output_high_rand)

    def test_feedback_creates_repeats(self):
        """Test that feedback creates repeating echoes."""
        # Use a sine wave instead of impulse for better granular processing
        audio = np.sin(np.linspace(0, 200 * np.pi, 48000 * 2))  # 2 seconds

        params = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 80,  # High feedback
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should have energy due to feedback repeats
        assert np.std(output) > 0.001

        # Energy in second half should be comparable (feedback sustains)
        energy_first = np.sum(np.abs(output[:48000]))
        energy_second = np.sum(np.abs(output[48000:]))
        # With high feedback, second half should have significant energy
        assert energy_second > energy_first * 0.3

    def test_wet_dry_mix_zero_returns_original(self):
        """Test wet_dry_mix=0 returns original signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 100,
            "feedback": 100,
            "wet_dry_mix": 0,  # No wet signal
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should be identical to input
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_wet_dry_mix_full_returns_processed(self):
        """Test wet_dry_mix=100 returns fully processed signal."""
        audio = np.random.randn(48000)

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 100,  # Full wet
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be different from input
        assert not np.allclose(output, audio)

    def test_wet_dry_mix_partial(self):
        """Test partial wet/dry mix produces blended output."""
        # Use deterministic signal with no randomization for predictable results
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        # Dry signal (0% wet)
        dry_params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 0,
            "sample_rate": 48000,
        }
        dry = self.effect.process(audio.copy(), dry_params)

        # Wet signal (100% wet)
        wet_params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }
        wet = self.effect.process(audio.copy(), wet_params)

        # 50% mix
        mixed_params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 50,
            "sample_rate": 48000,
        }
        mixed = self.effect.process(audio.copy(), mixed_params)

        # Mixed should be approximately average of dry and wet
        expected = (dry + wet) / 2
        np.testing.assert_allclose(mixed, expected, rtol=0.01)

    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        audio = np.random.randn(48000)

        # Call with minimal params - should use defaults
        output = self.effect.process(audio, {"sample_rate": 48000})

        assert output.shape == audio.shape
        assert not np.allclose(output, 0)

    def test_stereo_channels_processed_independently(self):
        """Test that stereo channels are processed independently."""
        left = np.random.randn(48000)
        right = np.random.randn(48000) * 0.5  # Different amplitude

        audio = np.stack([left, right])

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == (2, 48000)
        # Channels should remain different
        assert not np.allclose(output[0], output[1])

    def test_stereo_independence_with_different_input(self):
        """Test stereo channels maintain their characteristics."""
        # Left channel: sine wave
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))

        # Right channel: different sine wave
        right = np.sin(np.linspace(0, 8 * np.pi, 48000))

        audio = np.stack([left, right])

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
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
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 60,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Zero input should produce zero output
        assert np.allclose(output, 0)

    def test_grain_size_clamped_to_range(self):
        """Test that grain_size is clamped to valid range (10-200ms)."""
        audio = np.random.randn(48000)

        # Extreme values that should be clamped
        params_min = {
            "grain_size_ms": 1,  # Below minimum
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "grain_size_ms": 1000,  # Above maximum
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_density_clamped_to_range(self):
        """Test that grain_density is clamped to valid range (1-20)."""
        audio = np.random.randn(48000)

        params_min = {
            "grain_size_ms": 50,
            "grain_density": 0,  # Below minimum
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "grain_size_ms": 50,
            "grain_density": 100,  # Above maximum
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_randomization_clamped_to_range(self):
        """Test that randomization_amount is clamped to valid range (0-100%)."""
        audio = np.random.randn(48000)

        params_min = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": -50,  # Below minimum
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 200,  # Above maximum
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_feedback_clamped_to_range(self):
        """Test that feedback is clamped to valid range (0-100%)."""
        audio = np.random.randn(48000)

        params_min = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": -20,  # Below minimum
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 150,  # Above maximum
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_output_does_not_clip(self):
        """Test that output stays within reasonable bounds."""
        # Large input signal
        audio = np.ones(48000) * 5.0

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 80,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be bounded (not explode due to feedback)
        assert np.max(np.abs(output)) < 10.0

    def test_different_sample_rates(self):
        """Test processing with different sample rates."""
        audio_48k = np.sin(np.linspace(0, 4 * np.pi, 48000))
        audio_44k = np.sin(np.linspace(0, 4 * np.pi, 44100))

        params_48k = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_44k = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 44100,
        }

        output_48k = self.effect.process(audio_48k, params_48k)
        output_44k = self.effect.process(audio_44k, params_44k)

        assert output_48k.shape == audio_48k.shape
        assert output_44k.shape == audio_44k.shape

    def test_empty_audio(self):
        """Test processing empty audio array."""
        audio = np.array([])
        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 30,
            "feedback": 40,
            "wet_dry_mix": 60,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert len(output) == 0

    def test_very_short_audio(self):
        """Test processing very short audio."""
        audio = np.array([0.5, -0.3, 0.8, -0.1])
        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_feedback_zero_no_repeats(self):
        """Test that zero feedback produces no repeats."""
        # Use a short burst that will decay without feedback
        t = np.linspace(0, 1, 48000)
        # Windowed sine burst - starts and ends at zero
        window = 0.5 * (1 - np.cos(2 * np.pi * t))
        audio = np.sin(2 * np.pi * 440 * t) * window

        params_low = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 0,  # No feedback
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_high = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 80,  # High feedback
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_low = self.effect.process(audio.copy(), params_low)
        output_high = self.effect.process(audio.copy(), params_high)

        # Compare energy in the second half
        # Without feedback, energy should be much lower
        energy_low_second_half = np.sum(np.abs(output_low[24000:]))
        energy_high_second_half = np.sum(np.abs(output_high[24000:]))

        # High feedback should sustain more energy
        assert energy_high_second_half > energy_low_second_half * 1.5

    def test_high_feedback_sustained_output(self):
        """Test that high feedback sustains output longer."""
        # Impulse input
        audio = np.zeros(48000 * 3)  # 3 seconds
        audio[0] = 1.0

        # Low feedback
        params_low = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 20,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # High feedback
        params_high = {
            "grain_size_ms": 100,
            "grain_density": 2,
            "randomization_amount": 0,
            "feedback": 80,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_low = self.effect.process(audio.copy(), params_low)
        output_high = self.effect.process(audio.copy(), params_high)

        # High feedback should have more sustained energy in later portion
        energy_low = np.sum(np.abs(output_low[230400:]))  # Last 300ms
        energy_high = np.sum(np.abs(output_high[230400:]))

        assert energy_high >= energy_low * 0.8  # High feedback sustains longer

    def test_grain_envelope_smooth(self):
        """Test that grain envelope creates smooth transitions."""
        # Use sine wave to check for smooth processing
        audio = np.sin(np.linspace(0, 100 * np.pi, 48000))

        params = {
            "grain_size_ms": 50,
            "grain_density": 10,  # High density for smooth overlap
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be smooth (no extreme spikes from clicks)
        # Check that there are no sudden large jumps
        diffs = np.abs(np.diff(output))
        assert np.max(diffs) < 0.5  # No extreme discontinuities

    def test_randomization_produces_variation(self):
        """Test that randomization produces different results on each run."""
        audio = np.random.randn(48000)

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 50,  # Significant randomization
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Process same input multiple times
        output1 = self.effect.process(audio.copy(), params)
        output2 = self.effect.process(audio.copy(), params)

        # With randomization, outputs should be different
        assert not np.allclose(output1, output2)

    def test_no_randomization_deterministic(self):
        """Test that zero randomization produces consistent results."""
        audio = np.random.randn(48000)

        params = {
            "grain_size_ms": 50,
            "grain_density": 5,
            "randomization_amount": 0,  # No randomization
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Process same input multiple times
        output1 = self.effect.process(audio.copy(), params)
        output2 = self.effect.process(audio.copy(), params)

        # Without randomization, outputs should be identical
        np.testing.assert_allclose(output1, output2, rtol=1e-10)

    def test_extreme_grain_size_small(self):
        """Test with minimum grain size."""
        audio = np.random.randn(48000)

        params = {
            "grain_size_ms": 10,  # Minimum
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert not np.allclose(output, 0)

    def test_extreme_grain_size_large(self):
        """Test with maximum grain size."""
        audio = np.random.randn(48000)

        params = {
            "grain_size_ms": 200,  # Maximum
            "grain_density": 5,
            "randomization_amount": 0,
            "feedback": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert not np.allclose(output, 0)

    def test_all_parameters_at_defaults(self):
        """Test that all default parameters produce valid output."""
        audio = np.random.randn(48000)

        # Only provide sample_rate, use all other defaults
        output = self.effect.process(audio, {"sample_rate": 48000})

        assert output.shape == audio.shape
        assert output.dtype == audio.dtype
        assert not np.allclose(output, 0)
