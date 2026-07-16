"""Tests for PatternLibrary functionality."""

import json
import os
from pathlib import Path

import pytest

from openmusic.patterns.pattern_library import (
    PatternEntry,
    PatternLibrary,
)


class TestPatternEntryDataclass:
    """Tests for the PatternEntry dataclass."""

    def test_pattern_entry_creation(self):
        """Create a PatternEntry with required fields."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass", "high"],
        )
        assert entry.path == "/path/to/wav.wav"
        assert entry.duration == 30.0
        assert entry.bpm == 125
        assert entry.key == "Dm"
        assert entry.tags == ["bass", "high"]

    def test_pattern_entry_defaults(self):
        """Default values for quality_score, play_count, energy, density, phase."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"]
        )
        assert entry.play_count == 0
        assert entry.quality_score == 0.5
        assert entry.energy == 0.5
        assert entry.density == 0.5
        assert entry.phase == "build"
        assert entry.play_count == 0

    def test_quality_score_bounds(self):
        """quality_score accepts values in [0.0, 1.0] range."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
        )
        entry.quality_score = 1.5  # Out of range but acceptable
        entry.quality_score = -0.5  # Out of range but acceptable


class TestPatternLibraryBasics:
    """Tests for basic library operations."""

    def test_library_initialization(self, tmp_path):
        """Initialize library with default paths."""
        lib = PatternLibrary(path=tmp_path / "patterns.json")
        assert lib._path == tmp_path / "patterns.json"
        assert len(lib._patterns) == 0

    def test_add_pattern(self, tmp_path):
        """Add a pattern to the library."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)
        assert lib.count == 1

    def test_get_pattern_by_path(self, tmp_path):
        """Retrieve a pattern by its path."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)

        assert lib.count == 1
        assert lib.patterns[0].path == entry.path
        assert lib.patterns[0].duration == entry.duration

    def test_get_pattern_nonexistent(self, tmp_path):
        """Empty library returns no patterns."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        assert len(lib.patterns) == 0

    def test_get_all_patterns(self, tmp_path):
        """Retrieving all patterns returns complete list."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        entries = [
            PatternEntry(
                path=f"/path/to/wav{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass"],
            )
            for i in range(5)
        ]
        for entry in entries:
            lib.add(entry)

        patterns = lib.patterns
        assert len(patterns) == 5
        for p in patterns:
            assert p.path.startswith("/path/to/wav")


class TestPatternLibraryFiltering:
    """Tests for tag-based pattern filtering."""

    def test_filter_by_single_tag(self, tmp_path):
        """Filter patterns by a single tag."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)

        for i in range(3):
            entry = PatternEntry(
                path=f"/bass_{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass", "high"],
            )
            lib.add(entry)

        for i in range(2):
            entry = PatternEntry(
                path=f"/drums_{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["drums"],
            )
            lib.add(entry)

        bass_patterns = lib.get_by_tags(["bass"])
        assert len(bass_patterns) == 3

        for pattern in bass_patterns:
            assert "bass" in pattern.tags

    def test_filter_by_multiple_tags(self, tmp_path):
        """Filter patterns by multiple tags (AND logic)."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)

        entry1 = PatternEntry(
            path="/pattern1.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass", "high"],
        )
        lib.add(entry1)

        entry2 = PatternEntry(
            path="/pattern2.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"],
        )
        lib.add(entry2)

        entry3 = PatternEntry(
            path="/pattern3.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["high"],
        )
        lib.add(entry3)

        results = lib.get_by_tags(["bass", "high"], mode="all")
        assert len(results) == 1
        assert results[0].path == entry1.path

    def test_filter_empty_library(self, tmp_path):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        results = lib.get_by_tags(["bass"])
        assert len(results) == 0

    def test_filter_no_matches(self, tmp_path):
        """Filtering for tags that don't match returns empty list."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)

        entry = PatternEntry(
            path="/pattern1.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"],
        )
        lib.add(entry)

        results = lib.get_by_tags(["drums"])
        assert len(results) == 0


class TestPatternLibrarySampling:
    """Tests for random pattern sampling."""

    def test_sample_single_pattern(self, tmp_path):
        """Sample a single pattern from the library."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass"],
            )
            lib.add(entry)

        sampled = lib.sample(lib.patterns)
        assert sampled is not None
        assert isinstance(sampled, PatternEntry)

    def test_sample_respects_candidates(self, tmp_path):
        """Sample from a filtered subset of patterns."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass"],
            )
            lib.add(entry)

        candidates = lib.patterns[:3]
        sampled = lib.sample(candidates)
        assert sampled is not None
        assert sampled in candidates

    def test_sample_empty_candidates(self, tmp_path):
        """Sampling with empty candidates returns None."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        sampled = lib.sample([])
        assert sampled is None

    def test_sample_favors_unused_patterns(self, tmp_path):
        """Sample should favor patterns with lower play_count."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)

        entry = PatternEntry(
            path="/unused.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"],
        )
        lib.add(entry)
        used_entry = PatternEntry(
            path="/used.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"],
        )
        used_entry.play_count = 10
        lib.add(used_entry)

        results = set()
        for _ in range(50):
            sampled = lib.sample(lib.patterns)
            if sampled:
                results.add(sampled.path)

        # The unused pattern should be selected at least once
        assert "/unused.wav" in results

    def test_sample_empty_library(self, tmp_path):
        """Sampling from empty library returns None."""
        lib = PatternLibrary(path=tmp_path / "patterns.json", auto_load=False)
        sampled = lib.sample(lib.patterns)
        assert sampled is None


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self, tmp_path):
        """Save library and load it back."""
        db_path = tmp_path / "patterns.json"

        lib = PatternLibrary(path=db_path, auto_load=False)
        entries = [
            PatternEntry(
                path=f"/pattern{i}.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass" if i % 2 == 0 else "high"],
            )
            for i in range(3)
        ]
        for entry in entries:
            lib.add(entry)

        lib.save()

        new_lib = PatternLibrary(path=db_path, auto_load=True)
        patterns = new_lib.patterns
        assert len(patterns) == 3
        for i, pattern in enumerate(patterns):
            assert pattern.path == f"/pattern{i}.wav"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
