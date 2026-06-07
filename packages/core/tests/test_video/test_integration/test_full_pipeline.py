"""Integration test for full video pipeline nodes."""

from openmusic.video import build_video_pipeline_graph, VideoPipelineState
from openmusic.video.state import initialize_video_pipeline_state
from openmusic.video.nodes import (
    generate_all_audio_segments,
    generate_image_for_stage,
    apply_per_stage_audio_automation,
    render_video_with_crossfades,
    upload_to_youtube,
)


def test_all_nodes_importable():
    assert generate_all_audio_segments is not None
    assert generate_image_for_stage is not None
    assert apply_per_stage_audio_automation is not None
    assert render_video_with_crossfades is not None
    assert upload_to_youtube is not None


def test_graph_builds_with_all_nodes():
    config = {
        "length": 3600.0,
        "bpm": 125,
        "key": "Dm",
        "output_path": "mix.flac",
    }
    graph = build_video_pipeline_graph(config, confirm_upload=False)

    assert graph is not None
    node_names = set(graph.get_graph().nodes)
    assert "generate_all_audio_segments" in node_names
    assert "generate_image_for_stage" in node_names
    assert "images_join" in node_names
    assert "apply_per_stage_audio_automation" in node_names
    assert "render_video_with_crossfades" in node_names
    assert "upload_to_youtube" in node_names


def test_initial_state_valid():
    config = {
        "length": 3600.0,
        "bpm": 125,
        "key": "Dm",
        "output_path": "mix.flac",
    }
    state = initialize_video_pipeline_state(config, confirm_upload=False)

    assert state["config"] == config
    assert state["sdxl_model_path"] == "stabilityai/sdxl-turbo"
    assert state["confirm_upload"] is False
    assert state["audio_paths"] == []
    assert state["image_paths"] == {}
    assert state["errors"] == []