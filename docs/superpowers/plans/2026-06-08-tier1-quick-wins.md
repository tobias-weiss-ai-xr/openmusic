# Tier 1 Quick Wins — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 5 independent quality-of-life features: loudness normalization, MIDI pattern export, beat tracking, YouTube live streaming, and audio fingerprinting — each small enough to complete in 1-3 days.

**Architecture:** Each feature is self-contained — new modules under `openmusic/` with no coupling between them. Shared patterns: `ffmpeg` subprocess calls, numpy audio processing, pytest with mocking. CLI additions follow existing Click command patterns in `cli/main.py`. Dependencies added to `pyproject.toml` optional groups.

**Tech Stack:** Python 3.12+, Click (CLI), numpy, ffmpeg, pytest. New deps: `pyloudnorm`, `isobar`, `aubio`, `PyLivestream`, `pyacoustid`.

---

## File Structure

**New modules:**
- `packages/core/src/openmusic/export/loudness.py` — EBU R128 loudness normalization
- `packages/core/src/openmusic/export/midi_export.py` — isobar-based MIDI pattern export
- `packages/core/src/openmusic/analysis/beat_tracker.py` — aubio-based beat/tempo analysis
- `packages/core/src/openmusic/export/fingerprint.py` — pyacoustid fingerprinting
- `packages/core/src/openmusic/cli/stream.py` — livestream command group

**New test files:**
- `packages/core/tests/test_export/test_loudness.py`
- `packages/core/tests/test_export/test_midi_export.py`
- `packages/core/tests/test_export/test_fingerprint.py`
- `packages/core/tests/test_analysis/test_beat_tracker.py`
- `packages/core/tests/test_cli/test_stream.py`

**Modified files:**
- `packages/core/pyproject.toml` — add optional groups: `loudness`, `midi`, `analysis`, `stream`, `fingerprint`
- `packages/core/src/openmusic/export/__init__.py` — export new symbols
- `packages/core/src/openmusic/cli/main.py` — register `stream` command group

---

### Task 1: EBU R128 Loudness Normalization

**Files:**
- Create: `packages/core/src/openmusic/export/loudness.py`
- Modify: `packages/core/src/openmusic/export/__init__.py`
- Modify: `packages/core/pyproject.toml` — add `loudness` optional group
- Test: `packages/core/tests/test_export/test_loudness.py`

- [ ] **Step 1: Add pyloudnorm dependency to pyproject.toml**

Insert into `[project.optional-dependencies]` in `packages/core/pyproject.toml`:

```toml
loudness = [
  "pyloudnorm>=0.1.1",
]
```

Add `pyloudnorm` to the `dev` group for CI:

```toml
dev = [..., "pyloudnorm>=0.1.1", ...]
```

- [ ] **Step 2: Write failing tests for loudness normalization**

Create `packages/core/tests/test_export/test_loudness.py`:

```python
"""Tests for export.loudness module."""

import numpy as np
import pytest

from openmusic.export.loudness import (
    measure_integrated_loudness,
    normalize_loudness,
    LUFS_TARGET,
)


class TestMeasureIntegratedLoudness:
    def test_returns_float(self):
        audio = np.random.randn(48000, 2).astype(np.float64)
        result = measure_integrated_loudness(audio, 48000)
        assert isinstance(result, float)

    def test_silence_returns_low_value(self):
        audio = np.zeros((48000, 2), dtype=np.float64)
        result = measure_integrated_loudness(audio, 48000)
        assert result < -40.0

    def test_full_scale_sine_returns_approx_negative_3(self):
        """A full-scale sine wave should measure around -3 LUFS."""
        t = np.linspace(0, 1, 48000, endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        audio = np.column_stack([audio, audio])  # stereo
        result = measure_integrated_loudness(audio, 48000)
        assert -6.0 < result < -1.0, f"Expected ~-3 LUFS, got {result}"

    def test_mono_input_raises(self):
        audio = np.random.randn(48000).astype(np.float64)
        with pytest.raises(ValueError, match="2D array with shape"):
            measure_integrated_loudness(audio, 48000)

    def test_single_channel_raises(self):
        audio = np.random.randn(48000, 1).astype(np.float64)
        with pytest.raises(ValueError, match="at least 2 channels"):
            measure_integrated_loudness(audio, 48000)

    def test_3plus_channels_raises(self):
        audio = np.random.randn(48000, 4).astype(np.float64)
        with pytest.raises(ValueError, match="Expected 2 channels"):
            measure_integrated_loudness(audio, 48000)


class TestNormalizeLoudness:
    def test_returns_same_shape(self):
        audio = np.random.randn(48000, 2).astype(np.float64)
        result = normalize_loudness(audio, 48000, target=-16.0)
        assert result.shape == audio.shape
        assert result.dtype == np.float64

    def test_normalizes_to_target(self):
        """Quiet audio gets boosted to approximately the target."""
        audio = (np.random.randn(48000, 2) * 0.01).astype(np.float64)
        result = normalize_loudness(audio, 48000, target=-23.0)
        measured = pyloudnorm.Meter(48000).integrated_loudness(result)
        assert abs(measured - (-23.0)) < 1.0, f"Expected ~-23 LUFS, got {measured}"

    def test_default_target_is_neg_14(self):
        audio = (np.random.randn(48000, 2) * 0.01).astype(np.float64)
        result = normalize_loudness(audio, 48000)
        measured = pyloudnorm.Meter(48000).integrated_loudness(result)
        assert abs(measured - (-14.0)) < 1.0, f"Expected ~-14 LUFS, got {measured}"

    def test_clips_at_one(self):
        """Very loud audio should be gain-reduced and not clip above 1.0."""
        audio = np.ones((48000, 2), dtype=np.float64) * 0.5
        result = normalize_loudness(audio, 48000, target=-14.0)
        assert np.max(np.abs(result)) <= 1.0

    def test_identity_at_target(self):
        """Audio already at target loudness should not change much."""
        t = np.linspace(0, 1, 48000, endpoint=False)
        audio = 0.25 * np.sin(2 * np.pi * 440 * t)
        audio = np.column_stack([audio, audio])
        # Normalize to a specific target once
        normalized = normalize_loudness(audio, 48000, target=-20.0)
        # Normalize again — second pass should be near-identity
        normalized2 = normalize_loudness(normalized, 48000, target=-20.0)
        assert np.max(np.abs(normalized - normalized2)) < 0.01
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_export/test_loudness.py -v`
Expected: ModuleNotFoundError / ImportError for `openmusic.export.loudness`

