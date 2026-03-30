"""Tests for PipelineStage, PipelineResult, and run_pipeline."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openmusic.orchestrator.pipeline import (
    PipelineResult,
    PipelineStage,
    run_pipeline,
)
from openmusic.orchestrator.mix import MixConfig


class TestPipelineStage:
    def test_enum_values(self):
        assert PipelineStage.GENERATE.value == "generate"
        assert PipelineStage.PROCESS.value == "process"
        assert PipelineStage.CROSSFADE.value == "crossfade"
        assert PipelineStage.EXPORT.value == "export"


class TestPipelineResult:
    def test_successful_result(self):
        result = PipelineResult(
            stage=PipelineStage.GENERATE,
            duration=5.0,
            input_path=Path("/input.wav"),
            output_path=Path("/output.wav"),
            success=True,
            error=None,
        )
        assert result.stage == PipelineStage.GENERATE
        assert result.duration == 5.0
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        result = PipelineResult(
            stage=PipelineStage.PROCESS,
            duration=2.0,
            input_path=Path("/input.wav"),
            output_path=None,
            success=False,
            error="Node.js crashed",
        )
        assert result.success is False
        assert result.error == "Node.js crashed"
        assert result.output_path is None


class TestRunPipeline:
    @patch("openmusic.orchestrator.pipeline.AudioEncoder")
    @patch("openmusic.orchestrator.pipeline.MixArranger")
    @patch("openmusic.orchestrator.pipeline.MixOrchestrator")
    def test_yields_results_for_each_stage(self, MockOrch, MockArranger, MockEncoder):
        config = MixConfig(length=180)
        mock_orch = MockOrch.return_value
        mock_orch.segment_count = 1

        raw_path = Path("/tmp/raw.wav")
        processed_path = Path("/tmp/processed.wav")
        mock_orch._generate_segment.return_value = raw_path
        mock_orch._process_segment.return_value = processed_path

        mock_arranger = MockArranger.return_value
        mock_arranger.arrange_segments.return_value = Path("/tmp/arranged.wav")
        mock_encoder = MockEncoder.return_value
        mock_encoder.encode_flac.return_value = Path("mix.flac")

        results = list(run_pipeline(config))
        stages = [r.stage for r in results]
        assert PipelineStage.GENERATE in stages
        assert PipelineStage.PROCESS in stages
        assert PipelineStage.EXPORT in stages

    @patch("openmusic.orchestrator.pipeline.AudioEncoder")
    @patch("openmusic.orchestrator.pipeline.MixArranger")
    @patch("openmusic.orchestrator.pipeline.MixOrchestrator")
    def test_all_results_are_pipeline_results(
        self, MockOrch, MockArranger, MockEncoder
    ):
        config = MixConfig(length=180)
        mock_orch = MockOrch.return_value
        mock_orch.segment_count = 1
        mock_orch._generate_segment.return_value = Path("/tmp/raw.wav")
        mock_orch._process_segment.return_value = Path("/tmp/processed.wav")

        mock_arranger = MockArranger.return_value
        mock_arranger.arrange_segments.return_value = Path("/tmp/arranged.wav")
        mock_encoder = MockEncoder.return_value
        mock_encoder.encode_flac.return_value = Path("mix.flac")

        results = list(run_pipeline(config))
        for r in results:
            assert isinstance(r, PipelineResult)
