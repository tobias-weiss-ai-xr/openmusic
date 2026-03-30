"""End-to-end pipeline integration tests.

Mock ACE-Step (GPU) and Node.js effects engine.
Exercise real: ConfigParser, MixConfig, MixOrchestrator, bridge config
generation, ProgressReporter, run_pipeline, CLI commands.
"""

import io
import json
import os
import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from openmusic.cli.main import main as cli_main
from openmusic.config import ConfigParser
from openmusic.orchestrator.mix import MixConfig, MixOrchestrator
from openmusic.orchestrator.pipeline import (
    PipelineResult,
    PipelineStage,
    run_pipeline,
)
from openmusic.orchestrator.progress import ProgressReporter


def _make_minimal_wav(
    path: Path,
    duration_ms: int = 100,
    sample_rate: int = 48000,
    channels: int = 1,
) -> Path:
    """Create a minimal valid WAV file (silent PCM-16) at *path*."""
    num_samples = int(sample_rate * duration_ms / 1000)
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = num_samples * block_align
    file_size = 36 + data_size

    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", file_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))  # PCM format code
        f.write(struct.pack("<H", channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(b"\x00" * data_size)
    return path


@pytest.fixture
def sample_config_dict() -> dict:
    return {
        "length": 60,
        "bpm": 125,
        "key": "Dm",
        "output_path": "mix.flac",
        "segment_duration": 60,
        "effects_preset": "deep_dub",
        "format": "flac",
        "style": "dub_techno",
    }


@pytest.fixture
def sample_config_json(tmp_path: Path, sample_config_dict: dict) -> Path:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(sample_config_dict))
    return p


@pytest.fixture
def sample_config_yaml(tmp_path: Path, sample_config_dict: dict) -> Path:
    import yaml

    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(sample_config_dict))
    return p


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    return _make_minimal_wav(tmp_path / "stem.wav", duration_ms=50)


