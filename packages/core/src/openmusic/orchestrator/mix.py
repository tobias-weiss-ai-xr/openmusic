import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from openmusic.acestep import ACEStepGenerator


@dataclass
class MixConfig:
    length: float = 7200.0
    bpm: int = 125
    key: str = "Dm"
    output_path: str = "mix.flac"
    segment_duration: float = 180.0
    effects_preset: str = "deep_dub"


EFFECTS_BIN = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "effects"
    / "dist"
    / "index.js"
)


class MixOrchestrator:
    def __init__(self, config: MixConfig):
        self.config = config
        self.generator = ACEStepGenerator()
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

    def _process_segment(self, segment_path: Path) -> Path:
        with tempfile.TemporaryDirectory(prefix="openmusic-") as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_dir = tmpdir_path / "input"
            output_dir = tmpdir_path / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            shutil.copy2(segment_path, input_dir / "stem_0.wav")

            config = {
                "sampleRate": 48000,
                "channels": 2,
                "duration": self.config.segment_duration,
                "bpm": self.config.bpm,
                "key": self.config.key,
                "inputStems": [{"path": "input/stem_0.wav", "role": "main"}],
                "outputPath": "output/processed.wav",
                "effects": {
                    "filter": {
                        "type": "lowpass",
                        "frequency": 800,
                        "Q": 2.0,
                    },
                    "delay": {
                        "delayTime": 0.375,
                        "feedback": 0.35,
                        "wetLevel": 0.4,
                    },
                    "reverb": {
                        "duration": 3.0,
                        "decay": 2.5,
                        "wetLevel": 0.3,
                    },
                },
                "pattern": {
                    "style": "dub_techno",
                    "variation": 0.3,
                },
            }

            config_path = tmpdir_path / "config.json"
            with open(config_path, "w") as f:
                json.dump(config, f)

            result = subprocess.run(
                ["node", str(EFFECTS_BIN), "--config", str(config_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Effects processing failed: {result.stderr.strip()}"
                )

            return output_dir / "processed.wav"

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
