"""Tests for ACE-Step output caching."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from openmusic.acestep.cache import CacheManager


class TestCacheManager:
    """Tests for CacheManager file-based caching."""

    def test_default_cache_dir(self):
        cache = CacheManager()
        assert cache.cache_dir == Path.home() / ".cache" / "openmusic" / "acestep"

    def test_custom_cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))
            assert cache.cache_dir == Path(tmpdir)

    def test_get_cached_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))
            result = cache.get_cached("nonexistent_hash")
            assert result is None

    def test_set_and_get_cached(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))

            # Create a dummy file
            dummy_file = Path(tmpdir) / "dummy.wav"
            dummy_file.write_text("audio data")

            cache.set_cached("test_hash", dummy_file)
            result = cache.get_cached("test_hash")
            assert result is not None
            assert result == dummy_file

    def test_set_cached_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))

            dummy_file = Path(tmpdir) / "dummy.wav"
            dummy_file.write_text("audio data")

            cache.set_cached("abc123", dummy_file)

            # Cache entry dir should exist
            entry_dir = cache.cache_dir / "abc123"
            assert entry_dir.exists()

    def test_get_cached_returns_none_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=Path(tmpdir))

            # Create cache entry pointing to non-existent file
            entry_dir = cache.cache_dir / "bad_hash"
            entry_dir.mkdir(parents=True)
            (entry_dir / "path.txt").write_text("/nonexistent/file.wav")

            result = cache.get_cached("bad_hash")
            assert result is None

    def test_compute_hash_deterministic(self):
        cache = CacheManager()
        hash1 = cache.compute_hash("prompt", {"bpm": 125, "key": "Am"})
        hash2 = cache.compute_hash("prompt", {"bpm": 125, "key": "Am"})
        assert hash1 == hash2

    def test_compute_hash_different_inputs(self):
        cache = CacheManager()
        hash1 = cache.compute_hash("prompt_a", {"bpm": 125})
        hash2 = cache.compute_hash("prompt_b", {"bpm": 125})
        assert hash1 != hash2
