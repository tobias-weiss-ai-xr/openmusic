# AGENTS.md

## Project Overview

OpenMusic is an AI-powered dub techno generation framework. It combines ACE-Step 1.5 (AI audio generation) with Tone.js effects (TypeScript) orchestrated by a Python CLI. The system generates hours-long dub techno mixes by producing short AI segments, running them through a dub effects chain, and assembling the result with crossfades.

## Architecture

```
                          CLI (click)
                             |
                    MixConfig from flags/YAML
                             |
                     MixOrchestrator
                    /       |        \
                   /        |         \
    ACEStepGenerator  TypeScriptBridge  _assemble_segments()
          |                  |                  |
    ACE-Step DiT model   Node.js subprocess   numpy crossfade
    (GPU, 8 turbo steps)  (Tone.js effects)   (linear blend)
          |                  |                  |
      raw WAV files    processed WAV files   final mix.flac/.wav
```

## Module Map

### `packages/core/` (Python orchestrator)

The main package. Installed as `openmusic-core`.

| Path                                        | Purpose                                                                              |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `src/openmusic/cli/main.py`                 | Click CLI with `generate`, `validate`, `version` commands                            |
| `src/openmusic/orchestrator/mix.py`         | `MixConfig` dataclass, `MixOrchestrator` class, effects presets                      |
| `src/openmusic/orchestrator/pipeline.py`    | `run_pipeline()` generator that yields `PipelineResult` per stage                    |
| `src/openmusic/orchestrator/progress.py`    | `ProgressReporter` with ETA and callback hooks                                       |
| `src/openmusic/acestep/generator.py`        | `ACEStepGenerator` wraps ACE-Step DiT model for texture generation                   |
| `src/openmusic/acestep/config.py`           | `ACEStepConfig` and `GenerationParams` dataclasses                                   |
| `src/openmusic/acestep/cache.py`            | `CacheManager` with SHA-256 content-addressed cache at `~/.cache/openmusic/acestep/` |
| `src/openmusic/bridge/typescript_bridge.py` | `TypeScriptBridge` calls `node packages/effects/dist/index.js` via subprocess        |
| `src/openmusic/arrangement/mixer.py`        | `MixArranger` loads WAV, applies equal-power crossfade, saves result                 |
| `src/openmusic/arrangement/crossfade.py`    | Numpy crossfade functions (linear, equal-power curves)                               |
| `src/openmusic/arrangement/timeline.py`     | Timeline utilities for segment scheduling                                            |
| `src/openmusic/export/encoder.py`           | `AudioEncoder` wraps ffmpeg for FLAC/MP3 encoding with metadata                      |
| `src/openmusic/export/metadata.py`          | `TrackMetadata` dataclass and ffmpeg metadata embedding                              |

### `packages/effects/` (TypeScript effects engine)

Built with Tone.js. Runs inside Node.js, called from Python via `TypeScriptBridge`.

| Path                             | Purpose                                                                           |
| -------------------------------- | --------------------------------------------------------------------------------- |
| `src/index.ts`                   | Entry point. When run directly, reads `--config` JSON, renders audio, exports WAV |
| `src/engine/audio_engine.ts`     | `AudioEngine` orchestrates rendering pipeline                                     |
| `src/engine/decoder.ts`          | WAV decoder                                                                       |
| `src/engine/encoder.ts`          | WAV/FLAC/MP3 encoder                                                              |
| `src/chain.ts`                   | `DubTechnoEffectsChain` chains all effects in series                              |
| `src/config.ts`                  | Preset configs: `DEEP_DUB`, `MINIMAL_DUB`, `CLUB_DUB`, `DEFAULT_EFFECTS_CONFIG`   |
| `src/effects/delay.ts`           | Stereo multi-tap delay                                                            |
| `src/effects/reverb.ts`          | Convolution reverb with filtered input                                            |
| `src/effects/filter.ts`          | Bandpass/lowpass filter with LFO modulation                                       |
| `src/effects/distortion.ts`      | Waveshaper distortion                                                             |
| `src/effects/vinyl.ts`           | Vinyl noise simulation (crackle, hiss)                                            |
| `src/effects/tape_saturation.ts` | Tape saturation emulation                                                         |
| `src/effects/multi_tap_delay.ts` | Rhythmic multi-tap delay                                                          |
| `src/effects/granular_delay.ts`  | Granular processing delay                                                         |

