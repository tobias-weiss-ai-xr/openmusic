"""Test video pipeline graph."""

import pytest

try:
    from openmusic.video.graph import build_video_pipeline_graph
except (ModuleNotFoundError, ImportError):
    pytest.skip("video pipeline deps not available", allow_module_level=True)


def test_graph_structure():
    """Test graph builds without errors."""
    config = {
        "length": 3600.0,
        "bpm": 125,
        "key": "Dm",
        "output_path": "mix.flac",
    }
    from openmusic.video.state import initialize_video_pipeline_state
    graph = build_video_pipeline_graph(config, confirm_upload=False)
    initial_state = initialize_video_pipeline_state(config, confirm_upload=False)

    assert graph is not None
    assert graph.get_graph().nodes is not None


@pytest.mark.skip(reason="requires GPU (async nodes need async runner)")
def test_graph_execution_dry_run():
    """Test graph executes dummy nodes."""
    config = {
        "length": 60.0,
        "bpm": 125,
        "key": "Dm",
        "output_path": "/tmp/test.flac",
    }
    from openmusic.video.state import initialize_video_pipeline_state
    graph = build_video_pipeline_graph(config, confirm_upload=False)
    initial_state = initialize_video_pipeline_state(config, confirm_upload=False)

    results = list(graph.stream(initial_state))
    assert len(results) > 0