"""Tests for Bayesian pattern selector using Thompson sampling."""

import tempfile
import os

import pytest
from openmusic.patterns.bayesian import BayesianPatternSelector
from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


@pytest.fixture
def lib_path():
    """Provide a temporary path for PatternLibrary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "patterns.json")


def make_library(path: str) -> PatternLibrary:
    """Create an empty PatternLibrary at the given path."""
    return PatternLibrary(path=path, auto_load=False)


class TestBayesianPatternSelector:
    """Tests for Bayesian pattern selector."""

    def test_empty_candidates_returns_none(self, lib_path):
        """Returns None when no candidates are provided."""
        library = make_library(lib_path)
        selector = BayesianPatternSelector(library)
        result = selector.select([])
        assert result is None

    def test_selects_from_single_candidate(self, lib_path):
        """Selects the only available candidate."""
        library = make_library(lib_path)
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)

        selector = BayesianPatternSelector(library)
        result = selector.select([pattern])
        assert result == pattern

    def test_preferences_higher_quality_candidates(self, lib_path):
        """Thompson sampling favors higher quality patterns with enough samples."""
        library = make_library(lib_path)
        high_quality = PatternEntry(path="high.wav", duration=30.0, bpm=125, key="Dm")
        high_quality.quality_score = 0.9
        high_quality.play_count = 10
        low_quality = PatternEntry(path="low.wav", duration=30.0, bpm=125, key="Dm")
        low_quality.quality_score = 0.3
        low_quality.play_count = 10

        library.add(high_quality)
        library.add(low_quality)

        selector = BayesianPatternSelector(library)
        # With enough samples, should typically select high quality
        high_wins = 0
        for _ in range(20):
            result = selector.select([high_quality, low_quality])
            if result == high_quality:
                high_wins += 1
        assert high_wins >= 15  # Should be strongly biased toward high quality

    def test_quality_feedback_updates_scores(self, lib_path):
        """Setting quality feedback updates the pattern's quality score."""
        library = make_library(lib_path)
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        assert pattern.quality_score == 0.5

        selector = BayesianPatternSelector(library)
        selector.set_quality_feedback("test.wav", 0.8)

        assert pattern.quality_score == 0.8

    def test_select_increments_play_count(self, lib_path):
        """Selecting a pattern increments its play count."""
        library = make_library(lib_path)
        pattern = PatternEntry(path="test.wav", duration=30.0, bpm=125, key="Dm")
        library.add(pattern)
        assert pattern.play_count == 0

        selector = BayesianPatternSelector(library)
        selector.select([pattern])

        assert pattern.play_count == 1

    def test_select_from_library_patterns(self, lib_path):
        """Select from all patterns in the library."""
        library = make_library(lib_path)
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm"
            )
            library.add(entry)

        selector = BayesianPatternSelector(library)
        candidates = library.patterns
        result = selector.select(candidates)
        assert result is not None
        assert result.path.startswith("/pattern")
