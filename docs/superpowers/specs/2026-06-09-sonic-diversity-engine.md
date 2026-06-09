# Sonic Diversity Engine — Design Spec

> **Goal:** Eliminate sonic homogeneity across 40-segment mixes by introducing per-segment variation in generation parameters, prompts, effects routing, and effect parameters.

**Architecture:** Seven independent changes across the orchestrator (Python), ACE-Step generator, and TypeScript effects engine, each adding a new axis of per-segment diversity.

**Tech Stack:** Python 3.12+ (orchestrator, prompt pipeline, inference scheduling), TypeScript (effects chain wiring), ACE-Step + Tone.js

---

## Changes

### 1. Fix Prompt Key/BPM Bug

**Files:** `packages/core/src/openmusic/orchestrator/mix.py:733-748`

`_get_segment_prompt()` currently uses `self.config.key` and `self.config.bpm` (static mix defaults) instead of per-segment values. The prompt text passed to ACE-Step always says "in Dm, 125 BPM" regardless of key/bpm schedule.

**Fix:** Add `seg_key: str` and `seg_bpm: int` parameters to `_get_segment_prompt()`. Update callsite in `_generate_segment()` to pass the per-segment values that are already computed at lines 492-493.

### 2. Enrich Prompt Pool (Style Modifiers + Structure Cues)

**Files:** `packages/core/src/openmusic/orchestrator/mix.py:94-160`

Current `STAGE_PROMPTS` have 3-5 entries per stage, all in the format `"dub techno, {text}"`. Expand to include:
- **Style modifiers:** atmospheric, percussive, drone, minimal, spacious, filtered, hypnotic, rolling
- **Structure cues per stage:** ambient/intro stages get "slow evolving pads, spacious", peak stages get "driving rhythms, dense percussion"
- **Random combinatorial prompts:** pick 1 structure cue + 1 style modifier per segment instead of a fixed prompt string

The prompt builder (`_get_segment_prompt`, post-bugfix) will construct prompts as:
```
"dub techno, {cue}, {modifier}, in {seg_key}, {seg_bpm} BPM"
```

### 3. Cycle Effects Presets Per Stage

**Files:** `packages/core/src/openmusic/orchestrator/mix.py:533-539`

Replace single `effects_preset` with a stage-to-preset mapping:

| Stage | Effects Preset |
|-------|---------------|
| ambient | `minimal_dub` |
| build | `deep_dub` |
| peak-one | `deep_dub` |
| peak-two | `club_dub` |
| decay-one | `deep_dub` |
| decay-two | `minimal_dub` |
| dissolution | `minimal_dub` |

The `effects_modifiers` mechanism remains available for additional per-segment tweaks over the base preset.

### 4. Vary `pattern.variation` Per Stage

**Files:** `packages/core/src/openmusic/orchestrator/mix.py:597`

Replace hardcoded `0.3` with a stage-dependent value:

| Stage | variation |
|-------|-----------|
| ambient | 0.1 |
| build | 0.3 |
| peak-one | 0.5 |
| peak-two | 0.7 |
| decay-one | 0.4 |
| decay-two | 0.2 |
| dissolution | 0.1 |

### 5. Per-Segment Inference Steps

**Files:** `packages/core/src/openmusic/acestep/config.py:5-24`, `mix.py`

`ACEStepConfig.inference_steps` is currently static. Add an optional `inference_steps_range: tuple[int, int] = (8, 50)` to `MixConfig`. When set, map segment index across the range so early segments use fewer steps (lo-fi texture) and peak segments use more steps (clean detail). Pass the per-segment value to `ACEStepGenerator` via the existing `ACEStepConfig` mechanism or a new parameter in `generate_texture()`.

The default `(8, 50)` range means: ambient stages at ~8-15 steps (fast, rough), build stages at ~20-30 steps, peak stages at ~35-50 steps (slow, detailed).

### 6. Wire 3 Unused TypeScript Effects

**Files:** `packages/effects/src/chain.ts:1-59`, `packages/effects/src/config.ts:46-78`

Three effect types are fully defined in `config.ts` but never wired into `DubTechnoEffectsChain.process()`:

- **TapeSaturation** (config.ts:46-55) — warm drive emulation
- **MultiTapDelay** (config.ts:57-68) — rhythmic delay patterns
- **GranularDelay** (config.ts:70-78) — pitch-shifting granular processing

Wire each into `chain.ts` so they respond to config. Follow the existing pattern (effect instantiation in constructor, `.connect()` in chain builder, optional enable/disable via config).

Each effect should map to a field in the preset config. Presets can define non-zero values for these effects to enable them.

### 7. MIDI-Driven Effect Automation

**Files:** `packages/core/src/openmusic/export/midi_export.py` (already exists), `packages/core/src/openmusic/orchestrator/mix.py`

Use the existing `midi_export` module to generate simple rhythmic patterns that modulate effects parameters:
- Generate a short MIDI pattern (16 steps, 1 bar at mix BPM)
- Parse MIDI notes into modulation values (note velocity → effect parameter amount, note timing → LFO rate)
- Apply modulation to delay feedback, reverb mix, and filter cutoff per segment

This adds rhythmic evolution across segments — e.g., delay feedback pulsing at different rates during build vs peak stages.

---

## Testing Strategy

Each change has isolated test coverage:

| Change | Test File | Test Count |
|--------|-----------|------------|
| 1. Prompt bug fix | `test_mix.py` | Update existing prompt tests |
| 2. Enriched prompts | `test_mix.py` | 2 new tests (combinatorial prompt generation) |
| 3. Preset cycling | `test_mix.py` | 2 new tests (stage→preset mapping) |
| 4. Variation per stage | `test_mix.py` | 1 new test |
| 5. Inference steps schedule | `test_config.py` + `test_mix.py` | 3 new tests |
| 6. TS effects wiring | `chain.test.ts` | 3 new tests (each effect processes audio) |
| 7. MIDI modulation | `test_midi_modulation.py` | 3 new tests |

---

## Files Changed

| File | Change Type |
|------|-------------|
| `packages/core/src/openmusic/orchestrator/mix.py` | Modify — prompt bug, prompt pool, preset cycling, pattern.variation, steps schedule integration |
| `packages/core/src/openmusic/acestep/config.py` | Modify — make `inference_steps` overridable per-call |
| `packages/core/src/openmusic/acestep/generator.py` | Modify — accept per-call `inference_steps` |
| `packages/core/src/openmusic/orchestrator/mix_config.py` (inline in mix.py) | Modify — add `inference_steps_range` |
| `packages/effects/src/chain.ts` | Modify — wire 3 effects |
| `packages/effects/src/config.ts` | Modify — ensure preset structure includes new effects |
| `packages/core/tests/orchestrator_test/test_mix.py` | Modify/Add — tests for changes 1-5 |
| `packages/effects/src/chain.test.ts` | Modify/Add — tests for change 6 |
| `packages/core/tests/test_export/test_midi_modulation.py` | Create — tests for change 7 |

---

## Success Criteria

- [ ] After fix 1: prompt text uses per-segment key/bpm when schedule is active
- [ ] After fix 2: prompts contain style modifiers + structure cues varying per stage
- [ ] After fix 3: different stages use different effects presets automatically
- [ ] After fix 4: `pattern.variation` differs per stage
- [ ] After fix 5: inference steps vary across segment index within configured range
- [ ] After fix 6: tapeSaturation, multiTapDelay, granularDelay affect audio when configured
- [ ] After fix 7: MIDI patterns modulate delay/reverb/filter per segment
- [ ] All tests pass
- [ ] Generate a 10-minute test mix and verify audible diversity
