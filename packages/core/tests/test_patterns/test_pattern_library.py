"""Tests for PatternLibrary — matching current source API."""

import json
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
        """Default values for optional fields."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
        )
        assert entry.play_count == 0
        assert entry.quality_score == 0.5
        assert entry.energy == 0.5
        assert entry.density == 0.5
        assert entry.phase == "build"

    def test_to_dict_and_from_dict(self):
        """Round-trip serialization via to_dict / from_dict."""
        entry = PatternEntry(
            path="/path/to/wav.wav",
            duration=30.0,
            bpm=125,
            key="Dm",
            tags=["bass"],
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
        assert restored.density == entry.density
        assert restored.phase == entry.phase


class TestPatternLibraryBasics:
    """Tests for basic library operations."""

    def test_library_initialization(self):
        """Initialize library with a path."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert lib.count == 0

    def test_add(self):
        """Add a pattern to the library."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)
        assert lib.count == 1
        assert lib.patterns[0].path == "/path/to/wav.wav"

    def test_add_many(self):
        """Add multiple patterns at once."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entries = [
            PatternEntry(path=f"/path/{i}.wav", duration=30.0, bpm=125, key="Dm")
            for i in range(5)
        ]
        lib.add_many(entries)
        assert lib.count == 5

    def test_patterns_property_returns_copy(self):
        """patterns property returns a copy of the internal list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(path="/test.wav", duration=30.0, bpm=125, key="Dm")
        lib.add(entry)
        retrieved = lib.patterns
        retrieved.clear()
        assert lib.count == 1


class TestPatternLibraryFiltering:
    """Tests for filter methods."""

    def test_get_by_tags_any(self):
        """Filter patterns by tags with mode='any' (default)."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        for i in range(3):
            lib.add(PatternEntry(
                path=f"/bass_{i}.wav", duration=30.0, bpm=125, key="Dm",
                tags=["bass", "high"],
            ))
        for i in range(2):
            lib.add(PatternEntry(
                path=f"/drums_{i}.wav", duration=30.0, bpm=125, key="Dm",
                tags=["drums"],
            ))

        results = lib.get_by_tags(["bass"])
        assert len(results) == 3

    def test_get_by_tags_all(self):
        """Filter patterns by tags with mode='all'."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        e1 = PatternEntry(path="/p1.wav", duration=30.0, bpm=125, key="Dm",
                          tags=["bass", "high"])
        e2 = PatternEntry(path="/p2.wav", duration=30.0, bpm=125, key="Dm",
                          tags=["bass"])
        e3 = PatternEntry(path="/p3.wav", duration=30.0, bpm=125, key="Dm",
                          tags=["high"])
        lib.add_many([e1, e2, e3])

        results = lib.get_by_tags(["bass", "high"], mode="all")
        assert len(results) == 1

    def test_get_by_tags_empty_library(self):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib.get_by_tags(["bass"]) == []

    def test_get_by_tags_no_match(self):
        """Filtering for unmatched tags returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        lib.add(PatternEntry(
            path="/p1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"],
        ))
        assert lib.get_by_tags(["drums"]) == []

    def test_get_by_phase(self):
        """Filter by phase."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        lib.add(PatternEntry(path="/p1.wav", duration=30.0, bpm=125, key="Dm",
                             phase="intro"))
        lib.add(PatternEntry(path="/p2.wav", duration=30.0, bpm=125, key="Dm",
                             phase="build"))
        lib.add(PatternEntry(path="/p3.wav", duration=30.0, bpm=125, key="Dm",
                             phase="intro"))
        results = lib.get_by_phase("intro")
        assert len(results) == 2

    def test_get_by_energy_range(self):
        """Filter by energy range."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        lib.add(PatternEntry(path="/low.wav", duration=30.0, bpm=125, key="Dm",
                             energy=0.2))
        lib.add(PatternEntry(path="/mid.wav", duration=30.0, bpm=125, key="Dm",
                             energy=0.5))
        lib.add(PatternEntry(path="/high.wav", duration=30.0, bpm=125, key="Dm",
                             energy=0.9))
        results = lib.get_by_energy_range(0.3, 0.7)
        assert len(results) == 1
        assert results[0].path == "/mid.wav"

    def test_get_unused(self):
        """Get patterns with play_count == 0."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        lib.add(PatternEntry(path="/used.wav", duration=30.0, bpm=125, key="Dm",
                             play_count=5))
        lib.add(PatternEntry(path="/unused.wav", duration=30.0, bpm=125, key="Dm"))
        unused = lib.get_unused()
        assert len(unused) == 1
        assert unused[0].path == "/unused.wav"


class TestPatternLibrarySampling:
    """Tests for pattern sampling."""

    def test_sample_returns_single_pattern(self):
        """sample returns one PatternEntry from candidates."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entries = [
            PatternEntry(path=f"/p{i}.wav", duration=30.0, bpm=125, key="Dm")
            for i in range(5)
        ]
        lib.add_many(entries)
        sampled = lib.sample(entries)
        assert sampled is not None
        assert sampled in entries

    def test_sample_empty_candidates(self):
        """Sampling empty list returns None."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib.sample([]) is None

    def test_sample_prefers_unused(self):
        """Sample weighted toward patterns with lower play_count."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        unused = PatternEntry(path="/unused.wav", duration=30.0, bpm=125, key="Dm",
                              play_count=0)
        used = PatternEntry(path="/used.wav", duration=30.0, bpm=125, key="Dm",
                            play_count=10)
        lib.add_many([unused, used])
        results = [lib.sample([unused, used]) for _ in range(100)]
        unused_count = sum(1 for r in results if r == unused)
        assert unused_count > 50


class TestPatternLibraryPersistence:
    """Tests for saving and loading."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            lib = PatternLibrary(path=db_path)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm",
                    tags=["bass" if i % 2 == 0 else "high"],
                )
                for i in range(3)
            ]
            lib.add_many(entries)
            lib.save()

            new_lib = PatternLibrary(path=db_path)
            new_lib.load()
            assert new_lib.count == 3
            for i, p in enumerate(new_lib.patterns):
                assert p.path == f"/pattern{i}.wav"

    def test_load_nonexistent(self):
        """Loading from nonexistent file produces empty library."""
        lib = PatternLibrary(path="/tmp/nonexistent_patterns.json")
        lib.load()
        assert lib.count == 0

    def test_increment_play_count(self):
        """increment_play_count updates the matching pattern."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(path="/test.wav", duration=30.0, bpm=125, key="Dm")
        lib.add(entry)
        lib.increment_play_count("/test.wav")
        assert entry.play_count == 1
        lib.increment_play_count("/test.wav")
        assert entry.play_count == 2

    def test_update_quality_score(self):
        """update_quality_score updates the matching pattern."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        entry = PatternEntry(path="/test.wav", duration=30.0, bpm=125, key="Dm")
        lib.add(entry)
        lib.update_quality_score("/test.wav", 0.9)
        assert entry.quality_score == 0.9

    def test_save_reload_via_auto_load(self):
        """auto_load=True loads existing file on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            lib = PatternLibrary(path=db_path)
            lib.add(PatternEntry(path="/a.wav", duration=10.0, bpm=120, key="C"))
            lib.save()

            loaded = PatternLibrary(path=db_path, auto_load=True)
            assert loaded.count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
