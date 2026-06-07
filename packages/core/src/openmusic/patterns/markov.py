from __future__ import annotations

import random
from enum import Enum
from typing import Optional


class Phase(str, Enum):
    INTRO = "intro"
    BUILD = "build"
    PEAK = "peak"
    SUSTAIN = "sustain"
    RELEASE = "release"
    OUTRO = "outro"


_TRANSITION_MATRIX: dict[Phase, list[tuple[Phase, float]]] = {
    Phase.INTRO: [
        (Phase.INTRO, 0.30),
        (Phase.BUILD, 0.50),
        (Phase.PEAK, 0.15),
        (Phase.RELEASE, 0.05),
    ],
    Phase.BUILD: [
        (Phase.BUILD, 0.20),
        (Phase.PEAK, 0.55),
        (Phase.SUSTAIN, 0.15),
        (Phase.RELEASE, 0.10),
    ],
    Phase.PEAK: [
        (Phase.PEAK, 0.15),
        (Phase.SUSTAIN, 0.60),
        (Phase.RELEASE, 0.20),
        (Phase.OUTRO, 0.05),
    ],
    Phase.SUSTAIN: [
        (Phase.SUSTAIN, 0.35),
        (Phase.PEAK, 0.10),
        (Phase.RELEASE, 0.45),
        (Phase.OUTRO, 0.10),
    ],
    Phase.RELEASE: [
        (Phase.RELEASE, 0.25),
        (Phase.OUTRO, 0.50),
        (Phase.BUILD, 0.20),
        (Phase.INTRO, 0.05),
    ],
    Phase.OUTRO: [
        (Phase.INTRO, 0.80),
        (Phase.OUTRO, 0.15),
        (Phase.BUILD, 0.05),
    ],
}


class PhaseTransitionMatrix:
    """Markov chain for musical phase transitions."""

    def __init__(self, matrix: Optional[dict[Phase, list[tuple[Phase, float]]]] = None):
        self._matrix = matrix or _TRANSITION_MATRIX

    def next_phase(self, current: Phase) -> Phase:
        transitions = self._matrix.get(current)
        if not transitions:
            return Phase.OUTRO
        phases, weights = zip(*transitions)
        return random.choices(phases, weights=weights, k=1)[0]

    def generate_sequence(self, length: int, start: Phase = Phase.INTRO) -> list[Phase]:
        seq = [start]
        for _ in range(length - 1):
            seq.append(self.next_phase(seq[-1]))
        return seq

    @property
    def matrix(self) -> dict[Phase, list[tuple[Phase, float]]]:
        return dict(self._matrix)

    @classmethod
    def dub_techno(cls) -> "PhaseTransitionMatrix":
        return cls({
            Phase.INTRO: [(Phase.INTRO, 0.25), (Phase.BUILD, 0.55), (Phase.PEAK, 0.15), (Phase.RELEASE, 0.05)],
            Phase.BUILD: [(Phase.BUILD, 0.15), (Phase.PEAK, 0.60), (Phase.SUSTAIN, 0.15), (Phase.RELEASE, 0.10)],
            Phase.PEAK: [(Phase.PEAK, 0.10), (Phase.SUSTAIN, 0.65), (Phase.RELEASE, 0.20), (Phase.OUTRO, 0.05)],
            Phase.SUSTAIN: [(Phase.SUSTAIN, 0.30), (Phase.PEAK, 0.10), (Phase.RELEASE, 0.50), (Phase.OUTRO, 0.10)],
            Phase.RELEASE: [(Phase.RELEASE, 0.20), (Phase.OUTRO, 0.55), (Phase.BUILD, 0.20), (Phase.INTRO, 0.05)],
            Phase.OUTRO: [(Phase.INTRO, 0.80), (Phase.OUTRO, 0.15), (Phase.BUILD, 0.05)],
        })

    @classmethod
    def ambient(cls) -> "PhaseTransitionMatrix":
        return cls({
            Phase.INTRO: [(Phase.INTRO, 0.50), (Phase.BUILD, 0.30), (Phase.SUSTAIN, 0.15), (Phase.RELEASE, 0.05)],
            Phase.BUILD: [(Phase.BUILD, 0.30), (Phase.SUSTAIN, 0.50), (Phase.PEAK, 0.10), (Phase.RELEASE, 0.10)],
            Phase.PEAK: [(Phase.PEAK, 0.10), (Phase.SUSTAIN, 0.70), (Phase.RELEASE, 0.15), (Phase.OUTRO, 0.05)],
            Phase.SUSTAIN: [(Phase.SUSTAIN, 0.50), (Phase.RELEASE, 0.35), (Phase.OUTRO, 0.10), (Phase.PEAK, 0.05)],
            Phase.RELEASE: [(Phase.RELEASE, 0.30), (Phase.OUTRO, 0.50), (Phase.INTRO, 0.15), (Phase.SUSTAIN, 0.05)],
            Phase.OUTRO: [(Phase.INTRO, 0.80), (Phase.OUTRO, 0.15), (Phase.SUSTAIN, 0.05)],
        })


