import logging
import math
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from openmusic.acestep import ACEStepGenerator
from openmusic.bridge.typescript_bridge import TypeScriptBridge

logger = logging.getLogger(__name__)

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
    """Configuration for a dub techno mix generation session."""

    length: float = 7200.0
    bpm: int = 125
    key: str = "Dm"
    output_path: str = "mix.flac"
    segment_duration: float = 180.0
    effects_preset: str = "deep_dub"
    skip_effects: bool = False


class MixOrchestrator:
    """Orchestrates AI texture generation and effects processing into a complete mix."""

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

        # Assemble all segments into final output
        self._assemble_segments(segments, Path(self.config.output_path))

        # Clean up temporary segment files
        for seg in segments:
            try:
                seg.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up segment file {seg}: {e}")

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
        if self.config.skip_effects:
            # Bypass bridge entirely – copy raw WAV to a persistent temp file
            persistent_output = tempfile.NamedTemporaryFile(
                prefix="openmusic-seg-",
                suffix=".wav",
                delete=False,
            )
            persistent_output.close()
            persistent_path = Path(persistent_output.name)
            try:
                shutil.copy(str(segment_path), str(persistent_path))
            except Exception:
                if persistent_path.exists():
                    persistent_path.unlink()
                raise
            return persistent_path

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

        # Create persistent temp file outside the context manager
        persistent_output = tempfile.NamedTemporaryFile(
            prefix="openmusic-seg-",
            suffix=".wav",
            delete=False,
        )
        persistent_output.close()
        persistent_path = Path(persistent_output.name)

        try:
            with tempfile.TemporaryDirectory(prefix="openmusic-out-") as tmpdir:
                temp_output = Path(tmpdir) / "processed.wav"
                self.bridge.call_audio_engine(
                    input_files=[str(segment_path)],
                    output_path=str(temp_output),
                    config=config,
                )
                # Copy to persistent location before temp dir is deleted
                shutil.copy(str(temp_output), str(persistent_path))
        except Exception:
            # Clean up persistent file if processing failed
            if persistent_path.exists():
                persistent_path.unlink()
            raise

        return persistent_path

    def _assemble_segments(self, segments: list[Path], output_path: Path) -> None:
        """Concatenate audio segments with crossfade between them."""
        if not segments:
            raise ValueError("No segments to assemble")

        logger.info(f"Assembling {len(segments)} segments into {output_path}")

        # Load first segment to get audio properties
        first_audio, first_sr = sf.read(str(segments[0]))
        channels = 1 if first_audio.ndim == 1 else first_audio.shape[1]
        sample_rate = first_sr

        # Crossfade duration: ~1 second at 48kHz, but ensure it's less than segment length
        desired_crossfade = sample_rate  # 1 second
        # Calculate crossfade based on minimum segment length
        min_seg_len = len(first_audio)
        for seg_path in segments:
            audio, sr = sf.read(str(seg_path))
            if sr != sample_rate:
                raise ValueError(
                    f"Sample rate mismatch: {seg_path} has {sr}, expected {sample_rate}"
                )
            min_seg_len = min(min_seg_len, len(audio))

        # Use 1/4 of minimum segment length for crossfade, max 1 second
        crossfade_samples = min(desired_crossfade, min_seg_len // 4)
        if crossfade_samples < sample_rate // 100:  # At least 10ms
            crossfade_samples = sample_rate // 100

        # Load all segments
        segment_data = []
        total_samples = 0
        for seg_path in segments:
            audio, sr = sf.read(str(seg_path))
            if sr != sample_rate:
                raise ValueError(
                    f"Sample rate mismatch: {seg_path} has {sr}, expected {sample_rate}"
                )
            segment_data.append(audio)
            total_samples += len(audio)

        # Calculate total length with crossfade
        # For n segments: length = sum(segment_lengths) - (n-1) * crossfade
        total_samples -= (len(segments) - 1) * crossfade_samples

        # Create output array
        if channels == 1:
            combined = np.zeros(total_samples, dtype=np.float32)
        else:
            combined = np.zeros((total_samples, channels), dtype=np.float32)

        # Assemble with crossfade
        write_pos = 0
        for i, audio in enumerate(segment_data):
            seg_len = len(audio)
            if channels == 1 and audio.ndim == 1:
                audio = audio[:, np.newaxis]
            elif channels == 2 and audio.ndim == 1:
                audio = audio[:, np.newaxis]
                audio = np.repeat(audio, 2, axis=1)

            if i == 0:
                # First segment: write all except crossfade portion at end
                end_pos = seg_len - crossfade_samples
                combined[write_pos:end_pos] = audio[:end_pos]
                write_pos = end_pos
            elif i == len(segments) - 1:
                # Last segment: crossfade with previous, write remainder
                # Crossfade region
                crossfade_start = write_pos - crossfade_samples
                crossfade_end = write_pos
                for j in range(crossfade_samples):
                    alpha = j / crossfade_samples
                    combined[crossfade_start + j] = (1 - alpha) * combined[
                        crossfade_start + j
                    ] + alpha * audio[j]
                # Write remainder
                remaining_len = seg_len - crossfade_samples
                combined[write_pos : write_pos + remaining_len] = audio[
                    crossfade_samples:
                ]
            else:
                # Middle segments: crossfade with previous, write middle, reserve for next
                # Crossfade with previous segment
                crossfade_start = write_pos - crossfade_samples
                crossfade_end = write_pos
                for j in range(crossfade_samples):
                    alpha = j / crossfade_samples
                    combined[crossfade_start + j] = (1 - alpha) * combined[
                        crossfade_start + j
                    ] + alpha * audio[j]
                # Write main portion
                main_len = seg_len - 2 * crossfade_samples
                combined[write_pos : write_pos + main_len] = audio[
                    crossfade_samples : seg_len - crossfade_samples
                ]
                write_pos += main_len

            logger.info(f"Assembled segment {i + 1}/{len(segments)}")

        # Write output file with appropriate format
        format_str = "WAV" if output_path.suffix.lower() == ".wav" else "FLAC"
        sf.write(str(output_path), combined, sample_rate, format=format_str)
        logger.info(f"Mix written to {output_path}")

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
