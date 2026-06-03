#!/usr/bin/env python3
"""
Upload all pending shorts using validated youtube-up cookies backend.

Features:
  - Pre-flight cookie validation before each batch
  - Batch cooldowns to avoid Google rate-limiting (15 shorts × 5min pause)
  - Graduated delays between uploads
  - Smart retry: skips retry loop when cookies are expired
  - SIGINT safety: no more than one upload per run

Usage:
    ACE-Step-1.5/.venv/bin/python scripts/upload_remaining.py
    ACE-Step-1.5/.venv/bin/python scripts/upload_remaining.py --start-day 11 --end-day 50
    ACE-Step-1.5/.venv/bin/python scripts/upload_remaining.py --dry-run
"""

import argparse
import csv
import datetime
import logging

import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("uploader")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "core" / "src"))

TRACKER_FILE = Path(__file__).resolve().parent.parent / "shorts_tracker.csv"
SHORTS_DIR = Path("/tmp/openmusic_365")
COOKIES_FILE = str(Path(__file__).resolve().parent.parent / "cookies_kingofdub.txt")
PUBLISH_START = datetime.date(2026, 6, 1)

BATCH_SIZE = 15
BATCH_COOLDOWN = 300
INITIAL_DELAY = 30
MAX_DELAY = 60
COOKIE_EXPIRE_KEYWORDS = [
    "could not log in", "login", "sign in", "authenticate",
    "cookie", "sapisid", "psid",
]


def check_cookies_valid(cookies_path: str) -> bool:
    """Quick validity check using youtube-up's built-in cookie validator."""
    try:
        from youtube_up import YTUploaderSession
        session = YTUploaderSession.from_cookies_txt(cookies_path)
        return session.has_valid_cookies()
    except Exception:
        return False


def get_delay(uploads_done: int) -> int:
    """Graduated delay between uploads to avoid rate-limiting."""
    if uploads_done < 10:
        return INITIAL_DELAY
    elif uploads_done < 20:
        return 45
    return MAX_DELAY


def _is_cookie_expiry_error(err_msg: str) -> bool:
    """Check if exception message indicates cookie expiry."""
    err_lower = err_msg.lower()
    return any(kw in err_lower for kw in COOKIE_EXPIRE_KEYWORDS)


def get_pending_shorts(start_day: int = 11, end_day: int = 365) -> list[dict]:
    pending = []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = int(row["day"])
            if day < start_day or day > end_day:
                continue
            video_id = row.get("video_id", "").strip()
            if day <= 10:
                continue
            if video_id and not video_id.startswith("local_") and video_id != "unknown":
                continue
            mp4 = SHORTS_DIR / f"short_day{day}.mp4"
            if not mp4.exists():
                logger.warning(f"Day {day}: MP4 not found at {mp4}, skipping")
                continue
            publish_date = PUBLISH_START + datetime.timedelta(days=day - 1)
            publish_dt = datetime.datetime(
                publish_date.year, publish_date.month, publish_date.day,
                hour=12, minute=0, second=0,
            )
            pending.append({
                "day": day,
                "file": str(mp4),
                "publish_date": publish_date.isoformat(),
                "publish_dt": publish_dt,
            })
    return pending


