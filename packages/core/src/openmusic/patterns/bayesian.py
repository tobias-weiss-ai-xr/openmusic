from __future__ import annotations

import random
import math
from typing import Optional

from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


class BayesianPatternSelector:
    """Thompson-sampling pattern selector using Beta posterior distributions."""

    def __init__(self, library: PatternLibrary, alpha_prior: float = 2.0, beta_prior: float = 2.0):
        self._library = library
        self._alpha_prior = alpha_prior
        self._beta_prior = beta_prior

    def select(self, candidates: list[PatternEntry]) -> Optional[PatternEntry]:
        if not candidates:
            return None
        scores = []
        for p in candidates:
            alpha = self._alpha_prior + p.quality_score * (1 + p.play_count)
            beta = self._beta_prior + (1 - p.quality_score) * (1 + p.play_count)
            score = random.betavariate(alpha, beta)
            scores.append(score)
        best_idx = max(range(len(candidates)), key=lambda i: scores[i])
        selected = candidates[best_idx]
        self._library.increment_play_count(selected.path)
        return selected

    def set_quality_feedback(self, path: str, rating: float) -> None:
        self._library.update_quality_score(path, rating)
