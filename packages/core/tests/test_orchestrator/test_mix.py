"""Tests for MixConfig and MixOrchestrator."""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from openmusic.orchestrator.mix import MixConfig, MixOrchestrator


class TestMixConfigDefaults:
    def test_default_length_is_7200(self):
        config = MixConfig()
        assert config.length == 7200

    def test_default_bpm_is_125(self):
        config = MixConfig()
        assert config.bpm == 125

    def test_default_key_is_dm(self):
        config = MixConfig()
        assert config.key == "Dm"

    def test_default_output_path_is_mix_flac(self):
        config = MixConfig()
        assert config.output_path == "mix.flac"

    def test_default_segment_duration_is_180(self):
        config = MixConfig()
        assert config.segment_duration == 180.0

    def test_default_effects_preset_is_deep_dub(self):
        config = MixConfig()
        assert config.effects_preset == "deep_dub"


class TestMixConfigCustom:
    def test_custom_values(self):
        config = MixConfig(
            length=3600,
            bpm=130,
            key="Am",
            output_path="custom.flac",
            segment_duration=120,
            effects_preset="minimal",
        )
        assert config.length == 3600
        assert config.bpm == 130
        assert config.key == "Am"
        assert config.output_path == "custom.flac"
        assert config.segment_duration == 120
        assert config.effects_preset == "minimal"


class TestMixOrchestratorSegmentCount:
    def test_segment_count_for_2h_mix(self):
        config = MixConfig(length=7200, segment_duration=180)
        orchestrator = MixOrchestrator(config)
        assert orchestrator.segment_count == 40

    def test_segment_count_rounds_up(self):
        config = MixConfig(length=361, segment_duration=180)
        orchestrator = MixOrchestrator(config)
        assert orchestrator.segment_count == 3

    def test_segment_count_exact(self):
        config = MixConfig(length=360, segment_duration=180)
        orchestrator = MixOrchestrator(config)
        assert orchestrator.segment_count == 2


class TestMixOrchestratorSegmentPrompts:
    def test_early_segment_prompt_intro(self):
        config = MixConfig()
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(0, 10)
        assert any(
            w in prompt.lower() for w in ["intro", "build", "subtle", "atmosphere"]
        )

    def test_early_segment_includes_key_and_bpm(self):
        config = MixConfig(key="Am", bpm=130)
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(0, 10)
        assert "Am" in prompt
        assert "130" in prompt

    def test_mid_segment_prompt_development(self):
        config = MixConfig()
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(5, 10)
        assert any(
            w in prompt.lower()
            for w in ["dub techno", "development", "groove", "rhythm"]
        )

    def test_late_segment_prompt_climax(self):
        config = MixConfig()
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(9, 10)
        assert any(w in prompt.lower() for w in ["climax", "outro", "resolve", "fade"])

    def test_first_segment_is_intro(self):
        config = MixConfig()
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(0, 40)
        assert "dub techno" in prompt.lower()

    def test_last_segment_is_outro(self):
        config = MixConfig()
        orch = MixOrchestrator(config)
        prompt = orch._get_segment_prompt(39, 40)
        assert "outro" in prompt.lower()


class TestMixOrchestratorGenerateSegment:
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_generate_segment_calls_acestep(self, MockGenerator):
        config = MixConfig(length=180, segment_duration=180)
        mock_gen = MockGenerator.return_value
        mock_gen.generate_texture.return_value = Path("/tmp/segment_0.wav")

        orch = MixOrchestrator(config)
        result = orch._generate_segment(0, 1)

        mock_gen.generate_texture.assert_called_once()
        assert result == Path("/tmp/segment_0.wav")

    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_generate_segment_passes_prompt(self, MockGenerator):
        config = MixConfig(length=180, segment_duration=180, bpm=125, key="Dm")
        mock_gen = MockGenerator.return_value
        mock_gen.generate_texture.return_value = Path("/tmp/segment_0.wav")

        orch = MixOrchestrator(config)
        orch._generate_segment(0, 1)

        call_args = mock_gen.generate_texture.call_args
        assert call_args[1]["duration"] == 180
        assert call_args[1]["bpm"] == 125
        assert call_args[1]["key"] == "Dm"


