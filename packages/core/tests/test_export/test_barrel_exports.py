"""Tests for export barrel exports."""

from openmusic.export import (
    AudioEncoder,
    AudioInfo,
    EncoderNotFoundError,
    EncodingError,
    EmbeddingError,
    TrackMetadata,
    embed_metadata,
)


class TestBarrelExports:
    """Verify all public classes and functions are exported."""

    def test_audio_encoder_exported(self):
        assert AudioEncoder is not None

    def test_audio_info_exported(self):
        assert AudioInfo is not None

    def test_encoder_not_found_error_exported(self):
        assert EncoderNotFoundError is not None

    def test_encoding_error_exported(self):
        assert EncodingError is not None

    def test_embedding_error_exported(self):
        assert EmbeddingError is not None

    def test_track_metadata_exported(self):
        assert TrackMetadata is not None

    def test_embed_metadata_exported(self):
        assert embed_metadata is not None