### `ACE-Step-1.5/` (external AI model)

Cloned from https://github.com/ace-step/ACE-Step-1.5. Has its own Python venv with torch, transformers, diffusers. Not part of this monorepo's build system.

## Pipeline Flow

### Step 1: CLI parses arguments into MixConfig

```python
# cli/main.py
MixConfig(
    length=7200.0,      # 2h in seconds (parsed from "2h", "30m", "45s")
    bpm=125,
    key="Dm",
    output_path="mix.flac",
    segment_duration=180.0,
    effects_preset="deep_dub",
    skip_effects=False,
)
```

The `generate` command accepts `--length`, `--bpm`, `--key`, `--output`, `--config` (YAML), and `--no-effects`.

### Step 2: MixOrchestrator splits into segments

```python
segment_count = math.ceil(config.length / config.segment_duration)
# For a 2h mix: ceil(7200 / 180) = 40 segments
```

Each segment gets a position-aware prompt (intro/building, main groove, climax/outro).

### Step 3: ACE-Step generates raw WAV per segment

`ACEStepGenerator.generate_texture()` calls the ACE-Step DiT model:

- Uses `AceStepHandler` and `LLMHandler` from the `acestep` package
- `inference_steps=8` (turbo mode, ~12 seconds per segment on RTX 4080)
- Output: raw WAV at 48kHz stereo
- Cached by SHA-256 of (prompt + params) in `~/.cache/openmusic/acestep/`
- GPU detection: auto-selects CUDA if available, falls back to CPU

### Step 4: TypeScriptBridge applies effects

`TypeScriptBridge.call_audio_engine()`:

1. Creates a temp directory with `input/` and `output/` subdirs
2. Copies segment WAV into `input/stem_0.wav`
3. Writes a `config.json` with input stems, output path, effects config, and pattern
4. Runs `node packages/effects/dist/index.js --config <path>` with 600s timeout
5. Copies the processed WAV back to a persistent temp file
6. Cleans up the temp directory

If `skip_effects=True`, the bridge is bypassed entirely and the raw segment is copied as-is.

### Step 5: Segments assembled with crossfade

`_assemble_segments()` in `mix.py`:

- Loads all segment WAV files with `soundfile`
- Computes adaptive crossfade: `min(1s at 48kHz, shortest_segment / 4)`, minimum 10ms
- Applies linear crossfade between overlapping segments
- First segment: write all except tail crossfade
- Middle segments: crossfade in, write middle, reserve tail for next
- Last segment: crossfade in, write remainder
- Writes output as WAV (`.wav`) or FLAC (`.flac`) via `soundfile`

### Step 6: Output written

The final mix file lands at the path specified by `--output` (default: `mix.flac`).

## Key Configuration

### ACEStepConfig

| Field             | Default             | Description                                             |
| ----------------- | ------------------- | ------------------------------------------------------- |
| `model_path`      | `acestep-v15-turbo` | Model checkpoint name                                   |
| `device`          | `auto`              | `auto`, `cuda`, or `cpu`                                |
| `audio_format`    | `wav`               | Output audio format from ACE-Step                       |
| `max_duration`    | `600`               | Maximum single generation duration (seconds)            |
| `inference_steps` | `8`                 | Diffusion steps (lower = faster, slightly less quality) |

### MixConfig

