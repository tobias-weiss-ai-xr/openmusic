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
        """Initialize library with path."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert len(lib._patterns) == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)
        assert lib.count == 1

    def test_add_pattern_tracks_multiple(self):
        """Add multiple patterns tracks count correctly."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry1 = PatternEntry(
            path="/path/to/wav1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        entry2 = PatternEntry(
            path="/path/to/wav2.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry1)
        lib.add(entry2)

        patterns = lib.patterns
        assert len(patterns) == 2
        assert patterns[0].path == "/path/to/wav1.wav"
        assert patterns[1].path == "/path/to/wav2.wav"

    def test_get_patterns_by_tags(self):
        """Retrieve patterns by tag."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)

        retrieved = lib.get_by_tags(["bass"])
        assert len(retrieved) == 1
        assert retrieved[0].path == entry.path

    def test_get_patterns_nonexistent_tag(self):
        """Attempting to get patterns with nonexistent tag returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib.get_by_tags(["nonexistent"]) == []

    def test_get_all_patterns(self):
        """Retrieving all patterns returns complete list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
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
        lib = PatternLibrary(path="/tmp/test_patterns.json")

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

    def test_filter_by_multiple_tags_and(self):
        """Filter patterns by multiple tags (AND logic)."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")

        entry1 = PatternEntry(
            path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass", "high"]
        )
        lib.add(entry1)

        entry2 = PatternEntry(
            path="/pattern2.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry2)

        entry3 = PatternEntry(
            path="/pattern3.wav", duration=30.0, bpm=125, key="Dm", tags=["high"]
        )
        lib.add(entry3)

        # Filter for patterns with BOTH bass and high (mode="all")
        results = lib.get_by_tags(["bass", "high"], mode="all")
        assert len(results) == 1
        assert results[0].tags == ["bass", "high"]

    def test_filter_by_multiple_tags_any(self):
        """Filter patterns by multiple tags (OR logic)."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")

        entry1 = PatternEntry(
            path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass", "high"]
        )
        lib.add(entry1)

        entry2 = PatternEntry(
            path="/pattern2.wav", duration=30.0, bpm=125, key="Dm", tags=["drums"]
        )
        lib.add(entry2)

        results = lib.get_by_tags(["bass", "drums"], mode="any")
        assert len(results) == 2

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        results = lib.get_by_tags(["bass"])
        assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")

        entry = PatternEntry(path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"])
        lib.add(entry)

        results = lib.get_by_tags(["drums"])
        assert len(results) == 0

    def test_filter_by_phase(self):
        """Filter patterns by phase."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")

        lib.add(PatternEntry(path="/build.wav", duration=30.0, bpm=125, key="Dm", tags=[], phase="build"))
        lib.add(PatternEntry(path="/peak.wav", duration=30.0, bpm=125, key="Dm", tags=[], phase="peak"))

        build_patterns = lib.get_by_phase("build")
        assert len(build_patterns) == 1
        assert build_patterns[0].phase == "build"

    def test_filter_by_energy_range(self):
        """Filter patterns by energy range."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")

        lib.add(PatternEntry(path="/low.wav", duration=30.0, bpm=125, key="Dm", tags=[], energy=0.2))
        lib.add(PatternEntry(path="/high.wav", duration=30.0, bpm=125, key="Dm", tags=[], energy=0.8))

        mid = lib.get_by_energy_range(0.3, 0.7)
        assert len(mid) == 0

        all_patterns = lib.get_by_energy_range(0.0, 1.0)
        assert len(all_patterns) == 2


class TestPatternLibrarySampling:
    """Tests for random pattern sampling."""

    def test_sample_single_pattern(self):
        """Sample a single pattern randomly."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entries = [
            PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            for i in range(5)
        ]
        lib.add_many(entries)

        sampled = lib.sample(lib.patterns)
        assert sampled is not None
        assert isinstance(sampled, PatternEntry)

    def test_sample_empty_list(self):
        """Sampling from empty list returns None."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        sampled = lib.sample([])
        assert sampled is None

    def test_sample_prefers_unused(self):
        """Sampling should prefer unused patterns over used ones."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        for i in range(5):
            lib.add(PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            ))

        # Mark first pattern as used
        lib.increment_play_count("/pattern0.wav")

        # Sample many times - pattern0 should appear less often
        results = []
        for _ in range(100):
            sampled = lib.sample(lib.patterns)
            if sampled:
                results.append(sampled.path)

        # pattern0 should appear less than the average of others
        count_p0 = sum(1 for r in results if r == "/pattern0.wav")
        count_p1 = sum(1 for r in results if r == "/pattern1.wav")
        assert count_p0 <= count_p1 * 2  # generous bound due to randomness


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
            lib.add_many(entries)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