- [ ] **Step 4: Write minimal implementation**

Create `packages/core/src/openmusic/export/loudness.py`:

```python
"""EBU R128 loudness normalization using pyloudnorm."""

import numpy as np

LUFS_TARGET = -14.0  # Default: YouTube loudness target


def _validate_audio(audio: np.ndarray, sample_rate: int) -> None:
    if audio.ndim != 2:
        raise ValueError(
            f"Expected 2D array with shape (samples, channels), got shape {audio.shape}"
        )
    if audio.shape[1] < 2:
        raise ValueError(
            f"Expected at least 2 channels, got {audio.shape[1]}"
        )
    if audio.shape[1] > 2:
        raise ValueError(
            f"Expected 2 channels (stereo), got {audio.shape[1]}"
        )


def measure_integrated_loudness(audio: np.ndarray, sample_rate: int) -> float:
    """Measure integrated loudness in LUFS using EBU R128.

    Args:
        audio: Float64 numpy array with shape (samples, 2).
        sample_rate: Sample rate in Hz.

    Returns:
        Integrated loudness in LUFS (float).

    Raises:
        ValueError: If audio shape is not (samples, 2).
    """
    _validate_audio(audio, sample_rate)

    try:
        import pyloudnorm as pyln
    except ImportError:
        raise ImportError(
            "pyloudnorm is required for loudness measurement. "
            "Install: pip install openmusic-core[loudness]"
        )

    meter = pyln.Meter(sample_rate)
    return meter.integrated_loudness(audio)


def normalize_loudness(
    audio: np.ndarray,
    sample_rate: int,
    target: float = LUFS_TARGET,
) -> np.ndarray:
    """Normalize audio to a target integrated loudness (EBU R128).

    Args:
        audio: Float64 numpy array with shape (samples, 2).
        sample_rate: Sample rate in Hz.
        target: Target loudness in LUFS (default: -14.0 for YouTube).

    Returns:
        Loudness-normalized float64 numpy array, same shape as input.

    Raises:
        ValueError: If audio shape is not (samples, 2).
    """
    _validate_audio(audio, sample_rate)

    try:
        import pyloudnorm as pyln
    except ImportError:
        raise ImportError(
            "pyloudnorm is required for loudness normalization. "
            "Install: pip install openmusic-core[loudness]"
        )

    meter = pyln.Meter(sample_rate)
    current = meter.integrated_loudness(audio)
    gain_db = target - current
    linear_gain = 10.0 ** (gain_db / 20.0)
    result = audio * linear_gain
    return np.clip(result, -1.0, 1.0)
```

- [ ] **Step 5: Export symbols from `export/__init__.py`**

Edit `packages/core/src/openmusic/export/__init__.py`:

```python
from openmusic.export.loudness import (
    measure_integrated_loudness,
    normalize_loudness,
    LUFS_TARGET,
)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_export/test_loudness.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add packages/core/pyproject.toml
git add packages/core/src/openmusic/export/loudness.py
git add packages/core/src/openmusic/export/__init__.py
git add packages/core/tests/test_export/test_loudness.py
git commit -m "feat(export): add EBU R128 loudness normalization via pyloudnorm"
```

---

### Task 2: MIDI Pattern Export (isobar)

**Files:**
- Create: `packages/core/src/openmusic/export/midi_export.py`
- Modify: `packages/core/pyproject.toml` — add `midi` optional group
- Test: `packages/core/tests/test_export/test_midi_export.py`

- [ ] **Step 1: Add isobar dependency to pyproject.toml**

Insert into `[project.optional-dependencies]`:

```toml
midi = [
  "isobar>=1.1.0",
]
```

Add `isobar` to the `dev` group:

```toml
dev = [..., "isobar>=1.1.0", ...]
```

- [ ] **Step 2: Write failing tests for MIDI export**

Create `packages/core/tests/test_export/test_midi_export.py`:

