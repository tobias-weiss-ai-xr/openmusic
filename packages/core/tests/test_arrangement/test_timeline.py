"""Tests for Timeline and Track classes."""

from pathlib import Path

import pytest

from openmusic.arrangement.timeline import Timeline, Track


class TestTimelineInit:
    def test_create_timeline_with_defaults(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        assert timeline.total_duration == 180.0
        assert timeline.bpm == 125

    def test_total_duration_property(self):
        timeline = Timeline(total_duration=360.0, bpm=125)
        assert timeline.total_duration == 360.0

    def test_empty_timeline_has_no_segments(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        assert timeline.get_segments_at(0.0) == []


class TestTimelineAddSegment:
    def test_add_single_segment(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=10.0)
        segments = timeline.get_segments_at(5.0)
        assert len(segments) == 1

    def test_add_multiple_segments(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=10.0)
        timeline.add_segment("/audio/seg2.wav", start_time=10.0, duration=10.0)
        assert len(timeline.get_segments_at(5.0)) == 1
        assert len(timeline.get_segments_at(15.0)) == 1

    def test_segment_stores_path(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=10.0)
        track = timeline.get_segments_at(5.0)[0]
        assert track.audio_path == Path("/audio/seg1.wav")

    def test_overlapping_segments_returned(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=10.0)
        timeline.add_segment("/audio/seg2.wav", start_time=5.0, duration=10.0)
        segments = timeline.get_segments_at(7.0)
        assert len(segments) == 2

    def test_no_segments_at_gap(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=5.0)
        timeline.add_segment("/audio/seg2.wav", start_time=10.0, duration=5.0)
        assert timeline.get_segments_at(7.0) == []

    def test_segment_at_exact_start(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=10.0, duration=5.0)
        assert len(timeline.get_segments_at(10.0)) == 1

    def test_segment_at_exact_end_is_excluded(self):
        timeline = Timeline(total_duration=180.0, bpm=125)
        timeline.add_segment("/audio/seg1.wav", start_time=0.0, duration=10.0)
        assert len(timeline.get_segments_at(10.0)) == 0


class TestTrack:
    def test_track_properties(self):
        track = Track(
            audio_path=Path("/audio/seg.wav"),
            start_time=5.0,
            duration=10.0,
        )
        assert track.audio_path == Path("/audio/seg.wav")
        assert track.start_time == 5.0
        assert track.duration == 10.0
        assert track.end_time == 15.0

    def test_track_contains_time(self):
        track = Track(
            audio_path=Path("/audio/seg.wav"),
            start_time=5.0,
            duration=10.0,
        )
        assert track.contains(5.0)
        assert track.contains(10.0)
        assert track.contains(14.9)
        assert not track.contains(15.0)
        assert not track.contains(4.0)
