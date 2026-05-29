# AGENTS.md

## Project Overview

OpenMusic is an AI-powered dub techno generation framework. ACE-Step 1.5 generates raw audio segments (GPU, DiT model), a Tone.js effects chain processes them (Node.js, `web-audio-api`), and a Python CLI orchestrates everything into a seamless mix with crossfades.

**Version**: 0.1.0 (Python `openmusic-core`, TypeScript packages under pnpm workspace)

---

## Architecture

```
                            CLI (click / @openmusic/cli)
                                   |
                          MixConfig from flags/YAML
                                   |
                           MixOrchestrator
                          /       |        \
                         /        |         \
          ACEStepGenerator  TypeScriptBridge  _assemble_segments()
                |                  |                  |
          ACE-Step DiT model   Node.js subprocess   numpy crossfade
          (GPU, 8 turbo steps) (Tone.js effects)   (linear blend)
                |                  |                  |
            raw WAV          processed WAV        final mix.flac
```

**Bridge mechanism**: Python writes WAV stems + JSON config to `/tmp/openmusic-{uuid}/`, spawns `node packages/effects/dist/index.js --config <path>`, reads processed WAV back. File-based, no IPC. Temp dirs preserved on failure for debugging.

---

## Module Map

### `packages/core/` (Python orchestrator) — installed as `openmusic-core`

| Path | Purpose |
|------|---------|
| `src/openmusic/cli/main.py` | Click CLI: `generate`, `validate`, `version`, `auth-youtube` |
| `src/openmusic/orchestrator/mix.py` | `MixConfig` dataclass, `MixOrchestrator`, effects presets |
| `src/openmusic/orchestrator/pipeline.py` | `run_pipeline()` generator → `PipelineResult` per stage |
| `src/openmusic/orchestrator/progress.py` | `ProgressReporter` with ETA and callback hooks |
| `src/openmusic/acestep/generator.py` | `ACEStepGenerator` wraps ACE-Step DiT for texture generation |
| `src/openmusic/acestep/config.py` | `ACEStepConfig`, `GenerationParams` dataclasses |
| `src/openmusic/acestep/cache.py` | SHA-256 content-addressed cache at `~/.cache/openmusic/acestep/` |
| `src/openmusic/bridge/typescript_bridge.py` | `TypeScriptBridge` — spawns `node packages/effects/dist/index.js` |
| `src/openmusic/bridge/pedalboard_bridge.py` | Alternative bridge using Spotify's `pedalboard` (no Node.js needed) |
| `src/openmusic/arrangement/mixer.py` | `MixArranger` — loads WAV, applies crossfade, saves result |
| `src/openmusic/arrangement/crossfade.py` | Numpy crossfade functions (linear, equal-power) |
| `src/openmusic/arrangement/timeline.py` | Timeline utilities for segment scheduling |
| `src/openmusic/export/encoder.py` | `AudioEncoder` wraps ffmpeg for FLAC/MP3 encoding + metadata |
| `src/openmusic/export/metadata.py` | `TrackMetadata` dataclass, ffmpeg metadata embedding |
| `src/openmusic/export/youtube_uploader.py` | YouTube upload via google-api-python-client (OAuth) |
| `src/openmusic/export/cover_generator.py` | SVG-based cover art generation |
| `src/openmusic/effects/` | Python DSP effects (pedalboard-based): delay, compression, saturation, stereo widening, granular delay, LFO, VST scanner, spectral masking, mastering chain, frequency masking avoidance |
| `src/openmusic/config/parser.py` | YAML config file parser |
| `src/openmusic/mcp/orchestrator.py` | MCP server for external tool orchestration |
| `src/openmusic/video/` | Video generation pipeline: graph-based, with audio automation, SVG image gen, parallel rendering |
| `tests/` | ~529 test cases across 40 files (pytest) |

Optional dependency groups in `pyproject.toml`:
- `acestep` — torch/torchvision/torchaudio (CUDA 12.8), transformers, diffusers, accelerate, etc.
- `dsp` — pedalboard, librosa
- `youtube` — google-api-python-client, google-auth-oauthlib, youtube-up
- `video` — langgraph, diffusers, pedalboard, tenacity
- `artwork` — openart, svgwrite, cairosvg
- `dev` — pytest, google API libs

Custom PyTorch index in pyproject.toml:
```toml
[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu128", extra = "acestep" }
```

### `packages/effects/` (TypeScript — Tone.js effects engine)

