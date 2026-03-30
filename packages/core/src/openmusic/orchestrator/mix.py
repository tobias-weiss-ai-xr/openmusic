import math
from dataclasses import dataclass, field
from pathlib import Path

from openmusic.acestep import ACEStepGenerator
from openmusic.bridge.typescript_bridge import TypeScriptBridge

_EFFECTS_PRESETS: dict[str, dict] = {
    "deep_dub": {
        "delay": {
            "primaryTime": 0.375,
            "primaryFeedback": 0.5,
            "primaryMix": 0.6,
            "secondaryTime": 0.28125,
            "secondaryFeedback": 0.4,
            "secondaryMix": 0.5,
            "enabled": True,
        },
        "reverb": {
            "decay": 4.0,
            "preDelay": 30,
            "mix": 0.5,
            "inputFilterFreq": 800,
            "inputFilterQ": 1.5,
            "enabled": True,
        },
        "filter": {
            "type": "bandpass",
            "frequency": 600,
            "Q": 3.0,
            "lfoRate": 0.1,
            "lfoDepth": 150,
            "enabled": True,
        },
        "distortion": {
            "amount": 0.2,
            "mix": 0.3,
            "enabled": True,
        },
        "vinyl": {
            "level": 0.25,
            "hissLevel": 0.15,
            "enabled": True,
        },
    },
    "minimal_dub": {
        "delay": {
            "primaryTime": 0.375,
            "primaryFeedback": 0.3,
            "primaryMix": 0.35,
            "secondaryTime": 0.28125,
            "secondaryFeedback": 0.2,
            "secondaryMix": 0.25,
            "enabled": True,
        },
        "reverb": {
            "decay": 2.0,
            "preDelay": 20,
            "mix": 0.25,
            "inputFilterFreq": 1000,
            "inputFilterQ": 1.0,
            "enabled": True,
        },
        "filter": {
            "type": "bandpass",
            "frequency": 900,
            "Q": 2.0,
            "lfoRate": 0.2,
            "lfoDepth": 80,
            "enabled": True,
        },
        "distortion": {
            "amount": 0.1,
            "mix": 0.15,
            "enabled": True,
        },
        "vinyl": {
            "level": 0.1,
            "hissLevel": 0.05,
            "enabled": True,
        },
    },
    "club_dub": {
        "delay": {
            "primaryTime": 0.3,
            "primaryFeedback": 0.35,
            "primaryMix": 0.4,
            "secondaryTime": 0.225,
            "secondaryFeedback": 0.25,
            "secondaryMix": 0.3,
            "enabled": True,
        },
        "reverb": {
            "decay": 2.5,
            "preDelay": 15,
            "mix": 0.3,
            "inputFilterFreq": 1200,
            "inputFilterQ": 1.2,
            "enabled": True,
        },
        "filter": {
            "type": "bandpass",
            "frequency": 1000,
            "Q": 2.5,
            "lfoRate": 0.3,
            "lfoDepth": 120,
            "enabled": True,
        },
        "distortion": {
            "amount": 0.25,
            "mix": 0.35,
            "enabled": True,
        },
        "vinyl": {
            "level": 0.12,
            "hissLevel": 0.08,
            "enabled": True,
        },
    },
}


@dataclass
class MixConfig:
    length: float = 7200.0
    bpm: int = 125
    key: str = "Dm"
    output_path: str = "mix.flac"
    segment_duration: float = 180.0
    effects_preset: str = "deep_dub"


class MixOrchestrator:
    def __init__(self, config: MixConfig):
        self.config = config
        self.generator = ACEStepGenerator()
        self.bridge = TypeScriptBridge()
        self.segment_count = math.ceil(config.length / config.segment_duration)

    def generate_mix(self) -> Path:
        segments: list[Path] = []
        for i in range(self.segment_count):
            raw = self._generate_segment(i, self.segment_count)
            processed = self._process_segment(raw)
            segments.append(processed)
        return Path(self.config.output_path)

    def _generate_segment(self, index: int, total: int) -> Path:
        prompt = self._get_segment_prompt(index, total)
        return self.generator.generate_texture(
            prompt=prompt,
            duration=int(self.config.segment_duration),
            bpm=self.config.bpm,
            key=self.config.key,
        )

    def _get_effects_config(self) -> dict:
        preset_name = self.config.effects_preset
        if preset_name not in _EFFECTS_PRESETS:
            raise ValueError(
                f"Unknown effects preset '{preset_name}'. "
                f"Available: {sorted(_EFFECTS_PRESETS)}"
            )
        return _EFFECTS_PRESETS[preset_name]

    def _process_segment(self, segment_path: Path) -> Path:
        effects = self._get_effects_config()

        config = {
            "sampleRate": 48000,
            "channels": 2,
            "duration": self.config.segment_duration,
            "bpm": self.config.bpm,
            "key": self.config.key,
            "effects": effects,
            "pattern": {
                "style": "dub_techno",
                "variation": 0.3,
            },
        }

        import tempfile

        with tempfile.TemporaryDirectory(prefix="openmusic-out-") as tmpdir:
            output_path = str(Path(tmpdir) / "processed.wav")
            self.bridge.call_audio_engine(
                input_files=[str(segment_path)],
                output_path=output_path,
                config=config,
            )
            return Path(output_path)

    def _get_segment_prompt(self, index: int, total: int) -> str:
        position = index / max(total - 1, 1)

        if position <= 0.2:
            intensity = "subtle" if position < 0.1 else "building"
            return (
                f"dub techno intro with {intensity} atmosphere, "
                f"deep bass, sparse percussion, ambient pads in {self.config.key}, "
                f"{self.config.bpm} BPM"
            )

        if position >= 0.8:
            if position >= 0.95:
                return (
                    f"dub techno outro fading out, dissolving textures, "
                    f"reverb tails in {self.config.key}, {self.config.bpm} BPM"
                )
            return (
                f"dub techno climax with intense rhythmic drive, "
                f"heavy dub chords, thick reverb in {self.config.key}, "
                f"{self.config.bpm} BPM"
            )

        return (
            f"dub techno with evolving groove, deep bass lines, "
            f"dub chords with delay and reverb, hypnotic rhythm in {self.config.key}, "
            f"{self.config.bpm} BPM"
        )
