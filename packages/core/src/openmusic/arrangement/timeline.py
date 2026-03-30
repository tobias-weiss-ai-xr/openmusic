from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Track:
    audio_path: Path
    start_time: float
    duration: float

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    def contains(self, time: float) -> bool:
        return self.start_time <= time < self.end_time


class Timeline:
    def __init__(self, total_duration: float, bpm: int):
        self._total_duration = total_duration
        self._bpm = bpm
        self._tracks: list[Track] = []

    @property
    def total_duration(self) -> float:
        return self._total_duration

    @property
    def bpm(self) -> int:
        return self._bpm

    def add_segment(
        self, audio_path: str | Path, start_time: float, duration: float
    ) -> None:
        track = Track(
            audio_path=Path(audio_path),
            start_time=start_time,
            duration=duration,
        )
        self._tracks.append(track)

    def get_segments_at(self, time: float) -> list[Track]:
        return [t for t in self._tracks if t.contains(time)]
