"""LangGraph graph definition for video pipeline."""

from typing import Any, Dict

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from openmusic.video.state import VideoPipelineState
from openmusic.video.utils.stage_timing import STAGE_PROMPTS
from openmusic.video.nodes import (
    generate_all_audio_segments,
    generate_image_for_stage,
    apply_per_stage_audio_automation,
    render_video_with_crossfades,
    upload_to_youtube,
)


def _dispatch_image_generations(state: VideoPipelineState):
    """Dispatch parallel tasks for all 10 stage images."""
    # Pass essential state to dispatched tasks
    # Note: state objects (like semaphores) come from already-merged parent state
    return [
        Send("generate_image_for_stage", {
            "stage_name": stage_name,
            "stage_prompts": state.get("stage_prompts", {}),
            "sdxl_model_path": state.get("sdxl_model_path", "stabilityai/sdxl-turbo"),
            "max_concurrent_images": state.get("max_concurrent_images", 2),
        })
        for stage_name in STAGE_PROMPTS.keys()
    ]


def _images_join(state: VideoPipelineState) -> Dict[str, Any]:
    """Wait for all images to complete."""
    return {}


def build_video_pipeline_graph(
    config: Dict[str, Any],
    **kwargs,
) -> StateGraph:
    """Build the video pipeline LangGraph."""
    graph = StateGraph(VideoPipelineState)

    graph.add_node("generate_all_audio_segments", generate_all_audio_segments)
    graph.add_node("generate_image_for_stage", generate_image_for_stage)
    graph.add_node("images_join", _images_join)
    graph.add_node("apply_per_stage_audio_automation", apply_per_stage_audio_automation)
    graph.add_node("render_video_with_crossfades", render_video_with_crossfades)
    graph.add_node("upload_to_youtube", upload_to_youtube)

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