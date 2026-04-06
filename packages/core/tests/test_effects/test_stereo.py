"""Tests for MidSideStereoWidener effect."""

import numpy as np
import pytest

from openmusic.effects.stereo import MidSideStereoWidener


class TestMidSideStereoWidener:
    """Test suite for MidSideStereoWidener effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = MidSideStereoWidener()

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "mid_side_widener"

    def test_process_stereo_audio(self):
        """Test processing stereo audio signal."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": {},
            "side_compression": {},
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert output.shape[0] == 2

    def test_mono_audio_passed_through(self):
        """Test that mono audio is passed through unchanged."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {"sample_rate": 48000}

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        np.testing.assert_allclose(output, audio)

    def test_stereo_width_normal(self):
        """Test stereo_width=1.0 preserves original stereo image."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params = {"stereo_width": 1.0, "sample_rate": 48000}

        output = self.effect.process(audio, params)

        # Should be similar to input (may have minor differences due to float math)
        # The mid/side encode/decode is lossless for width=1
        np.testing.assert_allclose(output, audio, rtol=1e-3, atol=1e-15)

    def test_stereo_width_narrow(self):
        """Test stereo_width=0.5 narrows stereo image."""
        # Create wide stereo signal (left and right are opposite)
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = -left
        audio = np.stack([left, right])

        params_normal = {"stereo_width": 1.0, "sample_rate": 48000}
        params_narrow = {"stereo_width": 0.5, "sample_rate": 48000}

        output_normal = self.effect.process(audio.copy(), params_normal)
        output_narrow = self.effect.process(audio.copy(), params_narrow)

        # Narrower width = more mono = left and right should be more similar
        difference_normal = np.mean(np.abs(output_normal[0] - output_normal[1]))
        difference_narrow = np.mean(np.abs(output_narrow[0] - output_narrow[1]))

        assert difference_narrow < difference_normal

    def test_stereo_width_wide(self):
        """Test stereo_width=1.5 widens stereo image."""
        # Create narrow stereo signal (left and right are similar)
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = left * 0.98  # Slightly different
        audio = np.stack([left, right])

        params_normal = {"stereo_width": 1.0, "sample_rate": 48000}
        params_wide = {"stereo_width": 1.5, "sample_rate": 48000}

        output_normal = self.effect.process(audio.copy(), params_normal)
        output_wide = self.effect.process(audio.copy(), params_wide)

        # Wider width = more stereo = left and right should be more different
        difference_normal = np.mean(np.abs(output_normal[0] - output_normal[1]))
        difference_wide = np.mean(np.abs(output_wide[0] - output_wide[1]))

        assert difference_wide > difference_normal

    def test_stereo_width_clamped_to_range(self):
        """Test that stereo_width is clamped to 0-2 range."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params_min = {"stereo_width": -1.0, "sample_rate": 48000}
        params_max = {"stereo_width": 3.0, "sample_rate": 48000}

        # Should not raise errors
        output_min = self.effect.process(audio.copy(), params_min)
        output_max = self.effect.process(audio.copy(), params_max)

        assert output_min.shape == audio.shape
        assert output_max.shape == audio.shape

    def test_mid_eq_affects_mid_channel(self):
        """Test that mid EQ affects center information."""
        # Create signal with both mid and side components
        left = np.ones(48000) * 0.5
        right = np.ones(48000) * 0.5
        audio = np.stack([left, right])

        mid_eq_params = {
            "frequency": 1000,
            "gain_db": -20,
            "Q": 1.0,
        }

        params_with_eq = {
            "stereo_width": 1.0,
            "mid_eq": mid_eq_params,
            "side_eq": {},
            "side_compression": {},
            "sample_rate": 48000,
        }

        params_no_eq = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with_eq = self.effect.process(audio.copy(), params_with_eq)
        output_no_eq = self.effect.process(audio.copy(), params_no_eq)

        # Mid EQ should affect output (different from no EQ)
        assert not np.allclose(output_with_eq, output_no_eq)

    def test_side_eq_affects_side_channel(self):
        """Test that side EQ affects stereo information."""
        # Create pure side signal (left = -right)
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = -left
        audio = np.stack([left, right])

        side_eq_params = {
            "frequency": 1000,
            "gain_db": -20,
            "Q": 1.0,
        }

        params_with_eq = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": side_eq_params,
            "side_compression": {},
            "sample_rate": 48000,
        }

        params_no_eq = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with_eq = self.effect.process(audio.copy(), params_with_eq)
        output_no_eq = self.effect.process(audio.copy(), params_no_eq)

        # Side EQ should affect output (different from no EQ)
        assert not np.allclose(output_with_eq, output_no_eq)

    def test_side_compression_affects_side_channel(self):
        """Test that side compression affects stereo information."""
        # Create pure side signal with loud transients
        audio = np.zeros((2, 48000))
        # Create sustained loud signal, not single peak
        audio[0, 12000:24000] = 0.8  # Loud section in left
        audio[1, 12000:24000] = -0.8  # Loud section in right (pure side)

        # Fill with noise to keep it realistic
        audio[0] += np.random.randn(48000) * 0.1
        audio[1] += np.random.randn(48000) * 0.1

        side_comp_params = {
            "threshold_db": -6,  # Will compress the 0.8 level
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
        }

        params_with_comp = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": {},
            "side_compression": side_comp_params,
            "sample_rate": 48000,
        }

        params_no_comp = {"stereo_width": 1.0, "sample_rate": 48000}

        output_with_comp = self.effect.process(audio.copy(), params_with_comp)
        output_no_comp = self.effect.process(audio.copy(), params_no_comp)

        # Side compression should affect output (different from no compression)
        assert not np.allclose(output_with_comp, output_no_comp)

    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = np.stack([left, right])

        # Call with minimal params - should use defaults
        output = self.effect.process(audio, {"sample_rate": 48000})

        assert output.shape == audio.shape

    def test_zero_input(self):
        """Test processing zero input."""
        audio = np.zeros((2, 48000))
        params = {"sample_rate": 48000}

        output = self.effect.process(audio, params)

        assert np.allclose(output, 0)

    def test_empty_audio(self):
        """Test processing empty audio array."""
        # Empty stereo audio (2 channels, 0 samples)
        audio = np.array([[], []])
        params = {"sample_rate": 48000}

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape

    def test_equivalent_mono_to_stereo_conversion(self):
        """Test that mono signal converted to stereo behaves correctly."""
        mono = np.sin(np.linspace(0, 4 * np.pi, 48000))

        # Convert mono to stereo (same signal in both channels)
        stereo = np.stack([mono, mono])

        params = {"stereo_width": 1.0, "sample_rate": 48000}
        output = self.effect.process(stereo, params)

        # Output should still be identical in both channels
        np.testing.assert_allclose(output[0], output[1])

    def test_mid_side_decode_reversibility(self):
        """Test that encode/decode is reversible with width=1."""
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = np.stack([left, right])

        params = {"stereo_width": 1.0, "sample_rate": 48000}
        output = self.effect.process(audio, params)

        # Encode and decode should be lossless at width=1
        np.testing.assert_allclose(output, audio, rtol=1e-5)

    def test_mid_eq_parameters_clamped(self):
        """Test that EQ parameters are handled correctly."""
        left = np.random.randn(48000)
        right = np.random.randn(48000)
        audio = np.stack([left, right])

        # Various EQ parameter combinations
        eq_params = {
            "frequency": 1000,
            "gain_db": 0,
            "Q": 1.0,
        }

        params = {
            "stereo_width": 1.0,
            "mid_eq": eq_params,
            "side_eq": eq_params,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output = self.effect.process(audio, params)

        assert output.shape == audio.shape

    def test_compression_parameters_clamped(self):
        """Test that compression parameters are handled correctly."""
        audio = np.random.randn(48000)
        right = np.random.randn(48000)
        stereo_audio = np.stack([audio, right])

        # Various compression parameter combinations
        comp_params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
        }

        params = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": {},
            "side_compression": comp_params,
            "sample_rate": 48000,
        }

        # Should not raise errors
        output = self.effect.process(stereo_audio, params)

        assert output.shape == stereo_audio.shape

    def test_different_sample_rates(self):
        """Test processing with different sample rates."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params_48k = {"stereo_width": 1.0, "sample_rate": 48000}
        params_44k = {"stereo_width": 1.0, "sample_rate": 44100}
        params_96k = {"stereo_width": 1.0, "sample_rate": 96000}

        # Adjust audio for different sample rates
        audio_44k = audio[:, :44100]
        audio_96k = np.random.randn(2, 96000) * 0.1  # Random for 96k

        output_48k = self.effect.process(audio.copy(), params_48k)
        output_44k = self.effect.process(audio_44k, params_44k)
        output_96k = self.effect.process(audio_96k, params_96k)

        assert output_48k.shape == audio.shape
        assert output_44k.shape == audio_44k.shape
        assert output_96k.shape == audio_96k.shape

    def test_width_zero_creates_mono(self):
        """Test that width=0 creates mono output."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))  # Different signal
        audio = np.stack([left, right])

        params = {"stereo_width": 0.0, "sample_rate": 48000}
        output = self.effect.process(audio, params)

        # Output should be identical in both channels (mono)
        np.testing.assert_allclose(output[0], output[1])

    def test_width_two_extreme_stereo(self):
        """Test that width=2 creates extreme stereo."""
        # Create signal with both mid and side
        mid = np.ones(48000) * 0.3
        side = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.3

        left = (mid + side) / np.sqrt(2)
        right = (mid - side) / np.sqrt(2)
        audio = np.stack([left, right])

        params_normal = {"stereo_width": 1.0, "sample_rate": 48000}
        params_wide = {"stereo_width": 2.0, "sample_rate": 48000}

        output_normal = self.effect.process(audio.copy(), params_normal)
        output_wide = self.effect.process(audio.copy(), params_wide)

        # Wide width should create more stereo (left and right more different)
        difference_normal = np.mean(np.abs(output_normal[0] - output_normal[1]))
        difference_wide = np.mean(np.abs(output_wide[0] - output_wide[1]))

        assert difference_wide > difference_normal

    def test_invalid_channel_count_raises_error(self):
        """Test that non-stereo audio raises error."""
        # 3 channels instead of 2
        audio = np.random.randn(3, 48000)
        params = {"sample_rate": 48000}

        with pytest.raises(ValueError, match="stereo audio"):
            self.effect.process(audio, params)

    def test_mid_and_side_eq_independent(self):
        """Test that mid and side EQ work independently."""
        # Create signal with both mid and side content
        mid_content = np.ones(48000) * 0.5
        side_content = np.sin(np.linspace(0, 4 * np.pi, 48000)) * 0.5

        # M/S inverse to get L/R
        left = (mid_content + side_content) / np.sqrt(2)
        right = (mid_content - side_content) / np.sqrt(2)
        audio = np.stack([left, right])

        # Apply different EQ to mid and side
        params = {
            "stereo_width": 1.0,
            "mid_eq": {"frequency": 100, "gain_db": -10, "Q": 1.0},
            "side_eq": {"frequency": 5000, "gain_db": -10, "Q": 1.0},
            "side_compression": {},
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        # Should process without error
        assert output.shape == audio.shape
        # Output should be different from input
        assert not np.allclose(output, audio)

    def test_side_compression_does_not_affect_mid(self):
        """Test that side compression only affects side channel."""
        # Pure mid signal
        audio = np.stack(
            [
                np.ones(48000) * 0.5,
                np.ones(48000) * 0.5,
            ]
        )

        comp_params = {
            "threshold_db": -20,
            "ratio": 4,
            "attack_ms": 10,
            "release_ms": 200,
        }

        params_no_comp = {"stereo_width": 1.0, "sample_rate": 48000}
        params_with_comp = {
            "stereo_width": 1.0,
            "mid_eq": {},
            "side_eq": {},
            "side_compression": comp_params,
            "sample_rate": 48000,
        }

        output_no_comp = self.effect.process(audio.copy(), params_no_comp)
        output_with_comp = self.effect.process(audio.copy(), params_with_comp)

        # Pure mid signal should be unaffected by side compression
        np.testing.assert_allclose(output_no_comp, output_with_comp, rtol=1e-5)