| Path | Purpose |
|------|---------|
| `src/index.ts` | Entry point — reads `--config` JSON, renders audio via OfflineAudioContext, exports WAV |
| `src/chain.ts` | `DubTechnoEffectsChain` chains all effects in series |
| `src/config.ts` | Preset configs: `DEEP_DUB`, `MINIMAL_DUB`, `CLUB_DUB`, `DEFAULT_EFFECTS_CONFIG` |
| `src/engine/audio_engine.ts` | `AudioEngine` orchestrates rendering pipeline |
| `src/engine/decoder.ts` | WAV decoder |
| `src/engine/encoder.ts` | WAV/FLAC/MP3 encoder |
| `src/effects/delay.ts` | Stereo multi-tap delay |
| `src/effects/reverb.ts` | Convolution reverb with filtered input |
| `src/effects/filter.ts` | Bandpass/lowpass filter with LFO modulation |
| `src/effects/distortion.ts` | Waveshaper distortion |
| `src/effects/vinyl.ts` | Vinyl noise simulation (crackle, hiss) |
| `src/effects/tape_saturation.ts` | Tape saturation emulation |
| `src/effects/multi_tap_delay.ts` | Rhythmic multi-tap delay |
| `src/effects/granular_delay.ts` | Granular processing delay |

~172 test cases across 10 files (vitest). Tests live alongside source as `*.test.ts`.

### `packages/patterns/` (TypeScript — Strudel-inspired patterns + music theory)

| Path | Purpose |
|------|---------|
| `src/index.ts` | Public API exports |
| `src/strudel/` | Strudel-inspired pattern definitions for dub techno |
| `src/theory/` | Music theory: scales, chord progressions, voicings |

~85 test cases across 6 files (vitest).

### `packages/cli/` (TypeScript — user-facing CLI shim)

| Path | Purpose |
|------|---------|
| `src/index.ts` | CLI entrypoint — delegates to Python `openmusic-core` as subprocess |

Depends on `@openmusic/effects` and `@openmusic/patterns` as workspace dependencies.

### `ACE-Step-1.5/` (external AI model)

Cloned from https://github.com/ace-step/ACE-Step-1.5. Has its own Python venv with torch, transformers, diffusers. **Not part of this monorepo's build system**. Listed in `.gitignore`.

---

## Commands

### TypeScript (pnpm workspace — root)

```bash
pnpm install              # Install all workspace deps
pnpm build                # tsc -p packages/effects/tsconfig.json
pnpm test                 # vitest run (all packages)
pnpm format               # prettier --write .
pnpm lint                 # eslint .
pnpm docs                 # typedoc
```

### Per-package

```bash
# Python (openmusic-core)
cd packages/core
uv venv                   # Create venv
uv pip install -e ".[dev]"  # Install with dev deps
uv run pytest             # Run all Python tests
uv run pytest tests/test_cli/test_cli.py  # Single test file
uv run pytest -k "test_name"              # Single test (name match)

# TypeScript packages (from workspace root or package dir)
pnpm --filter @openmusic/effects test
pnpm --filter @openmusic/patterns test
```

### CI (`.github/workflows/ci.yml`)

Two parallel jobs on push/PR to `main`:
1. **typescript** — Node 22, npm install, `npx tsc -p packages/effects/tsconfig.json`, `npx vitest run`
2. **python** — uv, `uv pip install -e ".[dev]"`, `.venv/bin/python -m pytest`

Both install `ffmpeg` system dependency.

---

## CLI Reference

```
openmusic generate [OPTIONS]
  --length TEXT      Mix length (e.g. 2h, 30m, 45s)  [default: 1h]
  --bpm INTEGER      Beats per minute                 [default: 125]
  --key TEXT         Musical key (e.g. Dm, C, F#)    [default: Dm]
  --output TEXT      Output file path (.flac or .wav) [default: mix.flac]
  --config PATH      Path to YAML config file
  --no-effects       Bypass effects processing

openmusic validate CONFIG_PATH
  Checks YAML config has required keys: length, bpm, key, output_path

openmusic version
  Prints the current version

openmusic auth-youtube [OPTIONS]
  --code TEXT   OAuth code for non-interactive token generation
  --force       Force re-authentication
```

OAuth for YouTube: uses localhost:18080 callback, auto-captures code. Token stored in `youtube_token.json` (gitignored). Requires `client_secrets.json` (gitignored).

