# OpenMusic Roadmap

**Project**: AI-powered dub techno generation framework
**Version**: 0.1.0
**Status**: Core pipeline shipped, effects engine complete, first mix release pending

---

## Legend

- ✅ **Done** — implemented, tested, merged
- 🔄 **In Progress** — actively being worked on
- 📋 **Planned** — scoped but not started
- 💡 **Proposed** — under consideration

---

## Milestone: Ship the Pipeline ✅

Sprint 1 (Jun 14–27, 2026) delivered the complete generation pipeline.

### Core Pipeline

| Item                                | Status | Notes                                                                     |
| ----------------------------------- | ------ | ------------------------------------------------------------------------- |
| ACE-Step DiT integration            | ✅     | GPU-based audio generation, 8 turbo steps                                 |
| TypeScript effects engine (Tone.js) | ✅     | 175/177 tests passing across 10 files                                     |
| Python effects engine (pedalboard)  | ✅     | Full DSP chain: saturation, delay, reverb, compression, stereo, mastering |
| TypeScript ↔ Python bridge          | ✅     | File-based IPC via `/tmp/openmusic-{uuid}/`                               |
| MixOrchestrator                     | ✅     | Crossfade assembly, per-segment scheduling                                |
| `openmusic generate` CLI            | ✅     | --length, --bpm, --key, --output, --no-effects                            |
| `openmusic validate` CLI            | ✅     | YAML config validation                                                    |
| FFmpeg FLAC/MP3 export              | ✅     | TPDF dithering via ffmpeg                                                 |

### Effects Engine (Python — pedalboard)

| Effect                  | Status | Notes                                                              |
| ----------------------- | ------ | ------------------------------------------------------------------ |
| Tape Saturation         | ✅     | Tanh soft-clipping, drive/wet_dry/bias controls                    |
| Multi-Tap Delay         | ✅     | Programmable tap times, feedback, pan, filter in feedback path     |
| Granular Delay          | ✅     | Grain_size, density, randomization, feedback                       |
| Mid-Side Stereo Widener | ✅     | M/S encode/decode, mono sub-bass below 150Hz                       |
| Sidechain Compression   | ✅     | Internal envelope follower, configurable threshold/ratio/release   |
| Dual Delay with Detune  | ✅     | Parallel delays at dotted-8th/quarter, ±3 cent detune, hard-panned |
| LFO Modulation Engine   | ✅     | Sine/triangle/square/random waveforms, amplitude modulation        |
| Brickwall Limiter       | ✅     | Envelope follower, lookahead, in MasteringChain                    |
| LUFS Normalization      | ✅     | ITU-R BS.1770-style with gating                                    |
| Parameter Automation    | ✅     | Gain envelope, tremolo, random walk                                |

### CLI Commands

| Command                  | Status | Notes                                              |
| ------------------------ | ------ | -------------------------------------------------- |
| `openmusic generate`     | ✅     | Full mix generation                                |
| `openmusic release`      | ✅     | Generate + render MP4 + upload YouTube in one shot |
| `openmusic validate`     | ✅     | YAML config validation                             |
| `openmusic auth-youtube` | ✅     | OAuth with localhost:18080 callback                |
| `openmusic version`      | ✅     | Prints current version                             |
| `openmusic publish`      | ✅     | Legacy publish command                             |
| Shorts generation        | ✅     | Batch short generation with category rotation      |

### Quality & Infrastructure

| Item                    | Status | Notes                                                      |
| ----------------------- | ------ | ---------------------------------------------------------- |
| Python tests (~529)     | ✅     | All passing, 0 collection errors                           |
| TypeScript tests (~175) | ✅     | All passing                                                |
| CI (GitHub Actions)     | ✅     | Python + TypeScript parallel jobs                          |
| Effects chain order     | ✅     | HPF→Saturation→Pedalboard→Sidechain→M/S→Mastering          |
| YouTube OAuth + upload  | ✅     | `youtube_token.json`, auto-refresh                         |
| Cover art generation    | ✅     | SVG-based                                                  |
| Video pipeline          | ✅     | LangGraph-based, parallel rendering                        |
| `effects_chain` config  | 📋     | Defined in parser defaults, not yet in MixConfig dataclass |

---

## Milestone: First Mix Release (Jun 27)

| Item                        | Status | Notes                                    |
| --------------------------- | ------ | ---------------------------------------- |
| Deep Minimal Dub @125BPM Dm | 📋     | 2h mix, first public release             |
| YouTube upload & review     | 📋     | Unlisted → public after review           |
| Batch shorts from mix       | 📋     | Generate 6 shorts at staggered positions |

---

## Feature Roadmap

### Phase 3: Advanced Effects (Medium Impact, High Effort)

| Item                        | Status | Notes                                                             |
| --------------------------- | ------ | ----------------------------------------------------------------- |
| LFO Modulation Engine       | ✅     | Done in sound quality overhaul                                    |
| Spectral Gating             | 💡     | FFT-based adaptive gate with tempo sync — old broken code deleted |
| Frequency Masking Avoidance | 💡     | Automated EQ carving for layered mixes — old broken code deleted  |

### Quality Improvements

| Item                        | Status | Notes                                                 |
| --------------------------- | ------ | ----------------------------------------------------- |
| CLI package test coverage   | 📋     | `packages/cli/src/index.test.ts` has placeholder only |
| Patterns package test audit | 📋     | Verify meaningful test coverage                       |
| `MixConfig.effects_chain`   | 📋     | Add `EffectConfig` list for user-configurable chains  |

### Future Considerations

| Item                            | Notes                                |
| ------------------------------- | ------------------------------------ |
| `openmusic publish` deprecation | Superseded by `openmusic release`    |
| Dependabot auto-updates         | Configured for npm dependencies      |
| Playlist management             | Auto-create/append YouTube playlists |
| Cron-based mix generation       | Overnight GPU scheduling             |
| Analytics tracking              | Views/subs per content type          |
| MIDI-driven effect modulation   | Per-segment MIDI parameter control   |

---

## Content Operations (2026 H2)

See [release plan](.sisyphus/plans/2026-release-plan.md) for detailed schedule.

| Month     | Mixes  | Shorts  | Notes                                  |
| --------- | ------ | ------- | -------------------------------------- |
| Jul 2026  | 2      | 16      | Dark Ambient Dub, Detroit Techno       |
| Aug 2026  | 2      | 16      | Club Dub, Deep Hypnotic                |
| Sep 2026  | 2      | 18      | Berlin Sound, Sci-Fi Ambient           |
| Oct 2026  | 2      | 17      | Halloween Dark, Percussion Focus       |
| Nov 2026  | 2      | 17      | Vintage Basic Channel, Winter Deep     |
| Dec 2026  | 3      | 18      | Holiday Ambient, Year-End, NYE Special |
| **Total** | **13** | **102** |                                        |

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and [AGENTS.md](AGENTS.md) for architecture details.