class StyleFactory:
    """Convenience factory for predefined Markov chain styles."""

    STYLES = {
        "dub_techno": PhaseTransitionMatrix.dub_techno,
        "ambient": PhaseTransitionMatrix.ambient,
        "club": lambda: PhaseTransitionMatrix({
            Phase.INTRO: [(Phase.INTRO, 0.15), (Phase.BUILD, 0.60), (Phase.PEAK, 0.20), (Phase.RELEASE, 0.05)],
            Phase.BUILD: [(Phase.BUILD, 0.10), (Phase.PEAK, 0.70), (Phase.SUSTAIN, 0.10), (Phase.RELEASE, 0.10)],
            Phase.PEAK: [(Phase.PEAK, 0.10), (Phase.SUSTAIN, 0.70), (Phase.RELEASE, 0.15), (Phase.OUTRO, 0.05)],
            Phase.SUSTAIN: [(Phase.SUSTAIN, 0.20), (Phase.PEAK, 0.15), (Phase.RELEASE, 0.55), (Phase.OUTRO, 0.10)],
            Phase.RELEASE: [(Phase.RELEASE, 0.15), (Phase.OUTRO, 0.60), (Phase.BUILD, 0.20), (Phase.INTRO, 0.05)],
            Phase.OUTRO: [(Phase.INTRO, 0.80), (Phase.OUTRO, 0.15), (Phase.BUILD, 0.05)],
        }),
        "all_night": lambda: PhaseTransitionMatrix({
            Phase.INTRO: [(Phase.INTRO, 0.20), (Phase.BUILD, 0.40), (Phase.SUSTAIN, 0.25), (Phase.PEAK, 0.10), (Phase.RELEASE, 0.05)],
            Phase.BUILD: [(Phase.BUILD, 0.15), (Phase.PEAK, 0.35), (Phase.SUSTAIN, 0.30), (Phase.RELEASE, 0.15), (Phase.OUTRO, 0.05)],
            Phase.PEAK: [(Phase.PEAK, 0.10), (Phase.SUSTAIN, 0.50), (Phase.RELEASE, 0.25), (Phase.BUILD, 0.10), (Phase.OUTRO, 0.05)],
            Phase.SUSTAIN: [(Phase.SUSTAIN, 0.40), (Phase.RELEASE, 0.30), (Phase.PEAK, 0.10), (Phase.BUILD, 0.10), (Phase.OUTRO, 0.10)],
            Phase.RELEASE: [(Phase.RELEASE, 0.20), (Phase.OUTRO, 0.35), (Phase.SUSTAIN, 0.20), (Phase.BUILD, 0.15), (Phase.INTRO, 0.10)],
            Phase.OUTRO: [(Phase.INTRO, 0.80), (Phase.OUTRO, 0.15), (Phase.BUILD, 0.05)],
        }),
    }

    @classmethod
    def create(cls, style: str) -> PhaseTransitionMatrix:
        factory = cls.STYLES.get(style)
        if factory is None:
            raise ValueError(f"Unknown style '{style}'. Available: {list(cls.STYLES)}")
        return factory()