---

## Key Configuration

### MixConfig fields

| Field | Default | Description |
|---|---|---|
| `length` | `7200.0` (1h) | Total mix length in seconds |
| `bpm` | `125` | Beats per minute |
| `key` | `Dm` | Musical key |
| `output_path` | `mix.flac` | Output file path |
| `segment_duration` | `180.0` | Seconds per AI-generated segment |
| `effects_preset` | `deep_dub` | Effects preset name |
| `skip_effects` | `False` | Bypass effects processing |

### Effects presets

| Preset | Delay Mix | Reverb Decay | Filter | Character |
|---|---|---|---|---|
| `deep_dub` | 0.60 | 4.0s | 600Hz bandpass | Heavy, atmospheric |
| `minimal_dub` | 0.35 | 2.0s | 900Hz bandpass | Clean, restrained |
| `club_dub` | 0.40 | 2.5s | 1000Hz bandpass | Punchy, mid-focused |

### Crossfade behavior

In `MixOrchestrator._assemble_segments()`: linear crossfade between overlapping segments. Adaptive length:
- `min(1s at 48kHz, shortest_segment / 4)`, minimum 10ms
- First segment: write all except tail crossfade
- Middle: crossfade in, write middle, reserve tail
- Last: crossfade in, write remainder

---

## Setup

```bash
# 1. Clone ACE-Step-1.5 at repo root (must match the expected path)
git clone https://github.com/ace-step/ACE-Step-1.5.git

# 2. ACE-Step venv
cd ACE-Step-1.5 && python -m venv .venv
source .venv/bin/activate
pip install torch transformers diffusers

# 3. Install openmusic-core into ACE-Step's venv
uv pip install -e packages/core --python ACE-Step-1.5/.venv/bin/python

# 4. Build TS effects engine (using pnpm from workspace root)
cd packages/effects && npm install && npx tsc && cd ../..

# 5. Generate a 10m mix
ACE-Step-1.5/.venv/bin/python -m openmusic.cli.main generate --length 10m --bpm 125 --key Dm --output mix.flac
```

**Prerequisites**: Python 3.12+, Node.js, uv, ffmpeg, NVIDIA GPU with CUDA (recommended).

---

## Testing

- **Python**: `uv run pytest` from `packages/core/`. ~529 test cases across 40 files in `packages/core/tests/`. Uses `test_*.py` convention (NOT alongside source).
- **TypeScript**: `pnpm test` from root. ~172 test cases across 17 `*.test.ts` files. Tests live **alongside source** (e.g., `src/chain.test.ts`).
- **Coverage config** (pyproject.toml): omits `*/verify_spectral_masking.py` and `*/tests/*`.
- pytest: `testpaths = ["tests"]`, `pythonpath = ["src"]`.

---

## Style

- **Prettier**: semicolons, single quotes, 2-space tabs, trailing commas (ES5), 100 char print width (`.prettierrc`)
- **TypeScript**: `strict: true`, ES2022 target, ESNext modules, bundler module resolution, declarations enabled
- **Python**: runs on 3.12+, uses `click` for CLI, `soundfile` for audio I/O, `numpy` for signal processing

---

## Important Gotchas

- **ACE-Step-1.5 is external** — must be cloned separately at repo root. Not covered by pnpm or uv workspace. Has its own `requirements.txt`-style setup.
- **PyTorch CUDA 12.8**: Custom uv index defined for torch/torchvision/torchaudio. Install via `uv pip install "openmusic-core[acestep]"`.
- **Python venv for ACE-Step**: openmusic-core must be installed INTO ACE-Step's venv (the ACE-Step import path needs to resolve). The CLI entrypoint `openmusic` (Click) runs from ACE-Step's Python.
- **YAML config**: Must have keys `length`, `bpm`, `key`, `output_path`. Validated by `openmusic validate`.
- **Generated assets**: `*.wav`, `*.flac`, `*.mp3`, `*.mp4` are gitignored. Cache lives in `.cache/openmusic/` (gitignored).
- **OAuth**: `client_secrets.json` and `youtube_token.json` are gitignored. YouTube auth uses OAuth callback on port 18080.
- **pnpm for TypeScript, npm for build**: The root uses pnpm workspace, but CI and package build scripts use `npm install` / `npx tsc`. Both work — pnpm is the workspace manager, npm/npx are the actual runners.
- **type: "module"** in all package.json files — ES module imports throughout.
