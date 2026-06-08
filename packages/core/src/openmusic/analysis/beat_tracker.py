"""Beat tracking and tempo validation using aubio."""

from __future__ import annotations

from typing import Optional

import numpy as np

BEAT_TRACKING_METHODS = ["default", "specdiff", "phase"]

BUF_SIZE = 1024
HOP_SIZE = 512
MIN_AUDIO_SECONDS = 1.0


def _to_mono(audio: np.ndarray) -> np.ndarray:
    """Convert stereo audio to mono by averaging channels."""
    if audio.ndim == 1:
        return audio
    if audio.ndim == 2:
        return np.mean(audio, axis=1)
    return audio


def detect_tempo(
    audio: np.ndarray, sample_rate: int, method: str = "default"
) -> Optional[float]:
    """Detect tempo (BPM) from audio using aubio.

    Args:
        audio: Float64 numpy array (mono or stereo).
        sample_rate: Sample rate in Hz.
        method: Beat tracking method ('default', 'specdiff', or 'phase').

    Returns:
        Detected BPM as float, or None if no stable tempo found / audio too short.

    Raises:
        ValueError: If method is unknown.
        ImportError: If aubio is not installed.
    """
    if method not in BEAT_TRACKING_METHODS:
        raise ValueError(f"Unknown method: {method}. Must be one of {BEAT_TRACKING_METHODS}")

    audio = _to_mono(audio)
    duration = len(audio) / sample_rate

    if duration < MIN_AUDIO_SECONDS:
        return None

    if np.all(np.abs(audio) < 1e-10):
        return None

    import aubio  # type: ignore[import-untyped]

    tempo = aubio.tempo(method, BUF_SIZE, HOP_SIZE, sample_rate)  # type: ignore[attr-defined]

    total_frames = len(audio)
    position = 0
    while position + HOP_SIZE <= total_frames:
        frame = audio[position : position + HOP_SIZE].astype(np.float32)
        tempo(frame)
        position += HOP_SIZE

    bpm = tempo.get_bpm()
    if bpm is None or bpm <= 0:
        return None
    return float(bpm)


def detect_beats(
    audio: np.ndarray, sample_rate: int, method: str = "default"
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
    if method not in BEAT_TRACKING_METHODS:
        raise ValueError(f"Unknown method: {method}. Must be one of {BEAT_TRACKING_METHODS}")

    audio = _to_mono(audio)

    if np.all(np.abs(audio) < 1e-10):
        return []

    import aubio  # type: ignore[import-untyped]

    tempo = aubio.tempo(method, BUF_SIZE, HOP_SIZE, sample_rate)  # type: ignore[attr-defined]
    beats: list[float] = []

    total_frames = len(audio)
    position = 0
    while position + HOP_SIZE <= total_frames:
        frame = audio[position : position + HOP_SIZE].astype(np.float32)
        is_beat = tempo(frame)
        if is_beat:
            beat_time = tempo.get_last_s()
            if beat_time is not None:
                beats.append(float(beat_time))
        position += HOP_SIZE

    return beats


def validate_tempo_match(
    detected_bpm: Optional[float], expected_bpm: float, tolerance: float = 2.0
) -> bool:
    """Check if detected BPM matches expected BPM within tolerance.

    Returns True if detected BPM is within tolerance of expected BPM, False otherwise.
    Returns False if detected_bpm is None.
    """
    if detected_bpm is None:
        return False
    return abs(detected_bpm - expected_bpm) <= tolerance
