"""Tests for Bayesian pattern selector using Thompson sampling."""

import tempfile

import pytest
from openmusic.patterns.bayesian import BayesianPatternSelector
from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


class TestBayesianPatternSelector:
    """Tests for Bayesian pattern selector."""

    def test_empty_candidates_returns_none(self):
        """Returns None when no candidates are provided."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            library = PatternLibrary(path=f.name)
            selector = BayesianPatternSelector(library)
            result = selector.select([])
            assert result is None

    def test_selects_from_single_candidate(self):
        """Selects the only available candidate."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            library = PatternLibrary(path=f.name)
            pattern = PatternEntry(
                path="test.wav", duration=30.0, bpm=125, key="Dm"
            )
            library.add(pattern)
            selector = BayesianPatternSelector(library)
            result = selector.select([pattern])
            assert result == pattern

    def test_preferences_higher_quality_candidates(self):
        """Thompson sampling favors higher quality patterns with enough samples."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            library = PatternLibrary(path=f.name)
            high_quality = PatternEntry(
                path="high.wav", duration=30.0, bpm=125, key="Dm"
            )
            high_quality.quality_score = 0.9
            high_quality.play_count = 10
            low_quality = PatternEntry(
                path="low.wav", duration=30.0, bpm=125, key="Dm"
            )
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

    def test_quality_feedback_updates_scores(self):
        """Setting quality feedback updates the pattern's quality score."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            library = PatternLibrary(path=f.name)
            pattern = PatternEntry(
                path="test.wav", duration=30.0, bpm=125, key="Dm"
            )
            library.add(pattern)

            selector = BayesianPatternSelector(library)
            selector.set_quality_feedback("test.wav", 0.8)

            assert pattern.quality_score == 0.8
