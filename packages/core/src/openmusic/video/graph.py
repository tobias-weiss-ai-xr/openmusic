"""LangGraph graph definition for video pipeline."""

from typing import Any, Dict, Literal

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from openmusic.video.state import VideoPipelineState, initialize_video_pipeline_state
from openmusic.video.utils.stage_timing import STAGE_PROMPTS


def _dispatch_image_generations(state: VideoPipelineState):
    """Dispatch parallel tasks for all 10 stage images."""
    return [
        Send("generate_image_for_stage", {"stage_name": stage_name})
        for stage_name in STAGE_PROMPTS.keys()
    ]


def dummy_audio_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Dummy audio generation node."""
    return {
        "audio_paths": [],
        "stage_timings": [],
        "stage_prompts": STAGE_PROMPTS,
    }


def dummy_image_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Dummy image generation node for one stage."""
    stage_name = state.get("stage_name", "unknown")
    return {
        "image_paths": {stage_name: None},
    }


def dummy_images_join_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Wait for all images."""
    return {}


def dummy_audio_automation_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Dummy audio automation node."""
    return {}


def dummy_video_rendering_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Dummy video rendering node."""
    return {}


def dummy_youtube_upload_node(state: VideoPipelineState) -> Dict[str, Any]:
    """Dummy YouTube upload node."""
    return {"youtube_url": "https://example.com"}


def build_video_pipeline_graph(
    config: Dict[str, Any],
    **kwargs,
) -> StateGraph:
    """Build the video pipeline LangGraph."""
    graph = StateGraph(VideoPipelineState)

    graph.add_node("generate_all_audio_segments", dummy_audio_node)
    graph.add_node("generate_image_for_stage", dummy_image_node)
    graph.add_node("images_join", dummy_images_join_node)
    graph.add_node("apply_per_stage_audio_automation", dummy_audio_automation_node)
    graph.add_node("render_video_with_crossfades", dummy_video_rendering_node)
    graph.add_node("upload_to_youtube", dummy_youtube_upload_node)

    graph.set_entry_point("generate_all_audio_segments")

    graph.add_conditional_edges(
        "generate_all_audio_segments",
        _dispatch_image_generations,
        {"generate_image_for_stage": "generate_image_for_stage"},
    )

    graph.add_edge("generate_image_for_stage", "images_join")
    graph.add_edge("images_join", "apply_per_stage_audio_automation")
    graph.add_edge("apply_per_stage_audio_automation", "render_video_with_crossfades")
    graph.add_edge("render_video_with_crossfades", "upload_to_youtube")
    graph.add_edge("upload_to_youtube", END)

    return graph.compile()