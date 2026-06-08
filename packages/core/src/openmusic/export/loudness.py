"""EBU R128 loudness normalization using pyloudnorm."""

import numpy as np

LUFS_TARGET = -14.0


def _validate_audio(audio: np.ndarray) -> None:
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
    """Measure integrated loudness in LUFS using EBU R128."""
    _validate_audio(audio)
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
    """Normalize audio to a target integrated loudness (EBU R128)."""
    current = measure_integrated_loudness(audio, sample_rate)
    if not np.isfinite(current):
        return audio
    gain_db = target - current
    linear_gain = 10.0 ** (gain_db / 20.0)
    result = audio * linear_gain
    return np.clip(result, -1.0, 1.0)