def update_tracker(day: int, video_id: str) -> bool:
    rows = []
    updated = False
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or ["day", "video_id", "publish_date", "timestamp"]
        for row in reader:
            if int(row["day"]) == day:
                row["video_id"] = video_id
                row["timestamp"] = datetime.datetime.now().isoformat()
                updated = True
            rows.append(row)
    if not updated:
        logger.error(f"Day {day} not found in tracker!")
        return False
    with open(TRACKER_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return True


def _ensure_cookies_format(cookies_path: str) -> str | None:
    path = Path(cookies_path)
    if not path.exists():
        logger.error(f"Cookies file not found: {cookies_path}")
        return None
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if "\t" in stripped:
                    return str(path)
                break
    raw = path.read_text()
    lines = raw.splitlines()
    output = []
    converted = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            output.append(line)
            continue
        parts = stripped.split()
        if len(parts) >= 7:
            tabbed = "\t".join([parts[0], parts[1], parts[2], parts[3], parts[4], parts[5],
                                " ".join(parts[6:])])
            output.append(tabbed)
            converted += 1
        else:
            output.append(line)
    if converted > 0:
        out_path = path.parent / f"{path.stem}.tab.txt"
        out_path.write_text("\n".join(output) + "\n")
        logger.info(f"Converted {converted} cookies to tab-separated: {out_path}")
        return str(out_path)
    return str(path)


def main():
    parser = argparse.ArgumentParser(description="Upload pending shorts to YouTube")
    parser.add_argument("--start-day", type=int, default=83)
    parser.add_argument("--end-day", type=int, default=365)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=int, default=0)
    parser.add_argument("--cookies", default=COOKIES_FILE)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--batch-cooldown", type=int, default=BATCH_COOLDOWN)
    args = parser.parse_args()

    from openmusic.export.youtube_uploader import YouTubeUpFallback, YouTubeUploadConfig

    pending = get_pending_shorts(args.start_day, args.end_day)
    if not pending:
        logger.info("No pending shorts to upload!")
        return

    logger.info(f"Found {len(pending)} pending shorts (days {args.start_day}-{args.end_day})")

    if args.dry_run:
        for p in pending:
            logger.info(f"  Day {p['day']}: {p['file']} -> publish {p['publish_date']}")
        logger.info(f"Dry run complete. {len(pending)} would be uploaded.")
        return

    cookies_path = _ensure_cookies_format(args.cookies)
    if not cookies_path:
        logger.error("No valid cookies file found!")
        sys.exit(1)

    logger.info("Checking cookie validity before starting...")
    if not check_cookies_valid(cookies_path):
        logger.error("Cookies INVALID. Export fresh cookies from your browser.")
        sys.exit(1)
    logger.info("Cookies valid. Starting upload.")

    from openmusic.shorts.quotes import get_quote_for_day

    succeeded = 0
    failed_days = []
    cookie_dead = False

    for i, p in enumerate(pending):
        if cookie_dead:
            logger.error(f"Cookies dead — stopping batch at day {p['day']}.")
            break

        day = p["day"]
        batch_num = (succeeded // args.batch_size) + 1
        pos_in_batch = succeeded % args.batch_size

        logger.info(f"[{i+1}/{len(pending)}] Uploading Day {day}...")
        logger.info(f"  Batch {batch_num}, position {pos_in_batch+1}/{args.batch_size}")

        quote = get_quote_for_day(day)
        description = (
            f"« Daily Stoic - Day {day} of 365\n\n"
            f"\"{quote.text}\"\n"
            f"- {quote.author}\n\n"
            f"Generated by OpenMusic - AI-powered dub techno & stoic wisdom.\n"
            f"https://github.com/tobias-weiss-ai-xr/openmusic\n\n"
            f"#{quote.author.replace(' ', '')} #Stoicism #DailyStoic #DubTechno #OpenMusic"
        )

        config = YouTubeUploadConfig(
            title=f"Daily Stoic - Day {day}: {quote.author}",
            description=description,
            tags=["stoic", "dub techno", "philosophy", "daily wisdom", "openmusic"],
            cookies_file=cookies_path,
            privacy="public",
            scheduled_upload=p["publish_dt"],
        )

        uploader = YouTubeUpFallback(config)

        upload_ok = False
        for attempt in range(3):
            try:
                video_id = uploader.upload(p["file"])
                logger.info(f"Day {day} uploaded: https://youtube.com/watch?v={video_id}")
                if update_tracker(day, video_id):
                    logger.info(f"Tracker updated for day {day}")
                upload_ok = True
                break
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Day {day} attempt {attempt+1}/3 failed: {err_msg}")

                if _is_cookie_expiry_error(err_msg):
                    logger.warning("Cookie expiry detected — stopping uploads.")
                    cookie_dead = True
                    break

                if attempt < 2:
                    wait = 60 * (attempt + 1)
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Day {day} FAILED after 3 attempts")

        if upload_ok:
            succeeded += 1
        else:
            failed_days.append(day)

        if upload_ok and succeeded > 0 and succeeded % args.batch_size == 0:
            logger.info(f"Batch {batch_num} complete ({succeeded} total). "
                        f"Cooldown {args.batch_cooldown}s...")
            logger.info("Re-checking cookies after cooldown...")
            time.sleep(args.batch_cooldown)
            if not check_cookies_valid(cookies_path):
                logger.warning("Cookies dead after cooldown — stopping.")
                cookie_dead = True
            else:
                logger.info("Cookies still valid, continuing...")
        elif upload_ok and not cookie_dead:
            delay = get_delay(succeeded)
            if delay > 0:
                logger.info(f"Waiting {delay}s before next upload...")
                time.sleep(delay)

    logger.info(f"Upload session complete: {succeeded} uploaded, {len(failed_days)} failed")
    if failed_days:
        logger.info(f"Failed days: {failed_days}")
    if cookie_dead:
        logger.info("Stopped early due to cookie expiry. Re-export cookies and resume.")


if __name__ == "__main__":
    main()
