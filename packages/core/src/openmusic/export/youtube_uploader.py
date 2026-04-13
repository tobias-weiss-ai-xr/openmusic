"""YouTube video uploader with dual-backend support.

Primary: YouTube Data API v3 with OAuth 2.0
Fallback: youtube-up package (browser cookies, no quota)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class YouTubeUploadError(Exception):
    """Base exception for YouTube upload errors."""

    pass


class QuotaExceededError(YouTubeUploadError):
    """Raised when YouTube API quota is exceeded."""

    pass


class OAuthNotConfiguredError(YouTubeUploadError):
    """Raised when OAuth credentials are not configured."""

    pass


class YouTubeUpNotInstalledError(YouTubeUploadError):
    """Raised when youtube-up package is not installed."""

    pass


@dataclass
class YouTubeUploadConfig:
    """Configuration for YouTube video uploads."""

    title: str = "Dub Techno Mix"
    description: str = ""
    tags: list[str] = field(default_factory=lambda: ["dub techno", "electronic music"])
    category: str = "10"  # Music
    privacy: str = "private"  # public, private, unlisted
    made_for_kids: bool = False
    publish_at: str | None = None  # ISO 8601 for premiere
    thumbnail_path: str | None = None
    playlist_title: str | None = None
    client_secrets_file: str = "client_secrets.json"
    token_file: str = "youtube_token.json"
    cookies_file: str = "cookies.txt"  # For youtube-up fallback


class YouTubeAPIUploader:
    """Uploads using YouTube Data API v3 with OAuth 2.0."""

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(self, config: YouTubeUploadConfig):
        self.config = config
        self.youtube = None
        self.credentials = None

    def _check_dependencies(self) -> None:
        """Check if required packages are installed."""
        try:
            from googleapiclient.discovery import build
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials

            return
        except ImportError as e:
            raise YouTubeUploadError(
                f"YouTube API dependencies not installed. "
                f"Install with: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            ) from e

    def authenticate(self) -> None:
        """Authenticate with OAuth 2.0 flow."""
        self._check_dependencies()

        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        credentials = None
        token_path = Path(self.config.token_file)

        # Load existing token if available
        if token_path.exists():
            try:
                with open(token_path, "r") as f:
                    credentials_data = json.load(f)
                credentials = Credentials.from_authorized_user_info(credentials_data)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to load token file: {e}. Re-authenticating.")

        # Refresh or create new credentials
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(None)
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}. Re-authenticating.")
                credentials = None

        if not credentials or not credentials.valid:
            secrets_path = Path(self.config.client_secrets_file)
            if not secrets_path.exists():
                raise OAuthNotConfiguredError(
                    f"OAuth client secrets file not found: {self.config.client_secrets_file}\n"
                    f"Create OAuth credentials at https://console.cloud.google.com/apis/credentials"
                )

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.client_secrets_file, self.SCOPES
                )
                credentials = flow.run_local_server(port=0)
            except Exception as e:
                raise OAuthNotConfiguredError(
                    f"OAuth authentication failed: {e}"
                ) from e

            # Save credentials for future use
            try:
                with open(token_path, "w") as f:
                    f.write(credentials.to_json())
                logger.info(f"Saved OAuth token to {token_path}")
            except Exception as e:
                logger.warning(f"Failed to save token file: {e}")

        self.credentials = credentials
        self.youtube = build("youtube", "v3", credentials=credentials)

    def _is_quota_exceeded(self, error: Any) -> bool:
        """Check if HttpError is due to quota exceeded."""
        try:
            if hasattr(error, "resp") and hasattr(error.resp, "status"):
                if error.resp.status == 403:
                    error_details = getattr(error, "error_details", [])
                    if not error_details and hasattr(error, "content"):
                        try:
                            error_json = json.loads(error.content.decode())
                            error_details = error_json.get("error", {}).get(
                                "errors", []
                            )
                        except (
                            json.JSONDecodeError,
                            AttributeError,
                            UnicodeDecodeError,
                        ):
                            pass

                    for detail in error_details:
                        if detail.get("reason") == "quotaExceeded":
                            return True
            return False
        except Exception:
            return False

    def _upload_with_retry(self, video_path: str, body: dict, media_body: Any) -> dict:
        """Upload with exponential backoff retry."""
        from googleapiclient.errors import HttpError

        max_retries = 3
        base_delay = 5

        for attempt in range(max_retries):
            try:
                request = self.youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media_body,
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        logger.info(f"Upload progress: {int(status.progress() * 100)}%")

                return response

            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"Upload failed with status {e.resp.status}. "
                            f"Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue

                if self._is_quota_exceeded(e):
                    raise QuotaExceededError(
                        f"YouTube API quota exceeded. Consider using the youtube-up fallback."
                    ) from e

                raise YouTubeUploadError(f"Upload failed: {e}") from e

        raise YouTubeUploadError("Upload failed after max retries")

    def upload(self, video_path: str) -> str:
        """Upload a video to YouTube. Returns the video ID."""
        if not self.youtube:
            self.authenticate()

        from googleapiclient.http import MediaFileUpload

        video_file = Path(video_path)
        if not video_file.exists():
            raise YouTubeUploadError(f"Video file not found: {video_path}")

        snippet = {
            "title": self.config.title,
            "description": self.config.description,
            "tags": self.config.tags,
            "categoryId": self.config.category,
        }

        status = {
            "privacyStatus": self.config.privacy,
            "selfDeclaredMadeForKids": self.config.made_for_kids,
        }

        if self.config.publish_at:
            status["publishAt"] = self.config.publish_at

        body = {"snippet": snippet, "status": status}

        media_body = MediaFileUpload(
            str(video_file),
            mimetype="video/mp4",
            resumable=True,
        )

        response = self._upload_with_retry(video_path, body, media_body)

        video_id = response.get("id")
        if not video_id:
            raise YouTubeUploadError("Upload completed but no video ID returned")

        logger.info(
            f"Video uploaded successfully: https://youtube.com/watch?v={video_id}"
        )
        return video_id

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> None:
        """Set a custom thumbnail for the video."""
        if not self.youtube:
            self.authenticate()

        from googleapiclient.http import MediaFileUpload

        thumbnail_file = Path(thumbnail_path)
        if not thumbnail_file.exists():
            raise YouTubeUploadError(f"Thumbnail file not found: {thumbnail_path}")

        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_file)),
            ).execute()
            logger.info(f"Thumbnail set successfully for video {video_id}")
        except Exception as e:
            raise YouTubeUploadError(f"Failed to set thumbnail: {e}") from e

    def add_to_playlist(self, video_id: str, playlist_title: str) -> str:
        """Add video to a playlist (creates if not exists). Returns playlist ID."""
        if not self.youtube:
            self.authenticate()

        # Search for existing playlist
        try:
            playlists_response = (
                self.youtube.playlists()
                .list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                )
                .execute()
            )

            existing_playlist = None
            for playlist in playlists_response.get("items", []):
                if playlist["snippet"]["title"] == playlist_title:
                    existing_playlist = playlist
                    break

            if existing_playlist:
                playlist_id = existing_playlist["id"]
                logger.info(f"Using existing playlist: {playlist_title}")
            else:
                # Create new playlist
                create_response = (
                    self.youtube.playlists()
                    .insert(
                        part="snippet,status",
                        body={
                            "snippet": {
                                "title": playlist_title,
                                "description": f"Playlist created by OpenMusic",
                            },
                            "status": {"privacyStatus": self.config.privacy},
                        },
                    )
                    .execute()
                )
                playlist_id = create_response["id"]
                logger.info(f"Created new playlist: {playlist_title}")

            # Add video to playlist
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            ).execute()

            logger.info(f"Video added to playlist: {playlist_title}")
            return playlist_id

        except Exception as e:
            raise YouTubeUploadError(f"Failed to add video to playlist: {e}") from e


class YouTubeUpFallback:
    """Fallback uploader using youtube-up package (no API quota)."""

    def __init__(self, config: YouTubeUploadConfig):
        self.config = config

    def is_available(self) -> bool:
        """Check if youtube-up is installed."""
        try:
            import youtube_up  # noqa: F401

            return True
        except ImportError:
            return False

    def _check_dependencies(self) -> None:
        """Check if youtube-up is installed."""
        try:
            from youtube_up import (
                Metadata,
                PrivacyEnum,
                YTUploaderSession,
                Playlist,
            )
        except ImportError as e:
            raise YouTubeUpNotInstalledError(
                f"youtube-up package not installed. "
                f"Install with: pip install youtube-up"
            ) from e

    def upload(self, video_path: str) -> str:
        """Upload using youtube-up. Returns the video ID."""
        self._check_dependencies()

        from youtube_up import (
            Metadata,
            PrivacyEnum,
            YTUploaderSession,
            Playlist,
        )

        video_file = Path(video_path)
        if not video_file.exists():
            raise YouTubeUploadError(f"Video file not found: {video_path}")

        cookies_file = Path(self.config.cookies_file)
        if not cookies_file.exists():
            raise YouTubeUploadError(
                f"Cookies file not found: {self.config.cookies_file}\n"
                f"YouTube-up requires browser cookies from cookies.txt file."
            )

        try:
            # Map privacy status
            privacy_map = {
                "public": PrivacyEnum.PUBLIC,
                "private": PrivacyEnum.PRIVATE,
                "unlisted": PrivacyEnum.UNLISTED,
            }
            privacy = privacy_map.get(self.config.privacy, PrivacyEnum.PRIVATE)

            # Create metadata
            from youtube_up.metadata import CategoryEnum

            tag_list = tuple(self.config.tags) if self.config.tags else ()
            metadata = Metadata(
                title=self.config.title,
                description=self.config.description,
                tags=tag_list,
                category=CategoryEnum.MUSIC,
                privacy=privacy,
            )

            # Create session from cookies
            session = YTUploaderSession.from_cookies_txt(str(cookies_file))

            # Upload video
            logger.info(f"Uploading video using youtube-up fallback...")
            video_id = session.upload(
                file_path=str(video_file),
                metadata=metadata,
            )

            logger.info(
                f"Video uploaded successfully (youtube-up): https://youtube.com/watch?v={video_id}"
            )

            # Add to playlist if specified
            if self.config.playlist_title:
                try:
                    playlist = Playlist.from_title(self.config.playlist_title, session)
                    playlist.add_video(video_id)
                    logger.info(
                        f"Video added to playlist: {self.config.playlist_title}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to add video to playlist: {e}")

            return video_id

        except Exception as e:
            raise YouTubeUploadError(f"YouTube-up upload failed: {e}") from e


class YouTubeUploader:
    """Dual-backend uploader. Tries API v3, falls back to youtube-up on quota."""

    def __init__(self, config: YouTubeUploadConfig | None = None):
        self.config = config or YouTubeUploadConfig()
        self.api_uploader = YouTubeAPIUploader(self.config)
        self.fallback_uploader = YouTubeUpFallback(self.config)

    def upload(self, video_path: str) -> str:
        """Upload a video with automatic fallback. Returns the video ID."""
        # Try API uploader first
        try:
            logger.info("Attempting upload via YouTube Data API v3...")
            video_id = self.api_uploader.upload(video_path)

            # Set thumbnail if provided
            if self.config.thumbnail_path:
                self.api_uploader.set_thumbnail(video_id, self.config.thumbnail_path)

            # Add to playlist if specified
            if self.config.playlist_title:
                self.api_uploader.add_to_playlist(video_id, self.config.playlist_title)

            return video_id

        except QuotaExceededError:
            logger.warning("YouTube API quota exceeded. Falling back to youtube-up...")

        except YouTubeUploadError as e:
            logger.warning(
                f"YouTube API upload failed ({e}). Falling back to youtube-up..."
            )

        # Fallback to youtube-up
        logger.info("Using youtube-up fallback uploader...")
        return self.fallback_uploader.upload(video_path)
