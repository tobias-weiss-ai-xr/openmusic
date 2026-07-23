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
            tags=["bass"],
        )
        assert entry.play_count == 0
        assert entry.quality_score == 0.5
        assert entry.energy == 0.5
        assert entry.density == 0.5
        assert entry.phase == "build"

    def test_to_dict_roundtrip(self):
        """to_dict and from_dict produce the same entry."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass", "high"],
            energy=0.8,
            density=0.3,
            phase="peak",
        )
        d = entry.to_dict()
        restored = PatternEntry.from_dict(d)
        assert restored.path == entry.path
        assert restored.duration == entry.duration
        assert restored.bpm == entry.bpm
        assert restored.key == entry.key
        assert restored.tags == entry.tags
        assert restored.energy == entry.energy


class TestPatternLibraryBasics:
    """Tests for basic library operations."""

    def test_library_initialization(self):
        """Initialize library with a path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            assert lib._path == Path(db_path)
            assert len(lib.patterns) == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/path/to/wav.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
                tags=["bass"],
            )
            lib.add(entry)
            assert len(lib.patterns) == 1

    def test_add_many_patterns(self):
        """Add multiple patterns to the library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
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
            lib.add_many(entries)
            assert lib.count == 5

    def test_patterns_property_returns_copy(self):
        """The patterns property returns a copy, not the internal list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/path/to/wav.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
            )
            lib.add(entry)
            retrieved = lib.patterns
            assert len(retrieved) == 1
            assert retrieved[0].path == entry.path


class TestPatternLibraryFiltering:
    """Tests for tag-based and attribute pattern filtering."""

    def test_filter_by_single_tag_any(self):
        """Filter patterns by a single tag with any mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)

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

            bass_patterns = lib.get_by_tags(["bass"], mode="any")
            assert len(bass_patterns) == 3

            for pattern in bass_patterns:
                assert "bass" in pattern.tags

    def test_filter_by_multiple_tags_all(self):
        """Filter patterns by multiple tags with all mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)

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

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            results = lib.get_by_tags(["bass"])
            assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)

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

    def test_filter_by_phase(self):
        """Filter patterns by phase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)

            for i in range(3):
                lib.add(PatternEntry(
                    path=f"/build_{i}.wav",
                    duration=30.0,
                    bpm=125,
                    key="Dm",
                    phase="build",
                ))
            for i in range(2):
                lib.add(PatternEntry(
                    path=f"/peak_{i}.wav",
                    duration=30.0,
                    bpm=125,
                    key="Dm",
                    phase="peak",
                ))

            build_patterns = lib.get_by_phase("build")
            assert len(build_patterns) == 3

    def test_filter_by_energy_range(self):
        """Filter patterns by energy range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)

            lib.add(PatternEntry(path="/low.wav", duration=30.0, bpm=125, key="Dm", energy=0.2))
            lib.add(PatternEntry(path="/mid.wav", duration=30.0, bpm=125, key="Dm", energy=0.5))
            lib.add(PatternEntry(path="/high.wav", duration=30.0, bpm=125, key="Dm", energy=0.9))

            results = lib.get_by_energy_range(0.3, 0.8)
            assert len(results) == 1
            assert results[0].path == "/mid.wav"


class TestPatternLibrarySampling:
    """Tests for pattern sampling."""

    def test_sample_from_empty_list(self):
        """Sampling from empty candidate list returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            result = lib.sample([])
            assert result is None

    def test_sample_single_pattern(self):
        """Sample returns the only candidate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/pattern.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
            )
            lib.add(entry)
            result = lib.sample([entry])
            assert result is not None
            assert result.path == entry.path

    def test_sample_prefers_unused(self):
        """Sampling weights favor patterns with lower play_count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            used = PatternEntry(
                path="/used.wav", duration=30.0, bpm=125, key="Dm",
            )
            used.play_count = 10
            unused = PatternEntry(
                path="/unused.wav", duration=30.0, bpm=125, key="Dm",
            )
            lib.add(used)
            lib.add(unused)

            results = [lib.sample([used, unused]).path for _ in range(50)]
            unused_count = results.count("/unused.wav")
            assert unused_count > 25


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
                    duration=30.0,
                    bpm=125,
                    key="Dm",
                    tags=["bass" if i % 2 == 0 else "high"],
                )
                for i in range(3)
            ]
            lib.add_many(entries)

            lib.save()

            new_lib = PatternLibrary(path=db_path)
            new_lib.load()

            patterns = new_lib.patterns
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"

    def test_auto_load(self):
        """Library auto-loads existing file when auto_load=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path)
            lib.add(PatternEntry(
                path="/test.wav", duration=30.0, bpm=125, key="Dm",
            ))
            lib.save()

            lib2 = PatternLibrary(path=db_path, auto_load=True)
            assert lib2.count == 1

    def test_load_empty_file(self):
        """Loading a non-existent file returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "nonexistent.json")
            lib = PatternLibrary(path=db_path)
            lib.load()
            assert lib.count == 0


class TestPatternLibraryPlayCount:
    """Tests for play count tracking."""

    def test_increment_play_count(self):
        """Increment play count for a pattern by path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/test.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
            )
            lib.add(entry)
            lib.increment_play_count("/test.wav")
            assert entry.play_count == 1

    def test_get_unused_patterns(self):
        """get_unused returns patterns with play_count == 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            unused = PatternEntry(
                path="/unused.wav", duration=30.0, bpm=125, key="Dm",
            )
            used = PatternEntry(
                path="/used.wav", duration=30.0, bpm=125, key="Dm",
            )
            used.play_count = 5
            lib.add_many([unused, used])

            result = lib.get_unused()
            assert len(result) == 1
            assert result[0].path == "/unused.wav"


class TestPatternLibraryQualityScore:
    """Tests for quality score tracking."""

    def test_update_quality_score(self):
        """Update quality score for a pattern by path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/test.wav",
                duration=30.0,
                bpm=125,
                key="Dm",
            )
            lib.add(entry)
            lib.update_quality_score("/test.wav", 0.9)
            assert entry.quality_score == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