class TestMixOrchestratorProcessSegment:
    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_calls_bridge(self, MockGenerator, MockBridge):
        config = MixConfig()
        mock_bridge = MockBridge.return_value
        mock_bridge.call_audio_engine.return_value = (
            "/tmp/openmusic-out-xxx/processed.wav"
        )

        orch = MixOrchestrator(config)

        input_path = Path("/tmp/segment_0.wav")
        result = orch._process_segment(input_path)

        mock_bridge.call_audio_engine.assert_called_once()
        assert isinstance(result, Path)

    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_propagates_bridge_error(self, MockGenerator, MockBridge):
        from openmusic.bridge.typescript_bridge import BridgeError

        config = MixConfig()
        mock_bridge = MockBridge.return_value
        mock_bridge.call_audio_engine.side_effect = BridgeError(
            "Effects processing failed", stderr="config validation failed"
        )

        orch = MixOrchestrator(config)

        with pytest.raises(BridgeError, match="Effects processing failed"):
            orch._process_segment(Path("/tmp/segment_0.wav"))

    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_passes_effects_config_to_bridge(
        self, MockGenerator, MockBridge
    ):
        config = MixConfig()
        mock_bridge = MockBridge.return_value
        mock_bridge.call_audio_engine.return_value = (
            "/tmp/openmusic-out-xxx/processed.wav"
        )

        orch = MixOrchestrator(config)

        orch._process_segment(Path("/tmp/segment_0.wav"))

        call_args = mock_bridge.call_audio_engine.call_args
        passed_config = call_args[1]["config"]

        assert passed_config["bpm"] == 125
        assert passed_config["key"] == "Dm"
        assert passed_config["duration"] == 180.0
        assert passed_config["sampleRate"] == 48000
        assert passed_config["channels"] == 2

    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_effects_config_has_full_schema(
        self, MockGenerator, MockBridge
    ):
        config = MixConfig()
        mock_bridge = MockBridge.return_value
        mock_bridge.call_audio_engine.return_value = (
            "/tmp/openmusic-out-xxx/processed.wav"
        )

        orch = MixOrchestrator(config)
        orch._process_segment(Path("/tmp/segment_0.wav"))

        call_args = mock_bridge.call_audio_engine.call_args
        effects = call_args[1]["config"]["effects"]

        for key in ("delay", "reverb", "filter", "distortion", "vinyl"):
            assert key in effects, f"effects.{key} missing"
            assert "enabled" in effects[key], f"effects.{key}.enabled missing"

        assert "primaryTime" in effects["delay"]
        assert "secondaryTime" in effects["delay"]
        assert "primaryMix" in effects["delay"]
        assert "secondaryMix" in effects["delay"]
        assert "primaryFeedback" in effects["delay"]
        assert "secondaryFeedback" in effects["delay"]

        assert "decay" in effects["reverb"]
        assert "preDelay" in effects["reverb"]
        assert "mix" in effects["reverb"]
        assert "inputFilterFreq" in effects["reverb"]
        assert "inputFilterQ" in effects["reverb"]

        assert "type" in effects["filter"]
        assert "frequency" in effects["filter"]
        assert "Q" in effects["filter"]
        assert "lfoRate" in effects["filter"]
        assert "lfoDepth" in effects["filter"]

        assert "amount" in effects["distortion"]
        assert "mix" in effects["distortion"]

        assert "level" in effects["vinyl"]
        assert "hissLevel" in effects["vinyl"]

    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_uses_correct_preset(self, MockGenerator, MockBridge):
        config = MixConfig(effects_preset="club_dub")
        mock_bridge = MockBridge.return_value
        mock_bridge.call_audio_engine.return_value = (
            "/tmp/openmusic-out-xxx/processed.wav"
        )

        orch = MixOrchestrator(config)
        orch._process_segment(Path("/tmp/segment_0.wav"))

        call_args = mock_bridge.call_audio_engine.call_args
        effects = call_args[1]["config"]["effects"]
        assert effects["delay"]["primaryTime"] == 0.3
        assert effects["filter"]["frequency"] == 1000

    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    def test_process_segment_rejects_unknown_preset(self, MockGenerator, MockBridge):
        config = MixConfig(effects_preset="nonexistent")
        orch = MixOrchestrator(config)

        with pytest.raises(ValueError, match="Unknown effects preset"):
            orch._process_segment(Path("/tmp/segment_0.wav"))
