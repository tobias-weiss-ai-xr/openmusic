"""Tests for Bayesian pattern selector using Thompson sampling."""

import pytest
from openmusic.patterns.bayesian import BayesianPatternSelector
from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


class TestBayesianPatternSelector:
    """Tests for Bayesian pattern selector."""

    def test_empty_candidates_returns_none(self):
        """Returns None when no candidates are provided."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        selector = BayesianPatternSelector(library)
        result = selector.select([])
        assert result is None

    def test_selects_from_single_candidate(self):
        """Selects the only available candidate."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        selector = BayesianPatternSelector(library)
        result = selector.select([pattern])
        assert result == pattern

    def test_increments_play_count_on_select(self):
        """Selecting a pattern increments its play count."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        selector = BayesianPatternSelector(library)
        selector.select([pattern])
        assert pattern.play_count == 1

    def test_quality_feedback_updates_scores(self):
        """Setting quality feedback updates the pattern's quality score."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        selector = BayesianPatternSelector(library)
        selector.set_quality_feedback("test.wav", 0.8)
        assert pattern.quality_score == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
