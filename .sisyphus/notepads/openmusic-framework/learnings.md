=== Learnings from Task 05: Dub Techno Theory Spec ===

Date: Fri 27 Mar 22:12:39 CET 2026

## Parallel Chord Movement ===
- Maintain chord quality (minor) while shifting root by intervals
- Common movements: semitone, whole tone, minor third descents
- Extended chords (m9, m11) preferred over triads for dub techno

## Effect Chain Patterns ===
- Dual delays with different times (1/8 and 3/16 notes) create depth
- Tape delay error (5-15%) adds analog warmth
- Long reverb (3-4s decay) essential for atmospheric space
- Bandpass filter with LFO (0.1-0.5 Hz) creates movement
- Subtle saturation (10-30%) for analog warmth
- Vinyl crackle (10-25%) adds texture without overwhelming

## Structural Considerations ===
- Long-form mixes (60-120 min) require gradual evolution
- Sections: intro (2-4 min), development (40-80 min), climax (4-8 min), outro (2-4 min)
- Transitions: 16-32 bars with filter sweeps or crossfades
- Key changes occur at section boundaries, not within

## Rob Jenkins Style Characteristics ===
- Dark, atmospheric mood with minor keys (D, E, A minor preferred)
- BPM 120-130 (typically 122-128)
- Wide stereo image (120-150%) but sub-bass centered
- Controlled dynamics (-18 to -14 dB RMS) preserve headroom

=== Learnings from ACE-Step 1.5 Validation ===

Date: Fri 27 Mar 22:12 CET 2026

## Model Architecture ===
- Hybrid: LM (planner) + DiT (diffusion transformer)
- LM generates audio codes and metadata via Chain-of-Thought
- DiT performs diffusion for actual audio synthesis
- VAE decodes latents to waveform

## Output Specifications ===
- Sample Rate: 48000 Hz (fixed)
- Channels: Stereo
- Formats: MP3, WAV, FLAC (FLAC default for speed)
- Duration Range: 10s to 600s (10 min max)

## Performance ===
- A100: ~2s for full song
- RTX 3090: ~10s for full song
- With LM thinking: 40-50% time is LM planning
- Without LM: 70-80% time is DiT diffusion

## GPU Memory Tiers ===
- Auto-detects VRAM and configures settings
- ≤6GB: No LM, requires INT8 + CPU offload
- 6-12GB: 0.6B LM with pt backend
- 12-20GB: 1.7B LM with vllm
- ≥20GB: All LM models, no offload needed

## Dub Techno Prompts ===
- Include effects: "reverb", "delay", "tape saturation"
- Tempo: 120-130 BPM
- Mood: "deep", "atmospheric", "minimal"
- Key: Minor keys work well (Am, Dm, Em)

## Integration Options ===
- Python API: Direct function calls
- REST API: Async task-based at port 8001
- CLI: Interactive wizard or config file
- Gradio UI: Web interface at port 7860

=== Learnings from Task 03: ACE-Step Validation Test Script ===

Date: Sat 28 Mar 06:30 CET 2026

## ACE-Step API (Verified Against Source) ===
- GenerationParams: duration=-1.0 default (use positive float), inference_steps=8 for turbo
- GenerationConfig: batch_size=2 default, audio_format="flac" default
- generate_music() returns GenerationResult with .audios list of dicts
- Each audio dict: {path, tensor, key, sample_rate, params}
- Tensor shape: [channels, samples] (channels-first, float32)
- ACE-Step generates files with UUID-based filenames (not prompt-based)
- Docs at docs/acestep_validation.md are accurate — no discrepancies found

## Validation Script Design ===
- Uses sys.path manipulation (ACE-Step-1.5 at project root), not pip install
- Graceful handling: ImportError → exit 0, no GPU → exit 0 with message
- Dry-run mode validates params without model loading
- Three dub techno prompts: chord stabs, atmospheric bass, delay textures
- shift=3.0 recommended for dub techno (strong semantic guidance)

## Hardware Context ===
- Current GPU: RTX 2060, 6GB VRAM (Tier 2)
- LM not viable on 6GB; DiT-only mode with --use-lm omitted
- Test script warns about low VRAM and suggests skipping LM

=== Learnings from F1 Architecture Bug Fixes ===

Date: Mon 30 Mar 2026

## Integration Layer Patterns
- Bridge config schema changes require updating BOTH Python emitter and TypeScript receiver simultaneously
- TypeScriptBridge already had correct EFFECTS_BIN path (packages/effects/dist/index.js) — mix.py had a stale duplicate
- Refactoring to use TypeScriptBridge eliminated subprocess duplication AND fixed the path bug in one change

## Test Mocking Surface Changes
- When refactoring from raw subprocess to TypeScriptBridge, all tests that mocked `subprocess.run` and `shutil.copy2` must be updated to mock `TypeScriptBridge.call_audio_engine`
- Pipeline tests that mock MixOrchestrator but don't mock new dependencies (MixArranger, AudioEncoder) will fail
- Integration tests using `_capture_bridge_config` pattern need complete rewrite when mocking surface changes

## CLI Entry Point Testing
- Vitest caches module imports — `vi.resetModules()` + dynamic `import()` needed to re-execute top-level CLI guards
- `process.exit` mocking must use throw-based pattern to prevent actual process termination in tests

## Effects Preset Synchronization
- Python _EFFECTS_PRESETS dict must exactly match TypeScript DEEP_DUB/MINIMAL_DUB/CLUB_DUB constants
- Any preset change requires updating both Python and TypeScript

=== Learnings from F3 QA Attempt ===

Date: Tue Mar 31 2026

## ACE-Step Availability Check ===
- CLI correctly fails with clear error message when ACE-Step not installed
- Error: "ACE-Step is not installed. Install it from https://github.com/ace-step/ACE-Step-1.5"
- No synthetic audio fallback implemented yet
- Recommendation: Add fallback to synthetic generation for environments without GPU

## CLI Installation Required ===
- CLI must be installed via `pip install -e .` in packages/core
- After installation: `openmusic --help` works correctly
- Version command: `openmusic version` → "0.1.0"
- Generate command accepts --length, --bpm, --key, --output, --config flags

## Build and Test Status ===
- TypeScript build: SUCCESS (pnpm run build, 0 errors)
- TypeScript tests: PASS (174/174 via vitest)
- Python tests: PASS (331/331 via pytest)
- Python package: INSTALLED (openmusic-core 0.1.0)
- LSP errors: Present in test files (SharedArrayBuffer type mismatch) but tests pass

## Pipeline Validation ===
- Python orchestrator: WORKING (initializes correctly)
- TypeScript bridge: WORKING (would call audio engine correctly)
- Effects chain: NOT TESTED (blocked by ACE-Step)
- Export pipeline: NOT TESTED (blocked by ACE-Step)

## ACE-Step Installation Path ===
- Clone: git clone https://github.com/ace-step/ACE-Step-1.5
- Install: pip install -r requirements.txt
- GPU requirement: Minimum 6GB VRAM for DiT-only mode (RTX 2060 viable)
- LLM not viable on 6GB VRAM (use --use-lm omitted)
- Model download: ~5-10 GB on first run

