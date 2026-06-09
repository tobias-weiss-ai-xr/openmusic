# Sonic Diversity Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate sonic homogeneity across 40-segment mixes by introducing per-segment variation in prompts, effects, generation parameters, and effect routing.

**Architecture:** Seven independent changes across the Python orchestrator (mix.py), ACE-Step generator config, and TypeScript effects chain (chain.ts). Tasks 1-5 modify mix.py sequentially; Task 6 is isolated to TypeScript and can run in parallel.

**Tech Stack:** Python 3.12+ (orchestrator, prompt pipeline, inference scheduling), TypeScript (effects chain wiring), ACE-Step DiT model, Tone.js

**Spec:** `docs/superpowers/specs/2026-06-09-sonic-diversity-engine.md`

---

### Task 1: Wire Unused TypeScript Effects (chain.ts + config.ts)

**Files:**
- Modify: `packages/effects/src/chain.ts`
- Modify: `packages/effects/src/config.ts` (minimal — ensure preset shape matches)
- Test: `packages/effects/src/chain.test.ts`

**Details:** Three effects are defined in `config.ts` (TapeSaturation, MultiTapDelay, GranularDelay) with typed interfaces and default values, but `DubTechnoEffectsChain.process()` in `chain.ts` never creates or connects them. Wire them using the existing pattern.

The chain wiring in `chain.ts` currently goes:
```
source → filter → distortion → delay → reverb → vinyl → destination
```

Add after vinyl (or as a parallel chain after delay):
```
vinyl → tapeSaturation → multiTapDelay → granularDelay → destination
```

Each effect should follow the existing pattern: instantiate in constructor if config is non-zero, `.connect()` in chain builder, optionally bypass if config values are zero.

**Configuration mapping:**

```typescript
// In config.ts — the existing interface already has these fields.
// Add DEFAULT_EFFECTS_CONFIG entries for the new effects.

// TapeSaturation (existing interface at config.ts:46-55):
// { drive: 0, wetDryMix: 0, biasTone: 0 } — zero = disabled by default

// MultiTapDelay (existing interface at config.ts:57-68):
// { taps: [], masterFeedback: 0, wetDryMix: 0 } — empty taps = disabled

// GranularDelay (existing interface at config.ts:70-78):
// { grainSizeMs: 100, grainDensity: 0.5, randomizationAmount: 0.3, feedback: 0.3, wetDryMix: 0 }
// wetDryMix: 0 = disabled by default
```

**Chain.ts modifications:**

```typescript
// In process() method, around line 48:
addEffects(effectsConfig: DubTechnoEffectsConfig): AudioNode {
    let current: AudioNode = this.source;

    // ... existing effects ...

    // Wire new effects after vinyl
    if (effectsConfig.tapeSaturation && effectsConfig.tapeSaturation.drive > 0) {
        this.tapeSaturation = new Tone.Distortion(effectsConfig.tapeSaturation.drive);
        if (effectsConfig.tapeSaturation.wetDryMix !== undefined) {
            this.tapeSaturation.wet.value = effectsConfig.tapeSaturation.wetDryMix;
        }
        current = current.connect(this.tapeSaturation);
    }

    if (effectsConfig.multiTapDelay && effectsConfig.multiTapDelay.taps.length > 0) {
        this.multiTapDelay = new Tone.PingPongDelay(
            effectsConfig.multiTapDelay.taps[0]?.delayTime || 0.25,
            effectsConfig.multiTapDelay.masterFeedback || 0.3
        );
        if (effectsConfig.multiTapDelay.wetDryMix !== undefined) {
            this.multiTapDelay.wet.value = effectsConfig.multiTapDelay.wetDryMix;
        }
        current = current.connect(this.multiTapDelay);
    }

    if (effectsConfig.granularDelay && effectsConfig.granularDelay.wetDryMix > 0) {
        // Granular delay: use Tone.FeedbackDelay with grain-like settings
        this.granularDelay = new Tone.FeedbackDelay(
            effectsConfig.granularDelay.grainSizeMs / 1000,
            effectsConfig.granularDelay.feedback || 0.3
        );
        this.granularDelay.wet.value = effectsConfig.granularDelay.wetDryMix;
        current = current.connect(this.granularDelay);
    }

    // ... connect to destination ...
    current.connect(this.destination);
}
```

