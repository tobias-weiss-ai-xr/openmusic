"""Tests for Bayesian pattern selector using Thompson sampling."""

import pytest
from openmusic.patterns.bayesian import BayesianPatternSelector
from openmusic.patterns.pattern_library import PatternLibrary, PatternEntry


class TestBayesianPatternSelector:
    """Tests for Bayesian pattern selector."""

    def test_empty_candidates_returns_none(self):
        """Returns None when no candidates are provided."""
        library = PatternLibrary()
        selector = BayesianPatternSelector(library)
        result = selector.select([])
        assert result is None

    def test_selects_from_single_candidate(self):
        """Selects the only available candidate."""
        library = PatternLibrary()
        pattern = PatternEntry(path="test.py", name="test", description="Test pattern")
        if library._patterns is None:
            from openmusic.patterns.pattern_library import Patterns
            library._patterns = Patterns(patterns=[pattern])
        else:
            library._patterns.patterns = [pattern]
        selector = BayesianPatternSelector(library)
        result = selector.select([pattern])
        assert result == pattern

    def test_preferences_higher_quality_candidates(self):
        """Thompson sampling favors higher quality patterns with enough samples."""
        library = PatternLibrary()
        high_quality = PatternEntry(path="high.py", name="high", description="High quality")
        high_quality.quality_score = 0.9
        high_quality.play_count = 10
        low_quality = PatternEntry(path="low.py", name="low", description="Low quality")
        low_quality.quality_score = 0.3
        low_quality.play_count = 10

        if library._patterns is None:
            from openmusic.patterns.pattern_library import Patterns
            library._patterns = Patterns(patterns=[high_quality, low_quality])
        else:
            library._patterns.patterns = [high_quality, low_quality]

        selector = BayesianPatternSelector(library)
        # With enough samples, should typically select high quality
        high_wins = 0
        for _ in range(20):
            result = selector.select([high_quality, low_quality])
            if result == high_quality:
                high_wins += 1
        assert high_wins >= 15  # Should be strongly biased toward high quality

    def test_quality_feedback_updates_scores(self):
        """Setting quality feedback updates the pattern's quality score."""
        library = PatternLibrary()
        pattern = PatternEntry(path="test.py", name="test", description="Test pattern")
        if library._patterns is None:
            from openmusic.patterns.pattern_library import Patterns
            library._patterns = Patterns(patterns=[pattern])
        else:
            library._patterns.patterns = [pattern]

        selector = BayesianPatternSelector(library)
        selector.set_quality_feedback("test.py", 0.8)

        # The quality score should have been updated
        assert pattern.quality_score == 0.8
