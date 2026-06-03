"""yt-upload backend for reliable YouTube video uploads.

Uses Playwright persistent browser profile for long-lived auth sessions.
No more cookie expiry issues -- one-time login persists indefinitely.

API:
    YtUploadBackend.upload_video(file_path, config) -> str (video URL)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from openmusic.export.metadata import TrackMetadata

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "openmusic" / "yt-upload-profile"
DEFAULT_COOKIES_JSON = Path("cookies_kingofdub.json")


@dataclass
class YtUploadConfig:
    """Configuration for yt-upload backend."""

    user_data_dir: str = str(DEFAULT_PROFILE_DIR)
    google_profile: str = "Profile 1"
    cookies_json: str = str(DEFAULT_COOKIES_JSON)
    headless: bool = True
    scheduled_publish: Optional[datetime] = None


def _convert_to_playwright_cookies(cookies_txt_path: str) -> list[dict]:
    from http.cookiejar import MozillaCookieJar

    cj = MozillaCookieJar(cookies_txt_path)
    cj.load(ignore_discard=True, ignore_expires=True)

    result = []
    for c in cj:
        if not c.value:
            continue
        result.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "secure": c.secure,
                "httpOnly": False,
                "sameSite": "None" if c.secure else "Lax",
                "expires": int(c.expires) if c.expires else -1,
            }
        )
    return result


def ensure_cookies_json(
    cookies_txt: str | Path | None = None,
    cookies_json: str | Path | None = None,
) -> str:
    if cookies_json and Path(str(cookies_json)).exists():
        logger.info("Using existing cookies JSON: %s", cookies_json)
        return str(cookies_json)

    txt_path = str(cookies_txt) if cookies_txt else "cookies_kingofdub.txt"
    if not Path(txt_path).exists():
        from glob import glob

        found = glob("cookies*.txt")
        if found:
            txt_path = found[0]
            logger.info("Auto-detected cookies: %s", txt_path)
        else:
            logger.warning("No cookies file found at %s", txt_path)
            return ""

    json_path = str(cookies_json) if cookies_json else str(DEFAULT_COOKIES_JSON)
    pw_cookies = _convert_to_playwright_cookies(txt_path)

    with open(json_path, "w") as f:
        json.dump(pw_cookies, f, indent=2)

    logger.info("Converted %d cookies to Playwright format: %s", len(pw_cookies), json_path)
    return json_path


def _patch_yt_upload_channel():
    """Monkey-patch yt-upload Channel for Playwright 1.60+ compatibility and current YouTube Studio UI."""
    import yt_upload.channel as yt_channel_module
    from yt_upload.exceptions import YTError
    from yt_upload.utils import remove_indexddb_cache_files
    from playwright.async_api import async_playwright

    orig_start = yt_channel_module.Channel.start
    orig_stop = yt_channel_module.Channel.stop

    async def patched_start(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            channel="chrome",
            headless=self.headless,
            proxy=self.proxy,
            user_agent=self.user_agent,
            args=[
                "--no-sandbox",
                "--allow-profiles-outside-user-dir",
                f"--profile-directory={self.profile}",
            ],
        )
        await self.context.add_cookies(self.yt_cookies.model_dump())

        page = await self.context.new_page()
        studio_page = yt_channel_module.YTStudioPage(page)
        language = await studio_page.get_language()
        if not (self.change_language_to_eng or language == "en"):
            # Accept any English variant (en-GB, en-US, etc.)
            if language and language.startswith("en"):
                logger.info("Accepting English variant: %s", language)
            else:
                raise YTError(
                    f"YouTube language is '{language}', "
                    "need to change YouTube language to English. "
                    "Use either set change_language_to_eng = True "
                    "or do it manually in YouTube settings."
                )
        elif self.change_language_to_eng and not language == "en" and not (language and language.startswith("en")):
            await studio_page.change_language_to_eng()
        await page.close()

    async def patched_stop(self):
        try:
            remove_indexddb_cache_files(self.profile_path)
        except FileNotFoundError:
            pass
        await self.context.close()
        await self.playwright.stop()

    # Override _update_cookies to NOT overwrite the original cookies file
    # (yt-upload's default saves only studio.youtube.com cookies, losing .google.com auth cookies)
    async def patched_update_cookies(self):
        pass

    yt_channel_module.Channel._update_cookies = patched_update_cookies

    yt_channel_module.Channel.start = patched_start
    yt_channel_module.Channel.stop = patched_stop

    # Patch YTStudioPage to navigate to upload URL directly (bypasses #create-icon)
    from yt_upload.pages import YTStudioPage
    from yt_upload.components import YTStudioComponent

    # Upload URL directly opens the file picker — no need for CREATE button navigation
    UPLOAD_URL = "https://studio.youtube.com/upload"
    SELECT_FILES_XPATH = "//ytcp-button[@id='select-files-button']"

    orig_studio_load = YTStudioPage.load_page
    orig_studio_input = YTStudioPage.input_video

    async def patched_studio_load(self):
        """Navigate directly to upload URL, bypassing #create-icon selector."""
        await self.page.goto(
            UPLOAD_URL,
            timeout=self.time_out.GLOBAL,
            wait_until="domcontentloaded",
        )
        await self.page.wait_for_selector(
            SELECT_FILES_XPATH,
            timeout=self.time_out.GLOBAL,
        )

    async def patched_studio_input(self, filepath: str):
        """Trigger file chooser directly — skip CREATE/Upload menus since we're on upload page."""
        async with self.page.expect_file_chooser(
            timeout=self.time_out.select_files
        ) as fc_info:
            await self.page.locator(SELECT_FILES_XPATH).click(timeout=self.time_out.click)

        file_chooser = await fc_info.value
        await file_chooser.set_files(filepath, timeout=self.time_out.upload_files)
        await self.page.wait_for_timeout(self.time_sleep.upload_files)

    YTStudioPage.load_page = patched_studio_load
    YTStudioPage.input_video = patched_studio_input


