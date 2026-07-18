# OpenMusic — Roadmap

**Last updated**: 2026-07-18

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

| Item                                   | Status         | Notes                                                                                             |
| -------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------- |
| `openmusic release` command            | ✅ Complete    | One-shot generate + render + upload                                                               |
| Monthly batch short generation         | ✅ Complete    | `openmusic short batch`, `openmusic short devops-generate`                                        |
| Playlist management auto-create/append | ✅ Complete    | All three backends (API / youtube-up / yt-upload) support playlist creation and video appendage   |
| Scheduling system (cron-based)         | ✅ Complete    | `openmusic schedule add/remove/list/run/enable/disable`, cron validation, Telegram/Discord notifs |
| Analytics tracking                     | ⏳ Not started | YouTube Analytics API integration needed                                                          |

### OAuth Scope

The `auth-youtube` command generates tokens with `youtube` scope (was `youtube.upload`),
matching the `YouTubeAPIUploader.SCOPES` constant. The narrower scope would cause playlist
operations to fail with 403 Forbidden.

---

## Pre-existing Test Failures

### Resolved ✓

The following Python `patterns` subsystem test files have been updated to match current APIs:

| File                                    | Fix Applied                                                                      |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| `test_patterns/test_pattern_library.py` | Rewritten for current API: `add()`, `.patterns`, `get_by_tags()`, `sample()`     |
| `test_patterns/test_bayesian.py`        | Updated to use `PatternLibrary(path=...)`, removed `Patterns` wrapper references |
| `test_patterns/test_markov.py`          | Updated to string enum values, `StyleFactory.create()`, `next_phase()`           |

---

## Future Work

### Short-term

- **Dependency audit**: Several optional dependency groups (`acestep`, `dsp`, `video`, `artwork`)
  could benefit from explicit extras listing.

### Medium-term

- **Analytics tracking**: YouTube Analytics API v3 integration for per-content-type view/sub tracking.
  Design: `openmusic analytics` command with weekly summary reports.

### Long-term

- **CI/CD pipeline**: GitHub Actions with GPU runner for automated mix generation.
- **Content performance dashboard**: Web UI for tracking shorts vs. full-mix performance.
- **Multi-channel support**: Publish to multiple YouTube channels from one config.
