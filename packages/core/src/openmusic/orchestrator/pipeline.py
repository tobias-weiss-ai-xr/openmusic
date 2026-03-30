import time
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from openmusic.orchestrator.mix import MixConfig, MixOrchestrator
from openmusic.orchestrator.progress import ProgressReporter


class PipelineStage(Enum):
    GENERATE = "generate"
    PROCESS = "process"
    CROSSFADE = "crossfade"
    EXPORT = "export"


@dataclass
class PipelineResult:
    stage: PipelineStage
    duration: float
    input_path: Path | None = None
    output_path: Path | None = None
    success: bool = True
    error: str | None = None


def run_pipeline(config: MixConfig) -> Generator[PipelineResult]:
    orchestrator = MixOrchestrator(config)
    reporter = ProgressReporter(total=orchestrator.segment_count)
    segment_paths: list[Path] = []

    for i in range(orchestrator.segment_count):
        t0 = time.time()

        reporter.start_segment(i + 1)

        try:
            raw_segment = orchestrator._generate_segment(i, orchestrator.segment_count)
            yield PipelineResult(
                stage=PipelineStage.GENERATE,
                duration=time.time() - t0,
                input_path=None,
                output_path=raw_segment,
            )

            t1 = time.time()
            processed = orchestrator._process_segment(raw_segment)
            yield PipelineResult(
                stage=PipelineStage.PROCESS,
                duration=time.time() - t1,
                input_path=raw_segment,
                output_path=processed,
            )

            segment_paths.append(processed)
            reporter.finish_segment(time.time() - t0)
        except Exception as e:
            yield PipelineResult(
                stage=PipelineStage.GENERATE,
                duration=time.time() - t0,
                success=False,
                error=str(e),
            )

    t2 = time.time()
    output = Path(config.output_path)
    yield PipelineResult(
        stage=PipelineStage.EXPORT,
        duration=time.time() - t2,
        input_path=None,
        output_path=output,
    )
