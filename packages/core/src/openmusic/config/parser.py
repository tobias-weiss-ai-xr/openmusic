import json
import re
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


class ConfigParser:
    """Config parser for OpenMusic.

    Supports YAML (primary) and JSON (secondary) config files. Provides
    methods to parse, validate and produce default configurations compatible
    with the MixConfig dataclass in the orchestrator.
    """

    # Validation constants
    _MIN_BPM = 60
    _MAX_BPM = 200
    _MIN_LENGTH = 60
    _MAX_LENGTH = 14400
    _VALID_FORMATS = {"wav", "flac", "mp3"}
    _MIN_SEGMENT = 30
    _MAX_SEGMENT = 600
    _VALID_PRESETS = {"deep_dub", "minimal_dub", "club_dub"}
    _MINOR_KEY_REGEX = re.compile(r"^[A-G](?:#|b)?m$")

    def __init__(self) -> None:
        pass

    # Public API
    def parse(self, config_path: str) -> Dict[str, Any]:
        """Parse a YAML/JSON config file into a dictionary.

        If the file extension is YAML-like, YAML will be loaded. If JSON,
        JSON will be loaded. If the extension is unknown, YAML will be attempted
        first, then JSON as a fallback.
        The loaded data will be merged with defaults to ensure all keys exist.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        data: Dict[str, Any] = {}
        ext = path.suffix.lower()
        loaded = None

        # Helper to load YAML safely if available
        def _load_yaml(p: Path) -> Any:
            if yaml is None:
                raise RuntimeError(
                    "PyYAML is not installed; YAML parsing is unavailable."
                )
            with p.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)  # type: ignore

        # Helper to load JSON
        def _load_json(p: Path) -> Any:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)

        try:
            if ext in {".yaml", ".yml"}:
                loaded = _load_yaml(path)
            elif ext == ".json":
                loaded = _load_json(path)
            else:
                # Unknown extension: try YAML first, then JSON
                try:
                    loaded = _load_yaml(path)
                except Exception:
                    loaded = _load_json(path)
        except Exception:
            # If loading fails for any reason, raise to caller
            raise

        if not isinstance(loaded, dict):
            raise ValueError(
                "Config file must contain a JSON/YAML object at top level."
            )

        data = self.get_defaults()
        data.update(loaded)
        return data

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate the provided config dict. Returns a list of error messages."""
        errors: List[str] = []

        bpm = config.get("bpm")
        if not isinstance(bpm, int) or not (self._MIN_BPM <= bpm <= self._MAX_BPM):
            errors.append(
                f"bpm must be an integer between {self._MIN_BPM} and {self._MAX_BPM}"
            )

        length = config.get("length")
        if not isinstance(length, (int, float)) or not (
            self._MIN_LENGTH <= length <= self._MAX_LENGTH
        ):
            errors.append(
                f"length must be a number between {self._MIN_LENGTH} and {self._MAX_LENGTH} seconds"
            )

        key = config.get("key")
        if not isinstance(key, str) or not self._MINOR_KEY_REGEX.match(key):
            errors.append(
                "key must be a valid minor key, e.g. Dm, Em, Am, Cm, Fm, Bm, Gm"
            )

        fmt = config.get("format")
        if not isinstance(fmt, str) or fmt.lower() not in self._VALID_FORMATS:
            errors.append(f"format must be one of {sorted(self._VALID_FORMATS)}")

        segment = config.get("segment_duration")
        if not isinstance(segment, (int, float)) or not (
            self._MIN_SEGMENT <= segment <= self._MAX_SEGMENT
        ):
            errors.append(
                f"segment_duration must be between {self._MIN_SEGMENT} and {self._MAX_SEGMENT} seconds"
            )

        preset = config.get("effects_preset")
        if not isinstance(preset, str) or preset not in self._VALID_PRESETS:
            errors.append(
                f"effects_preset must be one of {sorted(self._VALID_PRESETS)}"
            )

        return errors

    def get_defaults(self) -> Dict[str, Any]:
        """Return the default configuration values."""
        return {
            "length": 7200,
            "bpm": 125,
            "key": "Dm",
            "output_path": "mix.flac",
            "segment_duration": 180,
            "effects_preset": "deep_dub",
            # Optional extras used by higher-level tooling / tests
            "format": "flac",
            "style": "dub_techno",
        }
