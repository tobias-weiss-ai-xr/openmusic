from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from openmusic.arrangement.crossfade import crossfade_numpy
from openmusic.arrangement.timeline import Timeline

DEFAULT_SAMPLE_RATE = 48000
CROSSFADE_BEATS = 4
SEGMENT_DURATION = 180.0


def load_audio(path: str | Path) -> np.ndarray:
    """Read a WAV file and return a float64 numpy array with shape (samples, channels)."""
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sample_width == 1:
        dtype = np.uint8
        max_val = 128.0
    elif sample_width == 2:
        dtype = np.int16
        max_val = 32768.0
    elif sample_width == 3:
        # 24-bit: unpack manually
        n_bytes = len(raw)
        n_samples = n_bytes // 3
        samples = np.zeros(n_samples, dtype=np.int32)
        for i in range(n_samples):
            b = raw[i * 3 : i * 3 + 3]
            samples[i] = int.from_bytes(b, byteorder="little", signed=True)
        samples = samples.reshape((n_frames, n_channels))
        return samples.astype(np.float64) / 8388608.0
    elif sample_width == 4:
        dtype = np.int32
        max_val = 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sample_width} bytes")

    samples = np.frombuffer(raw, dtype=dtype)
    samples = samples.reshape((n_frames, n_channels))
    if sample_width == 1:
        # uint8 WAV is unsigned (0-255), center at 128
        return (samples.astype(np.float64) - 128.0) / max_val
    return samples.astype(np.float64) / max_val


def save_audio(audio: np.ndarray, path: str | Path) -> None:
    """Write a float64 numpy array to a 16-bit PCM WAV file.

    Expects array with shape (samples, channels) or (samples,) for mono.
    """
    audio = np.clip(audio, -1.0, 1.0)
    if audio.ndim == 1:
        audio = audio.reshape((-1, 1))
    samples_int = (audio * 32767).astype(np.int16)
    n_frames, n_channels = samples_int.shape

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(DEFAULT_SAMPLE_RATE)
        wf.writeframes(samples_int.tobytes())


class MixArranger:
    def __init__(self, bpm: int, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.bpm = bpm
        self.sample_rate = sample_rate

    def get_crossfade_duration(self) -> float:
        return CROSSFADE_BEATS * (60.0 / self.bpm)

    def get_arrangement_length(self, segment_count: int) -> float:
        if segment_count <= 1:
            return SEGMENT_DURATION
        crossfade = self.get_crossfade_duration()
        return segment_count * SEGMENT_DURATION - (segment_count - 1) * crossfade

    def arrange_segments(
        self,
        segment_paths: list[str],
        curve_type: str = "equal_power",
    ) -> Path:
        if len(segment_paths) < 1:
            raise ValueError("segment_paths must contain at least one segment")

        segments = [load_audio(p) for p in segment_paths]

        if len(segments) == 1:
            output_path = Path("arranged_mix.wav")
            save_audio(segments[0], output_path)
            return output_path

        crossfade_dur = self.get_crossfade_duration()
        cf_samples = int(crossfade_dur * self.sample_rate)

        parts: list[np.ndarray] = [segments[0][:-cf_samples]]

        for i in range(1, len(segments)):
            a_tail = segments[i - 1][-cf_samples:]
            b_head = segments[i][:cf_samples]
            xfade = crossfade_numpy(
                a_tail, b_head, crossfade_dur, self.sample_rate, curve_type
            )
            parts.append(xfade)
            if i < len(segments) - 1:
                parts.append(segments[i][cf_samples:-cf_samples])
            else:
                parts.append(segments[i][cf_samples:])

        result = np.concatenate(parts)
        output_path = Path("arranged_mix.wav")
        save_audio(result, output_path)
        return output_path
