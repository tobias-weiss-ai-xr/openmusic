"""Tests for arrangement barrel exports."""

import pytest

from openmusic.arrangement import (
    Timeline,
    Track,
    crossfade_numpy,
    generate_crossfade_curve,
    MixArranger,
)


class TestBarrelExports:
    def test_timeline_exported(self):
        assert Timeline is not None

    def test_track_exported(self):
        assert Track is not None

    def test_crossfade_numpy_exported(self):
        assert crossfade_numpy is not None

    def test_generate_crossfade_curve_exported(self):
        assert generate_crossfade_curve is not None

    def test_mix_arranger_exported(self):
        assert MixArranger is not None
