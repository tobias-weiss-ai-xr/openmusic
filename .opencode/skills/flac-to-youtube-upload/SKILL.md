---
name: flac-to-youtube-upload
description: Use when converting a FLAC audio file to YouTube video with cover art and upload, or when generating a new OpenMusic mix for YouTube upload.
---

# FLAC to YouTube Upload

## Overview

Convert FLAC audio files to YouTube-ready videos with static cover images or slideshow, then upload via YouTube Data API v3.

**Existing command:** `openmusic publish` handles the full workflow end-to-end. Use this skill to understand what's happening underneath or to customize the workflow.

## When to Use

✅ **Use when:**
- User has a FLAC file and wants to upload it to YouTube
- User wants to publish a new OpenMusic mix to YouTube
- Need to understand the publish command's internal workflow
- Customizing video rendering (cover, slideshow, theme)
- Troubleshooting ffmpeg or YouTube upload issues

❌ **Don't use when:**
- Simple one-time upload - use `openmusic publish` directly
- User just wants to generate a mix (without upload)
- Working with non-YouTube platforms

## Workflow (3-Step Pipeline)

```
FLAC Audio
    │
    ├─→ Step 1: Generate Mix (if needed)
    │       └─→ MixOrchestrator or --use-bayesian-markov
    │
    ├─→ Step 2: Render MP4 with FFMPEG
    │       ├─→ Mode A: Auto-generated Cover Theme
    │       ├─→ Mode B: Custom Cover Image
    │       └─→ Mode C: Slideshow Mode
    │
    └─→ Step 3: Upload to YouTube
            ├─→ Method A: OAuth Token (preferred)
            └─→ Method B: Browser Cookies (fallback)
```

### Step 1: Generate Mix (if needed)

If you already have a FLAC file, skip this step. Otherwise:

```bash
openmusic generate --length 2h --bpm 125 --key Dm --output mix.flac
```

Or with Bayesian Markov pattern system (~80% faster):

```bash
openmusic generate --length 2h --use-bayesian-markov --output mix.flac
```

**Output:** `mix.flac` (374MB for 2h)

### Step 2: Render MP4 (FFMPEG)

Choose **one** of these rendering modes:

#### Mode A: Auto-generated Cover Theme

```bash
# Generate SVG→PNG cover, then loop it over audio
ffmpeg-loop-cover \
  --input mix.flac \
  --output mix.mp4 \
  --theme dark_industrial \
  --title "My Mix" \
  --artist "OpenMusic"
```

Underlying FFMPEG (lines 587-618 in main.py):

```bash
# Convert SVG to PNG
rsvg-convert -f png -o cover.png cover.svg

# Loop cover image over audio
ffmpeg -loop 1 -i cover.png \
       -i mix.flac \
       -c:v libx264 -preset ultrafast -tune stillimage \
       -c:a aac -b:a 256k -shortest -movflags +faststart \
       mix.mp4
```

**Features:** Auto-generated themes (dark_industrial, neon_cyberpunk, minimal_warm)

#### Mode B: Custom Cover Image

```bash
ffmpeg -loop 1 -i my_cover.jpg \
       -i mix.flac \
       -c:v libx264 -preset ultrafast -tune stillimage \
       -c:a aac -b:a 256k -shortest -movflags +faststart \
       mix.mp4
```

**Format:** JPG/PNG, recommended 1920×1080 or higher

#### Mode C: Slideshow Mode

For cycling through multiple images:

```bash
# Create playlist file (images.txt)
echo "file 'image1.jpg'" >> images.txt
echo "file 'image2.jpg'" >> images.txt
echo "file 'image3.jpg'" >> images.txt

# Concat with audio
ffmpeg -f concat -safe 0 -i images.txt \
       -i mix.flac \
       -filter_complex "[0:v]fps=1/5[v];[v][1:a]concat=n=1:v=1:a=1[outv][outa]" \
       -map "[outv]" -map "[outa]" \
       -c:v libx264 -preset ultrafast \
       -c:a aac -b:a 256k \
       mix.mp4
```

**Pattern:** `fps=1/5` = 5 seconds per image

### Step 3: Upload to YouTube

**Method A: OAuth Token (Preferred)**

```bash
# First-time auth (generates refresh token)
openmusic auth-youtube

# Upload with OAuth
youtube-up video \
  --cookies_file youtube_token.json \
  --title "My Dub Techno Mix | 2 Hours" \
  --description "AI-powered dub techno mix. https://graphwiz.ai" \
  --tags dub,techno,ai,music \
  --category 10 \
  mix.mp4
```

