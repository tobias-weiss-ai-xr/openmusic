import json
from pathlib import Path
import textwrap
import tempfile

import pytest

from openmusic.config import ConfigParser


def test_get_defaults_contains_expected_keys():
    cp = ConfigParser()
    defaults = cp.get_defaults()
    assert defaults["length"] == 7200
    assert defaults["bpm"] == 125
    assert defaults["key"] == "Dm"
    assert defaults["output_path"] == "mix.flac"
    assert defaults["segment_duration"] == 180
    assert defaults["effects_preset"] == "deep_dub"
    assert defaults["format"] == "flac"
    assert defaults["style"] == "dub_techno"


def test_parse_yaml_uses_defaults_and_overrides(tmp_path: Path):
    yaml_content = {
        "length": 3600,
        "bpm": 140,
        "key": "Am",
        "output_path": "out.flac",
        "segment_duration": 120,
        "effects_preset": "club_dub",
        "format": "flac",
        "style": "dub_techno",
    }
    p = tmp_path / "config.yaml"
    import yaml  # type: ignore

    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(yaml_content, f)

    cp = ConfigParser()
    cfg = cp.parse(str(p))
    assert cfg["length"] == 3600
    assert cfg["bpm"] == 140
    assert cfg["key"] == "Am"
    assert cfg["output_path"] == "out.flac"
    assert cfg["segment_duration"] == 120
    assert cfg["effects_preset"] == "club_dub"
    assert cfg["format"] == "flac"
    assert cfg["style"] == "dub_techno"


def test_parse_json_uses_defaults_and_overrides(tmp_path: Path):
    json_content = {
        "length": 1000,
        "bpm": 130,
        "key": "Em",
        "output_path": "data/mix.wav",
        "segment_duration": 60,
        "effects_preset": "minimal_dub",
        "format": "wav",
        "style": "dub_techno",
    }
    p = tmp_path / "config.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(json_content, f)

    cp = ConfigParser()
    cfg = cp.parse(str(p))
    assert cfg["length"] == 1000
    assert cfg["bpm"] == 130
    assert cfg["key"] == "Em"
    assert cfg["output_path"] == "data/mix.wav"
    assert cfg["segment_duration"] == 60
    assert cfg["effects_preset"] == "minimal_dub"
    assert cfg["format"] == "wav"
    assert cfg["style"] == "dub_techno"


def test_validate_valid_config_returns_no_errors():
    cp = ConfigParser()
    cfg = cp.get_defaults()
    errors = cp.validate(cfg)
    assert errors == []


def test_validate_invalid_values_returns_errors():
    cp = ConfigParser()
    cfg = cp.get_defaults().copy()
    cfg["bpm"] = 999  # invalid
    cfg["length"] = 10  # invalid
    cfg["key"] = "X#m"  # invalid minor key pattern
    cfg["format"] = "aac"  # invalid format
    cfg["segment_duration"] = 5  # invalid
    cfg["effects_preset"] = "superdub"  # invalid
    errors = cp.validate(cfg)
    assert len(errors) >= 1
