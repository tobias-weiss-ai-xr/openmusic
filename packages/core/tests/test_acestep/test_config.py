"""Tests for ACE-Step configuration dataclasses."""

import pytest
from dataclasses import dataclass, field
from openmusic.acestep.config import ACEStepConfig, GenerationParams


class TestACEStepConfig:
    """Tests for ACEStepConfig dataclass."""

    def test_default_values(self):
        config = ACEStepConfig()
        assert config.model_path == "acestep-v15-turbo"
        assert config.device == "auto"
        assert config.audio_format == "flac"
        assert config.max_duration == 600
        assert config.inference_steps == 8

    def test_custom_values(self):
        config = ACEStepConfig(
            model_path="acestep-v15-base",
            device="cuda",
            audio_format="wav",
            max_duration=300,
            inference_steps=16,
        )
        assert config.model_path == "acestep-v15-base"
        assert config.device == "cuda"
        assert config.audio_format == "wav"
        assert config.max_duration == 300
        assert config.inference_steps == 16

    def test_is_dataclass(self):
        assert hasattr(ACEStepConfig, "__dataclass_fields__")

    def test_frozen_is_false(self):
        """Config should be mutable."""
        config = ACEStepConfig()
        config.device = "cpu"
        assert config.device == "cpu"


class TestGenerationParams:
    """Tests for GenerationParams dataclass."""

    def test_default_values(self):
        params = GenerationParams()
        assert params.prompt == ""
        assert params.bpm is None
        assert params.key is None
        assert params.duration == 30
        assert params.instrumental is True

    def test_custom_values(self):
        params = GenerationParams(
            prompt="deep dub techno",
            bpm=125,
            key="Am",
            duration=180,
            instrumental=True,
        )
        assert params.prompt == "deep dub techno"
        assert params.bpm == 125
        assert params.key == "Am"
        assert params.duration == 180
        assert params.instrumental is True

    def test_is_dataclass(self):
        assert hasattr(GenerationParams, "__dataclass_fields__")