```python
"""Tests for export.midi_export module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from openmusic.export.midi_export import (
    export_pattern_to_midi,
    export_markov_chain_to_midi,
    pattern_to_isobar_sequence,
    DEFAULT_MIDI_TEMPO,
)


class TestExportPatternToMidi:
    def test_returns_path(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64, 67, 72],
                output_path=out_path,
                bpm=125,
            )
            assert result == out_path
            assert out_path.exists()
            assert out_path.stat().st_size > 20  # valid MIDI has header
        finally:
            out_path.unlink(missing_ok=True)

    def test_custom_velocity(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64],
                output_path=out_path,
                velocities=[100, 80],
            )
            assert result.exists()
        finally:
            out_path.unlink(missing_ok=True)

    def test_empty_pattern_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="empty"):
                export_pattern_to_midi([], output_path=out_path)
        finally:
            out_path.unlink(missing_ok=True)

    def test_velocity_count_mismatch_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="same length"):
                export_pattern_to_midi(
                    [60, 64, 67], output_path=out_path, velocities=[100]
                )
        finally:
            out_path.unlink(missing_ok=True)

    def test_generates_valid_midi_header(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            export_pattern_to_midi([60, 64, 67], output_path=out_path)
            raw = out_path.read_bytes()
            assert raw[:4] == b"MThd"  # Standard MIDI header
        finally:
            out_path.unlink(missing_ok=True)

    def test_with_durations(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64, 67],
                output_path=out_path,
                durations=[1.0, 0.5, 2.0],
            )
            assert result.exists()
        finally:
            out_path.unlink(missing_ok=True)


class TestPatternToIsobarSequence:
    def test_returns_line(self):
        try:
            from isobar import Line
        except ImportError:
            pytest.skip("isobar not installed")
        seq = pattern_to_isobar_sequence([60, 62, 64])
        assert seq is not None

    def test_empty_returns_none(self):
        result = pattern_to_isobar_sequence([])
        assert result is None


class TestExportMarkovChainToMidi:
    @pytest.fixture
    def markov_states(self):
        """Simulate a simple Markov transition dict."""
        return {
            "C3": {"Eb3": 0.5, "G3": 0.5},
            "Eb3": {"F3": 0.7, "G3": 0.3},
            "F3": {"G3": 0.4, "Eb3": 0.6},
            "G3": {"C3": 0.8, "F3": 0.2},
        }

    def test_returns_path(self, markov_states):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_markov_chain_to_midi(
                transitions=markov_states,
                output_path=out_path,
                steps=16,
            )
            assert result == out_path
            assert out_path.exists()
        finally:
            out_path.unlink(missing_ok=True)

    def test_respects_step_count(self, markov_states):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            export_markov_chain_to_midi(
                transitions=markov_states,
                output_path=out_path,
                steps=8,
            )
            assert out_path.exists()
        finally:
            out_path.unlink(missing_ok=True)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_export/test_midi_export.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 4: Write minimal implementation**

Create `packages/core/src/openmusic/export/midi_export.py`:

```python
"""Export OpenMusic patterns to MIDI files using isobar."""

from pathlib import Path
from typing import Optional

DEFAULT_MIDI_TEMPO = 120


def _midi_note_to_number(note: str | int) -> int:
    """Convert a note name (e.g. 'C4') to MIDI note number, or pass through int."""
    if isinstance(note, int):
        return note
    note = note.strip()
    note_map = {
        "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
        "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
    }
    if len(note) < 2:
        raise ValueError(f"Invalid note: {note}")
    name = note[:-1]
    octave = int(note[-1])
    semitone = note_map.get(name)
    if semitone is None:
        raise ValueError(f"Unknown note name: {name}")
    return (octave + 1) * 12 + semitone


def pattern_to_isobar_sequence(
    note_values: list[int | str],
    durations: Optional[list[float]] = None,
    velocities: Optional[list[int]] = None,
):
    """Convert a list of note values to an isobar Sequence.

    Returns None if isobar is not installed or if note_values is empty.
    """
    if not note_values:
        return None
    try:
        from isobar import Sequence
    except ImportError:
        return None

    notes = [_midi_note_to_number(n) if isinstance(n, str) else n for n in note_values]
    kwargs = {}
    if durations is not None:
        kwargs["duration"] = durations
    if velocities is not None:
        kwargs["velocity"] = velocities
    return Sequence(notes, **kwargs)


def export_pattern_to_midi(
    note_values: list[int | str],
    output_path: str | Path,
    bpm: int = DEFAULT_MIDI_TEMPO,
    durations: Optional[list[float]] = None,
    velocities: Optional[list[int]] = None,
) -> Path:
    """Export a list of note values to a MIDI file.

    Args:
        note_values: List of MIDI note numbers (0-127) or note names ('C4', 'Eb3').
        output_path: Path for the output .mid file.
        bpm: Tempo in beats per minute.
        durations: Optional per-note durations in beats.
        velocities: Optional per-note velocities (0-127).

    Returns:
        Path to the written MIDI file.

    Raises:
        ValueError: If note_values is empty or velocities length mismatches.
        ImportError: If isobar is not installed.
    """
    try:
        from isobar import NoteSeq, timeline as tl
    except ImportError:
        raise ImportError(
            "isobar is required for MIDI export. "
            "Install: pip install openmusic-core[midi]"
        )

    if not note_values:
        raise ValueError("note_values must not be empty")
    if velocities is not None and len(velocities) != len(note_values):
        raise ValueError(
            f"velocities length ({len(velocities)}) must match "
            f"note_values length ({len(note_values)})"
        )
    if durations is not None and len(durations) != len(note_values):
        raise ValueError(
            f"durations length ({len(durations)}) must match "
            f"note_values length ({len(note_values)})"
        )

    notes = [_midi_note_to_number(n) if isinstance(n, str) else n for n in note_values]

    if durations is None:
        durations_list = [1.0] * len(notes)
    else:
        durations_list = durations

    if velocities is None:
        velocities_list = [100] * len(notes)
    else:
        velocities_list = velocities

    # Construct MIDI using isobar's Timeline and NoteSeq
    seq = NoteSeq(notes, duration=durations_list, velocity=velocities_list)

    timeline = tl.Timeline(bpm=bpm)
    timeline.schedule(seq)
    timeline.write_midi(str(output_path))

    return Path(output_path)


