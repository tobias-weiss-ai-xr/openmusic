#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core", "src"))
import yt_upload.channel as yt_channel_module
import yt_upload.utils as yt_utils
from yt_upload.exceptions import YTError
from playwright.async_api import async_playwright


async def patched_start(self):
    self.playwright = await async_playwright().start()
    self.context = await self.playwright.chromium.launch_persistent_context(
        user_data_dir=self.user_data_dir,
        executable_path="/opt/google/chrome/chrome",
        headless=self.headless,
        proxy=self.proxy,
        user_agent=self.user_agent,
        args=[
            "--no-sandbox",
            "--allow-profiles-outside-user-dir",
            f"--profile-directory={self.profile}",
        ],
    )
    try:
        if self.yt_cookies and self.yt_cookies.cookies:
            await self.context.add_cookies(self.yt_cookies.model_dump())
    except Exception:
        pass

    page = await self.context.new_page()
    studio_page = yt_channel_module.YTStudioPage(page)
    language = await studio_page.get_language()
    if not (self.change_language_to_eng or language == "en"):
        raise YTError(
            f"YouTube language is '{language}', "
            "need to change YouTube language to English. "
            "Use either set change_language_to_eng = True "
            "or do it manually in YouTube settings."
        )
    elif self.change_language_to_eng and not language == "en":
        await studio_page.change_language_to_eng()
    await page.close()


async def patched_stop(self):
    try:
        yt_utils.remove_indexddb_cache_files(self.profile_path)
    except FileNotFoundError:
        pass
    await self.context.close()
    await self.playwright.stop()


yt_channel_module.Channel.start = patched_start
yt_channel_module.Channel.stop = patched_stop

from yt_upload import Channel


async def setup():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_dir = os.path.join(project_root, ".yt-profile")
    cookies_path = os.path.join(project_root, "cookies_kingofdub.json")

    channel = Channel(
        user_data_dir=profile_dir,
        google_profile="Default",
        cookies_path=cookies_path,
    )

    channel(
        youtube_channel="@kingofdub",
        headless=False,
        change_language_to_eng=True,
        enable_logging=False,
    )

    print("=" * 60)
    print("YouTube Studio will open in a browser window.")
    print("Please log in to your YouTube/Google account.")
    print("After successful login, you'll see YouTube Studio.")
    print("Then come back to this terminal and type: exit")
    print("=" * 60)

    try:
        async with channel as c:
            print("\n✅ Browser started. Waiting for you to log in...")
            await c.verification()

        print("\n✅ Login complete! Profile saved at:")
        print(f"   {profile_dir}")
        print(f"   Cookies saved at: {cookies_path}")
        print("\nFuture uploads can now run headless.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup())