class TestCLIGenerateWithMockedACEStep:
    """CLI generate — ACE-Step and Node.js mocked, real CLI/config flow."""

    def test_cli_generate_outputs_result_path(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test_mix.flac"
        runner = CliRunner()

        with patch("openmusic.cli.main.MixOrchestrator") as MockOrch:
            MockOrch.return_value.generate_mix.return_value = output_file
            result = runner.invoke(
                cli_main,
                [
                    "generate",
                    "--length",
                    "1m",
                    "--bpm",
                    "125",
                    "--key",
                    "Dm",
                    "--output",
                    str(output_file),
                ],
            )

        assert result.exit_code == 0
        assert str(output_file) in result.output

    def test_cli_generate_from_json_config(
        self, tmp_path: Path, sample_config_json: Path
    ) -> None:
        output_file = tmp_path / "from_json.flac"
        runner = CliRunner()

        with patch("openmusic.cli.main.MixOrchestrator") as MockOrch:
            MockOrch.return_value.generate_mix.return_value = output_file
            result = runner.invoke(
                cli_main,
                ["generate", "--config", str(sample_config_json)],
            )

        assert result.exit_code == 0

    def test_cli_generate_from_yaml_config(
        self, tmp_path: Path, sample_config_yaml: Path
    ) -> None:
        output_file = tmp_path / "from_yaml.flac"
        runner = CliRunner()

        with patch("openmusic.cli.main.MixOrchestrator") as MockOrch:
            MockOrch.return_value.generate_mix.return_value = output_file
            result = runner.invoke(
                cli_main,
                ["generate", "--config", str(sample_config_yaml)],
            )

        assert result.exit_code == 0

    def test_cli_generate_propagates_generation_error(self) -> None:
        runner = CliRunner()

        with patch("openmusic.cli.main.MixOrchestrator") as MockOrch:
            MockOrch.return_value.generate_mix.side_effect = RuntimeError("GPU OOM")
            result = runner.invoke(cli_main, ["generate", "--length", "1m"])

        assert result.exit_code != 0
        assert "GPU OOM" in result.output

    def test_cli_validate_accepts_valid_config(self, sample_config_json: Path) -> None:
        cfg = json.loads(sample_config_json.read_text())
        cfg["output_path"] = "mix.flac"
        sample_config_json.write_text(json.dumps(cfg))

        runner = CliRunner()
        result = runner.invoke(cli_main, ["validate", str(sample_config_json)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_cli_validate_rejects_missing_keys(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("bpm: 125\nkey: Dm\n")

        runner = CliRunner()
        result = runner.invoke(cli_main, ["validate", str(bad)])
        assert result.exit_code != 0


class TestConfigToOrchestratorFlow:
    """Real ConfigParser → MixConfig → MixOrchestrator construction."""

    def test_parse_json_creates_valid_mix_config(
        self, sample_config_json: Path
    ) -> None:
        parser = ConfigParser()
        parsed = parser.parse(str(sample_config_json))

        config = MixConfig(
            length=parsed["length"],
            bpm=parsed["bpm"],
            key=parsed["key"],
            output_path=parsed["output_path"],
            segment_duration=parsed["segment_duration"],
            effects_preset=parsed["effects_preset"],
        )

        assert config.length == 60
        assert config.bpm == 125
        assert config.key == "Dm"
        assert config.segment_duration == 60
        assert config.effects_preset == "deep_dub"

    def test_parse_yaml_creates_valid_mix_config(
        self, sample_config_yaml: Path
    ) -> None:
        parser = ConfigParser()
        parsed = parser.parse(str(sample_config_yaml))

        config = MixConfig(
            length=parsed["length"],
            bpm=parsed["bpm"],
            key=parsed["key"],
            output_path=parsed["output_path"],
            segment_duration=parsed["segment_duration"],
        )

        assert config.length == 60
        assert config.key == "Dm"

    def test_parsed_config_inits_orchestrator(self, sample_config_json: Path) -> None:
        parser = ConfigParser()
        parsed = parser.parse(str(sample_config_json))

        config = MixConfig(
            length=parsed["length"],
            bpm=parsed["bpm"],
            key=parsed["key"],
            output_path=parsed["output_path"],
            segment_duration=parsed["segment_duration"],
        )

        orch = MixOrchestrator(config)
        assert orch.segment_count == 1

    def test_multi_segment_orchestrator(self) -> None:
        config = MixConfig(length=360, segment_duration=60)
        orch = MixOrchestrator(config)
        assert orch.segment_count == 6

    def test_validation_accepts_valid_config(self, sample_config_dict: dict) -> None:
        parser = ConfigParser()
        errors = parser.validate(sample_config_dict)
        assert errors == []

    def test_validation_rejects_invalid_config(self) -> None:
        parser = ConfigParser()
        invalid = {
            "length": 5,
            "bpm": 999,
            "key": "C",
            "format": "aac",
            "segment_duration": 1,
            "effects_preset": "invalid",
        }
        errors = parser.validate(invalid)
        assert len(errors) >= 1

    def test_defaults_fill_missing_keys(self, tmp_path: Path) -> None:
        partial = {"bpm": 130, "key": "Am"}
        p = tmp_path / "partial.json"
        p.write_text(json.dumps(partial))

        parser = ConfigParser()
        parsed = parser.parse(str(p))

        assert parsed["bpm"] == 130
        assert parsed["key"] == "Am"
        assert parsed["length"] == 7200
        assert parsed["effects_preset"] == "deep_dub"
        assert parsed["format"] == "flac"


_BRIDGE_REQUIRED_KEYS = {
    "sampleRate",
    "channels",
    "duration",
    "bpm",
    "key",
    "inputStems",
    "outputPath",
    "effects",
    "pattern",
}


class TestBridgeConfigSchema:
    """Validate bridge config JSON against TypeScript BridgeConfig schema."""

    def _capture_bridge_config(self, orch: MixOrchestrator, stem: Path) -> dict:
        captured: dict = {}

        def intercept(cmd, **_kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured.update(json.load(f))
            return MagicMock(returncode=0, stderr="")

        with patch("openmusic.orchestrator.mix.subprocess.run", side_effect=intercept):
            with patch("openmusic.orchestrator.mix.shutil.copy2"):
                orch._process_segment(stem)

        return captured

    def test_all_required_keys_present(self, sample_wav: Path) -> None:
        config = MixConfig(length=60, segment_duration=60)
        orch = MixOrchestrator(config)
        bridge_cfg = self._capture_bridge_config(orch, sample_wav)

        missing = _BRIDGE_REQUIRED_KEYS - set(bridge_cfg)
        assert not missing, f"Missing keys: {missing}"

    def test_effects_block_has_filter_delay_reverb(self, sample_wav: Path) -> None:
        config = MixConfig(length=60, segment_duration=60)
        orch = MixOrchestrator(config)
        bridge_cfg = self._capture_bridge_config(orch, sample_wav)

        effects = bridge_cfg["effects"]
        for key in ("filter", "delay", "reverb"):
            assert key in effects, f"effects.{key} missing"

        assert "type" in effects["filter"]
        assert "frequency" in effects["filter"]
        assert "Q" in effects["filter"]

    def test_pattern_block_has_style_and_variation(self, sample_wav: Path) -> None:
        config = MixConfig(length=60, segment_duration=60)
        orch = MixOrchestrator(config)
        bridge_cfg = self._capture_bridge_config(orch, sample_wav)

        pattern = bridge_cfg["pattern"]
        assert "style" in pattern
        assert "variation" in pattern

    def test_input_stems_is_list_of_dicts(self, sample_wav: Path) -> None:
        config = MixConfig(length=60, segment_duration=60)
        orch = MixOrchestrator(config)
        bridge_cfg = self._capture_bridge_config(orch, sample_wav)

        stems = bridge_cfg["inputStems"]
        assert isinstance(stems, list)
        assert len(stems) >= 1
        for stem in stems:
            assert "path" in stem
            assert "role" in stem

    def test_config_reflects_mix_config_values(self, sample_wav: Path) -> None:
        config = MixConfig(length=60, segment_duration=60, bpm=130, key="Am")
        orch = MixOrchestrator(config)
        bridge_cfg = self._capture_bridge_config(orch, sample_wav)

        assert bridge_cfg["bpm"] == 130
        assert bridge_cfg["key"] == "Am"
        assert bridge_cfg["duration"] == 60


class TestProgressReportingFormat:
    """ProgressReporter console output format."""

    def test_single_segment_format(self) -> None:
        reporter = ProgressReporter(total=1)
        buf = io.StringIO()
        reporter._output = buf

        reporter.start_segment(1)

        output = buf.getvalue()
        assert "[1/1]" in output
        assert "Generating segment 1" in output

    def test_multiple_segments_sequential(self) -> None:
        reporter = ProgressReporter(total=3)
        buf = io.StringIO()
        reporter._output = buf

        reporter.start_segment(1)
        reporter.finish_segment(5.0)
        reporter.start_segment(2)
        reporter.finish_segment(5.0)
        reporter.start_segment(3)

        output = buf.getvalue()
        assert "[1/3]" in output
        assert "[2/3]" in output
        assert "[3/3]" in output

    def test_stage_change_callback_fires(self) -> None:
        reporter = ProgressReporter(total=2)
        stages_seen: list[str] = []
        reporter.on_stage_change(lambda **kw: stages_seen.append(kw["stage"]))

        reporter.start_segment(1)
        reporter.start_segment(2)

        assert stages_seen == ["generate", "generate"]

    def test_complete_callback_fires_on_last_segment(self) -> None:
        reporter = ProgressReporter(total=2)
        completed = False

        def mark_complete():
            nonlocal completed
            completed = True

        reporter.on_complete(mark_complete)

        reporter.start_segment(1)
        reporter.finish_segment(1.0)
        reporter.start_segment(2)
        reporter.finish_segment(1.0)

        assert completed is True


class TestPipelineGeneratorOutput:
    """run_pipeline yields correct PipelineResult objects."""

    def test_pipeline_yields_all_stages(self) -> None:
        config = MixConfig(length=60, segment_duration=60)

        with patch("openmusic.orchestrator.pipeline.MixOrchestrator") as MockOrch:
            mock_orch = MockOrch.return_value
            mock_orch.segment_count = 1
            mock_orch._generate_segment.return_value = Path("/tmp/raw.wav")
            mock_orch._process_segment.return_value = Path("/tmp/processed.wav")

            results = list(run_pipeline(config))

        stages = [r.stage for r in results]
        assert PipelineStage.GENERATE in stages
        assert PipelineStage.PROCESS in stages
        assert PipelineStage.EXPORT in stages

    def test_pipeline_results_are_successful(self) -> None:
        config = MixConfig(length=60, segment_duration=60)

        with patch("openmusic.orchestrator.pipeline.MixOrchestrator") as MockOrch:
            mock_orch = MockOrch.return_value
            mock_orch.segment_count = 1
            mock_orch._generate_segment.return_value = Path("/tmp/raw.wav")
            mock_orch._process_segment.return_value = Path("/tmp/processed.wav")

            results = list(run_pipeline(config))

        for r in results:
            assert isinstance(r, PipelineResult)
            assert r.success is True
            assert r.error is None
            assert r.duration >= 0

    def test_pipeline_reports_generation_failure(self) -> None:
        config = MixConfig(length=60, segment_duration=60)

        with patch("openmusic.orchestrator.pipeline.MixOrchestrator") as MockOrch:
            mock_orch = MockOrch.return_value
            mock_orch.segment_count = 1
            mock_orch._generate_segment.side_effect = RuntimeError(
                "ACE-Step not available"
            )

            results = list(run_pipeline(config))

        failed = [r for r in results if not r.success]
        assert len(failed) == 1
        assert "ACE-Step not available" in failed[0].error
        assert failed[0].stage == PipelineStage.GENERATE

    def test_pipeline_handles_process_failure(self) -> None:
        config = MixConfig(length=60, segment_duration=60)

        with patch("openmusic.orchestrator.pipeline.MixOrchestrator") as MockOrch:
            mock_orch = MockOrch.return_value
            mock_orch.segment_count = 1
            mock_orch._generate_segment.return_value = Path("/tmp/raw.wav")
            mock_orch._process_segment.side_effect = RuntimeError("Node.js crashed")

            results = list(run_pipeline(config))

        failed = [r for r in results if not r.success]
        assert len(failed) >= 1

    def test_pipeline_multi_segment(self) -> None:
        config = MixConfig(length=180, segment_duration=60)

        with patch("openmusic.orchestrator.pipeline.MixOrchestrator") as MockOrch:
            mock_orch = MockOrch.return_value
            mock_orch.segment_count = 3
            mock_orch._generate_segment.return_value = Path("/tmp/raw.wav")
            mock_orch._process_segment.return_value = Path("/tmp/processed.wav")

            results = list(run_pipeline(config))

        gen_results = [
            r for r in results if r.stage == PipelineStage.GENERATE and r.success
        ]
        proc_results = [
            r for r in results if r.stage == PipelineStage.PROCESS and r.success
        ]
        export_results = [r for r in results if r.stage == PipelineStage.EXPORT]

        assert len(gen_results) == 3
        assert len(proc_results) == 3
        assert len(export_results) == 1