_PATCHED = False


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    privacy: str = "unlisted",
    scheduled_publish: datetime | None = None,
    category: str = "Music",
    tags: list[str] | None = None,
    playlist: str | None = None,
    config: YtUploadConfig | None = None,
) -> str:
    global _PATCHED
    if not _PATCHED:
        _patch_yt_upload_channel()
        _PATCHED = True

    import yt_upload
    from yt_upload.models.video import Video
    from yt_upload.constants.visibilities import PUBLIC, PRIVATE, UNLISTED

    cfg = config or YtUploadConfig()

    json_path = ensure_cookies_json(cookies_json=cfg.cookies_json)
    if not json_path:
        raise FileNotFoundError(
            "No cookies file found. Create cookies_kingofdub.txt or cookies_kingofdub.json "
            "in the project directory."
        )

    profile_dir = os.path.join(cfg.user_data_dir, cfg.google_profile)
    os.makedirs(profile_dir, exist_ok=True)

    channel = yt_upload.Channel(
        user_data_dir=cfg.user_data_dir,
        google_profile=cfg.google_profile,
        cookies_path=json_path,
    )
    channel(
        youtube_channel="",
        headless=cfg.headless,
        change_language_to_eng=True,
        enable_logging=False,
    )

    privacy_map = {
        "public": PUBLIC,
        "unlisted": UNLISTED,
        "private": PRIVATE,
    }
    yt_visibility = privacy_map.get(privacy.lower(), UNLISTED)

    video_kwargs: dict = {
        "video_path": video_path,
        "title": title,
        "made_for_kids": False,
        "category": category,
        "visibility": yt_visibility,
    }
    if description:
        video_kwargs["description"] = description
    if tags:
        video_kwargs["tags"] = tags
    if scheduled_publish is not None:
        video_kwargs["schedule"] = scheduled_publish
    if playlist:
        video_kwargs["playlist"] = [playlist]

    video = Video(**video_kwargs)
    result = asyncio.run(_run_upload(channel, video))
    return result


async def _run_upload(channel, video) -> str:
    async with channel:
        logger.info("yt-upload Channel started, profile=%s", channel.profile_path)
        await channel.upload_video(video)
        logger.info("Upload completed successfully")
        video_url = f"https://youtube.com/watch?v={video.video_id}"
        return video_url


def setup_profile(
    user_data_dir: str | None = None,
    google_profile: str = "Profile 1",
    cookies_txt: str = "cookies_kingofdub.txt",
) -> str:
    """Set up the yt-upload persistent profile.

    Converts existing cookies.txt to JSON format and ensures profile dir exists.
    Returns the cookies.json path.
    """
    udir = user_data_dir or str(DEFAULT_PROFILE_DIR)
    os.makedirs(udir, exist_ok=True)

    json_path = ensure_cookies_json(cookies_txt=cookies_txt)
    logger.info("yt-upload profile ready at %s (cookies: %s)", udir, json_path)
    return json_path
