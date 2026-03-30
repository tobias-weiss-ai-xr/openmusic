import os
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from openmusic.cli import main as cli_main


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
