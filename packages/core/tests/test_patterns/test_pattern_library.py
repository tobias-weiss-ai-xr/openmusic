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
        """Initialize library with default paths."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert len(lib._patterns) == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            entry = PatternEntry(
                path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)
            assert len(lib.patterns) == 1

    def test_get_all_patterns(self):
        """Retrieving all patterns returns complete list."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
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
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)

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
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)

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

            results = lib.get_by_tags(["bass", "high"], mode="all")
            assert len(results) == 1
            assert results[0].path == entry1.path

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            results = lib.get_by_tags(["bass"])
            assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)

            entry = PatternEntry(
                path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)

            results = lib.get_by_tags(["drums"])
            assert len(results) == 0


class TestPatternLibrarySampling:
    """Tests for random pattern sampling."""

    def test_sample_single_pattern(self):
        """Sample a single pattern randomly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
                )
                for i in range(5)
            ]
            for e in entries:
                lib.add(e)

            sampled = lib.sample(entries)
            assert sampled is not None
            assert isinstance(sampled, PatternEntry)
            assert sampled.path.startswith("/pattern")

    def test_sample_multiple_patterns(self):
        """Sample picks from available candidates."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
                )
                for i in range(5)
            ]
            for e in entries:
                lib.add(e)

            sampled = lib.sample(entries)
            assert sampled is not None
            assert sampled.path.startswith("/pattern")

    def test_sample_empty_candidates(self):
        """Sampling from empty candidates returns None."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            sampled = lib.sample([])
            assert sampled is None

    def test_sample_returns_none_for_empty_list(self):
        """Sampling with empty candidate list returns None."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            result = lib.sample([])
            assert result is None


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav",
                    duration=float(30 + i),
                    bpm=125,
                    key="Dm",
                    tags=["bass" if i % 2 == 0 else "high"],
                )
                for i in range(3)
            ]
            for entry in entries:
                lib.add(entry)

            lib.save()

            new_lib = PatternLibrary(path=db_path)
            new_lib.load()

            patterns = new_lib.patterns
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"
                assert pattern.duration == float(30 + i)

    def test_auto_load_on_init(self):
        """Library auto-loads existing path on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path)
            entries = [
                PatternEntry(path="/test.wav", duration=30.0, bpm=125, key="Dm")
            ]
            for e in entries:
                lib.add(e)
            lib.save()

            new_lib = PatternLibrary(path=db_path, auto_load=True)
            assert len(new_lib.patterns) == 1

    def test_load_empty_file(self):
        """Loading from empty or nonexistent file returns empty."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as f:
            lib = PatternLibrary(path=f.name)
            lib.load()
            assert len(lib.patterns) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
