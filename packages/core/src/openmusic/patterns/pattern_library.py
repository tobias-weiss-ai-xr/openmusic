from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import random

logger = logging.getLogger(__name__)


@dataclass
class PatternEntry:
    """A single pre-generated audio pattern with metadata."""
    path: str
    duration: float
    bpm: int
    key: str
    tags: list[str] = field(default_factory=list)
    energy: float = 0.5       # 0.0 (low) - 1.0 (high)
    density: float = 0.5      # 0.0 (sparse) - 1.0 (dense)
    phase: str = "build"      # intro, build, peak, sustain, release, outro
    play_count: int = 0
    quality_score: float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PatternEntry":
        return cls(**d)


class PatternLibrary:
    """Manages a JSON-backed collection of pre-generated patterns."""

    def __init__(self, path: str | Path, auto_load: bool = True):
        self._path = Path(path)
        self._patterns: list[PatternEntry] = []
        if auto_load and self._path.exists():
            self.load()

    def add(self, entry: PatternEntry) -> None:
        self._patterns.append(entry)

    def add_many(self, entries: list[PatternEntry]) -> None:
        self._patterns.extend(entries)

    def get_by_tags(self, tags: list[str], mode: str = "any") -> list[PatternEntry]:
        if mode == "any":
            return [p for p in self._patterns if any(t in p.tags for t in tags)]
        return [p for p in self._patterns if all(t in p.tags for t in tags)]

    def get_by_phase(self, phase: str) -> list[PatternEntry]:
        return [p for p in self._patterns if p.phase == phase]

    def get_by_energy_range(self, low: float, high: float) -> list[PatternEntry]:
        return [p for p in self._patterns if low <= p.energy <= high]

    def get_unused(self) -> list[PatternEntry]:
        return [p for p in self._patterns if p.play_count == 0]

    def increment_play_count(self, path: str) -> None:
        for p in self._patterns:
            if p.path == path:
                p.play_count += 1
                break

    def update_quality_score(self, path: str, score: float) -> None:
        for p in self._patterns:
            if p.path == path:
                p.quality_score = score
                break

    def sample(self, candidates: list[PatternEntry]) -> Optional[PatternEntry]:
        if not candidates:
            return None
        weights = [1.0 / (1.0 + p.play_count) for p in candidates]
        total = sum(weights)
        normalized = [w / total for w in weights]
        return random.choices(candidates, weights=normalized, k=1)[0]

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [p.to_dict() for p in self._patterns]
        self._path.write_text(json.dumps(data, indent=2))

    def load(self) -> None:
        if not self._path.exists() or self._path.stat().st_size == 0:
            self._patterns = []
            return
        data = json.loads(self._path.read_text())
        self._patterns = [PatternEntry.from_dict(d) for d in data]

    @property
    def patterns(self) -> list[PatternEntry]:
        return list(self._patterns)

    @property
    def count(self) -> int:
        return len(self._patterns)

    def __len__(self) -> int:
        return self.count
