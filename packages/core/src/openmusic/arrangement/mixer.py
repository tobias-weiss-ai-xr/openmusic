from __future__ import annotations

from pathlib import Path

import numpy as np

from openmusic.arrangement.crossfade import crossfade_numpy
from openmusic.arrangement.timeline import Timeline

DEFAULT_SAMPLE_RATE = 48000
CROSSFADE_BEATS = 4
SEGMENT_DURATION = 180.0


def load_audio(path: str | Path) -> np.ndarray:
    return np.load(str(path))


def save_audio(audio: np.ndarray, path: str | Path) -> None:
    np.save(str(path), audio)


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
            output_path = Path("arranged_mix.npy")
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
        output_path = Path("arranged_mix.npy")
        save_audio(result, output_path)
        return output_path
