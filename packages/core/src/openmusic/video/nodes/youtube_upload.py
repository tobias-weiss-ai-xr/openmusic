"""YouTube upload node."""

import logging
from typing import Dict, Any

from openmusic.export.youtube_uploader import (
    YouTubeUploader,
    YouTubeUploadConfig,
)
from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


def upload_to_youtube(state: VideoPipelineState) -> Dict[str, Any]:
    """Upload video to YouTube with optional verification.

    Args:
        state: VideoPipelineState with final_video and config

    Returns:
        State updates: youtube_url
    """
    final_video = state.get("final_video")
    if not final_video:
        raise ValueError("No video available for upload")

    config = state["config"]
    confirm_upload = config.get("confirm_upload", True)
    playlist_id = config.get("playlist_id", "Dub Odyssee")

    logger.info(f"Uploading video: {final_video}")

    upload_config = YouTubeUploadConfig(
        title=config.get("title", "Dub Techno Mix"),
        description=config.get("description", ""),
        tags=config.get("tags", ["dub techno", "electronic music"]),
        privacy=config.get("privacy", "public"),
        playlist_title=playlist_id,
        client_secrets_file=config.get("client_secrets_file"),
        cookies_file=config.get("cookies_file"),
    )

    uploader = YouTubeUploader(upload_config)
    video_id = uploader.upload(final_video)

    youtube_url = f"https://youtube.com/watch?v={video_id}"
    logger.info(f"Uploaded: {youtube_url}")

    return {"youtube_url": youtube_url}