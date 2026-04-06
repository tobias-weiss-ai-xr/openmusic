"""Tests for SidechainCompression effect."""

import numpy as np
import pytest

from openmusic.effects.compression import SidechainCompression


class TestSidechainCompression:
    """Test suite for SidechainCompression effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = SidechainCompression()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "sidechain_compression"

    def test_process_mono_audio(self):
        """Test processing mono audio signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 70,
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
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 70,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[0] == 2  # Stereo channels

    def test_threshold_parameter_affects_compression(self):
        """Test that threshold determines when compression kicks in."""
        # Create audio that exceeds threshold
        audio = np.ones(48000) * 0.5  # -6 dB

        params_high = {
            "threshold_db": -20,  # Triggers compression
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,  # No knee for clarity
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_low = {
            "threshold_db": 0,  # No compression (signal below threshold)
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_compressed = self.effect.process(audio.copy(), params_high)
        output_uncompressed = self.effect.process(audio.copy(), params_low)

        # Compressed = lower output (steady state)
        # Check steady state after attack
        steady_compressed = np.max(np.abs(output_compressed[5000:]))
        steady_uncompressed = np.max(np.abs(output_uncompressed[5000:]))

        assert steady_compressed < steady_uncompressed

    def test_ratio_parameter_affects_compression(self):
        """Test that higher ratio creates more compression."""
        audio = np.ones(48000) * 0.5  # -6 dB

        params_low_ratio = {
            "threshold_db": -20,
            "ratio": 2,  # Low compression
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_high_ratio = {
            "threshold_db": -20,
            "ratio": 10,  # High compression
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_low = self.effect.process(audio.copy(), params_low_ratio)
        output_high = self.effect.process(audio.copy(), params_high_ratio)

        # Higher ratio = more compression = lower steady state output
        steady_low = np.max(np.abs(output_low[5000:]))
        steady_high = np.max(np.abs(output_high[5000:]))

        assert steady_high < steady_low

    def test_attack_time_affects_response(self):
        """Test that attack time controls compression speed."""
        # Create rising signal to better show attack behavior
        audio = np.linspace(0, 1.0, 10000)
        audio = np.concatenate([audio, np.ones(38000)])  # Rising then steady

        params_fast = {
            "threshold_db": -6,
            "ratio": 4,
            "attack_ms": 1,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_slow = {
            "threshold_db": -6,
            "ratio": 4,
            "attack_ms": 100,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_fast = self.effect.process(audio.copy(), params_fast)
        output_slow = self.effect.process(audio.copy(), params_slow)

        # Fast attack should reach compression sooner
        # Check peak value in early steady state region
        fast_steady = np.max(np.abs(output_fast[10500:11000]))
        slow_steady = np.max(np.abs(output_slow[10500:11000]))

        # Fast attack should result in lower steady-state output (compressed more)
        assert fast_steady < slow_steady

    def test_release_time_affects_recovery(self):
        """Test that release time controls compression recovery."""
        # Create signal that goes high then low
        audio = np.concatenate(
            [
                np.ones(10000) * 0.8,  # High part (well above threshold)
                np.ones(38000) * 0.05,  # Low part
            ]
        )

        params_fast_release = {
            "threshold_db": -6,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 10,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_slow_release = {
            "threshold_db": -6,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 500,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_fast = self.effect.process(audio.copy(), params_fast_release)
        output_slow = self.effect.process(audio.copy(), params_slow_release)

        # After transition to low part, fast release should recover quicker (higher output)
        # Check later in recovery period
        recovery_fast = np.max(np.abs(output_fast[20000:25000]))
        recovery_slow = np.max(np.abs(output_slow[20000:25000]))

        # Fast release = faster recovery = higher output after transition
        assert recovery_fast > recovery_slow

    def test_knee_smoothing(self):
        """Test that soft knee reduces abrupt gain changes."""
        audio = np.ones(48000) * 0.3  # -10.5 dB

        params_no_knee = {
            "threshold_db": -10.5,  # Right at threshold
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,  # Hard knee
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_soft_knee = {
            "threshold_db": -10.5,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 6,  # Soft knee
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output_no_knee = self.effect.process(audio.copy(), params_no_knee)
        output_soft_knee = self.effect.process(audio.copy(), params_soft_knee)

        # Soft knee should result in less compression (higher output)
        # when near threshold
        assert np.max(np.abs(output_soft_knee)) >= np.max(np.abs(output_no_knee))

    def test_wet_dry_mix_zero_returns_original(self):
        """Test wet_dry_mix=0 returns original signal."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 0,  # No wet signal
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should be identical to input
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_wet_dry_mix_full_returns_compressed(self):
        """Test wet_dry_mix=100 returns fully compressed signal."""
        audio = np.ones(48000) * 0.8  # Well above threshold

        params = {
            "threshold_db": -6,  # Triggers compression
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,  # Hard knee for predictable compression
            "wet_dry_mix": 100,  # Full wet
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be compressed (different from input)
        assert not np.allclose(output, audio)
        # Steady state should be lower than input after attack
        steady_output = np.max(np.abs(output[5000:]))
        assert steady_output < 0.8

    def test_wet_dry_mix_partial(self):
        """Test partial wet/dry mix produces blended output."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        # Dry signal (0% wet)
        dry_params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 0,
            "sample_rate": 48000,
        }
        dry = self.effect.process(audio.copy(), dry_params)

        # Wet signal (100% wet)
        wet_params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }
        wet = self.effect.process(audio.copy(), wet_params)

        # 50% mix
        mixed_params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
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
        assert not np.allclose(output, audio)

    def test_stereo_channels_processed_independently(self):
        """Test that stereo channels are processed independently."""
        left = np.random.randn(48000) * 0.5
        right = np.random.randn(48000) * 0.3

        audio = np.stack([left, right])

        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == (2, 48000)
        # Channels should remain different
        assert not np.allclose(output[0], output[1])

    def test_zero_input(self):
        """Test processing zero input."""
        audio = np.zeros(48000)
        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 70,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Zero input should produce zero output
        assert np.allclose(output, 0)

    def test_compression_reduces_gain_above_threshold(self):
        """Test that compression actually reduces gain when signal exceeds threshold."""
        # Audio that significantly exceeds threshold
        audio = np.ones(48000) * 0.8  # Well above -6 dB threshold

        params = {
            "threshold_db": -6,  # Will trigger compression
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output steady state should be lower than input (compression applied)
        output_steady = np.max(np.abs(output[5000:]))
        assert output_steady < 0.8

    def test_no_compression_below_threshold(self):
        """Test that no compression occurs when signal is below threshold."""
        # Audio below threshold
        audio = np.ones(48000) * 0.01  # -40 dB

        params = {
            "threshold_db": -20,  # Won't compress
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 0,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be nearly identical to input (no compression)
        # Allow small differences due to envelope smoothing
        assert np.allclose(output, audio, rtol=0.01)

    def test_threshold_clamped_to_range(self):
        """Test that threshold is clamped to valid range (-60 to 0 dB)."""
        audio = np.random.randn(48000)

        params_min = {
            "threshold_db": -100,  # Below minimum
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "threshold_db": 10,  # Above maximum
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_ratio_clamped_to_range(self):
        """Test that ratio is clamped to valid range (1 to 20)."""
        audio = np.random.randn(48000)

        params_min = {
            "threshold_db": -20,
            "ratio": 0,  # Below minimum
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "threshold_db": -20,
            "ratio": 50,  # Above maximum
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_attack_release_clamped_to_range(self):
        """Test that attack and release are clamped to valid ranges."""
        audio = np.random.randn(48000)

        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 0.5,  # Below minimum
            "release_ms": 2000,  # Above maximum
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_knee_clamped_to_range(self):
        """Test that knee is clamped to valid range (0 to 12 dB)."""
        audio = np.random.randn(48000)

        params_min = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": -5,  # Below minimum
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_max = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 20,  # Above maximum
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_output_does_not_clip_unnecessarily(self):
        """Test that compression doesn't cause excessive clipping."""
        # Large input signal
        audio = np.ones(48000) * 2.0

        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Output should be reasonable (not explode)
        assert np.max(np.abs(output)) < 5.0

    def test_different_sample_rates(self):
        """Test processing with different sample rates."""
        audio_48k = np.sin(np.linspace(0, 4 * np.pi, 48000))
        audio_44k = np.sin(np.linspace(0, 4 * np.pi, 44100))

        params_48k = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        params_44k = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
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
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 70,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert len(output) == 0

    def test_very_short_audio(self):
        """Test processing very short audio."""
        audio = np.array([0.5, -0.3, 0.8, -0.1])
        params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
            "knee_db": 4,
            "wet_dry_mix": 100,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
