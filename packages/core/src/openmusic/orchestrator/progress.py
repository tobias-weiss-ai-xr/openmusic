import io
import sys
import time


class ProgressReporter:
    """Tracks and reports progress of mix generation segments."""

    def __init__(self, total: int = 0):
        self.total = total
        self.current = 0
        self._start_time: float | None = None
        self._segment_start: float | None = None
        self._segment_times: list[float] = []
        self._stage_change_callbacks: list = []
        self._progress_callbacks: list = []
        self._complete_callbacks: list = []
        self._output = sys.stdout

    def on_stage_change(self, callback):
        self._stage_change_callbacks.append(callback)

    def on_progress(self, callback):
        self._progress_callbacks.append(callback)

    def on_complete(self, callback):
        self._complete_callbacks.append(callback)

    def start_segment(self, index: int):
        self.current = index
        if self._start_time is None:
            self._start_time = time.time()
        self._segment_start = time.time()

        stage = "generate"
        for cb in self._stage_change_callbacks:
            cb(stage=stage, index=index, total=self.total)
        for cb in self._progress_callbacks:
            cb(index=index, total=self.total)

        self._output.write(f"[{index}/{self.total}] Generating segment {index}...\n")
        self._output.flush()

    def finish_segment(self, duration: float):
        if self._segment_start is not None:
            self._segment_times.append(duration)

        if self.current >= self.total and self.total > 0:
            for cb in self._complete_callbacks:
                cb()

    def get_eta(self) -> float | None:
        if not self._segment_times:
            return None
        remaining = self.total - self.current
        if remaining <= 0:
            return 0
        avg = sum(self._segment_times) / len(self._segment_times)
        return avg * remaining
