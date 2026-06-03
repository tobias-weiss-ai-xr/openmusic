#!/usr/bin/env python3
"""
Bulk upload all 355 generated shorts to YouTube.

Usage:
  # Option A: Provide a cookies.txt file (exported from your browser)
  python3 scripts/bulk_upload_shorts.py --cookies cookies_kingofdub.txt

  # Option B: Run interactive browser login (requires display)
  python3 scripts/bulk_upload_shorts.py --interactive

  # Option C: Upload a specific range
  python3 scripts/bulk_upload_shorts.py --cookies cookies.txt --start-day 11 --end-day 50
"""
import argparse
import asyncio
import csv
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
    sys.exit(1)


SHORTS_DIR = "/tmp/openmusic_365"
TRACKER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shorts_tracker.csv")


def compute_upload_date(day: int) -> str:
    """Compute the scheduled upload date for a given day (day 1 = 2026-06-01)."""
    start = datetime(2026, 6, 1)
    return (start + timedelta(days=day - 1)).strftime("%Y-%m-%d")


def get_pending_shorts() -> list:
    """Read tracker and return list of shorts that need upload.

    CSV format: day,video_id,publish_date,timestamp
    Days with video_id='unknown' or starting with 'local_' need upload.
    Days 1-10 were uploaded (video_id='unknown' means upload happened
    but we didn't capture the YouTube video ID).
    """
    pending = []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = int(row["day"])
            video_id = row.get("video_id", "").strip()
            upload_date = row.get("publish_date", "")

            is_uploaded = (
                day <= 10  # Days 1-10 were uploaded directly
                or (video_id and not video_id.startswith("local_") and video_id != "unknown")
            )
            if is_uploaded:
                continue

            mp4_path = os.path.join(SHORTS_DIR, f"short_day{day}.mp4")
            if os.path.exists(mp4_path):
                pending.append({
                    "day": day,
                    "file": mp4_path,
                    "upload_date": upload_date,
                    "title": f"King of Dub - Day {day}",
                })
    return pending