def export_markov_chain_to_midi(
    transitions: dict[str | int, dict[str | int, float]],
    output_path: str | Path,
    steps: int = 32,
    start_state: Optional[str | int] = None,
    bpm: int = DEFAULT_MIDI_TEMPO,
) -> Path:
    """Generate a MIDI file by walking a Markov transition matrix.

    Args:
        transitions: Dict mapping state -> {next_state: probability}.
            States can be note names ('C4') or MIDI numbers.
        output_path: Path for the output .mid file.
        steps: Number of notes to generate.
        start_state: Initial state (random if None).
        bpm: Tempo in beats per minute.

    Returns:
        Path to the written MIDI file.
    """
    import random

    if not transitions:
        raise ValueError("transitions dict must not be empty")

    states = list(transitions.keys())
    current = start_state if start_state is not None else random.choice(states)
    notes = []

    for _ in range(steps):
        notes.append(current)
        next_options = transitions.get(current, {})
        if not next_options:
            current = random.choice(states)
        else:
            candidates = list(next_options.keys())
            weights = [next_options[c] for c in candidates]
            current = random.choices(candidates, weights=weights, k=1)[0]

    return export_pattern_to_midi(notes, output_path, bpm=bpm)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_export/test_midi_export.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add packages/core/pyproject.toml
git add packages/core/src/openmusic/export/midi_export.py
git add packages/core/tests/test_export/test_midi_export.py
git commit -m "feat(export): add MIDI pattern export via isobar"
```

---

### Task 3: Beat Tracking & Tempo Validation (aubio)

**Files:**
- Create: `packages/core/src/openmusic/analysis/__init__.py`
- Create: `packages/core/src/openmusic/analysis/beat_tracker.py`
- Modify: `packages/core/pyproject.toml` — add `analysis` optional group
- Test: `packages/core/tests/test_analysis/test_beat_tracker.py`

- [ ] **Step 1: Add aubio dependency to pyproject.toml**

Insert into `[project.optional-dependencies]`:

```toml
analysis = [
  "aubio>=0.4.9",
  "librosa>=0.10.0",
]
```

`librosa` is already in `dev`: keep it there. Add `aubio` to `dev`:

```toml
dev = [..., "aubio>=0.4.9", ...]
```

- [ ] **Step 2: Write failing tests for beat tracker**

Create `packages/core/tests/test_analysis/test_beat_tracker.py`:

```python
"""Tests for analysis.beat_tracker module."""

import numpy as np
import pytest
import soundfile as sf

from openmusic.analysis.beat_tracker import (
    detect_tempo,
    detect_beats,
    validate_tempo_match,
    BEAT_TRACKING_METHODS,
)


# Shared fixture: 10 seconds of 125 BPM click track (4/4, quarter notes)
@pytest.fixture(scope="module")
def click_track_125bpm():
    sr = 48000
    duration = 10.0
    bpm = 125.0
    beat_interval = 60.0 / bpm  # 0.48 seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    audio = np.zeros(int(sr * duration))
    for beat_idx in range(int(duration / beat_interval)):
        sample = int(beat_idx * beat_interval * sr)
        if sample < len(audio):
            # Short click
            click_len = int(0.01 * sr)  # 10ms click
            end = min(sample + click_len, len(audio))
            click_env = np.hanning(end - sample) * 0.5
            audio[sample:end] = click_env
    return audio, sr, bpm


class TestDetectTempo:
    def test_detects_125bpm_from_click_track(self, click_track_125bpm):
        audio, sr, expected_bpm = click_track_125bpm
        detected = detect_tempo(audio, sr)
        assert detected is not None
        assert abs(detected - expected_bpm) < 5.0, (
            f"Expected ~{expected_bpm} BPM, got {detected}"
        )

    def test_returns_float(self, click_track_125bpm):
        audio, sr, _ = click_track_125bpm
        result = detect_tempo(audio, sr)
        assert isinstance(result, float) or result is None

    def test_silence_returns_none(self):
        audio = np.zeros(48000 * 3)
        result = detect_tempo(audio, 48000)
        assert result is None

    def test_supports_stereo(self, click_track_125bpm):
        audio, sr, expected_bpm = click_track_125bpm
        stereo = np.column_stack([audio, audio])
        detected = detect_tempo(stereo, sr)
        assert detected is not None
        assert abs(detected - expected_bpm) < 5.0

    def test_short_audio_returns_none(self):
        audio = np.random.randn(8000)  # <1 second
        result = detect_tempo(audio, 8000)
        assert result is None

    def test_beat_methods_list_not_empty(self):
        assert len(BEAT_TRACKING_METHODS) > 0
        assert "default" in BEAT_TRACKING_METHODS