**OAuth flow:**
1. Desktop app flow (no PKCE)
2. Generates `youtube_token.json` with refresh_token
3. Auto-refreshes expired tokens
4. Client ID: `718607879176-86p0sb6pumjgtbgvj4g3oo71ma79dr2k`

**Method B: Browser Cookies (Fallback)**

```bash
youtube-up video \
  --cookies_file cookies_kingofdub.txt \
  --title "My Mix" \
  --description "Description..." \
  --tags tag1,tag2,tag3 \
  mix.mp4
```

**Limitation:** Cookies expire, need re-export from browser

## Full Publish Command (All-in-One)

```bash
openmusic publish \
  --length 2h \
  --bpm 125 \
  --key Dm \
  --output mix.flac \
  --cover-theme dark_industrial \
  --title "Fat Bass Heavy Dub Techno Mix | 2 Hours" \
  --description "Deep dub techno mix with fat basslines. https://graphwiz.ai" \
  --privacy unlisted \
  --client-secrets client_secrets.json
```

**What it does internally:**
1. Generates mix via MixOrchestrator
2. Renders MP4 with ffmpeg auto-generated cover
3. Uploads to YouTube via OAuth

## Common Settings

| Setting | Recommended Value | Notes |
|---------|-------------------|-------|
| Video codec | libx264 | YouTube standard |
| Preset | ultrafast | Faster rendering |
| Tune | stillimage | Optimized for static cover |
| Audio codec | aac | iPhone/Android compatible |
| Audio bitrate | 256k | Good quality, reasonable size |
| Movflags | +faststart | Web-optimized (MVP) |
| Privacy | unlisted | Review before public |
| Category | 10 (Music) | YouTube category ID |

## Quick Reference: FFMPEG Patterns

**Loop cover over audio:**
```bash
ffmpeg -loop 1 -i cover.png \
       -i audio.flac \
       -c:v libx264 -preset ultrafast -tune stillimage \
       -c:a aac -b:a 256k -shortest -movflags +faststart \
       output.mp4
```

**Slideshow with concat demuxer:**
```bash
# images.txt format
file 'img1.jpg'
file 'img2.jpg'
file 'img3.jpg'

ffmpeg -f concat -safe 0 -i images.txt \
       -i audio.flac \
       -filter_complex "[0:v]fps=1/5[v];[v][1:a]concat=n=1:v=1:a=1[outv][outa]" \
       -map "[outv]" -map "[outa]" \
       -c:v libx264 -preset ultrafast \
       -c:a aac -b:a 256k \
       output.mp4
```

**YouTube upload (OAuth):**
```bash
youtube-up video \
  --cookies_file youtube_token.json \
  --title "Title" \
  --description "Description with link https://graphwiz.ai" \
  --tags tag1,tag2 \
  --category 10 \
  mix.mp4
```

## Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/openmusic/cli/main.py` | Publish command | 630-760 |
| `src/openmusic/export/youtube_uploader.py` | YouTube API wrapper | All |
| `src/openmusic/orchestrator/mix.py` | MixOrchestrator | All |
| `ffmpeg` (system) | Video rendering | N/A |

## Common Mistakes

❌ **Wrong preset:** Using `medium` or `slow` presets takes forever. `ultrafast` recommended for cover art videos.

❌ **Missing +faststart:** Video won't play smoothly on web browsers.

❌ **Audio format:** YouTube rejects FLAC directly. Must be AAC or MP3.

❌ **Category ID wrong:** Use numeric IDs (10=Music), not names.

❌ **Privacy public first:** Always `unlisted` for review, then change to `public`.

❌ **No website link:** All OpenMusic videos should link to https://graphwiz.ai

## Troubleshooting

**FFMPEG hangs or slow:**
- Check input audio format (FLAC OK)
- Verify `-shortest` flag is set
- Lower resolution if needed

**YouTube upload fails 401:**
- OAuth token expired → regenerate with `openmusic auth-youtube`
- Refresh token missing → re-auth

**Video rejected:**
- Check duration (< 12 hours)
- Verify audio codec is AAC
- Category ID must be numeric

**Cookies not working:**
- Export fresh from Chrome (developer tools)
- Use cookies_kingofdub.txt format
- OAuth preferred for long-term use

## Real-World Impact

Generated 2h mix (374MB FLAC) → 190MB MP4 → YouTube upload in under 30 minutes:
- FFMPEG rendering: 2-3 minutes
- YouTube upload: 5-10 minutes (20-30 Mbps)
- End result: Professional video with cover art

Reference: https://youtube.com/watch?v=NbvV4qQzELk
