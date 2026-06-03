#!/usr/bin/env python3
"""Upload 365 shorts via YouTube Data API v3 with OAuth."""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

SHORTS_DIR = Path("/tmp/openmusic_365")
TRACKER_FILE = PROJECT_DIR / "shorts_tracker.csv"
TOKEN_FILE = PROJECT_DIR / "youtube_token.json"
CLIENT_SECRETS_FILE = PROJECT_DIR / "client_secrets.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner",
]

_G = {"no_interactive": False}

CHUNK_SIZE = 1024 * 1024
UPLOAD_DELAY = 10
MAX_RETRIES = 3
CATEGORY_ID = "10"


def get_credentials(force_reauth=False):
    creds = None
    if not force_reauth and TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            creds = Credentials.from_authorized_user_info(data, SCOPES)
        except (json.JSONDecodeError, ValueError, KeyError):
            creds = None

    if creds and creds.expired and creds.refresh_token:
        print("  Token expired, refreshing...")
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
            print("  Token refreshed and saved")
            return creds
        except Exception as e:
            print(f"  Token refresh failed: {e}")
            creds = None

    if creds and creds.valid:
        exp = creds.expiry.isoformat() if creds.expiry else "unknown"
        print(f"  Using existing token (expires: {exp})")
        return creds

    if not CLIENT_SECRETS_FILE.exists():
        print()
        print("=" * 70)
        print("  NO OAuth CLIENT SECRETS FOUND")
        print("=" * 70)
        print()
        print("  Step 1: Go to https://console.cloud.google.com/apis/credentials")
        print("  Step 2: Create OAuth client ID -> 'Desktop application'")
        print("  Step 3: Download the JSON file")
        print("  Step 4: Save it as 'client_secrets.json' in project root")
        print()
        print(f"  Expected: {CLIENT_SECRETS_FILE}")
        print()
        sys.exit(1)

    print()
    print("=" * 70)
    print("  FIRST-TIME AUTHENTICATION")
    print("=" * 70)
    print()
    print("  A browser window will open. Log into the Google account")
    print("  that owns the @kingofdub YouTube channel.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE), SCOPES
    )

    if not _G.get("no_interactive"):
        try:
            creds = flow.run_local_server(
                port=8080,
                authorization_prompt_message="",
                success_message="Auth successful! You can close this window.",
                open_browser=True,
            )
            TOKEN_FILE.write_text(creds.to_json())
            print(f"  Token saved to {TOKEN_FILE}")
            return creds
        except Exception as e:
            print(f"  Browser OAuth failed: {e}")
            print()

    print("  Console-based OAuth (no browser needed):")
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    print(f"\n  {'=' * 60}")
    print("  Visit this URL in your browser and log in:")
    print(f"  {'=' * 60}")
    print(f"\n  {auth_url}\n")
    print("  After authorizing, you'll get a code in the redirect URL.")
    print("  Paste the FULL redirect URL or just the code below.")
    code = input("  Authorization code: ").strip()
    if not code:
        print("  No code provided. Exiting.")
        sys.exit(1)
    flow.fetch_token(code=code)
    creds = flow.credentials
    TOKEN_FILE.write_text(creds.to_json())
    print(f"  Token saved to {TOKEN_FILE}")
    return creds


def get_pending_shorts():
    if not TRACKER_FILE.exists():
        print(f"  Tracker not found: {TRACKER_FILE}")
        return []

    pending = []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = int(row["day"])
            video_id = row.get("video_id", "").strip()
            is_uploaded = (
                day <= 10
                or (video_id and not video_id.startswith("local_") and video_id != "unknown")
            )
            if is_uploaded:
                continue
            mp4_path = SHORTS_DIR / f"short_day{day}.mp4"
            if mp4_path.exists():
                pending.append({
                    "day": day,
                    "file": str(mp4_path),
                    "publish_date": row.get("publish_date", ""),
                    "title": f"King of Dub \u2014 Day {day}",
                })
    return pending