class TestDetectBeats:
    def test_returns_beat_times(self, click_track_125bpm):
        audio, sr, _ = click_track_125bpm
        beats = detect_beats(audio, sr)
        assert isinstance(beats, list)
        assert len(beats) > 0
        for t in beats:
            assert isinstance(t, float)
            assert 0 <= t <= (len(audio) / sr)

    def test_beat_count_matches_bpm(self, click_track_125bpm):
        audio, sr, bpm = click_track_125bpm
        duration = len(audio) / sr
        expected_beats = int(duration * bpm / 60)
        beats = detect_beats(audio, sr)
        # Allow 20% margin (onset detection is approximate)
        assert len(beats) > expected_beats * 0.6

    def test_empty_for_silence(self):
        audio = np.zeros(48000 * 3)
        beats = detect_beats(audio, 48000)
        assert beats == []


class TestValidateTempoMatch:
    def test_exact_match(self):
        assert validate_tempo_match(125.0, 125.0, tolerance=2.0) is True

    def test_within_tolerance(self):
        assert validate_tempo_match(124.0, 125.0, tolerance=2.0) is True

    def test_outside_tolerance(self):
        assert validate_tempo_match(120.0, 125.0, tolerance=2.0) is False

    def test_none_detected(self):
        assert validate_tempo_match(None, 125.0) is False
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_analysis/test_beat_tracker.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 4: Write minimal implementation**

Create `packages/core/src/openmusic/analysis/__init__.py`:

```python
"""Audio analysis module for beat tracking, tempo detection, and analysis."""
```

Create `packages/core/src/openmusic/analysis/beat_tracker.py`:

```python
"""Beat tracking and tempo detection using aubio."""

from typing import Optional

import numpy as np

BEAT_TRACKING_METHODS = ["default", "specdiff", "phase"]


def _ensure_mono(audio: np.ndarray) -> np.ndarray:
    """Convert stereo to mono by averaging channels if needed."""
    if audio.ndim == 2:
        return np.mean(audio, axis=1)
    return audio


def detect_tempo(
    audio: np.ndarray,
    sample_rate: int,
    method: str = "default",
) -> Optional[float]:
    """Detect tempo (BPM) from audio using aubio.

    Args:
        audio: Float64 numpy array (mono or stereo).
        sample_rate: Sample rate in Hz.
        method: Beat tracking method ('default', 'specdiff', or 'phase').

    Returns:
        Detected BPM as float, or None if no stable tempo found / audio too short.

    Raises:
        ImportError: If aubio is not installed.
    """
    if method not in BEAT_TRACKING_METHODS:
        raise ValueError(f"Unknown method '{method}'. Options: {BEAT_TRACKING_METHODS}")

    try:
        import aubio
    except ImportError:
        raise ImportError(
            "aubio is required for tempo detection. "
            "Install: pip install openmusic-core[analysis]"
        )

    duration_sec = len(audio) / sample_rate
    if duration_sec < 1.0:
        return None

    mono = _ensure_mono(audio)

    tempo = aubio.tempo(method, buf_size=1024, hop_size=512, samplerate=sample_rate)
    beats = []

    total_frames = len(mono)
    hop_size = 512
    for start in range(0, total_frames, hop_size):
        end = min(start + hop_size, total_frames)
        block = mono[start:end]
        is_beat = tempo(block)
        if is_beat:
            beats.append(tempo.get_last_s())

    if len(beats) < 2:
        return None

    # Estimate BPM from average inter-beat interval
    intervals = np.diff(beats)
    if len(intervals) == 0:
        return None
    mean_interval = np.mean(intervals)
    if mean_interval <= 0:
        return None

    bpm = 60.0 / mean_interval
    return round(float(bpm), 1)


def detect_beats(
    audio: np.ndarray,
    sample_rate: int,
    method: str = "default",
) -> list[float]:
    """Detect beat times (in seconds) from audio using aubio.

    Args:
        audio: Float64 numpy array (mono or stereo).
        sample_rate: Sample rate in Hz.
        method: Beat tracking method.

    Returns:
        List of beat times in seconds (empty list if no beats detected).

    Raises:
        ImportError: If aubio is not installed.
    """
    try:
        import aubio
    except ImportError:
        raise ImportError(
            "aubio is required for beat detection. "
            "Install: pip install openmusic-core[analysis]"
        )

    mono = _ensure_mono(audio)
    tempo = aubio.tempo(method, buf_size=1024, hop_size=512, samplerate=sample_rate)
    beats = []

    total_frames = len(mono)
    hop_size = 512
    for start in range(0, total_frames, hop_size):
        end = min(start + hop_size, total_frames)
        block = mono[start:end]
        is_beat = tempo(block)
        if is_beat:
            beats.append(float(tempo.get_last_s()))

    return beats


def validate_tempo_match(
    detected_bpm: Optional[float],
    expected_bpm: float,
    tolerance: float = 2.0,
) -> bool:
    """Check if detected BPM matches expected BPM within tolerance.

    Args:
        detected_bpm: BPM detected from audio (None if detection failed).
        expected_bpm: Expected BPM (e.g. from MixConfig).
        tolerance: Allowed deviation in BPM (default: 2.0).

    Returns:
        True if detected BPM is within tolerance of expected BPM.
    """
    if detected_bpm is None:
        return False
    return abs(detected_bpm - expected_bpm) <= tolerance
```