| Field              | Default    | Description                      |
| ------------------ | ---------- | -------------------------------- |
| `length`           | `7200.0`   | Total mix length in seconds      |
| `bpm`              | `125`      | Beats per minute                 |
| `key`              | `Dm`       | Musical key                      |
| `output_path`      | `mix.flac` | Output file path                 |
| `segment_duration` | `180.0`    | Seconds per AI-generated segment |
| `effects_preset`   | `deep_dub` | Effects preset name              |
| `skip_effects`     | `False`    | Bypass effects processing        |

### Effects Presets

Three built-in presets, each configuring delay, reverb, filter, distortion, and vinyl:

- **`deep_dub`**: Heavy delay (0.6 mix, 0.5 feedback), long reverb (4s decay, 0.5 mix), low bandpass (600Hz), moderate distortion, noticeable vinyl noise
- **`minimal_dub`**: Lighter delay (0.35 mix), shorter reverb (2s decay, 0.25 mix), higher bandpass (900Hz), subtle distortion, faint vinyl
- **`club_dub`**: Medium delay (0.4 mix), medium reverb (2.5s decay, 0.3 mix), mid bandpass (1000Hz), punchy distortion, moderate vinyl

## Environment Setup

### Prerequisites

- Python 3.12+
- Node.js (for effects engine)
- uv package manager
- ffmpeg (for MP3/FLAC encoding)
- NVIDIA GPU with CUDA (recommended)

### Setup Steps

```bash
# 1. Clone the repo
git clone <repo-url> openmusic
cd openmusic

# 2. Clone ACE-Step-1.5 at repo root
git clone https://github.com/ace-step/ACE-Step-1.5.git ACE-Step-1.5

# 3. Set up ACE-Step venv
cd ACE-Step-1.5
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install torch transformers diffusers
cd ..

# 4. Install openmusic-core into ACE-Step's venv
uv pip install -e packages/core --python ACE-Step-1.5/.venv/Scripts/python.exe

# 5. Build TypeScript effects engine
cd packages/effects
npm install
npx tsc
cd ../..

# 6. Generate a mix
ACE-Step-1.5/.venv/Scripts/python.exe -m openmusic.cli.main generate --length 10m --bpm 125 --key Dm --output mix.flac
```

### GPU Tiers

| Tier | VRAM    | Example GPUs    |
| ---- | ------- | --------------- |
| 1    | <=4 GB  | GTX 1650        |
| 2    | <=6 GB  | RTX 2060        |
| 3    | <=8 GB  | RTX 3060        |
| 4    | <=12 GB | RTX 4080        |
| 5    | <=16 GB | RTX 4080 Super  |
| 6    | <=20 GB | RTX 4090        |
| 7    | <=24 GB | RTX 4090 (24GB) |
| 8    | >24 GB  | A100, H100      |

## CLI Reference

```
openmusic generate [OPTIONS]
  --length TEXT      Mix length (e.g. 2h, 30m, 45s)  [default: 1h]
  --bpm INTEGER      Beats per minute  [default: 125]
  --key TEXT         Musical key (e.g. Dm, C, F#)  [default: Dm]
  --output TEXT      Output file path  [default: mix.flac]
  --config PATH      Path to YAML config file
  --no-effects       Bypass effects processing

openmusic validate CONFIG_PATH
  Validates a YAML config file has required keys: length, bpm, key, output_path

openmusic version
  Shows version (0.1.0)
```

## Post-Processing

Convert to MP3:

```bash
ffmpeg -i mix.flac -c:a libmp3lame -b:a 320k mix.mp3
```

Create YouTube-ready MP4 with a static image:

```bash
ffmpeg -loop 1 -i cover.jpg -i mix.flac -c:v libx264 -tune stillimage -c:a aac -b:a 256k -shortest -movflags +faststart output.mp4
```

## Testing

- 473 Python tests
- 174 TypeScript tests
- Tests live alongside source files as `*.test.py` / `*.test.ts`

## Cache

Generated segments are cached at `~/.cache/openmusic/acestep/` keyed by SHA-256 hash of the prompt and generation parameters. Re-running with identical prompts/settings skips generation entirely.
