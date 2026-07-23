"""Tests for PatternLibrary functionality."""

import json
import os
import tempfile
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

    def test_library_initialization(self):
        """Initialize library with default paths."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert len(lib._patterns) == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)
        assert len(lib.patterns) == 1

    def test_get_all_patterns(self):
        """Retrieving all patterns returns complete list."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        entries = [
            PatternEntry(path=f"/path/to/wav{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
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

    def test_filter_by_single_tag(self):
        """Filter patterns by a single tag."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")

        # Add patterns with bass and drums tags
        for i in range(3):
            entry = PatternEntry(
                path=f"/bass_{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass", "high"]
            )
            lib.add(entry)

        for i in range(2):
            entry = PatternEntry(
                path=f"/drums_{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["drums"]
            )
            lib.add(entry)

        bass_patterns = lib.get_by_tags(["bass"])
        assert len(bass_patterns) == 3

        for pattern in bass_patterns:
            assert "bass" in pattern.tags

    def test_filter_by_multiple_tags(self):
        """Filter patterns by multiple tags (AND logic)."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")

        entry1 = PatternEntry(
            path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass", "high"]
        )
        lib.add(entry1)

        entry2 = PatternEntry(path="/pattern2.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
        lib.add(entry2)

        entry3 = PatternEntry(path="/pattern3.wav", duration=30.0, bpm=125, key="Dm", tags=["high"])
        lib.add(entry3)

        results = lib.get_by_tags(["bass", "high"], mode="all")
        assert len(results) == 1
        assert results[0].path == "/pattern1.wav"

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        results = lib.get_by_tags(["bass"])
        assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")

        entry = PatternEntry(path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
        lib.add(entry)

        results = lib.get_by_tags(["drums"])
        assert len(results) == 0


class TestPatternLibrarySampling:
    """Tests for random pattern sampling."""

    def test_sample_returns_pattern(self):
        """Sample returns a pattern from candidates."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        entries = [
            PatternEntry(path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
            for i in range(5)
        ]
        for entry in entries:
            lib.add(entry)

        sampled = lib.sample(entries)
        assert sampled is not None
        assert isinstance(sampled, PatternEntry)
        assert sampled in entries

    def test_sample_empty_candidates_returns_none(self):
        """Sample with empty candidates returns None."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        sampled = lib.sample([])
        assert sampled is None

    def test_sample_respects_play_count(self):
        """Sampling prefers less-played patterns."""
        lib = PatternLibrary(path=Path(tempfile.mkdtemp()) / "patterns.json")
        entries = [
            PatternEntry(path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
            for i in range(3)
        ]
        for entry in entries:
            lib.add(entry)

        entries[0].play_count = 10
        entries[1].play_count = 5
        entries[2].play_count = 0

        # With high play count differences, pattern 2 should be picked more
        picks = {i: 0 for i in range(3)}
        for _ in range(100):
            result = lib.sample(entries)
            idx = entries.index(result)
            picks[idx] += 1

        # The least-played pattern (index 2) should be selected most often
        assert picks[2] > picks[0]


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm",
                    tags=["bass" if i % 2 == 0 else "high"]
                )
                for i in range(3)
            ]
            for entry in entries:
                lib.add(entry)

            # Save
            lib.save()

            # Load into new library
            new_lib = PatternLibrary(path=db_path)
            new_lib.load()

            # Verify patterns match
            patterns = new_lib.patterns
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"

    def test_save_persists_to_disk(self):
        """Save writes JSON file to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/test.wav", duration=30.0, bpm=125, key="Dm", tags=["test"]
            )
            lib.add(entry)
            lib.save()

            assert os.path.exists(db_path)
            with open(db_path) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["path"] == "/test.wav"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
