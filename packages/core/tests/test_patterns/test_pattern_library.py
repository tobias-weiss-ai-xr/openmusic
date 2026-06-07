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


# Default paths that would be programmatically generated
DEFAULT_CACHE_DIR = Path.home() / ".openmusic" / "cache" / "patterns"
DEFAULT_PATTERN_DB_PATH = DEFAULT_CACHE_DIR / "patterns.json"


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
        lib = PatternLibrary()
        entry = PatternEntry(
            path="/path/to/wav.wav", prompt="test prompt", tags=["bass"]
        )
        lib.add_pattern(entry)
        assert len(lib.get_all_patterns()) == 1

    def test_add_pattern_generates_id(self):
        """Add pattern should auto-increment next_id."""
        lib = PatternLibrary()
        entry1 = PatternEntry(
            path="/path/to/wav1.wav", prompt="test1", tags=["bass"]
        )
        entry2 = PatternEntry(
            path="/path/to/wav2.wav", prompt="test2", tags=["bass"]
        )
        lib.add_pattern(entry1)
        lib.add_pattern(entry2)

        patterns = lib.get_all_patterns()
        pattern_ids = [p.id for p in patterns]

        assert pattern_ids[0] == 1
        assert pattern_ids[1] == 2

    def test_get_pattern_by_id(self):
        """Retrieve a pattern by its ID."""
        lib = PatternLibrary()
        entry = PatternEntry(
            path="/path/to/wav.wav", prompt="test prompt", tags=["bass"]
        )
        lib.add_pattern(entry)

        retrieved = lib.get_pattern(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id
        assert retrieved.path == entry.path

    def test_get_pattern_nonexistent(self):
        """Attempting to get nonexistent pattern returns None."""
        lib = PatternLibrary()
        assert lib.get_pattern(999) is None

    def test_get_all_patterns(self):
        """Retrieving all patterns returns complete list."""
        lib = PatternLibrary()
        entries = [
            PatternEntry(path=f"/path/to/wav{i}.wav", prompt=f"test{i}", tags=["bass"])
            for i in range(5)
        ]
        for entry in entries:
            lib.add_pattern(entry)

        patterns = lib.get_all_patterns()
        assert len(patterns) == 5
        for p in patterns:
            assert p.path.startswith("/path/to/wav")


class TestPatternLibraryFiltering:
    """Tests for tag-based pattern filtering."""

    def test_filter_by_single_tag(self):
        """Filter patterns by a single tag."""
        lib = PatternLibrary()

        # Add patterns with bass and drums tags
        for i in range(3):
            entry = PatternEntry(
                path=f"/bass_{i}.wav", prompt=f"bass{i}", tags=["bass", "high"]
            )
            lib.add_pattern(entry)

        for i in range(2):
            entry = PatternEntry(
                path=f"/drums_{i}.wav", prompt=f"drums{i}", tags=["drums"]
            )
            lib.add_pattern(entry)

        bass_patterns = lib.get_patterns_by_tags(["bass"])
        assert len(bass_patterns) == 3

        for pattern in bass_patterns:
            assert "bass" in pattern.tags

    def test_filter_by_multiple_tags(self):
        """Filter patterns by multiple tags (AND logic)."""
        lib = PatternLibrary()

        # Pattern with both bass and high
        entry1 = PatternEntry(
            path="/pattern1.wav", prompt="test1", tags=["bass", "high"]
        )
        lib.add_pattern(entry1)

        # Pattern with only bass
        entry2 = PatternEntry(path="/pattern2.wav", prompt="test2", tags=["bass"])
        lib.add_pattern(entry2)

        # Pattern with only high
        entry3 = PatternEntry(path="/pattern3.wav", prompt="test3", tags=["high"])
        lib.add_pattern(entry3)

        # Filter for patterns with BOTH bass and high
        results = lib.get_patterns_by_tags(["bass", "high"])
        assert len(results) == 1
        assert results[0].id == entry1.id

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary()
        results = lib.get_patterns_by_tags(["bass"])
        assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        lib = PatternLibrary()

        entry = PatternEntry(path="/pattern1.wav", prompt="test1", tags=["bass"])
        lib.add_pattern(entry)

        results = lib.get_patterns_by_tags(["drums"])
        assert len(results) == 0


class TestPatternLibrarySampling:
    """Tests for random pattern sampling."""

    def test_sample_single_pattern(self):
        """Sample a single pattern randomly."""
        lib = PatternLibrary()
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", prompt=f"test{i}", tags=["bass"]
            )
            lib.add_pattern(entry)

        sampled = lib.sample(1)
        assert len(sampled) == 1
        assert isinstance(sampled[0], PatternEntry)

    def test_sample_multiple_patterns(self):
        """Sample multiple patterns without replacement."""
        lib = PatternLibrary()
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", prompt=f"test{i}", tags=["bass"]
            )
            lib.add_pattern(entry)

        sampled = lib.sample(3)
        assert len(sampled) == 3

        # All sampled patterns should be unique
        sampled_ids = [p.id for p in sampled]
        assert len(sampled_ids) == len(set(sampled_ids))

    def test_sample_more_than_available(self):
        """Sampling more patterns than available should return all patterns."""
        lib = PatternLibrary()
        for i in range(3):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", prompt=f"test{i}", tags=["bass"]
            )
            lib.add_pattern(entry)

        sampled = lib.sample(10)
        assert len(sampled) == 3

    def test_sample_filtered(self):
        """Sample from patterns that match tags filter."""
        lib = PatternLibrary()

        # Add bass and drums patterns
        for i in range(5):
            entry = PatternEntry(
                path=f"/bass_{i}.wav", prompt=f"bass{i}", tags=["bass", "high"]
            )
            lib.add_pattern(entry)

        for i in range(5):
            entry = PatternEntry(
                path=f"/drums_{i}.wav", prompt=f"drums{i}", tags=["drums"]
            )
            lib.add_pattern(entry)

        # Sample 2 bass patterns
        sampled = lib.sample(2, tags=["bass"])
        assert len(sampled) == 2
        for pattern in sampled:
            assert "bass" in pattern.tags

    def test_sample_empty_library(self):
        """Sampling from empty library returns empty list."""
        lib = PatternLibrary()
        sampled = lib.sample(5)
        assert len(sampled) == 0


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(db_path=db_path)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", prompt=f"test{i}", tags=["bass" if i % 2 == 0 else "high"]
                )
                for i in range(3)
            ]
            for entry in entries:
                lib.add_pattern(entry)

            # Save
            lib.save()

            # Load into new library
            new_lib = PatternLibrary(db_path=db_path)
            new_lib.load()

            # Verify patterns match
            patterns = new_lib.get_all_patterns()
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"
                assert pattern.prompt == f"test{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
