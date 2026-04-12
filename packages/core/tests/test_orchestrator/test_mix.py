"""Tests for MixConfig and MixOrchestrator."""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import numpy as np
import pytest
import soundfile as sf

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

        orch = MixOrchestrator(config)

        input_path = Path("/tmp/segment_0.wav")

        # Create actual file for bridge to return
        def mock_bridge_call(input_files, output_path, config):
            import tempfile

            # Create a minimal WAV file
            sample_rate = 48000
            num_samples = sample_rate  # 1 second
            audio = np.zeros((num_samples, 2), dtype=np.float32)
            sf.write(output_path, audio, sample_rate, format="WAV")
            return output_path

        mock_bridge.call_audio_engine.side_effect = mock_bridge_call

        result = orch._process_segment(input_path)

        mock_bridge.call_audio_engine.assert_called_once()
        assert isinstance(result, Path)
        assert result.exists()

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

        orch = MixOrchestrator(config)

        # Create actual file for bridge to return
        def mock_bridge_call(input_files, output_path, config):
            sample_rate = 48000
            num_samples = sample_rate  # 1 second
            audio = np.zeros((num_samples, 2), dtype=np.float32)
            sf.write(output_path, audio, sample_rate, format="WAV")
            return output_path

        mock_bridge.call_audio_engine.side_effect = mock_bridge_call

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

        orch = MixOrchestrator(config)

        # Create actual file for bridge to return
        def mock_bridge_call(input_files, output_path, config):
            sample_rate = 48000
            num_samples = sample_rate  # 1 second
            audio = np.zeros((num_samples, 2), dtype=np.float32)
            sf.write(output_path, audio, sample_rate, format="WAV")
            return output_path

        mock_bridge.call_audio_engine.side_effect = mock_bridge_call

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

        orch = MixOrchestrator(config)

        # Create actual file for bridge to return
        def mock_bridge_call(input_files, output_path, config):
            sample_rate = 48000
            num_samples = sample_rate  # 1 second
            audio = np.zeros((num_samples, 2), dtype=np.float32)
            sf.write(output_path, audio, sample_rate, format="WAV")
            return output_path

        mock_bridge.call_audio_engine.side_effect = mock_bridge_call

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


class TestMixOrchestratorAssembly:
    def _make_test_wav(self, path: Path, duration_ms: int = 100) -> Path:
        """Create a minimal valid WAV file using soundfile."""
        sample_rate = 48000
        channels = 2
        num_samples = int(sample_rate * duration_ms / 1000)
        # Create silent audio
        audio = np.zeros((num_samples, channels), dtype=np.float32)
        sf.write(str(path), audio, sample_rate, format="WAV")
        return path

    def test_assemble_segments_creates_output_file(self, tmp_path: Path) -> None:
        config = MixConfig(output_path=str(tmp_path / "mix.wav"))
        orch = MixOrchestrator(config)

        # Create two test segments
        seg1 = self._make_test_wav(tmp_path / "seg1.wav", duration_ms=100)
        seg2 = self._make_test_wav(tmp_path / "seg2.wav", duration_ms=100)

        orch._assemble_segments([seg1, seg2], Path(config.output_path))

        output_path = Path(config.output_path)
        assert output_path.exists()

        # Verify the output file has reasonable duration
        audio, sr = sf.read(str(output_path))
        # Two 100ms segments (4800 each) minus crossfade (1200 = 1/4 of 4800)
        expected_samples = 4800 + 4800 - 1200
        assert audio.shape[0] == expected_samples

    def test_assemble_segments_with_single_segment(self, tmp_path: Path) -> None:
        config = MixConfig(output_path=str(tmp_path / "mix.wav"))
        orch = MixOrchestrator(config)

        seg = self._make_test_wav(tmp_path / "seg.wav", duration_ms=100)
        orch._assemble_segments([seg], Path(config.output_path))

        audio, sr = sf.read(str(config.output_path))
        expected_samples = int(48000 * 0.1)
        assert audio.shape[0] == expected_samples

    def test_assemble_segments_handles_wav_format(self, tmp_path: Path) -> None:
        config = MixConfig(output_path=str(tmp_path / "output.wav"))
        orch = MixOrchestrator(config)

        seg1 = self._make_test_wav(tmp_path / "seg1.wav")
        seg2 = self._make_test_wav(tmp_path / "seg2.wav")

        orch._assemble_segments([seg1, seg2], Path(config.output_path))

        output_path = Path(config.output_path)
        assert output_path.exists()
        assert output_path.suffix == ".wav"

    def test_assemble_segments_handles_flac_format(self, tmp_path: Path) -> None:
        config = MixConfig(output_path=str(tmp_path / "output.flac"))
        orch = MixOrchestrator(config)

        seg1 = self._make_test_wav(tmp_path / "seg1.wav")
        seg2 = self._make_test_wav(tmp_path / "seg2.wav")

        orch._assemble_segments([seg1, seg2], Path(config.output_path))

        output_path = Path(config.output_path)
        assert output_path.exists()
        assert output_path.suffix == ".flac"

    def test_assemble_segments_empty_list_raises_error(self, tmp_path: Path) -> None:
        config = MixConfig(output_path=str(tmp_path / "mix.wav"))
        orch = MixOrchestrator(config)

        with pytest.raises(ValueError, match="No segments to assemble"):
            orch._assemble_segments([], Path(config.output_path))

    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    def test_process_segment_copies_file_from_temp_dir(
        self, MockBridge, MockGenerator, tmp_path: Path
    ) -> None:
        config = MixConfig(length=60, segment_duration=60)
        mock_bridge = MockBridge.return_value

        orch = MixOrchestrator(config)
        orch.config.output_path = str(tmp_path / "test_output.wav")

        input_path = self._make_test_wav(tmp_path / "input.wav", duration_ms=50)

        # The bridge will write to a temp path that gets deleted
        def write_to_temp(input_files, output_path, config):
            # Write a file to the temp path
            self._make_test_wav(Path(output_path), duration_ms=50)
            return output_path

        mock_bridge.call_audio_engine.side_effect = write_to_temp

        result = orch._process_segment(input_path)

        # The returned path should point to a file that exists
        assert result.exists()
        assert result.is_file()

    @patch("openmusic.orchestrator.mix.ACEStepGenerator")
    @patch("openmusic.orchestrator.mix.TypeScriptBridge")
    def test_generate_mix_assembles_segments(
        self, MockBridge, MockGenerator, tmp_path: Path
    ) -> None:
        config = MixConfig(
            length=120, segment_duration=60, output_path=str(tmp_path / "mix.wav")
        )
        mock_gen = MockGenerator.return_value
        mock_bridge = MockBridge.return_value

        orch = MixOrchestrator(config)

        # Set up mocks to create actual files
        counter = [0]

        def mock_generate_texture(prompt, duration, bpm, key):
            counter[0] += 1
            return self._make_test_wav(tmp_path / f"raw_{counter[0]}.wav")

        def write_to_temp(input_files, output_path, config):
            return self._make_test_wav(Path(output_path), duration_ms=50)

        mock_gen.generate_texture.side_effect = mock_generate_texture
        mock_bridge.call_audio_engine.side_effect = write_to_temp

        result_path = orch.generate_mix()

        # Verify output file exists
        assert result_path.exists()
        assert result_path == Path(config.output_path)

        # Verify the file has reasonable duration (should be ~2 segments)
        audio, sr = sf.read(str(result_path))
        # 2 segments of 50ms (2400 samples each) minus crossfade (600 = 1/4 of 2400)
        expected_samples = 2400 + 2400 - 600
        assert audio.shape[0] >= expected_samples
