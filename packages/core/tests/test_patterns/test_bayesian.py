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
        pattern = PatternEntry(
            path="/test.wav", duration=30.0, bpm=125, key="Dm", tags=[]

        )
        library.add(pattern)
        selector = BayesianPatternSelector(library)
        result = selector.select([pattern])
        assert result == pattern

    def test_sets_quality_feedback_updates_scores(self):
        """Setting quality feedback updates the pattern's quality score."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        pattern = PatternEntry(
            path="/test.wav", duration=30.0, bpm=125, key="Dm", tags=[]
        )
        library.add(pattern)

        selector = BayesianPatternSelector(library)
        selector.set_quality_feedback("/test.wav", 0.8)

        # The quality score should have been updated
        for p in library.patterns:
            if p.path == "/test.wav":
                assert p.quality_score == 0.8
                break
        else:
            pytest.fail("Pattern not found in library")

    def test_select_increments_play_count(self):
        """Selecting a pattern increments its play count."""
        library = PatternLibrary(path="/tmp/test_bayesian.json")
        pattern = PatternEntry(
            path="/test.wav", duration=30.0, bpm=125, key="Dm", tags=[]
        )
        library.add(pattern)
        selector = BayesianPatternSelector(library)

        assert pattern.play_count == 0
        selector.select([pattern])
        assert pattern.play_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
