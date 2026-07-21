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
        """Initialize library with path."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert lib.count == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            entry = PatternEntry(
                path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)
            assert len(lib.patterns) == 1

    def test_get_all_patterns(self):
        """Retrieve all patterns from library."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
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
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
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
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
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

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            results = lib.get_by_tags(["bass"])
            assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
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
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            entries = []
            for i in range(5):
                entry = PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
                )
                lib.add(entry)
                entries.append(entry)
            sampled = lib.sample(entries)
            assert sampled is not None
            assert isinstance(sampled, PatternEntry)

    def test_sample_empty_candidates(self):
        """Sampling from empty candidates returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            sampled = lib.sample([])
            assert sampled is None

    def test_sample_filtered(self):
        """Sample from patterns filtered by tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            bass_entries = []
            for i in range(5):
                entry = PatternEntry(
                    path=f"/bass_{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass", "high"]
                )
                lib.add(entry)
                bass_entries.append(entry)
            for i in range(5):
                entry = PatternEntry(
                    path=f"/drums_{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["drums"]
                )
                lib.add(entry)

            bass_candidates = lib.get_by_tags(["bass"])
            sampled = lib.sample(bass_candidates)
            assert sampled is not None
            assert "bass" in sampled.tags

    def test_sample_empty_library(self):
        """Sampling from empty library returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = PatternLibrary(path=Path(tmpdir) / "patterns.json")
            sampled = lib.sample([])
            assert sampled is None


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
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

            lib.save()

            new_lib = PatternLibrary(path=db_path)
            new_lib.load()

            patterns = new_lib.patterns
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"

    def test_auto_load_from_existing(self):
        """Library auto-loads from existing path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "patterns.json"
            lib = PatternLibrary(path=db_path)
            entry = PatternEntry(
                path="/saved.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)
            lib.save()

            loaded = PatternLibrary(path=db_path, auto_load=True)
            assert loaded.count == 1
            assert loaded.patterns[0].path == "/saved.wav"

    def test_from_dict_round_trip(self):
        """PatternEntry serialization round-trip."""
        entry = PatternEntry(
            path="/test.wav", duration=60.0, bpm=130, key="Am",
            tags=["pad"], energy=0.7, density=0.4, phase="peak"
        )
        d = entry.to_dict()
        restored = PatternEntry.from_dict(d)
        for key in d:
            assert getattr(restored, key) == d[key]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
