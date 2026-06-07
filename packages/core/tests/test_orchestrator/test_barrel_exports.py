"""Tests for orchestrator barrel exports."""

from openmusic.orchestrator import (
    MixConfig,
    MixOrchestrator,
    PipelineResult,
    PipelineStage,
    ProgressReporter,
    run_pipeline,
)


class TestBarrelExports:
    def test_mix_config_exported(self):
        assert MixConfig is not None

    def test_mix_orchestrator_exported(self):
        assert MixOrchestrator is not None

    def test_pipeline_result_exported(self):
        assert PipelineResult is not None

    def test_pipeline_stage_exported(self):
        assert PipelineStage is not None

    def test_progress_reporter_exported(self):
        assert ProgressReporter is not None

    def test_run_pipeline_exported(self):
        assert run_pipeline is not None
