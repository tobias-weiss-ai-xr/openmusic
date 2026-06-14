import numpy as np
import pytest
from openmusic.effects.parameter_automation import ParameterAutomation


class TestParameterAutomation:
    def setup_method(self):
        self.effect = ParameterAutomation()

    def test_initialization(self):
        assert self.effect.name == "parameter_automation"

    def test_gain_envelope_from_zero(self):
        audio = np.ones(48000) * 0.5
        params = {"auto_type": "gain_envelope", "start": 0.0, "end": 1.0, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert output[0] < output[-1]  # Should ramp up

    def test_tremolo_modulates(self):
        audio = np.ones(48000) * 0.5
        params = {"auto_type": "tremolo", "rate_hz": 2.0, "depth": 1.0, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
        assert not np.allclose(output, audio, atol=1e-6)

    def test_random_walk_works(self):
        audio = np.ones(48000) * 0.5
        params = {"auto_type": "random_walk_gain", "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape

    def test_unknown_type_passthrough(self):
        audio = np.random.randn(48000) * 0.5
        params = {"auto_type": "unknown", "sample_rate": 48000}
        output = self.effect.process(audio, params)
        np.testing.assert_allclose(output, audio, atol=1e-10)

    def test_stereo_audio(self):
        audio = np.random.randn(2, 48000) * 0.5
        params = {"auto_type": "gain_envelope", "start": 0.0, "end": 0.5, "sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
