import copy
import logging
import math
import random
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import soundfile as sf

from openmusic.acestep import ACEStepGenerator
from openmusic.bridge.typescript_bridge import TypeScriptBridge
from openmusic.patterns import PatternLibrary, PhaseTransitionMatrix, BayesianPatternSelector
from openmusic.patterns.markov import Phase
from openmusic.generators import AudioGenerator, StableAudioGenerator

logger = logging.getLogger(__name__)


def _pedalboard_available() -> bool:
    """Check if pedalboard native extension loads without crashing.

    Some prebuilt wheels (esp. for Python 3.14+) include AVX-512 instructions
    that trigger SIGILL on CPUs without AVX-512. The OS-level signal can't
    be caught with try/except ImportError, so we probe via a subprocess.
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-c", "from pedalboard import Pedalboard; print('ok')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip() == "ok"
    except (subprocess.SubprocessError, OSError):
        return False


__all__ = [
    "MixConfig",
    "MixOrchestrator",
    "STAGE_BOUNDARIES",
    "STAGE_PROMPTS",
    "STAGE_PRESETS",
    "STAGE_VARIATION",
    "_get_stage_for_segment",
    "_compute_stage_timings",
]


def _parse_schedule(raw: Optional[str], default: int | str) -> list[tuple[int, int | str]]:
    if not raw or not raw.strip():
        return []
    schedule = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+):(.+)$", part)
        if not m:
            raise ValueError(f"Invalid schedule entry: '{part}'. Use format 'segment:value', e.g. '0:125,20:130'")
        seg = int(m.group(1))
        val = m.group(2)
        if isinstance(default, int):
            val = int(val)
        schedule.append((seg, val))
    return sorted(schedule)


def _interpolate_schedule(schedule: list[tuple[int, int | str]], seg_index: int, default: int | str) -> int | str:
    if not schedule:
        return default
    if len(schedule) == 1:
        return schedule[0][1]
    if seg_index <= schedule[0][0]:
        return schedule[0][1]
    if seg_index >= schedule[-1][0]:
        return schedule[-1][1]
    for i in range(len(schedule) - 1):
        s0, v0 = schedule[i]
        s1, v1 = schedule[i + 1]
        if s0 <= seg_index < s1:
            if isinstance(v0, int) and isinstance(v1, int):
                t = (seg_index - s0) / (s1 - s0)
                return round(v0 + (v1 - v0) * t)
            return v0
    return schedule[-1][1]


STAGE_BOUNDARIES = [
    (0.00, "ambient-intro"),
    (0.10, "early-build"),
    (0.25, "mid-build"),
    (0.45, "pre-peak-one"),
    (0.60, "peak-one"),
    (0.75, "post-peak"),
    (0.85, "peak-two"),
    (1.00, "decay-one"),
    (1.15, "decay-two"),
    (1.30, "dissolution"),
]


STYLE_MODIFIERS = [
    "atmospheric",
    "percussive",
    "drone",
    "minimal",
    "spacious",
    "filtered",
    "hypnotic",
    "rolling",
]

STRUCTURE_CUES = {
    "ambient-intro": ["slow evolving pads", "spacious soundscape", "textural drone"],
    "early-build": ["building tension", "layered percussion", "rhythmic foundation"],
    "mid-build": ["driving rhythms", "dense percussion", "full spectrum"],
    "pre-peak-one": ["rising intensity", "crushing bass", "maximal presence"],
    "peak-one": ["peak energy", "all elements firing", "powerful low-end"],
    "post-peak": ["sustaining intensity", "peak saturation", "controlled explosion"],
    "peak-two": ["renewed energy surge", "layered textures", "high-impact rhythm"],
    "decay-one": ["receding elements", "looming bass", "wide space"],
    "decay-two": ["scattered fragments", "bare rhythm", "hollow space"],
    "dissolution": ["fading textures", "sparse echoes", "dissolving drone"],
}

STAGE_PROMPTS = {
    "ambient-intro": [
        "subtle atmospheric texture, barely perceptible rhythm, warm analog haze, "
        "distant reverb-drenched percussion, hypnotic repetition, minimal groove",
    ],
    "early-build": [
        "subtle percussion emerging, textural layers slowly accumulating, "
        "rhythmic foundation taking shape, room tones warming, gentle pulse",
    ],
    "mid-build": [
        "driving four-on-the-floor kick, evolving groove, building bass weight, "
        "percussion interlocking, dynamic tension escalating, hypnotic forward motion",
    ],
    "pre-peak-one": [
        "intense rhythmic drive, peak energy, full harmonic content, "
        "crushing bass, transilient percussion, maximal presence and impact",
    ],
    "peak-one": [
        "maximum energy and intensity, all elements firing, powerful low-end, "
        "crystallized rhythm, transcendent momentum, visceral impact",
    ],
    "post-peak": [
        "controlled explosion, sustaining intensity, peak textures held, "
        "balanced chaos, powerful momentum, peak saturation",
    ],
    "peak-two": [
        "second wind of intensity, renewed energy surge, layered textures, "
        "punchy transients, high-impact rhythm, sustained drive",
    ],
    "decay-one": [
        "gradual energy release, textures dissolving, rhythm relaxing, "
        "space opening, bass softening, hypnotic slowdown",
    ],
    "decay-two": [
        "fading into dissolution, minimal elements, echo trails, "
        "ambient fade, sparse textures, distant and dreamlike",
    ],
    "dissolution": [
        "textural fadeout, echo chamber decay, final breath, "
        "ambient dissolution, minimal signal, fading into silence",
    ],
}


STAGE_PRESETS = {
    "ambient-intro": "minimal_dub",
    "early-build": "deep_dub",
    "mid-build": "deep_dub",
    "pre-peak-one": "deep_dub",
    "peak-one": "deep_dub",
    "post-peak": "club_dub",
    "peak-two": "club_dub",
    "decay-one": "deep_dub",
    "decay-two": "minimal_dub",
    "dissolution": "minimal_dub",
}

STAGE_VARIATION = {
    "ambient-intro": 0.1,
    "early-build": 0.2,
    "mid-build": 0.4,
    "pre-peak-one": 0.5,
    "peak-one": 0.6,
    "post-peak": 0.5,
    "peak-two": 0.4,
    "decay-one": 0.3,
    "decay-two": 0.2,
    "dissolution": 0.1,
}


def _get_stage_for_segment(segment_index: int, total_segments: int) -> str:
    if total_segments == 0:
        return "ambient-intro"
    position = segment_index / total_segments
    for threshold, stage in reversed(STAGE_BOUNDARIES):
        if position >= threshold:
            return stage
    return "ambient-intro"


def _compute_stage_timings(total_duration: float) -> list[tuple[float, float, str]]:
    """Compute (start, end, stage_name) timestamps for each stage.

    Args:
        total_duration: Total mix duration in seconds

    Returns:
        List of tuples: [(start_time, end_time, stage_name), ...]
    """
    timings = []
    prev_time = 0.0

    for i, (boundary, stage) in enumerate(STAGE_BOUNDARIES):
        if i == 0:
            continue  # ambient-intro starts at 0

        start_time = prev_time
        end_time = total_duration * boundary
        prev_stage_name = STAGE_BOUNDARIES[i-1][1]

        timings.append((start_time, end_time, prev_stage_name))
        prev_time = end_time

    return timings


def _parse_effects_modifiers(modifiers_str: Optional[str]) -> Dict[str, List[tuple]]:
    if not modifiers_str:
        return {}
    result = {}
    for modifier in modifiers_str.split(";"):
        if ":" not in modifier:
            continue
        stage_part, param_part = modifier.split(":", 1)
        stage = stage_part.strip()
        if stage not in result:
            result[stage] = []
        for param_mod in param_part.split(","):
            param_mod = param_mod.strip()
            if not param_mod:
                continue
            op_idx = max(param_mod.find("+"), param_mod.find("-"),
                        param_mod.find("*"), param_mod.find("/"))
            if op_idx <= 0:
                continue
            op = param_mod[op_idx]
            param = param_mod[:op_idx].strip()
            value = param_mod[op_idx+1:].strip()
            try:
                val = float(value) if "." in value else int(value)
            except ValueError:
                continue
            result[stage].append((param, op, val))
    return result


def interpolate_effects(base_preset: dict, modifiers: Dict[str, List[tuple]],
                       stage_id: str, segment_position: float) -> dict:
    import copy
    result = copy.deepcopy(base_preset)
    if stage_id in modifiers:
        for param, op, value in modifiers[stage_id]:
            if param not in result or not isinstance(result[param], dict):
                continue
            if op == "+":
                for k in result[param]:
                    if isinstance(result[param][k], (int, float)):
                        result[param][k] += value
            elif op == "-":
                for k in result[param]:
                    if isinstance(result[param][k], (int, float)):
                        result[param][k] -= value
            elif op == "*":
                for k in result[param]:
                    if isinstance(result[param][k], (int, float)):
                        result[param][k] *= value
            elif op == "/":
                for k in result[param]:
                    if isinstance(result[param][k], (int, float)) and value != 0:
                        result[param][k] /= value
    return result


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
    effects_backend: str = "pedalboard"  # "pedalboard", "typescript", "none"
    effects_modifiers: Optional[str] = None
    generate_cover: bool = False
    cover_theme: str = "dark_industrial"
    cover_title: str = ""
    cover_artist: str = "OpenMusic"
    bpm_schedule: Optional[str] = None
    key_schedule: Optional[str] = None
    model: str = "ace-step"
    model_preset: str = "sft"
    use_bayesian_markov: bool = False
    pattern_style: str = "dub_techno"
    pattern_library_path: str = ""
    inference_steps_range: tuple[int, int] | None = None  # e.g., (8, 50)

    def _inference_steps_for_segment(self, index: int, total: int) -> int | None:
        if self.inference_steps_range is None:
            return None
        lo, hi = self.inference_steps_range
        if total <= 1:
            return (lo + hi) // 2
        fraction = index / (total - 1)
        return int(lo + fraction * (hi - lo))

    def bpm_for_segment(self, index: int) -> int:
        sched = _parse_schedule(self.bpm_schedule, self.bpm)
        val = _interpolate_schedule(sched, index, self.bpm)
        return int(val)

    def key_for_segment(self, index: int) -> str:
        sched = _parse_schedule(self.key_schedule, self.key)
        val = _interpolate_schedule(sched, index, self.key)
        return str(val)


class MixOrchestrator:
    """Orchestrates AI texture generation and effects processing into a complete mix."""

    def __init__(self, config: MixConfig):
        self.config = config
        self.generator = self._create_generator(config.model, config.model_preset)
        self.segment_count = math.ceil(config.length / config.segment_duration)

        # Select effects backend
        if config.skip_effects or config.effects_backend == "none":
            self._bridge = None
        elif config.effects_backend == "pedalboard":
            try:
                if not _pedalboard_available():
                    raise ImportError(
                        "pedalboard native extension not loadable "
                        "(incompatible CPU or missing library)"
                    )
                from openmusic.bridge.pedalboard_bridge import PythonDSPBridge

                self._bridge = PythonDSPBridge(
                    preset=config.effects_preset,
                    apply_mastering=True,
                )
            except ImportError:
                logger.warning(
                    "pedalboard not available, falling back to TypeScript bridge"
                )
                self._bridge = TypeScriptBridge()
        else:
            self._bridge = TypeScriptBridge()

        # Initialize Bayesian Markov pattern system
        self._pattern_library: Optional[PatternLibrary] = None
        self._phase_matrix: Optional[PhaseTransitionMatrix] = None
        self._pattern_selector: Optional[BayesianPatternSelector] = None
        if config.use_bayesian_markov:
            from openmusic.patterns.markov import StyleFactory
            lib_path = config.pattern_library_path or "patterns/pattern_library.json"
            self._pattern_library = PatternLibrary(lib_path)
            self._phase_matrix = StyleFactory.create(config.pattern_style)
            self._pattern_selector = BayesianPatternSelector(self._pattern_library)

        # Keep bridge attribute for backward compatibility with tests
        self.bridge = self._bridge if self._bridge is not None else TypeScriptBridge()

    @staticmethod
    def _create_generator(model: str, model_preset: str = "sft") -> AudioGenerator:
        if model == "stable-audio-open":
            if not StableAudioGenerator.is_available():
                logger.warning(
                    "Stable Audio Open not available, falling back to ACE-Step"
                )
                return ACEStepGenerator()
            return StableAudioGenerator()
        from openmusic.acestep.config import ACEStepConfig

        return ACEStepGenerator(config=ACEStepConfig(model_preset=model_preset))

    def generate_mix(self) -> Path:
        segments: list[Path] = []
        for i in range(self.segment_count):
            raw = self._generate_segment(i, self.segment_count)
            processed = self._process_segment(raw, i, self.segment_count)
            segments.append(processed)

        # Assemble all segments into final output
        self._assemble_segments(segments, Path(self.config.output_path))

        # Generate cover art if requested
        if self.config.generate_cover:
            cover_path = self._generate_cover_art(Path(self.config.output_path))
            logger.info(f"Cover art generated: {cover_path}")

        # Clean up temporary segment files
        for seg in segments:
            try:
                seg.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up segment file {seg}: {e}")

        return Path(self.config.output_path)

    def _generate_segment(self, index: int, total: int) -> Path:
        use_patterns = (
            self.config.use_bayesian_markov
            and self._pattern_library is not None
            and self._phase_matrix is not None
            and self._pattern_selector is not None
        )

        if use_patterns:
            return self._generate_segment_from_pattern(index, total)

        stage_id = _get_stage_for_segment(index, total)
        seg_bpm = self.config.bpm_for_segment(index)
        seg_key = self.config.key_for_segment(index)
        prompt = self._get_segment_prompt(index, total, stage_id=stage_id, seg_key=seg_key, seg_bpm=seg_bpm)
        inference_steps = self.config._inference_steps_for_segment(index, total)
        return self.generator.generate_texture(
            prompt=prompt,
            duration=int(self.config.segment_duration),
            bpm=seg_bpm,
            key=seg_key,
            inference_steps=inference_steps,
        )

    def _generate_segment_from_pattern(self, index: int, total: int) -> Path:
        phase = self._phase_matrix.generate_sequence(total, start=Phase.INTRO)[index]
        candidates = self._pattern_library.get_by_phase(phase.value)

        if not candidates or not self._pattern_selector:
            stage_id = _get_stage_for_segment(index, total)
            seg_bpm = self.config.bpm_for_segment(index)
            seg_key = self.config.key_for_segment(index)
            prompt = self._get_segment_prompt(index, total, stage_id=stage_id, seg_key=seg_key, seg_bpm=seg_bpm)
            inference_steps = self.config._inference_steps_for_segment(index, total)
            return self.generator.generate_texture(
                prompt=prompt,
                duration=int(self.config.segment_duration),
                bpm=seg_bpm,
                key=seg_key,
                inference_steps=inference_steps,
            )

        selected = self._pattern_selector.select(candidates)
        if selected:
            return Path(selected.path)

        stage_id = _get_stage_for_segment(index, total)
        seg_bpm = self.config.bpm_for_segment(index)
        seg_key = self.config.key_for_segment(index)
        prompt = self._get_segment_prompt(index, total, stage_id=stage_id, seg_key=seg_key, seg_bpm=seg_bpm)
        inference_steps = self.config._inference_steps_for_segment(index, total)
        return self.generator.generate_texture(
            prompt=prompt,
            duration=int(self.config.segment_duration),
            bpm=seg_bpm,
            key=seg_key,
            inference_steps=inference_steps,
        )

    def _get_effects_config(self, preset_name: str | None = None) -> dict:
        name = preset_name or self.config.effects_preset
        if name not in _EFFECTS_PRESETS:
            raise ValueError(
                f"Unknown effects preset '{name}'. "
                f"Available: {sorted(_EFFECTS_PRESETS)}"
            )
        return copy.deepcopy(_EFFECTS_PRESETS[name])

    def _process_segment(self, segment_path: Path, index: int, total: int) -> Path:
        if self._bridge is None:
            # No effects - copy raw WAV
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

        # Use PythonDSPBridge
        if hasattr(self._bridge, "process"):
            persistent_output = tempfile.NamedTemporaryFile(
                prefix="openmusic-seg-",
                suffix=".wav",
                delete=False,
            )
            persistent_output.close()
            persistent_path = Path(persistent_output.name)
            try:
                self._bridge.process(str(segment_path), str(persistent_path))
            except Exception:
                if persistent_path.exists():
                    persistent_path.unlink()
                raise
            return persistent_path

        # Fallback: TypeScript bridge (existing logic)
        seg_bpm = self.config.bpm_for_segment(index)
        seg_key = self.config.key_for_segment(index)
        stage_id = _get_stage_for_segment(index, total)
        # Stage-specific preset for sonic diversity
        preset_name = STAGE_PRESETS.get(stage_id, self.config.effects_preset)
        base_effects = self._get_effects_config(preset_name=preset_name)
        if self.config.effects_modifiers:
            modifiers = _parse_effects_modifiers(self.config.effects_modifiers)
            segment_pos = index / max(total - 1, 1)
            effects = interpolate_effects(base_effects, modifiers, stage_id, segment_pos)
        else:
            effects = base_effects

        variation = STAGE_VARIATION.get(stage_id, 0.3)

        # Apply MIDI-driven effect modulation
        from openmusic.orchestrator.midi_modulation import get_modulation_for_segment
        mod = get_modulation_for_segment(index, total, bpm=seg_bpm)
        if "delay" in effects:
            effects["delay"]["primaryFeedback"] = float(
                np.clip(
                    effects["delay"].get("primaryFeedback", 0.5) * mod["delay_feedback_mod"] * 2,
                    0.0, 1.0,
                )
            )
            effects["delay"]["primaryMix"] = float(
                np.clip(
                    mod["reverb_mix_mod"],
                    0.0, 1.0,
                )
            )
        if "filter" in effects:
            effects["filter"]["frequency"] = int(mod["filter_cutoff_mod"])

        config = {
            "sampleRate": 48000,
            "channels": 2,
            "duration": self.config.segment_duration,
            "bpm": seg_bpm,
            "key": seg_key,
            "effects": effects,
            "pattern": {
                "style": "dub_techno",
                "variation": variation,
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
                self._bridge.call_audio_engine(
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

        # Crossfade duration: ~3 seconds at 48kHz, but ensure it's less than segment length
        desired_crossfade = sample_rate * 3  # 3 seconds
        # Calculate crossfade based on minimum segment length
        min_seg_len = len(first_audio)
        for seg_path in segments:
            audio, sr = sf.read(str(seg_path))
            if sr != sample_rate:
                raise ValueError(
                    f"Sample rate mismatch: {seg_path} has {sr}, expected {sample_rate}"
                )
            min_seg_len = min(min_seg_len, len(audio))

        # Use 1/3 of minimum segment length for crossfade, max 3 seconds
        crossfade_samples = min(desired_crossfade, min_seg_len // 3)
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
                # Last segment: equal-power crossfade with previous, write remainder
                crossfade_start = write_pos - crossfade_samples
                for j in range(crossfade_samples):
                    t = j / crossfade_samples
                    fade_out = np.cos(t * np.pi / 2.0)
                    fade_in = np.sin(t * np.pi / 2.0)
                    combined[crossfade_start + j] = (
                        fade_out * combined[crossfade_start + j]
                        + fade_in * audio[j]
                    )
                remaining_len = seg_len - crossfade_samples
                combined[write_pos : write_pos + remaining_len] = audio[
                    crossfade_samples:
                ]
            else:
                # Middle segments: equal-power crossfade with previous, write middle, reserve for next
                crossfade_start = write_pos - crossfade_samples
                for j in range(crossfade_samples):
                    t = j / crossfade_samples
                    fade_out = np.cos(t * np.pi / 2.0)
                    fade_in = np.sin(t * np.pi / 2.0)
                    combined[crossfade_start + j] = (
                        fade_out * combined[crossfade_start + j]
                        + fade_in * audio[j]
                    )
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

    def _get_segment_prompt(
        self,
        index: int,
        total: int,
        stage_id: Optional[str] = None,
        seg_key: Optional[str] = None,
        seg_bpm: Optional[int] = None,
    ) -> str:
        if stage_id is None:
            stage_id = _get_stage_for_segment(index, total)
        if seg_key is None:
            seg_key = self.config.key
        if seg_bpm is None:
            seg_bpm = self.config.bpm

        # Combinatorial prompt: structure cue + style modifier
        cues = STRUCTURE_CUES.get(stage_id, ["textural drone"])
        cue = random.choice(cues)
        modifier = random.choice(STYLE_MODIFIERS)

        return (
            f"dub techno, {cue}, {modifier}, in {seg_key}, "
            f"{seg_bpm} BPM"
        )

    def _generate_cover_art(self, output_path: Path) -> Path:
        """Generate cover art SVG and optionally PNG alongside the mix output.

        Args:
            output_path: Path to the generated mix file (e.g., "mix.flac")

        Returns:
            Path to the generated cover file (SVG, with PNG as bonus if available)
        """
        try:
            from openart.config import ArtworkConfig
            from openart.generator import ArtworkGenerator
        except ImportError:
            logger.warning(
                "openart not installed. Install with: uv pip install -e "
                "'C:\\Users\\Tobias\\workspace\\artwork\\openart' "
                "--python ACE-Step-1.5/.venv/Scripts/python.exe -U openmusic-core[artwork]"
            )
            # Return a dummy path so code doesn't crash
            return output_path.parent / f"{output_path.stem}_cover.svg"

        # Derive cover path from mix output path
        stem = output_path.stem
        cover_svg_path = output_path.parent / f"{stem}_cover.svg"

        # Determine title
        title = self.config.cover_title if self.config.cover_title else "Dub Techno Mix"

        # Create artwork config
        config = ArtworkConfig(
            width=1000,
            height=1000,
            title=title,
            subtitle="",
            artist=self.config.cover_artist,
            theme=self.config.cover_theme,
        )

        # Generate SVG
        generator = ArtworkGenerator(config)
        svg_path = generator.save(str(cover_svg_path))
        logger.info(f"Cover SVG saved to: {svg_path}")

        # Try to convert to PNG
        try:
            import cairosvg

            cover_png_path = output_path.parent / f"{stem}_cover.png"
            cairosvg.svg2png(url=str(svg_path), write_to=str(cover_png_path))
            logger.info(f"Cover PNG saved to: {cover_png_path}")
        except ImportError:
            logger.info("cairosvg not available, skipping PNG conversion")
        except Exception as e:
            logger.warning(f"Failed to convert SVG to PNG: {e}")

        return Path(svg_path)
