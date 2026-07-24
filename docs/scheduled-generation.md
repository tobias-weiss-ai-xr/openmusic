# Scheduled Generation Setup

OpenMusic supports fully automated mix generation on a recurring schedule.
This guide explains how to set it up using cron (Linux/macOS) or Task Scheduler (Windows).

## Prerequisites

- OpenMusic installed with ACE-Step 1.5 (see [Setup](../README.md#setup))
- `ffmpeg` installed and available in PATH
- (For YouTube uploads) Valid OAuth credentials or `cookies.txt`
- (For notifications) Webhook URL or SMTP credentials

## Quick Start

### 1. Create a Schedule Config

Start from the example config:

```bash
cp examples/schedule.yaml my_schedule.yaml
# Edit my_schedule.yaml with your desired parameters
```

Key fields in the config:

| Field         | Default    | Description                                 |
| ------------- | ---------- | ------------------------------------------- |
| `length`      | `1h`       | Mix duration (e.g. `30m`, `2h`, `45s`)      |
| `bpm`         | `125`      | Beats per minute                            |
| `key`         | `Dm`       | Musical key (minor keys: Dm, Am, Em, etc.)  |
| `output_path` | `mix.flac` | Output file path                            |
| `upload`      | —          | YouTube upload metadata (title, tags, etc.) |

### 2. Test the Pipeline

Run once to verify everything works:

```bash
# Just generate the mix (no upload)
python -m openmusic.cli.main generate --config my_schedule.yaml

# Full release pipeline (generate + render + upload)
python -m openmusic.cli.main release --config my_schedule.yaml
```

### 3. Set Up Cron (Linux/macOS)

Use the bundled shell script:

```bash
# Edit your crontab
crontab -e

# Add a line (example: daily at 6:00 UTC)
0 6 * * * cd /path/to/openmusic && ./scripts/schedule-mix.sh /path/to/my_schedule.yaml >> /var/log/openmusic/schedule.log 2>&1
```

The shell script automatically:

- Activates the correct Python venv
- Runs the `openmusic release` pipeline
- Logs output to `logs/schedule-YYYYMMDD-HHMMSS.log`
- Rotates logs (keeps last 20 runs)

#### Cron with Notifications

```bash
# Webhook on completion
OPENMUSIC_NOTIFY_WEBHOOK="https://hooks.slack.com/services/..." \
  ./scripts/schedule-mix.sh my_schedule.yaml

# Email on completion
OPENMUSIC_NOTIFY_EMAIL="you@example.com" \
  OPENMUSIC_SMTP_SERVER="smtp.gmail.com" \
  OPENMUSIC_SMTP_USERNAME="you@gmail.com" \
  OPENMUSIC_SMTP_PASSWORD="your-app-password" \
  ./scripts/schedule-mix.sh my_schedule.yaml

# Or combine both
OPENMUSIC_NOTIFY_WEBHOOK="..." \
OPENMUSIC_NOTIFY_EMAIL="you@example.com" \
  ./scripts/schedule-mix.sh my_schedule.yaml
```

### 4. Set Up Task Scheduler (Windows)

Create a batch file `run_scheduled_mix.bat`:

```batch
@echo off
cd C:\path\to\openmusic
call ACE-Step-1.5\.venv\Scripts\activate.bat
python -m openmusic.cli.main release --config my_schedule.yaml
```

Then create a scheduled task via Task Scheduler GUI or:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\run_scheduled_mix.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 6am
Register-ScheduledTask -TaskName "OpenMusic Daily Mix" -Action $action -Trigger $trigger
```

## Notification Configuration

### Webhook

The CLI sends a JSON POST to your webhook URL with this payload:

```json
{
  "status": "success",
  "title": "Dub Techno Mix | AI Generated",
  "output_path": "/path/to/mix.mp4",
  "video_id": "dQw4w9WgXcQ",
  "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_seconds": 3600.0
}
```

On failure, the payload includes an `error_message` field.

You can also pass `--notify-webhook-secret` for HMAC-SHA256 signed payloads
(the signature is sent in the `X-Signature-256` header).

### Email

Email notifications require SMTP credentials. Set these environment variables:

| Variable                  | Description                                     |
| ------------------------- | ----------------------------------------------- |
| `OPENMUSIC_EMAIL_FROM`    | Sender address (default: `openmusic@localhost`) |
| `OPENMUSIC_SMTP_SERVER`   | SMTP host (e.g. `smtp.gmail.com`)               |
| `OPENMUSIC_SMTP_PORT`     | SMTP port (default: `587`)                      |
| `OPENMUSIC_SMTP_USERNAME` | SMTP login username                             |
| `OPENMUSIC_SMTP_PASSWORD` | SMTP login password or app token                |

### Notification Flags

When running `openmusic release` directly:

```
--notify-webhook URL               Webhook URL for JSON POST
--notify-webhook-secret SECRET     HMAC-SHA256 signing secret
--notify-email EMAIL               Recipient email address(es)
```

When running `openmusic schedule add`:

```
--notify-webhook URL               Webhook URL for JSON POST
--notify-webhook-secret SECRET     HMAC-SHA256 signing secret
--notify-email EMAIL               Recipient email address(es)
--telegram-token TOKEN             Telegram bot token
--telegram-chat CHAT_ID            Telegram chat ID
--discord-webhook URL              Discord webhook URL
--notify-on EVENTS                 Events to notify on (default: success,failure)
```

For `schedule add`, SMTP credentials for email are read from the same
environment variables (`OPENMUSIC_EMAIL_FROM`, `OPENMUSIC_SMTP_SERVER`, etc.).

## Logging

The schedule shell script logs to `logs/schedule-YYYYMMDD-HHMMSS.log`.
The 20 most recent logs are automatically preserved; older ones are pruned.

To check the last run:

```bash
ls -lt logs/schedule-*.log | head -5
tail -50 "$(ls -t logs/schedule-*.log | head -1)"
```

## YouTube Scheduled Publishing

Use the `--schedule` flag to set a YouTube premiere time:

```bash
python -m openmusic.cli.main release \
  --config my_schedule.yaml \
  --schedule 2026-07-21T12:00:00Z
```

Or set it in your YAML config:

```yaml
upload:
  schedule: '2026-07-21T12:00:00Z'
```

## 365-Day Shorts Pipeline

For automated short-form content, see `scripts/schedule_365_shorts.py`:

```bash
python scripts/schedule_365_shorts.py --start-day 1 --end-day 365
```

This generates, renders, and uploads one short per day with staggered
publish dates.