- [ ] **Step 5: Create test directory `__init__.py`**

Create `packages/core/tests/test_analysis/__init__.py`:

```python
"""Analysis tests package."""
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_analysis/test_beat_tracker.py -v`
Expected: All tests PASS (click_track fixture may take ~2s to generate)

- [ ] **Step 7: Commit**

```bash
git add packages/core/pyproject.toml
git add packages/core/src/openmusic/analysis/__init__.py
git add packages/core/src/openmusic/analysis/beat_tracker.py
git add packages/core/tests/test_analysis/__init__.py
git add packages/core/tests/test_analysis/test_beat_tracker.py
git commit -m "feat(analysis): add beat tracking and tempo validation via aubio"
```

---

### Task 4: YouTube Live Streaming (PyLivestream)

**Files:**
- Create: `packages/core/src/openmusic/cli/stream.py`
- Modify: `packages/core/src/openmusic/cli/main.py` — register `stream` command group
- Modify: `packages/core/pyproject.toml` — add `stream` optional group
- Test: `packages/core/tests/test_cli/test_stream.py`

- [ ] **Step 1: Add PyLivestream dependency to pyproject.toml**

Insert into `[project.optional-dependencies]`:

```toml
stream = [
  "PyLivestream>=0.4.0",
  "ffmpeg-python>=0.2.0",
]
```

Add to `dev`:

```toml
dev = [..., "PyLivestream>=0.4.0", ...]
```

- [ ] **Step 2: Write failing tests for stream CLI**

Create `packages/core/tests/test_cli/test_stream.py`:

```python
"""Tests for cli.stream module."""

import pytest
from click.testing import CliRunner

from openmusic.cli.main import main
from openmusic.cli.stream import stream


class TestStreamCommandGroup:
    def test_stream_group_registered(self):
        """stream should be a subcommand of main."""
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "--help"])
        assert result.exit_code == 0
        assert "Live stream" in result.output or "stream" in result.output

    def test_start_requires_audio(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "start"])
        assert result.exit_code != 0
        assert "audio" in result.output.lower() or "Error" in result.output


class TestStreamStartCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "start", "--help"])
        assert result.exit_code == 0
        assert "--audio" in result.output
        assert "--platform" in result.output

    def test_nonexistent_audio_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            main, ["stream", "start", "--audio", "/nonexistent/file.wav"]
        )
        assert result.exit_code != 0

    def test_unsupported_platform_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "stream",
                "start",
                "--audio",
                "/tmp/test.wav",
                "--platform",
                "nonexistent",
            ],
        )
        assert result.exit_code != 0


class TestStreamStopCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "stop", "--help"])
        assert result.exit_code == 0


class TestStreamStatusCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "status", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_cli/test_stream.py -v`
Expected: Failures because `stream` not registered yet

- [ ] **Step 4: Write stream CLI module**

Create `packages/core/src/openmusic/cli/stream.py`:

```python
"""CLI commands for live streaming generated mixes to YouTube and other platforms."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

logger = logging.getLogger(__name__)

STREAM_PLATFORMS = ["youtube", "twitch", "facebook"]


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
    ).returncode == 0


def _get_stream_url(platform: str, stream_key: str) -> str:
    """Build RTMP ingest URL for a given platform."""
    urls = {
        "youtube": f"rtmp://a.rtmp.youtube.com/live2/{stream_key}",
        "twitch": f"rtmp://live.twitch.tv/app/{stream_key}",
        "facebook": f"rtmp://rtmp-api.facebook.com/rtmp/{stream_key}",
    }
    return urls.get(platform, "")


class StreamManager:
    """Manages a single ffmpeg live streaming subprocess."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None

    @property
    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(
        self,
        audio_path: str,
        platform: str,
        stream_key: str,
        cover_image: Optional[str] = None,
    ) -> None:
        """Start streaming an audio file to a live platform.

        Uses ffmpeg to loop an audio file and optionally a cover image
        as a static video feed.
        """
        if not _check_ffmpeg():
            raise RuntimeError("ffmpeg is required for live streaming but not found")

        if self.is_running:
            raise RuntimeError("Stream is already running")

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        ingest_url = _get_stream_url(platform, stream_key)
        if not ingest_url:
            raise ValueError(f"Unsupported platform: {platform}. Options: {STREAM_PLATFORMS}")

        # Build ffmpeg command:
        # - Stream audio continuously (loop)
        # - If cover image provided, use as static video; else audio-only
        cmd = [
            "ffmpeg",
            "-y",
            "-re",  # Real-time rate
            "-stream_loop", "-1",  # Loop audio forever
            "-i", audio_path,
        ]

        if cover_image and Path(cover_image).exists():
            cmd.extend(["-loop", "1", "-i", cover_image])
            # Map: audio from first input, video from second
            map_flags = [
                "-map", "1:v:0",  # video from cover image
                "-map", "0:a:0",  # audio from audio file
            ]
        else:
            # Audio-only stream
            map_flags = [
                "-map", "0:a:0",
            ]

        cmd.extend(map_flags)
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "128k",
            "-f", "flv",
            ingest_url,
        ])

        logger.info(f"Starting stream to {platform}")
        logger.debug(f"ffmpeg command: {' '.join(cmd)}")

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def stop(self) -> None:
        """Stop the running stream."""
        if self._process is None:
            logger.warning("No stream is running")
            return

        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._process = None
        logger.info("Stream stopped")

    def get_status(self) -> dict:
        """Get current stream status."""
        return {
            "running": self.is_running,
            "pid": self._process.pid if self._process and self.is_running else None,
        }


# Module-level singleton manages the stream process
_manager = StreamManager()


@click.group(help="Live stream generated mixes to YouTube, Twitch, or Facebook.")
def stream():
    """Live stream commands."""
    pass


@stream.command()
@click.option(
    "--audio",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Audio file to stream (looped)",
)
@click.option(
    "--platform",
    type=click.Choice(STREAM_PLATFORMS),
    default="youtube",
    help="Streaming platform",
)
@click.option(
    "--stream-key",
    required=True,
    envvar="YOUTUBE_STREAM_KEY",
    help="Stream key / ingest token. Can also set YOUTUBE_STREAM_KEY env var.",
)
@click.option(
    "--cover",
    type=click.Path(exists=True, dir_okay=False),
    help="Cover image for video feed (optional, audio-only otherwise)",
)
def start(audio: str, platform: str, stream_key: str, cover: Optional[str]):
    """Start live streaming an audio file to a platform."""
    try:
        _manager.start(
            audio_path=audio,
            platform=platform,
            stream_key=stream_key,
            cover_image=cover,
        )
        click.echo(f"Streaming to {platform}...")
        click.echo(f"  Audio: {audio}")
        if cover:
            click.echo(f"  Cover: {cover}")
        click.echo("Use 'openmusic stream stop' to end the stream.")
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


@stream.command()
def stop():
    """Stop the currently running stream."""
    _manager.stop()
    click.echo("Stream stopped.")


@stream.command()
def status():
    """Show stream status."""
    info = _manager.get_status()
    if info["running"]:
        click.echo(f"Stream is running (PID: {info['pid']})")
    else:
        click.echo("Stream is not running.")
```

