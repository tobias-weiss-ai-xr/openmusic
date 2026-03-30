from __future__ import annotations

import numpy as np

VALID_CURVE_TYPES = frozenset({"linear", "equal_power", "sine"})


def generate_crossfade_curve(
    duration_samples: int,
    curve_type: str,
) -> tuple[np.ndarray, np.ndarray]:
    if curve_type not in VALID_CURVE_TYPES:
        raise ValueError(
            f"Invalid curve_type '{curve_type}'. Must be one of: {sorted(VALID_CURVE_TYPES)}"
        )

    t = np.linspace(0.0, 1.0, duration_samples)

    if curve_type == "linear":
        fade_in = t
        fade_out = 1.0 - t
    elif curve_type == "equal_power":
        half_pi = np.linspace(0, np.pi / 2, duration_samples)
        fade_in = np.sin(half_pi) ** 2
        fade_out = np.cos(half_pi) ** 2
    else:
        half_pi = np.linspace(0, np.pi / 2, duration_samples)
        fade_in = np.sin(half_pi)
        fade_out = np.cos(half_pi)

    return fade_in, fade_out


def crossfade_numpy(
    audio_a: np.ndarray,
    audio_b: np.ndarray,
    fade_duration: float,
    sample_rate: int,
    curve_type: str = "equal_power",
) -> np.ndarray:
    fade_samples = int(fade_duration * sample_rate)

    if audio_a.shape[0] != audio_b.shape[0]:
        raise ValueError("audio_a and audio_b must have the same length")
    if fade_samples > audio_a.shape[0]:
        raise ValueError("fade_duration is longer than audio arrays")

    fade_in, fade_out = generate_crossfade_curve(fade_samples, curve_type)

    a = audio_a.astype(np.float64)
    b = audio_b.astype(np.float64)

    if a.ndim == 1:
        a[-fade_samples:] *= fade_out
        b[:fade_samples] *= fade_in
        return a.copy()

    if a.ndim == 2:
        result = a.copy()
        result[-fade_samples:, :] *= fade_out[:, np.newaxis]
        b_faded = b.copy()
        b_faded[:fade_samples, :] *= fade_in[:, np.newaxis]
        result[-fade_samples:, :] += b_faded[:fade_samples, :]
        return result

    raise ValueError(f"Unsupported audio shape: {a.ndim} dimensions")
