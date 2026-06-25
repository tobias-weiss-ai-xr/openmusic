"""Test video pipeline state."""

import pytest

try:
    from openmusic.video.state import VideoPipelineState, initialize_video_pipeline_state
except (ModuleNotFoundError, ImportError):
    pytest.skip("video pipeline deps not available", allow_module_level=True)


def test_state_initialization():
    config = {
        "length": 3600.0,
        "bpm": 125,
        "key": "Dm",
        "output_path": "mix.flac",
    }
    state = initialize_video_pipeline_state(config)

    assert "config" in state
    assert state["config"] == config
    assert state["sdxl_model_path"] == "stabilityai/sdxl-turbo"
    assert state["max_concurrent_images"] == 2
    assert state["crossfade_duration"] == 30
    assert state["audio_paths"] == []
    assert state["stage_timings"] == {}
    assert state["audio_with_automation"] is None
    assert state["image_paths"] == {}
    assert state["final_video"] is None
    assert state["youtube_url"] is None
    assert state["errors"] == []


def test_state_custom_parameters():
    config = {"length": 1800.0, "bpm": 130, "key": "Cm", "output_path": "short.flac"}
    state = initialize_video_pipeline_state(
        config,
        sdxl_model_path="custom/model",
        max_concurrent_images=4,
        crossfade_duration=20,
        confirm_upload=False,
        playlist_id="Custom Playlist",
    )

    assert state["sdxl_model_path"] == "custom/model"
    assert state["max_concurrent_images"] == 4
    assert state["crossfade_duration"] == 20
    assert state["confirm_upload"] is False
    assert state["playlist_id"] == "Custom Playlist"