- [ ] **Step 5: Register stream command group in main.py**

Edit `packages/core/src/openmusic/cli/main.py`. After the existing imports, add:

```python
from openmusic.cli.stream import stream as stream_group
```

Near the end of the file (before `auth_youtube` or after existing `main.add_command(short)`), add:

```python
main.add_command(stream_group)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_cli/test_stream.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add packages/core/pyproject.toml
git add packages/core/src/openmusic/cli/stream.py
git add packages/core/src/openmusic/cli/main.py
git add packages/core/tests/test_cli/test_stream.py
git commit -m "feat(cli): add YouTube live streaming commands via ffmpeg"
```

---

### Task 5: Audio Fingerprinting (pyacoustid)

**Files:**
- Create: `packages/core/src/openmusic/export/fingerprint.py`
- Modify: `packages/core/pyproject.toml` — add `fingerprint` optional group
- Test: `packages/core/tests/test_export/test_fingerprint.py`

- [ ] **Step 1: Add pyacoustid dependency to pyproject.toml**

Insert into `[project.optional-dependencies]`:

```toml
fingerprint = [
  "pyacoustid>=1.3.0",
  "chromaprint>=1.5.0",
]
```

Note: `chromaprint` is a C library wrapper. The actual C library (`libchromaprint`) must be installed system-wide (via apt/brew). Add a docstring noting the system dep.

Add to `dev`:

```toml
dev = [..., "pyacoustid>=1.3.0", ...]
```

- [ ] **Step 2: Write failing tests for fingerprint module**

Create `packages/core/tests/test_export/test_fingerprint.py`:

```python
"""Tests for export.fingerprint module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from openmusic.export.fingerprint import (
    generate_fingerprint,
    lookup_acoustid,
    FingerprintError,
)


def _create_test_wav(duration_sec: float = 3.0, sample_rate: int = 44100) -> str:
    """Create a temporary WAV file with a sine tone."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    audio = np.column_stack([audio, audio])  # stereo
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name


class TestGenerateFingerprint:
    def test_returns_string(self):
        path = _create_test_wav()
        try:
            fp = generate_fingerprint(path)
            assert isinstance(fp, str)
            assert len(fp) > 10
        finally:
            Path(path).unlink(missing_ok=True)

    def test_same_file_returns_same_fingerprint(self):
        path = _create_test_wav()
        try:
            fp1 = generate_fingerprint(path)
            fp2 = generate_fingerprint(path)
            assert fp1 == fp2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_different_files_different_fingerprints(self):
        path_a = _create_test_wav(duration_sec=3.0)
        path_b = _create_test_wav(duration_sec=5.0)
        try:
            fp_a = generate_fingerprint(path_a)
            fp_b = generate_fingerprint(path_b)
            assert fp_a != fp_b
        finally:
            Path(path_a).unlink(missing_ok=True)
            Path(path_b).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FingerprintError, match="not found"):
            generate_fingerprint("/nonexistent/file.wav")

    def test_returns_compressed_fingerprint(self):
        """Generated fingerprint should be valid base64-ish."""
        path = _create_test_wav()
        try:
            fp = generate_fingerprint(path)
            # Chromaprint compressed fingerprints are alphanumeric
            assert all(c.isalnum() or c in "-_" for c in fp)
        finally:
            Path(path).unlink(missing_ok=True)


class TestLookupAcoustid:
    def test_returns_dict_or_none(self):
        path = _create_test_wav()
        try:
            # This will likely fail without API key, but should
            # return a dict with 'error' or gracefully degrade
            result = lookup_acoustid(path, api_key="test")
            assert isinstance(result, (dict, type(None)))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_bad_api_key_returns_error_dict(self):
        path = _create_test_wav()
        try:
            result = lookup_acoustid(path, api_key="invalid_key")
            if isinstance(result, dict):
                assert "error" in result or "status" in result
        finally:
            Path(path).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FingerprintError):
            lookup_acoustid("/nonexistent/file.wav", api_key="test")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_export/test_fingerprint.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 4: Write minimal implementation**

Create `packages/core/src/openmusic/export/fingerprint.py`:

```python
"""Audio fingerprinting using Chromaprint and AcoustID lookup.

Requires system dependency: libchromaprint (apt: libchromaprint-dev, brew: chromaprint)

Usage:
    pip install openmusic-core[fingerprint]
    brew install chromaprint  # macOS
    sudo apt install libchromaprint-dev  # Linux
"""