def update_tracker(day, video_id):
    rows = []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or ["day", "video_id", "publish_date", "timestamp"])
        for fn in ["uploaded_at"]:
            if fn not in fieldnames:
                fieldnames.append(fn)
        for row in reader:
            if int(row["day"]) == day:
                row["video_id"] = video_id
                row["uploaded_at"] = datetime.now().isoformat()
            rows.append(row)
    with open(TRACKER_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upload_video(youtube, video_path, title, description, tags,
                 privacy_status="public", publish_at=None):
    if not os.path.exists(video_path):
        print(f"    File not found: {video_path}")
        return None

    size_mb = os.path.getsize(video_path) / 1024 / 1024
    print(f"    File: {os.path.basename(video_path)} ({size_mb:.1f} MB)")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(video_path, chunksize=CHUNK_SIZE, resumable=True)
    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = request.execute()
            if response and response.get("id"):
                return response["id"]
        except HttpError as e:
            s = str(e)
            if "quotaExceeded" in s:
                wait = 60 * (attempt + 1)
                print(f"    Quota exceeded, waiting {wait}s...")
                time.sleep(wait)
                continue
            elif "publishAt" in s or "scheduling" in s.lower():
                print("    Scheduling unavailable, retrying as unlisted...")
                body["status"].pop("publishAt", None)
                body["status"]["privacyStatus"] = "unlisted"
                request = youtube.videos().insert(
                    part=",".join(body.keys()), body=body, media_body=media
                )
                continue
            else:
                print(f"    Upload failed (attempt {attempt+1}): {s[:200]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(10 * (attempt + 1))
                    continue
                return None
        except Exception as e:
            print(f"    Unexpected error (attempt {attempt+1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(10)
                continue
            return None
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Upload 365 shorts via YouTube Data API v3 OAuth"
    )
    parser.add_argument("--start-day", type=int, default=11)
    parser.add_argument("--end-day", type=int, default=365)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reauth", action="store_true")
    parser.add_argument("--no-interactive", action="store_true")
    parser.add_argument("--delay", type=int, default=UPLOAD_DELAY)
    args = parser.parse_args()

    print()
    print("KING OF DUB - 365 SHORTS UPLOADER")
    print("YouTube Data API v3 + OAuth 2.0")
    print()

    print("Step 1: Scanning for pending shorts...")
    all_pending = get_pending_shorts()
    pending = [v for v in all_pending if args.start_day <= v["day"] <= args.end_day]
    if not pending:
        print(f"  No pending shorts for days {args.start_day}-{args.end_day}.")
        return

    pending.sort(key=lambda v: v["day"])
    total_gb = sum(os.path.getsize(v["file"]) for v in pending if os.path.exists(v["file"])) / 1024**3
    est_min = len(pending) * args.delay // 60
    print(f"  Found {len(pending)} shorts ({args.start_day}-{args.end_day})")
    print(f"  Total: {total_gb:.1f} GB, ~{est_min} min at {args.delay}s intervals")
    print()

    if args.dry_run:
        print("DRY RUN - pending shorts:")
        for v in pending:
            mb = os.path.getsize(v["file"]) / 1024 / 1024
            print(f"  Day {v['day']:3d} | {mb:.0f} MB | {v['title']}")
        print(f"\nTotal: {len(pending)} ({total_gb:.1f} GB)")
        return

    print("Step 2: Authenticating...")
    print(f"  Token: {TOKEN_FILE}")
    print(f"  Secrets: {CLIENT_SECRETS_FILE}")
    _G["no_interactive"] = args.no_interactive
    creds = get_credentials(force_reauth=args.reauth)
    print()

    print("Step 3: Connecting to YouTube API...")
    try:
        youtube = build("youtube", "v3", credentials=creds)
        channels = youtube.channels().list(part="snippet", mine=True).execute()
        cn = channels["items"][0]["snippet"]["title"]
        ci = channels["items"][0]["id"]
        print(f"  Connected: {cn} ({ci})")
    except HttpError as e:
        print(f"  API connection failed: {e}")
        print()
        print("  Enable YouTube Data API at:")
        print("  https://console.cloud.google.com/apis/library/youtube.googleapis.com")
        sys.exit(1)
    print()

    print("Step 4: Uploading...\n")
    success = fail = 0

    for i, video in enumerate(pending):
        day = video["day"]
        title = video["title"]
        file_path = video["file"]
        publish_date = video.get("publish_date", "")

        description = (
            f"King of Dub \u2014 Day {day}/365\n"
            f"Scheduled: {publish_date}\n\n"
            f"Deep, hypnotic dub techno generated with AI.\n\n"
            f"Generated by OpenMusic\n"
            f"github.com/tobias-weiss-ai-xr/openmusic\n\n"
            f"#dubtechno #kingofdub #electronicmusic #dub #techno"
        )

        privacy = "public"
        publish_at = None
        if publish_date:
            try:
                pd = datetime.strptime(publish_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if pd > datetime.now(timezone.utc):
                    publish_at = publish_date + "T12:00:00Z"
                    privacy = "private"
            except ValueError:
                pass

        print(f"  [{i+1}/{len(pending)}] Day {day}: {title}")
        sched = f"scheduled={publish_at}" if publish_at else "immediate"
        print(f"    {sched} | privacy={privacy}")

        if not os.path.exists(file_path):
            print("    File missing, skipping")
            continue

        video_id = upload_video(
            youtube, file_path, title, description,
            tags=["dubtechno", "kingofdub", "electronicmusic", "dub", "techno"],
            privacy_status=privacy, publish_at=publish_at,
        )

        if video_id:
            print(f"    uploaded: https://youtube.com/watch?v={video_id}")
            update_tracker(day, video_id)
            success += 1
        else:
            print(f"    FAILED day {day}")
            fail += 1
            print("\n  Stopping. Resume with --start-day.")
            break

        if i < len(pending) - 1:
            time.sleep(args.delay)

    print()
    print("=" * 60)
    print(f"  Done: {success} uploaded, {fail} failed")
    print("=" * 60)
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