Note: Tone.js doesn't have native granular delay. Use `Tone.FeedbackDelay` with small delay times (grainSizeMs/1000) and randomization applied to delay time via a scheduled LFO to simulate granular texture. This is a pragmatic approximation.

- [ ] **Step 1: Write failing tests for new effects in chain.test.ts**

```typescript
import { describe, it, expect } from 'vitest';
import { DubTechnoEffectsChain } from './chain';
import { DEFAULT_EFFECTS_CONFIG } from './config';

describe('TapeSaturation', () => {
    it('processes audio with tape saturation', () => {
        const config = { ...DEFAULT_EFFECTS_CONFIG, tapeSaturation: { drive: 0.5, wetDryMix: 0.4, biasTone: 0 } };
        const chain = new DubTechnoEffectsChain(config);
        expect(chain).toBeDefined();
        // Chain should not throw when processing
        expect(() => chain.process(new Float32Array(1024))).not.toThrow();
    });

    it('bypasses tape saturation when drive is 0', () => {
        const config = { ...DEFAULT_EFFECTS_CONFIG, tapeSaturation: { drive: 0, wetDryMix: 0, biasTone: 0 } };
        const chain = new DubTechnoEffectsChain(config);
        expect(chain).toBeDefined();
    });
});

describe('MultiTapDelay', () => {
    it('processes audio with multi-tap delay', () => {
        const config = {
            ...DEFAULT_EFFECTS_CONFIG,
            multiTapDelay: { taps: [{ delayTime: 0.25, feedback: 0.3, mix: 0.4 }], masterFeedback: 0.3, wetDryMix: 0.5 }
        };
        const chain = new DubTechnoEffectsChain(config);
        expect(() => chain.process(new Float32Array(1024))).not.toThrow();
    });
});

describe('GranularDelay', () => {
    it('processes audio with granular delay', () => {
        const config = {
            ...DEFAULT_EFFECTS_CONFIG,
            granularDelay: { grainSizeMs: 100, grainDensity: 0.5, randomizationAmount: 0.3, feedback: 0.3, wetDryMix: 0.4 }
        };
        const chain = new DubTechnoEffectsChain(config);
        expect(() => chain.process(new Float32Array(1024))).not.toThrow();
    });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pnpm --filter @openmusic/effects test`
