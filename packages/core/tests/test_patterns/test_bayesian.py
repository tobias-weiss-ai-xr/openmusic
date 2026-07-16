"""Tests for Bayesian pattern selector using Thompson sampling."""

import pytest
from openmusic.patterns.bayesian import BayesianPatternSelector
from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


class TestBayesianPatternSelector:
    """Tests for Bayesian pattern selector."""

    def test_empty_candidates_returns_none(self, tmp_path):
        """Returns None when no candidates are provided."""
        library = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        selector = BayesianPatternSelector(library)
        result = selector.select([])
        assert result is None

    def test_selects_from_single_candidate(self, tmp_path):
        """Selects the only available candidate."""
        library = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        pattern = PatternEntry(path="test.py", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        selector = BayesianPatternSelector(library)
        result = selector.select([pattern])
        assert result == pattern

    def test_preferences_higher_quality_candidates(self, tmp_path):
        """Thompson sampling favors higher quality patterns with enough samples."""
        library = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        high_quality = PatternEntry(path="high.py", duration=30.0, bpm=125, key="Dm")
        high_quality.quality_score = 0.9
        high_quality.play_count = 10
        low_quality = PatternEntry(path="low.py", duration=30.0, bpm=125, key="Dm")
        low_quality.quality_score = 0.3
        low_quality.play_count = 10

        library.add(high_quality)
        library.add(low_quality)

        selector = BayesianPatternSelector(library)
        high_wins = 0
        for _ in range(20):
            result = selector.select([high_quality, low_quality])
            if result == high_quality:
                high_wins += 1
        assert high_wins >= 15

    def test_quality_feedback_updates_scores(self, tmp_path):
        """Setting quality feedback updates the pattern's quality score."""
        library = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        pattern = PatternEntry(path="test.py", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)

        selector = BayesianPatternSelector(library)
        selector.set_quality_feedback("test.py", 0.8)

        assert pattern.quality_score == 0.8