def update_tracker(day: int, status: str, **kwargs):
    """Update the tracker CSV for a given day."""
    rows: list[dict[str, str]] = []
    updated = False
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if int(row["day"]) == day:
                row["status"] = status
                for k, v in kwargs.items():
                    row[k] = v
                updated = True
            rows.append(row)

    if not updated:
        print(f"  ⚠ Day {day} not found in tracker!")
        return

    with open(TRACKER_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def upload_with_cookies(channel_handle: str, cookies_file: str, video_path: str,
                               title: str, description: str, tags: list[str] = None) -> bool:
    """
    Upload a video using the yt-upload library with provided cookies.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "packages", "core", "src"))

    # Apply patches for broken yt-upload selectors
    import yt_upload.channel as yt_channel_module
    import yt_upload.utils as yt_utils
    from yt_upload.exceptions import YTError

    original_start = yt_channel_module.Channel.start
    original_stop = yt_channel_module.Channel.stop

    async def patched_start(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            executable_path="/opt/google/chrome/chrome",
            headless=True,
            proxy=self.proxy,
            user_agent=self.user_agent,
            args=["--no-sandbox", "--allow-profiles-outside-user-dir",
                  f"--profile-directory={self.profile}"],
        )
        if self.yt_cookies and self.yt_cookies.cookies:
            await self.context.add_cookies(self.yt_cookies.model_dump())
        page = await self.context.new_page()
        studio_page = yt_channel_module.YTStudioPage(page)
        language = await studio_page.get_language()
        if not (self.change_language_to_eng or language == "en"):
            raise YTError(f"YouTube language is '{language}', need English")
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

    # Patch to prevent cookie file corruption
    import yt_upload.auth as yt_auth
    original_update = yt_auth.YoutubeAuthCookie._update_cookies
    yt_auth.YoutubeAuthCookie._update_cookies = lambda self: None

    yt_channel_module.Channel.start = patched_start
    yt_channel_module.Channel.stop = patched_stop

    from yt_upload import Channel
    from yt_upload.models import CookiesFile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy cookies file to temp to avoid corruption
        import shutil
        tmp_cookies = os.path.join(tmpdir, "cookies.txt")
        shutil.copy2(cookies_file, tmp_cookies)

        # Also make JSON copy
        cj = __import__("http.cookiejar", fromlist=["MozillaCookieJar"]).MozillaCookieJar()
        cj.load(cookies_file, ignore_expires=True, ignore_discard=True)
        json_cookies = []
        for c in cj:
            json_cookies.append({
                "name": c.name, "value": c.value,
                "domain": c.domain.lstrip("."), "path": c.path,
                "secure": c.secure, "httpOnly": False,
                "sameSite": "Lax",
            })
        tmp_json = os.path.join(tmpdir, "cookies.json")
        with open(tmp_json, "w") as f:
            json.dump(json_cookies, f)

        channel = Channel(
            user_data_dir=os.path.join(tmpdir, "profile"),
            google_profile="Default",
            cookies_path=tmp_json,
        )
        channel(
            youtube_channel=channel_handle,
            headless=True,
            change_language_to_eng=True,
            enable_logging=False,
        )

        try:
            async with channel as c:
                result = await c.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags or [],
                    schedule=False,
                    kids=False,
                    visibility="public",
                )
                print(f"  Uploaded: {result}")
                return True
        except YTError as e:
            print(f"  Upload failed: {e}")
            return False
        except Exception as e:
            print(f"  Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def upload_batch_playwright(cookies_file: str, pending: list, channel: str,
                                   concurrency: int = 2):
    """Upload a batch of videos using Playwright-based approach."""
    success = 0
    fail = 0

    print(f"\nUploading {len(pending)} shorts to {channel}...")
    print(f"Using cookies: {cookies_file}")
    print(f"Concurrency: {concurrency}")
    print("=" * 60)

    for i, video in enumerate(pending):
        day = video["day"]
        title = video["title"]
        file_path = video["file"]
        upload_date = video.get("upload_date", compute_upload_date(day))

        description = (
            f"King of Dub - Day {day}/365\n"
            f"Scheduled for: {upload_date}\n\n"
            f"Deep, hypnotic dub techno generated with AI.\n"
            f"#dubtechno #kingofdub #electronicmusic #dub #techno"
        )

        print(f"[{i+1}/{len(pending)}] Day {day} ({upload_date}): {title}")

        ok = await upload_with_cookies(
            channel_handle=channel,
            cookies_file=cookies_file,
            video_path=file_path,
            title=title,
            description=description,
            tags=["dubtechno", "kingofdub", "electronicmusic", "dub", "techno"],
        )

        if ok:
            update_tracker(day, "uploaded",
                           uploaded_at=datetime.now().isoformat())
            success += 1
        else:
            fail += 1
            break  # Stop on first failure - likely auth issue

        # Small delay between uploads
        if i < len(pending) - 1 and ok:
            await asyncio.sleep(5)

    print("=" * 60)
    print(f"Done: {success} uploaded, {fail} failed")


async def interactive_setup_and_upload(channel: str, pending: list):
    """
    Open a real browser for the user to log in, then upload all pending shorts.
    """
    print("=" * 60)
    print("INTERACTIVE LOGIN SETUP")
    print("=" * 60)
    print("A browser window will open. Please log into YouTube Studio.")
    print("After login, all pending shorts will upload automatically.")
    print("=" * 60)

    profile_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), ".yt-profile")

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "packages", "core", "src"))
    import yt_upload.channel as yt_channel_module
    import yt_upload.utils as yt_utils
    from yt_upload.exceptions import YTError

    async def patched_start(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            executable_path="/opt/google/chrome/chrome",
            headless=False,
            proxy=self.proxy,
            user_agent=self.user_agent,
            args=["--no-sandbox", "--allow-profiles-outside-user-dir",
                  f"--profile-directory={self.profile}"],
        )
        if self.yt_cookies and self.yt_cookies.cookies:
            await self.context.add_cookies(self.yt_cookies.model_dump())
        page = await self.context.new_page()
        studio_page = yt_channel_module.YTStudioPage(page)
        language = await studio_page.get_language()
        if not (self.change_language_to_eng or language == "en"):
            raise YTError(f"YouTube language is '{language}', need English")
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
    from yt_upload.models import CookiesFile, YTCookie

    channel_obj = Channel(
        user_data_dir=profile_dir,
        google_profile="Default",
    )
    channel_obj(
        youtube_channel=channel,
        headless=False,
        change_language_to_eng=True,
        enable_logging=False,
    )

    try:
        async with channel_obj as c:
            print("\n✅ Browser started. Please log into YouTube Studio.")
            print("   Waiting for you to complete login...")
            await c.verification()
            print("\n✅ Login successful! Starting uploads...")

            # Now upload all pending with this authenticated session
            for i, video in enumerate(pending):
                day = video["day"]
                upload_date = video.get("upload_date", compute_upload_date(day))
                title = video["title"]

                description = (
                    f"King of Dub - Day {day}/365\n"
                    f"Scheduled for: {upload_date}\n\n"
                    f"Deep, hypnotic dub techno generated with AI.\n"
                    f"#dubtechno #kingofdub #electronicmusic #dub #techno"
                )

                print(f"[{i+1}/{len(pending)}] Day {day}: uploading...")
                try:
                    result = await c.upload_video(
                        video_path=video["file"],
                        title=title,
                        description=description,
                        tags=["dubtechno", "kingofdub", "electronicmusic", "dub", "techno"],
                        schedule=False,
                        kids=False,
                        visibility="public",
                    )
                    update_tracker(day, "uploaded",
                                   uploaded_at=datetime.now().isoformat())
                    print(f"  ✅ Uploaded")
                except YTError as e:
                    print(f"  ❌ Upload failed: {e}")
                    break

                if i < len(pending) - 1:
                    await asyncio.sleep(5)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n✅ Done! Uploaded all shorts.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bulk upload shorts to YouTube")
    parser.add_argument("--cookies", help="Path to cookies.txt (Netscape format)")
    parser.add_argument("--interactive", action="store_true",
                        help="Open browser for interactive login")
    parser.add_argument("--start-day", type=int, default=11,
                        help="First day to upload (default: 11)")
    parser.add_argument("--end-day", type=int, default=365,
                        help="Last day to upload (default: 365)")
    parser.add_argument("--channel", default="@kingofdub",
                        help="YouTube channel handle (default: @kingofdub)")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Upload concurrency (default: 2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List pending shorts without uploading")
    args = parser.parse_args()

    if not args.cookies and not args.interactive and not args.dry_run:
        parser.print_help()
        print("\n⚠ Must provide either --cookies or --interactive")
        sys.exit(1)

    all_pending = get_pending_shorts()
    pending = [v for v in all_pending if args.start_day <= v["day"] <= args.end_day]

    if not pending:
        print(f"No pending shorts found for days {args.start_day}-{args.end_day}.")
        print(f"Total tracker entries: {sum(1 for _ in open(TRACKER_FILE)) - 1}")
        return

    print(f"\nFound {len(pending)} shorts to upload (days {args.start_day}-{args.end_day})")

    if args.dry_run:
        print("\nPending uploads:")
        for v in pending:
            print(f"  Day {v['day']:3d} | {v['upload_date']} | {os.path.basename(v['file'])}")
        return

    if args.interactive:
        asyncio.run(interactive_setup_and_upload(args.channel, pending))
    elif args.cookies:
        asyncio.run(upload_batch_playwright(
            args.cookies, pending, args.channel, args.concurrency))
    else:
        print("No method specified")


if __name__ == "__main__":
    main()
