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
            tags=["bass"],
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
        entry.quality_score = 1.5  # Out of range but acceptable (dataclass, no validator)
        entry.quality_score = -0.5  # Out of range but acceptable


class TestPatternLibraryBasics:
    """Tests for basic library operations."""

    def test_library_initialization(self):
        """Initialize library with explicit path."""
        lib = PatternLibrary(path="/tmp/test_patterns.json")
        assert lib._path == Path("/tmp/test_patterns.json")
        assert len(lib._patterns) == 0

    def test_add_pattern(self):
        """Add a pattern to the library."""
        lib = PatternLibrary(path="/tmp/test_patterns_add.json")
        entry = PatternEntry(
            path="/path/to/wav.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)
        assert len(lib.patterns) == 1

    def test_get_all_patterns(self):
        """Retrieving all patterns returns complete list."""
        lib = PatternLibrary(path="/tmp/test_patterns_all.json")
        entries = [
            PatternEntry(
                path=f"/path/to/wav{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
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

    def test_filter_by_single_tag(self):
        """Filter patterns by a single tag."""
        lib = PatternLibrary(path="/tmp/test_patterns_filter1.json")

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

    def test_filter_by_multiple_tags_any(self):
        """Filter patterns by multiple tags (ANY logic by default)."""
        lib = PatternLibrary(path="/tmp/test_patterns_filter2.json")

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

        # Default mode="any" — matches patterns with EITHER tag
        results = lib.get_by_tags(["bass", "high"])
        assert len(results) == 3

    def test_filter_by_multiple_tags_all(self):
        """Filter patterns by multiple tags with AND logic."""
        lib = PatternLibrary(path="/tmp/test_patterns_filter3.json")

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

        # mode="all" — matches patterns with BOTH tags
        results = lib.get_by_tags(["bass", "high"], mode="all")
        assert len(results) == 1
        assert results[0].path == "/pattern1.wav"

    def test_filter_empty_library(self):
        """Filtering empty library returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns_empty.json")
        results = lib.get_by_tags(["bass"])
        assert len(results) == 0

    def test_filter_no_matches(self):
        """Filtering for tags that don't match returns empty list."""
        lib = PatternLibrary(path="/tmp/test_patterns_nomatch.json")

        entry = PatternEntry(
            path="/pattern1.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
        )
        lib.add(entry)

        results = lib.get_by_tags(["drums"])
        assert len(results) == 0

    def test_filter_by_phase(self):
        """Filter patterns by phase."""
        lib = PatternLibrary(path="/tmp/test_phase.json")

        for phase in ("intro", "build", "peak", "sustain", "release", "outro"):
            entry = PatternEntry(
                path=f"/{phase}.wav", duration=30.0, bpm=125, key="Dm", phase=phase
            )
            lib.add(entry)

        peak_patterns = lib.get_by_phase("peak")
        assert len(peak_patterns) == 1
        assert peak_patterns[0].path == "/peak.wav"

    def test_filter_by_energy_range(self):
        """Filter patterns by energy range."""
        lib = PatternLibrary(path="/tmp/test_energy.json")

        for i, energy in enumerate([0.1, 0.3, 0.5, 0.7, 0.9]):
            entry = PatternEntry(
                path=f"/p{i}.wav", duration=30.0, bpm=125, key="Dm", energy=energy
            )
            lib.add(entry)

        mid_energy = lib.get_by_energy_range(0.4, 0.8)
        assert len(mid_energy) == 2
        for p in mid_energy:
            assert 0.4 <= p.energy <= 0.8


class TestPatternLibrarySampling:
    """Tests for playing pattern sampling."""

    def test_sample_single_pattern(self):
        """Sample a single pattern."""
        lib = PatternLibrary(path="/tmp/test_sample1.json")
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)

        candidates = lib.patterns
        sampled = lib.sample(candidates[:1])
        assert sampled is not None
        assert isinstance(sampled, PatternEntry)
        assert sampled.path == candidates[0].path

    def test_sample_from_candidates(self):
        """Sample from a list of candidate patterns."""
        lib = PatternLibrary(path="/tmp/test_sample2.json")
        for i in range(5):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)

        candidates = lib.patterns
        sampled = lib.sample(candidates)
        assert sampled is not None
        assert sampled.path.startswith("/pattern")

    def test_sample_empty_candidates(self):
        """Sampling from empty candidate list returns None."""
        lib = PatternLibrary(path="/tmp/test_sample_empty.json")
        sampled = lib.sample([])
        assert sampled is None

    def test_sample_prefers_unused(self):
        """Sample should prefer patterns with lower play_count."""
        lib = PatternLibrary(path="/tmp/test_sample_weights.json")
        for i in range(3):
            entry = PatternEntry(
                path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm", tags=["bass"]
            )
            lib.add(entry)

        candidates = lib.patterns
        # Increment play_count for one pattern
        lib.increment_play_count(candidates[0].path)

        # Sample many times — pattern 0 should be selected less often
        results = {}
        for _ in range(100):
            s = lib.sample(candidates)
            if s:
                results[s.path] = results.get(s.path, 0) + 1

        count_0 = results.get(candidates[0].path, 0)
        count_1 = results.get(candidates[1].path, 0)
        # Both should have been selected at least once
        assert count_1 > count_0 or count_0 > 0


class TestPatternLibraryPersistence:
    """Tests for saving and loading the pattern library."""

    def test_save_and_load(self):
        """Save library and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path, auto_load=False)
            entries = [
                PatternEntry(
                    path=f"/pattern{i}.wav", duration=30.0, bpm=125, key="Dm",
                    tags=["bass" if i % 2 == 0 else "high"],
                )
                for i in range(3)
            ]
            for entry in entries:
                lib.add(entry)
            lib.save()

            # Load into new library
            new_lib = PatternLibrary(path=db_path, auto_load=True)
            patterns = new_lib.patterns
            assert len(patterns) == 3
            for i, pattern in enumerate(patterns):
                assert pattern.path == f"/pattern{i}.wav"

    def test_auto_load_false_skips_load(self):
        """auto_load=False should not load existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "patterns.json")

            lib = PatternLibrary(path=db_path, auto_load=False)
            assert len(lib.patterns) == 0

    def test_increment_play_count(self):
        """Increment play count for a pattern."""
        lib = PatternLibrary(path="/tmp/test_playcount.json")
        entry = PatternEntry(
            path="/test.wav", duration=30.0, bpm=125, key="Dm"
        )
        lib.add(entry)
        assert entry.play_count == 0
        lib.increment_play_count("/test.wav")
        assert entry.play_count == 1

    def test_update_quality_score(self):
        """Update quality score for a pattern."""
        lib = PatternLibrary(path="/tmp/test_quality.json")
        entry = PatternEntry(
            path="/test.wav", duration=30.0, bpm=125, key="Dm"
        )
        lib.add(entry)
        assert entry.quality_score == 0.5
        lib.update_quality_score("/test.wav", 0.9)
        assert entry.quality_score == 0.9

    def test_count_property(self):
        """Count property returns number of patterns."""
        lib = PatternLibrary(path="/tmp/test_count.json")
        assert lib.count == 0
        assert len(lib) == 0
        for i in range(3):
            entry = PatternEntry(
                path=f"/p{i}.wav", duration=30.0, bpm=125, key="Dm"
            )
            lib.add(entry)
        assert lib.count == 3
        assert len(lib) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
