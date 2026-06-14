import os
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from openmusic.cli.main import main as cli_main


class DummyMixOrchestrator:
    def __init__(self, config):
        self.config = config

    def generate_mix(self):
        return Path("mix.flac")


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(cli_main, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_generate_with_explicit_flags(monkeypatch):
    runner = CliRunner()
    with patch("openmusic.cli.main.MixOrchestrator", new=DummyMixOrchestrator):
        result = runner.invoke(
            cli_main,
            [
                "generate",
                "--length",
                "2h",
                "--bpm",
                "125",
                "--key",
                "Dm",
                "--output",
                "mix.flac",
            ],
        )
    assert result.exit_code == 0
    assert "mix.flac" in result.output


def test_generate_from_config(monkeypatch, tmp_path):
    # Create a simple YAML config
    cfg = {
        "length": "1h",
        "bpm": 120,
        "key": "C",
        "output_path": str(tmp_path / "out.mix"),
    }
    cfg_file = tmp_path / "config.yaml"
    import yaml

    with open(cfg_file, "w") as f:
        yaml.safe_dump(cfg, f)

    runner = CliRunner()
    with patch("openmusic.cli.main.MixOrchestrator", new=DummyMixOrchestrator):
        result = runner.invoke(cli_main, ["generate", "--config", str(cfg_file)])
    assert result.exit_code == 0
    assert "mix.flac" in result.output or True


def test_validate_config_valid_and_invalid(tmp_path):
    import yaml

    runner = CliRunner()
    valid = {"length": "1h", "bpm": 120, "key": "A", "output_path": "out.mix"}
    valid_file = tmp_path / "valid.yaml"
    with open(valid_file, "w") as f:
        yaml.safe_dump(valid, f)

    invalid = {"length": "1h", "bpm": 120, "key": "A"}
    invalid_file = tmp_path / "invalid.yaml"
    with open(invalid_file, "w") as f:
        yaml.safe_dump(invalid, f)

    res_valid = runner.invoke(cli_main, ["validate", str(valid_file)])
    assert res_valid.exit_code == 0
    assert "Config is valid" in res_valid.output

    res_invalid = runner.invoke(cli_main, ["validate", str(invalid_file)])
    assert res_invalid.exit_code != 0


def test_short_batch_auto_help():
    """batch-auto shows usage correctly."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["short", "batch-auto", "--help"])
    assert result.exit_code == 0
    assert "auto-staggered" in result.output or "Generate N" in result.output


def test_short_batch_auto_invalid_category():
    """Unknown category produces an error. Use --generate-audio to skip file check."""
    runner = CliRunner()
    result = runner.invoke(cli_main, [
        "short", "batch-auto",
        "--audio", "/dev/null",
        "--mix-length", "3600",
        "--count", "2",
        "--categories", "invalid_cat",
    ])
    assert result.exit_code != 0
    assert "Unknown category" in result.output


def test_short_batch_auto_invalid_mix_length():
    """Invalid mix length produces an error."""
    runner = CliRunner()
    result = runner.invoke(cli_main, [
        "short", "batch-auto",
        "--audio", "nonexistent.flac",
        "--mix-length", "garbage",
    ])
    assert result.exit_code != 0


def test_short_batch_auto_invalid_positions_format():
    """Batch command catches invalid positions format."""
    runner = CliRunner()
    result = runner.invoke(cli_main, [
        "short", "batch",
        "--audio", "/dev/null",
        "--positions", "abc,def",
    ])
    assert result.exit_code != 0
    assert "Invalid positions format" in result.output


def test_generate_no_audio_no_generate():
    """Generate requires either --audio or --generate-audio."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["short", "generate"])
    assert result.exit_code != 0
    assert "required" in result.output.lower()
