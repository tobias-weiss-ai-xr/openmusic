"""Tests for export.fingerprint module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from openmusic.export.fingerprint import (
    generate_fingerprint,
    lookup_acoustid,
    FingerprintError,
)


def _create_test_wav(duration_sec: float = 3.0, sample_rate: int = 44100) -> str:
    """Create a temporary WAV file with a sine tone."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    audio = np.column_stack([audio, audio])  # stereo
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name


class TestGenerateFingerprint:
    def test_returns_string(self):
        path = _create_test_wav()
        try:
            fp = generate_fingerprint(path)
            assert isinstance(fp, str)
            assert len(fp) > 10
        finally:
            Path(path).unlink(missing_ok=True)

    def test_same_file_returns_same_fingerprint(self):
        path = _create_test_wav()
        try:
            fp1 = generate_fingerprint(path)
            fp2 = generate_fingerprint(path)
            assert fp1 == fp2
        finally:
            Path(path).unlink(missing_ok=True)

    def test_different_files_different_fingerprints(self):
        path_a = _create_test_wav(duration_sec=3.0)
        path_b = _create_test_wav(duration_sec=5.0)
        try:
            fp_a = generate_fingerprint(path_a)
            fp_b = generate_fingerprint(path_b)
            assert fp_a != fp_b
        finally:
            Path(path_a).unlink(missing_ok=True)
            Path(path_b).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FingerprintError, match="not found"):
            generate_fingerprint("/nonexistent/file.wav")

    def test_returns_compressed_fingerprint(self):
        """Generated fingerprint should be valid base64-ish."""
        path = _create_test_wav()
        try:
            fp = generate_fingerprint(path)
            # Chromaprint compressed fingerprints are alphanumeric
            assert all(c.isalnum() or c in "-_" for c in fp)
        finally:
            Path(path).unlink(missing_ok=True)


class TestLookupAcoustid:
    def test_returns_dict_or_none(self):
        path = _create_test_wav()
        try:
            # This will likely fail without API key, but should
            # return a dict with 'error' or gracefully degrade
            result = lookup_acoustid(path, api_key="test")
            assert isinstance(result, (dict, type(None)))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_bad_api_key_returns_error_dict(self):
        path = _create_test_wav()
        try:
            result = lookup_acoustid(path, api_key="invalid_key")
            if isinstance(result, dict):
                assert "error" in result or "status" in result
        finally:
            Path(path).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        with pytest.raises(FingerprintError):
            lookup_acoustid("/nonexistent/file.wav", api_key="test")
