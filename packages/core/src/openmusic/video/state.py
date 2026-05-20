"""Video pipeline state schema for LangGraph."""

import asyncio
from pathlib import Path
from typing import Annotated, Dict, List, Optional, Tuple, TypedDict

from operator import add


class VideoPipelineState(TypedDict):
    """Shared state object for all LangGraph nodes in video pipeline."""

    # Inputs
    config: Dict[str, object]
    sdxl_model_path: str
    max_concurrent_images: int
    crossfade_duration: int
    confirm_upload: bool
    playlist_id: Optional[str]

    # Audio
    audio_paths: List[Path]
    stage_timings: List[Tuple[float, float, str]]
    audio_with_automation: Optional[Path]

    # Visuals
    image_paths: Annotated[Dict[str, Optional[Path]], "replace"]

    # Output
    final_video: Optional[Path]
    youtube_url: Optional[str]

    # GPU Resource Management
    gpu_semaphore: asyncio.Semaphore
    video_gpu_semaphore: asyncio.Semaphore

    # Error tracking
    errors: Annotated[List[str], add]


def initialize_video_pipeline_state(
    config: Dict[str, object],
    sdxl_model_path: str = "stabilityai/sdxl-turbo",
    max_concurrent_images: int = 2,
    crossfade_duration: int = 30,
    confirm_upload: bool = True,
    playlist_id: Optional[str] = "Dub Odyssee",
) -> VideoPipelineState:
    """Initialize default state for video pipeline."""
    return VideoPipelineState(
        config=config,
        sdxl_model_path=sdxl_model_path,
        max_concurrent_images=max_concurrent_images,
        crossfade_duration=crossfade_duration,
        confirm_upload=confirm_upload,
        playlist_id=playlist_id,
        audio_paths=[],
        stage_timings=[],
        audio_with_automation=None,
        image_paths={},
        final_video=None,
        youtube_url=None,
        gpu_semaphore=asyncio.Semaphore(max_concurrent_images),
        video_gpu_semaphore=asyncio.Semaphore(1),
        errors=[],
    )