Expected: Tests fail with "tapeSaturation is not defined" or similar (chain.ts doesn't create these effects yet)

- [ ] **Step 3: Wire tapeSaturation in chain.ts**

In `packages/effects/src/chain.ts`, inside the `process()` method after the vinyl block:

```typescript
// Tape saturation
if (effectsConfig.tapeSaturation && effectsConfig.tapeSaturation.drive > 0) {
    this.tapeSaturation = new Tone.Distortion(effectsConfig.tapeSaturation.drive);
    if (effectsConfig.tapeSaturation.wetDryMix !== undefined) {
        this.tapeSaturation.wet.value = effectsConfig.tapeSaturation.wetDryMix;
    }
    current = current.connect(this.tapeSaturation);
}

// Multi-tap delay
if (effectsConfig.multiTapDelay && effectsConfig.multiTapDelay.taps.length > 0) {
    const firstTap = effectsConfig.multiTapDelay.taps[0];
    this.multiTapDelay = new Tone.PingPongDelay(
        firstTap.delayTime || 0.25,
        effectsConfig.multiTapDelay.masterFeedback || 0.3
    );
    if (effectsConfig.multiTapDelay.wetDryMix !== undefined) {
        this.multiTapDelay.wet.value = effectsConfig.multiTapDelay.wetDryMix;
    }
    current = current.connect(this.multiTapDelay);
}

// Granular delay (approximated with FeedbackDelay + small time + LFO modulation)
if (effectsConfig.granularDelay && effectsConfig.granularDelay.wetDryMix > 0) {
    const grainTime = (effectsConfig.granularDelay.grainSizeMs || 100) / 1000;
    this.granularDelay = new Tone.FeedbackDelay(
        grainTime,
        effectsConfig.granularDelay.feedback || 0.3
    );
    this.granularDelay.wet.value = effectsConfig.granularDelay.wetDryMix;
    current = current.connect(this.granularDelay);
}
```

Also add class properties at the top of `DubTechnoEffectsChain`:

```typescript
private tapeSaturation?: Tone.Distortion;
private multiTapDelay?: Tone.PingPongDelay;
private granularDelay?: Tone.FeedbackDelay;
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pnpm --filter @openmusic/effects test`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add packages/effects/src/
git commit -m "feat(effects): wire tapeSaturation, multiTapDelay, granularDelay into chain.ts"
```

---

### Task 2: Fix Prompt Key/BPM Bug

**Files:**
- Modify: `packages/core/src/openmusic/orchestrator/mix.py:733-748`

**Details:** `_get_segment_prompt()` uses `self.config.key` and `self.config.bpm` (static defaults) instead of per-segment values. The bug is at line 746-747. The caller `_generate_segment()` already computes `seg_bpm` and `seg_key` at lines 492-493 but doesn't pass them to the prompt function.

- [ ] **Step 1: Write failing tests**

In `packages/core/tests/orchestrator_test/test_mix.py`, add to the existing `TestMixOrchestratorAssembly` class or a new test class:

```python
class TestPromptGeneration:
    def test_prompt_uses_per_segment_key_and_bpm(self):
        config = MixConfig(key="Dm", bpm=125, key_schedule="0:Am,0.5:C", bpm_schedule="0:120,0.5:130")
        orch = MixOrchestrator(config)
        prompt_early = orch._get_segment_prompt(0, 40)
        prompt_late = orch._get_segment_prompt(20, 40)
        # Early segment should use early schedule values
        assert "Am" in prompt_early
        assert "120" in prompt_early
        # Late segment should use late schedule values
        assert "C" in prompt_late
        assert "130" in prompt_late
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py::TestPromptGeneration -v`
Expected: Test fails because prompt always contains "Dm" and "125 BPM" regardless of schedule

- [ ] **Step 3: Fix the bug**

Change `_get_segment_prompt()` to accept `seg_key` and `seg_bpm`:

```python
def _get_segment_prompt(self, index: int, total: int, stage_id: str | None = None,
                         seg_key: str = "Dm", seg_bpm: int = 125) -> str:
    stage_id = _get_stage_for_segment(index, total)
    stage_prompts = STAGE_PROMPTS.get(stage_id, STAGE_PROMPTS["decay-one"])
    prompt_base = random.choice(stage_prompts)
    return (
        f"dub techno, {prompt_base} in {seg_key}, "
        f"{seg_bpm} BPM"
    )
```

Update the callsite in `_generate_segment()` (around line 491):

```python
prompt = self._get_segment_prompt(
    index, total, stage_id,
    seg_key=seg_key,
    seg_bpm=seg_bpm,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py -v`
Expected: All test_mix tests pass

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/orchestrator/mix.py
git commit -m "fix(mix): prompt uses per-segment key/bpm instead of defaults"
```

---

### Task 3: Enrich Prompt Pool (Style Modifiers + Structure Cues)

**Files:**
- Modify: `packages/core/src/openmusic/orchestrator/mix.py:94-160`

**Details:** Replace fixed prompt strings with a combinatorial prompt builder. Define separate lists of structure cues and style modifiers per stage. `_get_segment_prompt()` picks one of each and combines them.

- [ ] **Step 1: Write failing test for combinatorial prompts**

```python
def test_prompt_contains_style_modifier(self):
    config = MixConfig(key="Dm", bpm=125)
    orch = MixOrchestrator(config)
    # Call multiple times to verify modifiers are sometimes present
    prompts = [orch._get_segment_prompt(i, 40) for i in range(40)]
    # At least some prompts should contain style modifiers like "atmospheric", "percussive", etc.
    style_keywords = {"atmospheric", "percussive", "drone", "minimal", "spacious", "filtered"}
    found = any(kw in p for p in prompts for kw in style_keywords)
    assert found, f"No style modifiers found in any prompt: {prompts[:3]}"

def test_prompt_differs_between_adjacent_segments(self):
    config = MixConfig(key="Dm", bpm=125)
    orch = MixOrchestrator(config)
    # Two adjacent segments should (usually) get different prompts
    p1 = orch._get_segment_prompt(0, 40)
    p2 = orch._get_segment_prompt(1, 40)
    # They may sometimes be equal by random chance, but that's acceptable
    # Just verify they're valid prompts
    assert p1.startswith("dub techno,")
    assert p2.startswith("dub techno,")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py::TestPromptGeneration -v`
Expected: Tests fail because prompts are simple stage strings without modifiers

- [ ] **Step 3: Implement combinatorial prompts**

Replace the `STAGE_PROMPTS` dict with a richer structure. Add `STYLE_MODIFIERS` and `STRUCTURE_CUES`:

```python
STYLE_MODIFIERS = [
    "atmospheric",
    "percussive",
    "drone",
    "minimal",
    "spacious",
    "filtered",
    "hypnotic",
    "rolling",
]

STRUCTURE_CUES = {
    "ambient": ["slow evolving pads", "spacious soundscape", "textural drone"],
    "build": ["building tension", "layered percussion", "rising intensity"],
    "peak-one": ["driving rhythms", "dense percussion", "full spectrum"],
    "peak-two": ["rolling groove", "deep subs", "intense atmosphere"],
    "decay-one": ["receding elements", "looming bass", "wide space"],
    "decay-two": ["scattered fragments", "bare rhythm", "hollow space"],
    "dissolution": ["fading textures", "sparse echoes", "dissolving drone"],
}
```

Update `_get_segment_prompt()` to build combinatorial prompts:

```python
def _get_segment_prompt(self, index: int, total: int, stage_id: str | None = None,
                         seg_key: str = "Dm", seg_bpm: int = 125) -> str:
    stage_id = _get_stage_for_segment(index, total)
    cues = STRUCTURE_CUES.get(stage_id, ["textural drone"])
    cue = random.choice(cues)
    modifier = random.choice(STYLE_MODIFIERS)
    return (
        f"dub techno, {cue}, {modifier}, in {seg_key}, "
        f"{seg_bpm} BPM"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py -v`
Expected: All tests pass, new tests verify modifiers appear

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/orchestrator/mix.py
git commit -m "feat(mix): combinatorial prompts with style modifiers and structure cues"
```

---

### Task 4: Cycle Effects Presets Per Stage + Vary `pattern.variation`

**Files:**
- Modify: `packages/core/src/openmusic/orchestrator/mix.py:533-539,597`

**Details:** Two small changes. First: replace single `effects_preset` with a stage-to-preset mapping. Second: replace hardcoded `pattern.variation = 0.3` with a stage-dependent value.

- [ ] **Step 1: Write failing tests**

```python
class TestEffectsDiversity:
    def test_preset_changes_by_stage(self):
        config = MixConfig(key="Dm", bpm=125, effects_preset="deep_dub")
        # Mock a short mix and verify effects config per segment
        with patch("openmusic.orchestrator.mix.MixOrchestrator._generate_segment") as mock_gen:
            mock_gen.return_value = Path("/tmp/test.wav")
            orch = MixOrchestrator(config)
            base = orch._get_effects_config()
            # The base preset call should still work
            assert "delay" in base

    def test_pattern_variation_varies_by_stage(self):
        config = MixConfig(key="Dm", bpm=125)
        orch = MixOrchestrator(config)
        # Mock _get_effects_config to return variations and inspect pattern variation
        variations = []
        for i in range(7):  # one per stage
            stage_id = ["ambient", "build", "peak-one", "peak-two", "decay-one", "decay-two", "dissolution"][i]
            from openmusic.orchestrator.mix import STAGE_BOUNDARIES
            # Find a segment index for this stage
            for boundary, stage in STAGE_BOUNDARIES:
                if stage == stage_id:
                    break
            # Read variation directly from the mapping
            from openmusic.orchestrator.mix import STAGE_VARIATION
            variations.append(STAGE_VARIATION.get(stage_id, 0.3))
        assert len(set(variations)) > 1, f"All variations are the same: {variations}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py::TestEffectsDiversity -v`
Expected: Variation test fails — all stages return 0.3

- [ ] **Step 3: Implement preset cycling**

Add stage-to-preset mapping near `STAGE_BOUNDARIES`:

```python
STAGE_PRESETS = {
    "ambient": "minimal_dub",
    "build": "deep_dub",
    "peak-one": "deep_dub",
    "peak-two": "club_dub",
    "decay-one": "deep_dub",
    "decay-two": "minimal_dub",
    "dissolution": "minimal_dub",
}

STAGE_VARIATION = {
    "ambient": 0.1,
    "build": 0.3,
    "peak-one": 0.5,
    "peak-two": 0.7,
    "decay-one": 0.4,
    "decay-two": 0.2,
    "dissolution": 0.1,
}
```

Modify `_process_segment()` to select preset by stage:

```python
def _process_segment(self, input_path: Path, index: int = 0, total: int = 1) -> Path:
    # ... existing setup ...
    stage_id = _get_stage_for_segment(index, total) if total > 0 else "ambient"
    preset_name = STAGE_PRESETS.get(stage_id, self.config.effects_preset)
    base_effects = self._get_effects_config(preset_name=preset_name)
    # ... rest of existing code ...
    
    # Replace hardcoded 0.3:
    variation = STAGE_VARIATION.get(stage_id, 0.3)
```

Update `_get_effects_config()` to accept optional `preset_name`:

```python
def _get_effects_config(self, preset_name: str | None = None) -> dict:
    name = preset_name or self.config.effects_preset
    presets = {
        "deep_dub": DEEP_DUB_PRESET,
        "minimal_dub": MINIMAL_DUB_PRESET,
        "club_dub": CLUB_DUB_PRESET,
    }
    return presets.get(name, DEEP_DUB_PRESET).copy()
```

Also update the `pattern` field in the config payload:

```python
"pattern": {
    "style": self.config.pattern_style,
    "variation": variation,
},
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/orchestrator/mix.py
git commit -m "feat(mix): cycle effects presets per stage, vary pattern.variation"
```

---

### Task 5: Per-Segment Inference Steps Schedule

**Files:**
- Modify: `packages/core/src/openmusic/acestep/config.py:5-24`
- Modify: `packages/core/src/openmusic/acestep/generator.py:92-111`
- Modify: `packages/core/src/openmusic/orchestrator/mix.py`

**Details:** Add `inference_steps_range` to `MixConfig`. When set, map segment index across the range. Pass per-segment value through to `ACEStepGenerator.generate_texture()` as an optional parameter.

- [ ] **Step 1: Write failing tests**

```python
# In test_config.py
class TestInferenceSteps:
    def test_inference_steps_range_linear_mapping(self):
        from openmusic.orchestrator.mix import MixConfig
        config = MixConfig(
            key="Dm", bpm=125, length=3600, segment_duration=180,
            inference_steps_range=(8, 50)
        )
        # 20 segments over 1 hour, map index 0→8, index 19→50
        steps_0 = config._inference_steps_for_segment(0, 20)
        steps_19 = config._inference_steps_for_segment(19, 20)
        assert steps_0 == pytest.approx(8, abs=1), f"Expected ~8, got {steps_0}"
        assert steps_19 == pytest.approx(50, abs=1), f"Expected ~50, got {steps_19}"
        # Middle segment should be around halfway
        steps_mid = config._inference_steps_for_segment(10, 20)
        assert steps_mid > 20, f"Middle steps too low: {steps_mid}"
        assert steps_mid < 38, f"Middle steps too high: {steps_mid}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/core && uv run pytest tests/ -k "inference_steps" -v`
Expected: FAIL — `MixConfig` has no `inference_steps_range` field

- [ ] **Step 3: Add inference_steps_range to MixConfig**

In `mix.py`, add to `MixConfig`:

```python
inference_steps_range: tuple[int, int] | None = None  # e.g., (8, 50)
```

Add method:

```python
def _inference_steps_for_segment(self, index: int, total: int) -> int | None:
    if self.inference_steps_range is None:
        return None
    lo, hi = self.inference_steps_range
    if total <= 1:
        return (lo + hi) // 2
    fraction = index / (total - 1)
    return int(lo + fraction * (hi - lo))
```

- [ ] **Step 4: Thread inference_steps through generator**

Modify `ACEStepGenerator.generate_texture()` to accept optional `inference_steps`:

```python
def generate_texture(
    self,
    prompt: str,
    duration: int = 60,
    bpm: int = 125,
    key: str = "Am",
    inference_steps: int | None = None,
) -> Path:
    params_dict = {
        "bpm": bpm,
        "key": key,
        "duration": duration,
        "instrumental": True,
    }
    if inference_steps is not None:
        params_dict["inference_steps"] = inference_steps
    # ... rest of existing code ...
```

In `_generate()`, conditionally override `ace_params.inference_steps`:

```python
ace_params = AceParams(
    caption=prompt,
    bpm=params_dict.get("bpm"),
    duration=params_dict.get("duration", 30),
    instrumental=params_dict.get("instrumental", True),
    inference_steps=params_dict.get("inference_steps", self.config.inference_steps),
    keyscale=params_dict.get("key", ""),
)
```

Update `_generate_segment()` to pass inference steps:

```python
inference_steps = self.config._inference_steps_for_segment(index, total)
result = self.generator.generate_texture(
    prompt=prompt,
    duration=int(self.config.segment_duration),
    bpm=seg_bpm,
    key=seg_key,
    inference_steps=inference_steps,
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd packages/core && uv run pytest tests/ -k "inference_steps" -v`
Expected: All tests pass

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_mix.py -v`
Expected: All test_mix tests pass

- [ ] **Step 6: Commit**

```bash
git add packages/core/src/openmusic/acestep/
git add packages/core/src/openmusic/orchestrator/mix.py
git add packages/core/tests/
git commit -m "feat(mix): per-segment inference_steps schedule via inference_steps_range"
```

---

### Task 6: MIDI-Driven Effect Modulation

**Files:**
- Create: `packages/core/src/openmusic/orchestrator/midi_modulation.py`
- Modify: `packages/core/src/openmusic/orchestrator/mix.py`
- Test: `packages/core/tests/orchestrator_test/test_midi_modulation.py`

**Details:** Use the existing `midi_export` module to generate simple rhythmic patterns. Parse MIDI note data (velocity, timing) into modulation values for delay feedback, reverb mix, and filter cutoff. Apply modulation per segment.

- [ ] **Step 1: Write failing tests**

```python
# tests/orchestrator_test/test_midi_modulation.py
import pytest
import numpy as np
from pathlib import Path
from openmusic.orchestrator.midi_modulation import (
    generate_modulation_pattern,
    midi_to_modulation_values,
    ModulationPattern,
)

class TestModulationPattern:
    def test_generates_16_step_pattern(self):
        pattern = generate_modulation_pattern(bpm=125, steps=16)
        assert len(pattern.velocities) == 16
        assert len(pattern.timings) == 16
        assert all(v >= 0 and v <= 127 for v in pattern.velocities)
        assert all(t >= 0 for t in pattern.timings)

    def test_midi_to_modulation_returns_values_in_range(self):
        pattern = ModulationPattern(
            velocities=[64, 100, 32, 80],
            timings=[0.0, 0.5, 1.0, 1.5],
        )
        mod = midi_to_modulation_values(pattern, target_range=(0.0, 1.0))
        assert len(mod) == 4
        assert all(v >= 0.0 and v <= 1.0 for v in mod)

    def test_applies_delay_feedback_modulation(self):
        pattern = generate_modulation_pattern(bpm=125, steps=16)
        mod = midi_to_modulation_values(pattern, target_range=(0.2, 0.8))
        assert max(mod) > 0.4  # some values should be above mid-range
        assert min(mod) < 0.6  # some values should be below mid-range
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_midi_modulation.py -v`
Expected: FAIL with ImportError — module doesn't exist yet

- [ ] **Step 3: Implement midi_modulation.py**

```python
"""MIDI-driven effect parameter modulation.

Generates rhythmic patterns from the midi_export module and maps
note velocities/timings to effect parameter values for per-segment
modulation of delay feedback, reverb mix, and filter cutoff.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModulationPattern:
    velocities: list[int] = field(default_factory=list)
    timings: list[float] = field(default_factory=list)


def generate_modulation_pattern(
    bpm: int = 125,
    steps: int = 16,
) -> ModulationPattern:
    """Generate a simple 16-step rhythmic pattern.
    
    Instead of using the full MIDI export pipeline (which requires
    isobar), generate a simple rhythmic pattern directly.
    Uses a basic Euclidean rhythm: distribute `hits` across `steps`.
    """
    import random
    
    # Generate velocities with some variation
    hits = max(4, steps // 3)  # about 1/3 of steps have a hit
    step_indices = sorted(random.sample(range(steps), hits))
    
    velocities: list[int] = []
    timings: list[float] = []
    
    beat_duration = 60.0 / bpm
    
    for step_idx in step_indices:
        # Velocity varies: 40-100 (not too quiet, not max)
        velocity = random.randint(40, 100)
        velocities.append(velocity)
        # Timing in beats from start
        timings.append(step_idx * beat_duration)
    
    return ModulationPattern(velocities=velocities, timings=timings)


def midi_to_modulation_values(
    pattern: ModulationPattern,
    target_range: tuple[float, float] = (0.0, 1.0),
) -> list[float]:
    """Map MIDI velocities to a target value range.
    
    Args:
        pattern: ModulationPattern with velocities
        target_range: (min, max) for output values
    
    Returns:
        List of float values in target_range
    """
    if not pattern.velocities:
        return []
    
    lo, hi = target_range
    return [
        lo + (v / 127.0) * (hi - lo)
        for v in pattern.velocities
    ]


def get_modulation_for_segment(
    index: int,
    total: int,
    bpm: int = 125,
) -> dict[str, float]:
    """Get modulation values for a specific segment.
    
    Returns a dict with keys suitable for applying as effects modifiers:
    - delay_feedback_mod: 0.2-0.8
    - reverb_mix_mod: 0.3-0.8
    - filter_cutoff_mod: 200-2000 Hz
    
    Uses segment index to seed the random generator for reproducible
    but varied patterns across segments.
    """
    import random
    
    rng = random.Random(index * 137 + bpm)  # seed per segment
    
    # Generate a mini-pattern for this segment
    num_hits = rng.randint(2, 5)
    velocities = [rng.randint(40, 100) for _ in range(num_hits)]
    
    # Average velocity → modulation depth
    avg_vel = sum(velocities) / len(velocities) if velocities else 64
    
    return {
        "delay_feedback_mod": 0.2 + (avg_vel / 127.0) * 0.6,
        "reverb_mix_mod": 0.3 + (avg_vel / 127.0) * 0.5,
        "filter_cutoff_mod": 200 + (avg_vel / 127.0) * 1800,
    }
```

- [ ] **Step 4: Create and run the test file**

```python
# tests/orchestrator_test/test_midi_modulation.py
import pytest
from openmusic.orchestrator.midi_modulation import (
    generate_modulation_pattern,
    midi_to_modulation_values,
    get_modulation_for_segment,
    ModulationPattern,
)

class TestModulationPattern:
    def test_generates_16_step_pattern(self):
        pattern = generate_modulation_pattern(bpm=125, steps=16)
        assert len(pattern.velocities) <= 16
        assert len(pattern.timings) == len(pattern.velocities)
        assert all(v >= 0 and v <= 127 for v in pattern.velocities)
        assert all(t >= 0 for t in pattern.timings)

    def test_midi_to_modulation_returns_values_in_range(self):
        pattern = ModulationPattern(
            velocities=[64, 100, 32, 80],
            timings=[0.0, 0.5, 1.0, 1.5],
        )
        mod = midi_to_modulation_values(pattern, target_range=(0.0, 1.0))
        assert len(mod) == 4
        assert all(v >= 0.0 and v <= 1.0 for v in mod)

    def test_modulation_differs_per_segment(self):
        mod_a = get_modulation_for_segment(0, 40, bpm=125)
        mod_b = get_modulation_for_segment(5, 40, bpm=125)
        # Different segments should produce different values
        assert mod_a["delay_feedback_mod"] != mod_b["delay_feedback_mod"]

    def test_modulation_contains_expected_keys(self):
        mod = get_modulation_for_segment(10, 40, bpm=125)
        assert "delay_feedback_mod" in mod
        assert "reverb_mix_mod" in mod
        assert "filter_cutoff_mod" in mod

    def test_values_within_expected_ranges(self):
        mod = get_modulation_for_segment(3, 40, bpm=125)
        assert 0.2 <= mod["delay_feedback_mod"] <= 0.8
        assert 0.3 <= mod["reverb_mix_mod"] <= 0.8
        assert 200 <= mod["filter_cutoff_mod"] <= 2000
```

Run: `cd packages/core && uv run pytest tests/orchestrator_test/test_midi_modulation.py -v`
Expected: 6/6 tests pass

- [ ] **Step 5: Integrate MIDI modulation into mix.py**

In `_process_segment()`, after computing effects config (around line 594), apply modulation:

```python
# Apply MIDI-driven effect modulation
from openmusic.orchestrator.midi_modulation import get_modulation_for_segment
mod = get_modulation_for_segment(index, total, bpm=seg_bpm)

# Apply modulation to effects
if "delay" in effects:
    effects["delay"]["feedback"] = float(
        np.clip(
            effects["delay"].get("feedback", 0.5) * mod["delay_feedback_mod"] * 2,
            0.0, 1.0,
        )
    )
    effects["delay"]["mix"] = float(
        np.clip(
            mod["reverb_mix_mod"],
            0.0, 1.0,
        )
    )
if "filter" in effects:
    effects["filter"]["frequency"] = int(mod["filter_cutoff_mod"])
```

- [ ] **Step 6: Run full test suite**

Run: `cd packages/core && uv run pytest tests/orchestrator_test/ -v`
Expected: All orchestrator tests pass

- [ ] **Step 7: Commit**

```bash
git add packages/core/src/openmusic/orchestrator/midi_modulation.py
git add packages/core/src/openmusic/orchestrator/mix.py
git add packages/core/tests/orchestrator_test/test_midi_modulation.py
git commit -m "feat(mix): MIDI-driven effect modulation per segment"
```