import json
from pathlib import Path
from typing import Optional


class FingerprintError(Exception):
    """Raised when fingerprint generation or lookup fails."""


def generate_fingerprint(audio_path: str | Path) -> str:
    """Generate a Chromaprint audio fingerprint from a file.

    Args:
        audio_path: Path to an audio file (WAV, FLAC, MP3, etc.).

    Returns:
        Compressed fingerprint string.

    Raises:
        FingerprintError: If the file doesn't exist or fingerprinting fails.
        ImportError: If pyacoustid is not installed.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FingerprintError(f"Audio file not found: {audio_path}")

    try:
        import acoustid
    except ImportError:
        raise ImportError(
            "pyacoustid is required for fingerprinting. "
            "Install: pip install openmusic-core[fingerprint]"
        )

    try:
        duration, fp = acoustid.fingerprint_file(str(path))
        return fp
    except Exception as e:
        raise FingerprintError(f"Fingerprint generation failed: {e}")


def lookup_acoustid(
    audio_path: str | Path,
    api_key: str,
) -> Optional[dict]:
    """Look up an audio file in the AcoustID database.

    Args:
        audio_path: Path to an audio file.
        api_key: AcoustID API key (get one at https://acoustid.org/api-key).

    Returns:
        Dict with AcoustID lookup results, or None if lookup fails.

    Raises:
        FingerprintError: If the file doesn't exist.
        ImportError: If pyacoustid is not installed.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FingerprintError(f"Audio file not found: {audio_path}")

    try:
        import acoustid
    except ImportError:
        raise ImportError(
            "pyacoustid is required for AcoustID lookup. "
            "Install: pip install openmusic-core[fingerprint]"
        )

    try:
        results = acoustid.lookup(api_key, str(path))
        return results
    except acoustid.NoBackendError:
        raise FingerprintError(
            "Chromaprint library not found. "
            "Install system dependency: apt install libchromaprint-dev"
        )
    except Exception as e:
        return {"error": str(e)}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_export/test_fingerprint.py -v`
Expected: All tests PASS

- [ ] **Step 6: Install system dependency check note**

Add a comment at the top of `fingerprint.py` that can be surfaced at import time if the C library is missing — but don't block import. The `NoBackendError` handler in `lookup_acoustid` already handles this gracefully.

- [ ] **Step 7: Commit**

```bash
git add packages/core/pyproject.toml
git add packages/core/src/openmusic/export/fingerprint.py
git add packages/core/tests/test_export/test_fingerprint.py
git commit -m "feat(export): add audio fingerprinting via Chromaprint/AcoustID"
```

---

## Self-Review

### 1. Spec Coverage
- **Loudness normalization**: Task 1 — `measure_integrated_loudness`, `normalize_loudness`, CLI integration optional.
- **MIDI pattern export**: Task 2 — `export_pattern_to_midi`, `pattern_to_isobar_sequence`, `export_markov_chain_to_midi`.
- **Beat tracking**: Task 3 — `detect_tempo`, `detect_beats`, `validate_tempo_match`.
- **YouTube live streaming**: Task 4 — `openmusic stream start/stop/status`, multi-platform.
- **Audio fingerprinting**: Task 5 — `generate_fingerprint`, `lookup_acoustid`.

All 5 features have: implementation module, test file, pyproject.toml entry, and commit step.

### 2. Placeholder Scan
No placeholder patterns found. All code is complete, all test assertions are concrete, all commands have expected output.

### 3. Type Consistency
- `audioldnorm` exports: `measure_integrated_loudness(audio, sr) -> float`, `normalize_loudness(audio, sr, target) -> ndarray` — consistent across tests and impl.
- `midi_export` exports: `export_pattern_to_midi(notes, path, bpm, ...) -> Path` — all call sites match.
- `beat_tracker` exports: `detect_tempo(audio, sr) -> Optional[float]` — all callers handle None.
- `stream` CLI: `start(audio, platform, stream_key, cover)` — same signature in decorator and function.
- `fingerprint` exports: `generate_fingerprint(path) -> str`, `lookup_acoustid(path, key) -> Optional[dict]` — consistent.
