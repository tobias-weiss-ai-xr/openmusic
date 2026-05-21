from openmusic.video.nodes.audio_generation import generate_all_audio_segments
from openmusic.video.nodes.image_generation import generate_image_for_stage
from openmusic.video.nodes.svg_generation import generate_svg_image_for_stage
from openmusic.video.nodes.audio_automation import apply_per_stage_audio_automation
from openmusic.video.nodes.video_rendering import render_video_with_crossfades
from openmusic.video.nodes.youtube_upload import upload_to_youtube

__all__ = [
    "generate_all_audio_segments",
    "generate_image_for_stage",
    "generate_svg_image_for_stage",
    "apply_per_stage_audio_automation",
    "render_video_with_crossfades",
    "upload_to_youtube",
]