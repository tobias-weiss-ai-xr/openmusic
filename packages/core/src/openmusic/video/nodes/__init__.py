"""LangGraph nodes for video pipeline."""

from openmusic.video.nodes.audio_generation import generate_all_audio_segments
from openmusic.video.nodes.image_generation import generate_image_for_stage
from openmusic.video.nodes.audio_automation import apply_per_stage_audio_automation

__all__ = [
    "generate_all_audio_segments",
    "generate_image_for_stage",
    "apply_per_stage_audio_automation",
]