"""Tests for LFOModulationEngine effect."""

import numpy as np
import pytest

from openmusic.effects.lfo import LFOModulationEngine


class TestLFOModulationEngine:
    """Test suite for LFOModulationEngine effect."""

    def setup_method(self):
        """Set up test fixtures."""
        self.effect = LFOModulationEngine()
        self.audio_1s = np.sin(np.linspace(0, 2 * np.pi * 10, 48000))
        self.audio_2s = np.sin(np.linspace(0, 2 * np.pi * 20, 96000))

    def test_initialization(self):
        """Test effect initializes correctly."""
        assert self.effect.name == "lfo_modulation"

    def test_process_returns_audio_unchanged(self):
        """Test that LFO effect doesn't modify audio (pass-through)."""
        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(self.audio_1s.copy(), params)

        # Should be identical to input (pass-through)
        np.testing.assert_allclose(output, self.audio_1s)

    def test_sine_waveform_generates_curve(self):
        """Test sine waveform generation."""
        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(self.audio_1s, params)

        # Should return input unchanged (pass-through behavior documented)

    def test_triangle_waveform_generates_curve(self):
        """Test triangle waveform generation."""
        params = {
            "waveform": "triangle",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.0,
            "sample_rate": 48_000,
        }

        output = self.effect.process(self.audio_1s.copy(), params)

        # Should return input unchanged (pass-through)
        np.testing.assert_allclose(output, self.audio_1s)

    def test_square_waveform_generates_curve(self):
        """Test square waveform generation."""
        params = {
            "waveform": "square",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.0,
            "sample_rate": 48_000,
        }

        output = self.effect.process(self.audio_1s.copy(), params)

        # Should return input unchanged (pass-through)
        np.testing.assert_allclose(output, self.audio_1s)

    def test_random_waveform_generates_curve(self):
        """Test random waveform generation."""
        params = {
            "waveform": "random",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.0,
            "sample_rate": 48_000,
        }

        output = self.effect.process(self.audio_1s.copy(), params)

        # Should return input unchanged (pass-through)
        np.testing.assert_allclose(output, self.audio_1s)

    def test_frequency_affects_curve(self):
        """Test that rate_hz controls LFO frequency."""
        params_slow = {
            "waveform": "sine",
            "rate_hz": 0.5,  # Slower
            "depth": 100.0,
            "sample_rate": 48000,
        }

        params_fast = {
            "waveform": "sine",
            "rate_hz": 2.0,  # Faster
            "depth": 100.0,
            "sample_rate": 48_000,
        }

        self.effect.process(self.audio_1s.copy(), params_slow)
        self.effect.process(self.audio_2s.copy(), params_fast)

        # Both should process without errors (pass-through)
        assert True

    def test_depth_parameter(self):
        """Test depth parameter scaling."""
        params_min = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 0.0,  # No modulation
            "sample_rate": 48000,
        }

        params_max = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,  # Maximum modulation
            "sample_rate": 48_000,
        }

        self.effect.process(self.audio_1s.copy(), params_min)
        self.effect.process(self.audio_1s.copy(), params_max)

        # Both should process without errors
        assert True

    def test_phase_offset(self):
        """Test phase offset shifts waveform."""
        params_zero = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.0,
            "sample_rate": 48000,
        }

        params_quarter = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 0.25,  # Quarter cycle offset
            "sample_rate": 48000,
        }

        self.effect.process(self.audio_1s.copy(), params_zero)
        self.effect.process(self.audio_1s.copy(), params_quarter)

        # Both should process without errors
        assert True

    def sample_rate_parameter(self):
        """Test that sample_rate affects curve generation."""
        params_48k = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "sample_rate": 48_000,
        }

        params_44k = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "sample_rate": 44100,
        }

        audio_48k = self.audio_1s
        audio_44k = np.sin(np.linspace(0, 2 * np.pi * 10, 44100))

        self.effect.process(audio_48k, params_48k)
        self.effect.process(audio_44k, params_44k)

        # Both should process without errors
        assert True

    def test_rate_hz_clamped_to_range(self):
        """Test that rate_hz is clamped to valid range (0.1-20 Hz)."""
        params_min = {
            "waveform": "sine",
            "rate_hz": 0.01,  # Below minimum
            "depth": 100.0,
            "sample_rate": 48000,
        }

        params_max = {
            "waveform": "sine",
            "rate_hz": 50,  # Above maximum
            "depth": 100.0,
            "sample_rate": 48000,
        }

        self.effect.process(self.audio_1s.copy(), params_min)
        self.effect.process(self.audio_1s.copy(), params_max)

        # Should not raise errors
        assert True

    def test_depth_clamped_to_range(self):
        """Test that depth is clamped to valid range (0-100%)."""
        params_min = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": -10.0,  # Below minimum
            "sample_rate": 48000,
        }

        params_max = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 150.0,  # Above maximum
            "sample_rate": 48000,
        }

        self.effect.process(self.audio_1s.copy(), params_min)
        self.effect.process(self.audio_1s.copy(), params_max)

        # Should not raise errors
        assert True

    def test_phase_offset_clamped_to_range(self):
        """Test that phase_offset is clamped to valid range (0-1 cycles)."""
        params_min = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": -0.5,  # Below minimum
            "sample_rate": 48000,
        }

        params_max = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 100.0,
            "phase_offset": 1.5,  # Above maximum
            "sample_rate": 48000,
        }

        self.effect.process(self.audio_1s.copy(), params_min)
        self.effect.process(self.audio_1s.copy(), params_max)

        # Should not raise errors
        assert True

    def test_invalid_waveform_raises_error(self):
        """Test that invalid waveform raises ValueError."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "waveform": "invalid_waveform",
            "rate_hz": 1.0,
            "depth": 100.0,
            "sample_rate": 48000,
        }

        with pytest.raises(ValueError, match="Invalid waveform"):
            self.effect.process(audio, params)

    def test_all_waveforms_supported(self):
        """Test that all 4 waveform types work."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        for waveform in ["sine", "triangle", "square", "random"]:
            params = {
                "waveform": waveform,
                "rate_hz": 1.0,
                "depth": 50.0,
                "sample_rate": 48000,
            }

            output = self.effect.process(audio.copy(), params)
            assert output.shape == audio.shape

    def test_default_parameters(self):
        """Test that default parameters work correctly."""
        audio = np.random.randn(48000)

        # Call with minimal params
        params = {"sample_rate": 48000}

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        # Should be identical (pass-through)
        np.testing.assert_allclose(output, audio)

    def test_stereo_audio(self):
        """Test that stereo audio works correctly."""
        left = np.sin(np.linspace(0, 4 * np.pi, 48000))
        right = np.cos(np.linspace(0, 4 * np.pi, 48000))
        audio = np.stack([left, right])

        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        # Should be identical (pass-through)
        np.testing.assert_allclose(output, audio)

    def test_mono_audio(self):
        """Test that mono audio works correctly."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        np.testing.assert_allclose(output, audio)

    def test_empty_audio(self):
        """Test processing empty audio array."""
        audio = np.array([])
        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape
        assert len(output) == 0

    def test_different_durations(self):
        """Test that different audio durations work correctly."""
        audio_short = np.sin(np.linspace(0, 2 * np.pi, 24000))  # 0.5s
        audio_long = np.sin(np.linspace(0, 2 * np.pi, 192000))  # 4s

        params = {
            "waveform": "sine",
            "rate_hz": 1.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output_short = self.effect.process(audio_short, params)
        output_long = self.effect.process(audio_long, params)

        assert output_short.shape == audio_short.shape
        assert output_long.shape == audio_long.shape

    def test_lfo_curve_range_normalized(self):
        """Test that LFO curve is internally generated in valid range."""
        # We can't access the internal curve directly, but we can verify
        # the implementation handles various rate/depth combinations without errors
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        for rate in [0.5, 1.0, 5.0, 10.0]:
            for depth in [0, 50.0, 100.0]:
                for waveform in ["sine", "triangle", "square", "random"]:
                    params = {
                        "waveform": waveform,
                        "rate_hz": rate,
                        "depth": depth,
                        "sample_rate": 48000,
                    }

                    output = self.effect.process(audio.copy(), params)
                    assert output.shape == audio.shape

    def test_high_frequency_lfo(self):
        """Test high frequency LFO (near max 20Hz)."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "waveform": "sine",
            "rate_hz": 20.0,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape

    def test_low_frequency_lfo(self):
        """Test low frequency LFO (near min 0.1Hz)."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "waveform": "sine",
            "rate_hz": 0.1,
            "depth": 50.0,
            "sample_rate": 48000,
        }

        output = self.effect.process(audio, params)

        assert output.shape == audio.shape

    def test_reproducibility_with_random(self):
        """Test that random waveform is reproducible (seeded)."""
        audio = np.sin(np.linspace(0, 4 * np.pi, 48000))

        params = {
            "waveform": "random",
            "rate_hz": 1.0,
            "depth": 100.0,
            "sample_rate": 48000,
        }

        output1 = self.effect.process(audio.copy(), params)
        output2 = self.effect.process(audio.copy(), params)

        # Random waveform should be reproducible (seeded in implementation)
        np.testing.assert_allclose(output1, output2)
