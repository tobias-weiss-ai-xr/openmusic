#!/usr/bin/env python3
"""Check YouTube cookies validity for all three upload backends.

Usage:
    python scripts/check_cookies.py [--cookies cookies_kingofdub.txt]

Returns exit code 0 if at least one backend can authenticate.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("check_cookies")

BACKEND_TICK = "\033[92m\u2713\033[0m"
BACKEND_CROSS = "\033[91m\u2717\033[0m"


def check_youtube_up(cookies_txt: str) -> bool:
    """Test youtube-up backend (requests + SAPISIDHASH)."""
    try:
        from youtube_up import YTUploaderSession
    except ImportError:
        logger.info("  %s youtube-up not installed", BACKEND_CROSS)
        return False

    if not Path(cookies_txt).exists():
        logger.info("  %s cookies file not found: %s", BACKEND_CROSS, cookies_txt)
        return False

    try:
        session = YTUploaderSession.from_cookies_txt(cookies_txt)
        valid = session.has_valid_cookies()
        if valid:
            logger.info("  %s youtube-up: cookies VALID", BACKEND_TICK)
        else:
            logger.info("  %s youtube-up: cookies INVALID (server rejected)", BACKEND_CROSS)
        return valid
    except Exception as e:
        logger.info("  %s youtube-up: error: %s", BACKEND_CROSS, e)
        return False


def check_yt_upload(cookies_json: str) -> bool:
    """Test yt-upload backend (Playwright persistent context)."""
    try:
        import yt_upload  # noqa: F401
    except ImportError:
        logger.info("  %s yt-upload not installed", BACKEND_CROSS)
        return False

    if not Path(cookies_json).exists():
        logger.info("  %s cookies JSON not found: %s", BACKEND_CROSS, cookies_json)
        return False

    import asyncio
    from playwright.async_api import async_playwright
    import tempfile

    async def _test():
        pw = await async_playwright().start()
        profile = tempfile.mkdtemp(suffix="-yt-upload-check")
        with open(cookies_json) as f:
            cookies = json.load(f)

        context = await pw.chromium.launch_persistent_context(
            user_data_dir=profile,
            channel="chrome",
            headless=True,
            args=["--no-sandbox"],
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto("https://studio.youtube.com/upload", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        url = page.url
        valid = "accounts.google.com" not in url
        await context.close()
        await pw.stop()
        return valid

    try:
        valid = asyncio.run(_test())
        if valid:
            logger.info("  %s yt-upload (Playwright): authenticated", BACKEND_TICK)
        else:
            logger.info("  %s yt-upload (Playwright): redirected to login", BACKEND_CROSS)
        return valid
    except Exception as e:
        logger.info("  %s yt-upload (Playwright): error: %s", BACKEND_CROSS, e)
        return False


def check_oauth(client_secrets: str) -> bool:
    """Test YouTube Data API v3 OAuth."""
    from pathlib import Path

    secrets_path = Path(client_secrets)
    if not secrets_path.exists():
        logger.info("  %s OAuth: no client_secrets.json", BACKEND_CROSS)
        return False

    token_path = secrets_path.parent / "youtube_token.json"
    if not token_path.exists():
        logger.info("  %s OAuth: no youtube_token.json (needs interactive auth)", BACKEND_CROSS)
        return False

    try:
        import json
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        data = json.loads(token_path.read_text())
        creds = Credentials.from_authorized_user_info(data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            logger.info("  %s OAuth: token refreshed successfully", BACKEND_TICK)
            return True
        elif not creds.expired:
            logger.info("  %s OAuth: token valid until %s", BACKEND_TICK, data.get("expiry", "?"))
            return True
        else:
            logger.info("  %s OAuth: expired, no refresh token", BACKEND_CROSS)
            return False
    except Exception as e:
        logger.info("  %s OAuth: error: %s", BACKEND_CROSS, e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Check YouTube cookies validity")
    parser.add_argument("--cookies-txt", default="cookies_kingofdub.txt", help="Netscape cookies.txt")
    parser.add_argument("--cookies-json", default="cookies_kingofdub.json", help="Playwright cookies JSON")
    parser.add_argument("--client-secrets", default="client_secrets.json", help="OAuth client secrets")
    args = parser.parse_args()

    print("\nYouTube Upload Backend Check\n")

    oauth_ok = check_oauth(args.client_secrets)
    ytup_ok = check_youtube_up(args.cookies_txt)
    yt_upload_ok = check_yt_upload(args.cookies_json)

    print()
    if oauth_ok or ytup_ok or yt_upload_ok:
        print("At least one backend is ready. Ready to upload!")
        sys.exit(0)
    else:
        print("No backend is ready. You need fresh authentication.")
        print("  Option 1: Export fresh cookies from your browser to cookies_kingofdub.txt")
        print("  Option 2: Create a new OAuth client_secrets.json on Google Cloud Console")
        sys.exit(1)


if __name__ == "__main__":
    main()
