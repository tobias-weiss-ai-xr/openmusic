# OpenMusic — Roadmap

**Last updated**: 2026-07-16

---

## Project Status

OpenMusic is an AI-powered dub techno generation framework with a complete pipeline:
ACE-Step 1.5 generates raw audio (GPU), Tone.js effects process it (Node.js), and a
Python CLI orchestrates everything into seamless mixes with YouTube upload.

### What's Built

- **`openmusic generate`** — Generate mixes from CLI flags or YAML config
- **`openmusic publish`** — Generate + render MP4 + upload to YouTube in one shot
- **`openmusic release`** — Simplified one-shot: generate + render + upload
- **`openmusic publish-video`** — AI-generated imagery video pipeline (SDXL/SVG)
- **`openmusic upload`** — Upload existing MP4 with metadata
- **`openmusic short`** — Generate and batch-upload Shorts (batch, devops-generate)
- **`openmusic stream`** — Live streaming audio
- **`openmusic mcp`** — MCP orchestration (Ableton Live, ComfyUI status checks)
- **`openmusic auth-youtube`** — OAuth token generation with localhost callback
- **`openmusic validate`** — YAML config validation

### Tech Stack

| Layer              | Technology                                                    |
| ------------------ | ------------------------------------------------------------- |
| Audio generation   | ACE-Step 1.5 (DiT, 8 turbo steps, CUDA 12.8)                  |
| Effects processing | Tone.js via Node.js OfflineAudioContext                       |
| CLI                | Click (Python)                                                |
| YouTube upload     | YouTube Data API v3 + youtube-up fallback                     |
| Tests              | pytest (Python, ~705 tests) + vitest (TypeScript, ~177 tests) |

---

## Automation Roadmap

All code-level automation features in the [2026 release plan](.sisyphus/plans/2026-release-plan.md)
are now implemented:

| Item                                   | Status         | Notes                                                                                           |
| -------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------- |
| `openmusic release` command            | ✅ Complete    | One-shot generate + render + upload                                                             |
| Monthly batch short generation         | ✅ Complete    | `openmusic short batch`, `openmusic short devops-generate`                                      |
| Playlist management auto-create/append | ✅ Complete    | All three backends (API / youtube-up / yt-upload) support playlist creation and video appendage |
| Scheduling system (cron-based)         | ⏳ Not started | Operational concern; see below                                                                  |
| Analytics tracking                     | ⏳ Not started | YouTube Analytics API integration needed                                                        |

### Playlist Management — Implementation Details

- **YouTube API backend**: `YouTubeAPIUploader.add_to_playlist()` (lines 278-338) searches
  existing playlists via `playlists().list(mine=True)` and creates via `playlists().insert()`
  before appending via `playlistItems().insert()`.
- **youtube-up backend**: Uses `Playlist` objects with `create_if_title_doesnt_exist=True` (line 511).
- **yt-upload backend**: Passes `playlist` parameter to config (line 425).
- **CLI integration**: All upload commands (`publish`, `release`, `upload`, `publish-video`) accept `--playlist` / `--playlist-id`.

### OAuth Scope

Fixed in this commit: `auth-youtube` generates tokens with `youtube` scope (was `youtube.upload`),
matching the `YouTubeAPIUploader.SCOPES` constant. The narrower scope would cause playlist
operations to fail with 403 Forbidden.

---

## Pre-existing Test Failures

36 Python test failures exist in the `patterns` subsystem (unrelated to core functionality):

| File                                    | Failure Count | Root Cause                                                                    |
| --------------------------------------- | ------------- | ----------------------------------------------------------------------------- |
| `test_patterns/test_pattern_library.py` | 20            | `PatternLibrary.__init__()` requires `path` argument; test creates without it |
| `test_patterns/test_bayesian.py`        | 1             | Same `PatternLibrary` constructor issue                                       |
| `test_patterns/test_markov.py`          | 15            | Missing `PhaseTransitionMatrix.create_style` and undefined `TransitionStyle`  |

These tests reference classes whose APIs have changed during development. The `packages/patterns/`
TypeScript package has its own test suite that passes cleanly (85 tests).

---

## Future Work

### Short-term

- **Pattern library test fixes**: Update Python tests to match current `PatternLibrary`,
  `PhaseTransitionMatrix`, and `TransitionStyle` APIs.
- **Dependency audit**: Several optional dependency groups (`acestep`, `dsp`, `video`, `artwork`)
  could benefit from explicit extras listing.

### Medium-term

- **Scheduling system**: Cron-based overnight mix generation with Telegram/Discord notifications.
  Design: `openmusic schedule --cron "0 2 * * 5" --command "generate --length 2h"` with output
  to a scheduled YouTube premiere.
- **Analytics tracking**: YouTube Analytics API v3 integration for per-content-type view/sub tracking.
  Design: `openmusic analytics` command with weekly summary reports.

### Long-term

- **CI/CD pipeline**: GitHub Actions with GPU runner for automated mix generation.
- **Content performance dashboard**: Web UI for tracking shorts vs. full-mix performance.
- **Multi-channel support**: Publish to multiple YouTube channels from one config.
