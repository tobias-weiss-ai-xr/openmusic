"""Tests for ProgressReporter."""

import io
import time
from unittest.mock import MagicMock

from openmusic.orchestrator.progress import ProgressReporter


class TestProgressReporterInit:
    def test_init_defaults(self):
        reporter = ProgressReporter()
        assert reporter.total == 0
        assert reporter.current == 0

    def test_init_with_total(self):
        reporter = ProgressReporter(total=40)
        assert reporter.total == 40
        assert reporter.current == 0


class TestProgressReporterCallbacks:
    def test_on_stage_change_callback(self):
        reporter = ProgressReporter(total=3)
        callback = MagicMock()
        reporter.on_stage_change(callback)

        reporter.start_segment(1)
        callback.assert_called_once_with(stage="generate", index=1, total=3)

    def test_on_progress_callback(self):
        reporter = ProgressReporter(total=3)
        callback = MagicMock()
        reporter.on_progress(callback)

        reporter.start_segment(1)
        callback.assert_called()

    def test_on_complete_callback(self):
        reporter = ProgressReporter(total=2)
        callback = MagicMock()
        reporter.on_complete(callback)

        reporter.start_segment(1)
        reporter.finish_segment(1.5)
        reporter.start_segment(2)
        reporter.finish_segment(2.0)

        callback.assert_called_once()


class TestProgressReporterConsoleOutput:
    def test_console_output_format(self):
        reporter = ProgressReporter(total=3)
        buf = io.StringIO()
        reporter.on_progress(lambda *a, **kw: None)

        reporter._output = buf

        reporter.start_segment(1)
        output = buf.getvalue()
        assert "[1/3]" in output
        assert "Generating" in output

    def test_console_output_format_later_segment(self):
        reporter = ProgressReporter(total=40)
        buf = io.StringIO()
        reporter._output = buf

        reporter.start_segment(20)
        output = buf.getvalue()
        assert "[20/40]" in output


class TestProgressReporterETA:
    def test_eta_returns_none_when_no_segments_complete(self):
        reporter = ProgressReporter(total=10)
        assert reporter.get_eta() is None

    def test_eta_after_one_segment(self):
        reporter = ProgressReporter(total=3)
        reporter.start_segment(1)
        reporter.finish_segment(10.0)  # 10 seconds for first segment

        eta = reporter.get_eta()
        assert eta is not None
        # 2 remaining segments * 10s average = ~20s
        assert eta > 15
        assert eta < 25

    def test_eta_averages_across_segments(self):
        reporter = ProgressReporter(total=3)
        reporter.start_segment(1)
        reporter.finish_segment(10.0)
        reporter.start_segment(2)
        reporter.finish_segment(20.0)  # 10s + 20s = 30s total, avg 15s

        eta = reporter.get_eta()
        assert eta is not None
        # 1 remaining * 15s avg = ~15s
        assert eta > 10
        assert eta < 20

    def test_eta_zero_when_all_complete(self):
        reporter = ProgressReporter(total=2)
        reporter.start_segment(1)
        reporter.finish_segment(10.0)
        reporter.start_segment(2)
        reporter.finish_segment(10.0)

        eta = reporter.get_eta()
        assert eta == 0
