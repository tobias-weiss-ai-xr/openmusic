"""Tests for Stable Audio Open generator wrapper."""

import pytest


class TestStableAudioGenerator:
    def test_config_dataclass_defaults(self):
        from openmusic.acestep.stable_audio_generator import StableAudioConfig

        config = StableAudioConfig()
        assert config.model_name == "stabilityai/stable-audio-open-1.0"
        assert config.sample_rate == 32000
        assert config.max_duration == 30

    def test_config_dataclass_custom(self):
        from openmusic.acestep.stable_audio_generator import StableAudioConfig

        config = StableAudioConfig(model_name="custom/model", max_duration=60)
        assert config.model_name == "custom/model"
        assert config.max_duration == 60
