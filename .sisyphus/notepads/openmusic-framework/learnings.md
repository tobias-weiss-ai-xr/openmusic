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

- Python \_EFFECTS_PRESETS dict must exactly match TypeScript DEEP_DUB/MINIMAL_DUB/CLUB_DUB constants
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

=== Learnings from Task: ACE-Step 1.5 Windows Installation ===

Date: Sun Apr 12 2026

## PyTorch CUDA Installation

- Replaced CPU-only torch 2.8.0 with CUDA-enabled 2.10.0+cu128
- Install command: pip install torch==2.10.0+cu128 torchvision==0.25.0+cu128 torchaudio==2.10.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
- GPU detected correctly: NVIDIA RTX 4080 Laptop GPU, 12GB VRAM

## ACE-Step 1.5 Repository Setup

- Cloned to C:\Users\Tobias\git\openmusic\ACE-Step-1.5
- No Windows resource module issue (#951) found in current codebase
- uv sync installed 121 packages including torch 2.7.1+cu128 in separate .venv

## Integration Strategy

- pip install -e failed due to local nano-vllm dependency
- Solution: Add ACE-Step-1.5 to PYTHONPATH
- Required imports work: acestep.handler, acestep.llm_inference, acestep.inference
- Warning messages about training dependencies (PEFT, Lightning, LyCORIS) are expected and non-blocking

## Hardware Tier

- RTX 4080 Laptop GPU = 12GB VRAM = Tier 4
- Recommended model: acestep-v15-turbo (8 steps, ~4.7GB VRAM)
- LM model: acestep-5Hz-lm-0.6B (PyTorch backend)

=== Learnings from Task: UV Migration ===

Date: Sun Apr 12 2026

## UV Workspace Configuration

- Root pyproject.toml defines [tool.uv.workspace] with members array
- Members must have their own pyproject.toml files
- TypeScript packages (packages/cli, packages/effects, packages/patterns) must be excluded from Python workspace
- Solution: Use explicit members = [''packages/core''] instead of wildcards packages/\*

## Build Backend Migration

- Changed from setuptools to hatchling: requires = [''hatchling''], build-backend = ''hatchling.build''
- Package name kept as ''openmusic-core'' to maintain compatibility
- CLI entry point preserved: openmusic = ''openmusic.cli.main:main''

## PyTorch CUDA with UV

- torch package names with +cu128 suffix (e.g., torch==2.10.0+cu128) fail resolution
- Solution: Use standard versioning (torch==2.10.0) and let uv handle CUDA via [[tool.uv.source]]
- [[tool.uv.source]] with url pointing to pytorch wheel index enables CUDA wheel selection
- Optional dependencies in [project.optional-dependencies] acestep include all ACE-Step requirements

## Dependency Management

- Dev dependencies remain in separate optional-dependencies group
- Core dependencies kept at package level (click, PyYAML, numpy, soundfile)
- uv sync --all-extras installs all optional dependency groups
- uv.lock is generated automatically and must be committed to repository

## CI/CD Updates

- Replaced actions/setup-python@v5 with astral-sh/setup-uv@v4
- Removed pip install pytest step - uv sync handles all dependencies
- Run tests with uv run pytest instead of pytest
- No Python version specification needed in CI - .python-version file handles it

## Documentation Updates

- README.md added uv installation and usage instructions
- CONTRIBUTING.md updated to reference uv instead of pip
- pytest remains as test runner - uv run pytest is the correct invocation

## Verification Checklist

- uv sync generates .venv and uv.lock successfully
- uv run pytest packages/core/tests passes all 466 tests
- uv run openmusic version returns 0.1.0 correctly
- uv run openmusic --help shows CLI commands
- No pip/setuptools references remain in Python source files

=== Learnings from Task: MixOrchestrator Assembly Fix ===

Date: Sun Apr 12 2026

## Bug 1: Temp Directory Cleanup

- Problem: `_process_segment()` created files in temp dir that were deleted when context exited
- Fix: Create persistent temp file outside context manager using `tempfile.NamedTemporaryFile(delete=False)`
- Copy processed file from temp dir to persistent location before cleanup
- Clean up persistent file in `generate_mix()` after assembly

## Bug 2: Missing Assembly Logic

- Problem: `generate_mix()` collected segment paths but never concatenated them
- Fix: Created new `_assemble_segments()` method that:
  - Loads all WAV segments using soundfile
  - Calculates crossfade duration (1 second max, 1/4 of shortest segment min)
  - Concatenates segments with linear interpolation crossfade
  - Writes output in WAV or FLAC format based on extension

## Mock Pattern: Create Actual Files When Implementation Expects File I/O

- Problem: Mock functions that only return paths don't create files for implementations that use file I/O
- Solution: Mock subprocess.run side_effects must create actual output files in temp directory
- Pattern: In intercept functions, use `kw.get("cwd")` to get temp dir and create output file
- Test updates: All bridge tests that mock subprocess must now create output/processed.wav

## Test Update Strategy

- Created `_mock_subprocess_with_output(cwd: str | None)` helper for tests
- Helper creates output/processed.wav in temp directory before returning mock result
- Updated all subprocess.run mocks to either:
  - Use `_mock_subprocess_with_output()` for success cases
  - Return error mocks directly for error cases (no output file needed)
- Mock count adjustments: test_call_audio_engine_copies_input_stems now expects 3 copy2 calls (2 inputs + 1 output)

## Verification

- All 473 tests pass (up from 472)
- No blocking LSP diagnostics
- One harmless redeclaration warning (false positive, functions in separate scopes)

## Test Strategy

- Followed TDD: wrote failing tests first, then implemented code
- Used soundfile library to create real WAV files for tests
- Mocked bridge to create actual files instead of returning paths
- Updated 4 existing tests to create real files instead of mocking paths
- Added 7 new tests in TestMixOrchestratorAssembly class
- All 31 tests in test_mix.py pass
- Integration and CLI tests remain passing

## Dependencies Used

- numpy: Array manipulation and concatenation
- soundfile: Reading and writing WAV/FLAC files
- Both are core dependencies (no new deps added)

## Logging

- Added `logging` module usage for progress messages
- Logger tracks segment assembly progress (e.g., "Assembling segment 3/40...")

## Code Quality

- No LSP diagnostics on changed files
- Used pathlib.Path consistently
- Proper error handling with file cleanup on failure

=== Learnings from Task: Integration Test Mock Fix ===

Date: Sun Apr 12 2026

## Mock Update Pattern for File I/O

- Problem: When changing implementation to use `shutil.copy()` on bridge output files, existing mocks that only returned paths caused FileNotFoundError
- Solution: Mock functions must create actual files when the implementation expects them to exist
- Pattern: In intercept/side_effect functions, write minimal test files using soundfile before returning path

## Test Files Requiring Updates

- `tests/test_integration/test_pipeline.py::TestBridgeConfigSchema._capture_bridge_config`
- Updated intercept function to write 480 samples of stereo float32 audio at 48kHz
- Uses soundfile: `sf.write(output_path, np.zeros((480, 2)), 48000, format="WAV")`

## Unrelated Test Fix

- `tests/test_acestep/test_config.py::TestACEStepConfig.test_default_values`
- Updated expected audio_format from "flac" to "wav" to match actual default
- Default changed in previous task (TypeScript bridge migrated to WAV)

## Verification

- All 473 tests pass (up from 472 after MixOrchestrator fix + test updates)
- Integration tests: 29/29 pass
- No new LSP diagnostics introduced
- Mock pattern: create actual files when implementation expects them

=== Learnings from Task: UV Migration Bug Fixes ===

Date: Sun Apr 12 2026

## PyTorch CUDA Wheel Resolution with UV

- [[tool.uv.source]] is WRONG — must use [[tool.uv.index]] for package index URLs
- Correct syntax: [[tool.uv.index]] with name, url, and explicit = true
- [tool.uv.sources] is required to pin specific packages to custom indexes
- Torch packages MUST have +cu128 suffix (e.g., torch==2.10.0+cu128)
- Without +cu128 suffix, uv cannot select the correct CUDA wheel from the custom index

## UV Workspace Extras Accessibility

- Root pyproject.toml needs [project.optional-dependencies] to expose member extras
- Dependencies on workspace members require [tool.uv.sources] with workspace = true
- Example: openmusic-core = { workspace = true }
- Example: acestep = [''openmusic-core[acestep]'']

## Hatchling Build Configuration

- Hatchling cannot auto-detect package location in src layout
- Must add [tool.hatch.build.targets.wheel] with packages = [''src/openmusic'']
- Without this, hatchling raises ValueError: Unable to determine which files to ship

## UV Sync with Extras

- uv sync --extra acestep from root now works correctly
- Resolves workspace member with its optional dependencies
- Downloads CUDA-enabled PyTorch wheels from custom index
- All 466 tests pass with acestep extra installed
- CLI works correctly: uv run openmusic version returns 0.1.0

## Verification Steps

- uv run --extra acestep python -c ''import torch; print(torch.cuda.is_available())'' returns True
- torch.**version** shows 2.10.0+cu128 confirming CUDA build
- uv run pytest packages/core/tests passes all 466 tests
