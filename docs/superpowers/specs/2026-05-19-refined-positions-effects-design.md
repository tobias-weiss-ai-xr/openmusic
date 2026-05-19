# Refined Positions + Interpolated Effects Design

> **For agentic workers:** IMPLEMENTATION: Follow sections below. Confirm spec with user before proceeding.

---

## Goal

Add per-segment musical variation to OpenMusic through:
1. **Refined position stages:** 10 stages (vs. current 4) for more granular progression
2. **Effect interpolation:** Base preset + stage modifiers, linearly interpolated per segment
3. **Stage-aware prompts:** Unique prompt vibe for each of the 10 stages

---

## Architecture

**Data flow per segment:**

```
segment parameters (BPM, key) from schedule
         ↓
    stage determination (10-stage mapping)
         ↓
    ├──> prompt generation (stage-aware text)
    ├──> effects interpolation (base preset + modifiers)
    └──> ACE-Step generation + effects processing
         ↓
    segment audio
         ↓
    crossfade → final mix
```

**Components:**
- `MixConfig`: Add `effects_modifiers`, stage mapping
- `MixOrchestrator`: `interpolate_effects()`, `_get_stage_for_segment()`
- Generator prompt: 10-stage prompt dictionary
- CLI: `--effects-modifiers` flag

---

## Implementation Sections

### 1. Refined Position Stages

**Current:** 4 stages (intro, building, climax, outro), linear by segment index.

**New:** 10 stages with proportional mapping:

| Stage | Segment % of mix | Prompt Vibe | Effects Bias |
|---|---|---|---|
| `ambient-intro` | 0–10% | Subtle drift, sparse tones, ethereal | Minimal reverb, low filter |
| `early-build` | 10–25% | Layers emerge, gentle groove | Light delay, gradual filter |
| `mid-build` | 25–45% | Thickening texture, pushing | Tighter delay, deeper reverb |
| `pre-peak-one` | 45–60% | Tension building, restrained | Reduce filter, build feedback |
| `peak-one` | 60–75% | Maximum intensity | Full effects, heaviest |
| `post-peak` | 75–85% | Slight release, energetic | Reduce distortion slightly |
| `peak-two` | 85–100% | Second climax (optional) | Re-engage full effects |
| `decay-one` | 100–115% | Pulling back, driving | Lift filter, soften |
| `decay-two` | 115–130% | Fading, spacious | Open filter, less delay |
| `dissolution` | 130%+ | Dissolving into silence | Barely any wet signal |

**Mapping function:**

```python
# mix.py
STAGE_BOUNDARIES = [
    (0.00, "ambient-intro"),
    (0.10, "early-build"),
    (0.25, "mid-build"),
    (0.45, "pre-peak-one"),
    (0.60, "peak-one"),
    (0.75, "post-peak"),
    (0.85, "peak-two"),
    (1.00, "decay-one"),
    (1.15, "decay-two"),
    (1.30, "dissolution"),
]

def _get_stage_for_segment(segment_index: int, total_segments: int) -> str:
    """Return stage identifier for given segment position."""
    position = segment_index / total_segments
    for threshold, stage in reversed(STAGE_BOUNDARIES):
        if position >= threshold:
            return stage
    return "ambient-intro"  # Fallback
```

---

### 2. Effects Interpolation System

**Format:** Base preset + stage modifiers.

```
effects_modifiers: "early-build:delay+0.1,filter-100;peak-one:distortion*1.3;decay-one:reverb-2"
```

**Syntax parsing:**

- Modifiers separated by `;`
- Each modifier: `stage:param<operation>value`
- Operations: `+`, `-`, `*`, `/`
- Parameters: `delay`, `reverb`, `filter`, `distortion`, `vinyl`, `tape`

**Parser function:**

```python
# mix.py
from typing import Dict, List, Optional

def _parse_effects_modifiers(modifiers_str: Optional[str]) -> Dict[str, List[tuple]]:
    """Parse effects_modifiers string into {stage: [(param, op, value), ...]}."""
    if not modifiers_str:
        return {}

    result = {}
    for modifier in modifiers_str.split(";"):
        if ":" not in modifier:
            continue

        stage_part, param_part = modifier.split(":", 1)
        stage = stage_part.strip()

        if stage not in result:
            result[stage] = []

        for param_mod in param_part.split(","):
            param_mod = param_mod.strip()
            if not param_mod:
                continue

            # Extract operation and value
            op_idx = max(param_mod.find("+"), param_mod.find("-"),
                       param_mod.find("*"), param_mod.find("/"))
            if op_idx == 0:  # If operation is at index 0 (invalid)
                continue

            op = param_mod[op_idx] if op_idx >= 0 else "+"
            param = param_mod[:op_idx].strip()
            value = param_mod[op_idx+1:].strip()

            try:
                if "." in value:
                    val = float(value)
                else:
                    val = int(value)
            except ValueError:
                continue

            result[stage].append((param, op, val))

    return result
```

**Interpolation logic:**

```python
# mix.py
def _apply_modifier(base_value: float, param: str, op: str, value: float) -> float:
    """Apply single modifier to base value."""
    if op == "+":
        return base_value + value
    elif op == "-":
        return base_value - value
    elif op == "*":
        return base_value * value
    elif op == "/":
        return base_value / value
    return base_value


def interpolate_effects(base_preset: str, modifiers: Dict[str, List[tuple]],
                       stage_id: str, segment_position: float) -> dict:
    """Interpolate effects config for given segment."""
    import copy

    # Load base preset
    if base_preset == "deep_dub":
        base = DEEP_DUB.copy()
    elif base_preset == "minimal_dub":
        base = MINIMAL_DUB.copy()
    elif base_preset == "club_dub":
        base = CLUB_DUB.copy()
    else:
        base = DEEP_DUB.copy()

    # Apply modifiers for current stage
    if stage_id in modifiers:
        for param, op, value in modifiers[stage_id]:
            if param in base:
                base[param] = _apply_modifier(base[param], param, op, value)

    # Interpolate between modifier applications could be implemented here
    # For now, discrete stage changes

    return base
```

---

### 3. Stage-Aware Prompts

**Generator prompt dictionary:**

```python
# generator.py (or new prompts.py)
STAGE_PROMPTS = {
    "ambient-intro": "Deep ambient textures, subtle drift, barely-there rhythm, ethereal atmosphere",
    "early-build": "Layers emerge, gentle groove introduction, soft percussive elements",
    "mid-build": "Thickening texture, rhythmic intensity builds, fuller sound palette",
    "pre-peak-one": "Tension building, restrained energy, anticipation of release",
    "peak-one": "Maximum intensity, driving rhythm, full frequency spectrum, powerful energetic flow",
    "post-peak": "Slight release, energetic but easing, still driving forward",
    "peak-two": "Second climax, energetic return, reinforcing intensity",
    "decay-one": "Pulling back, driving but loosening, tension gradually releasing",
    "decay-two": "Fading into space, spacious atmosphere, elements dissolving",
    "dissolution": "Minimal dissolution, echoes and whispers, fading into silence",
}
```

**Updated prompt generation:**

```python
# generator.py
def _get_segment_prompt(self, index: int, total_segments: int, stage_id: str) -> str:
    """Generate prompt for given segment with stage awareness."""
    from .orchestrator.mix import STAGE_PROMPTS

    base_prompt = STAGE_PROMPTS.get(stage_id, "Deep dub techno texture")

    return f"{base_prompt}, dub techno atmosphere"
```

---

### 4. MixConfig Updates

**Add `effects_modifiers` field:**

```python
# mix.py
@dataclass
class MixConfig:
    length: float
    bpm: int
    key: str
    output_path: str
    segment_duration: float = 180.0
    effects_preset: str = "deep_dub"
    effects_backend: str = "typescript"
    effects_modifiers: Optional[str] = None  # NEW
    skip_effects: bool = False
    # ... existing fields
```

---

### 5. CLI Integration

**Add flag:**

```python
# main.py (publish command)
@click.option(
    "--effects-modifiers",
    type=str,
    default=None,
    help="Effects modifiers in format: stage:param+value;stage:param*value",
)
def publish(
    effects_modifiers: Optional[str],
    # ... other params
):
    """Generate mix, render MP4, upload to YouTube."""
    # ...
    mix_config = MixConfig(
        effects_modifiers=effects_modifiers,
        # ...
    )
```

---

### 6. Integration Points

**Segment generation loop:**

```python
# mix.py (MixOrchestrator.generate_mix)
def generate_mix(self) -> Path:
    segment_count = math.ceil(self.config.length / self.config.segment_duration)
    segments = []

    # Parse modifiers once
    modifiers = _parse_effects_modifiers(self.config.effects_modifiers)

    for index in range(segment_count):
        # Determine stage
        stage_id = _get_stage_for_segment(index, segment_count)

        # Get per-segment BPM/key from schedule
        current_bpm = self.config.bpm_for_segment(index)
        current_key = self.config.key_for_segment(index)

        # Stage-aware prompt
        prompt = self._get_segment_prompt(index, segment_count, stage_id)

        # Generate
        raw_audio = self._generate_segment(index, prompt, current_bpm, current_key)

        # Interpolated effects
        effects_config = interpolate_effects(
            self.config.effects_preset,
            modifiers,
            stage_id,
            index / segment_count
        )

        processed_audio = self._process_segment(raw_audio, index, effects_config)
        segments.append(processed_audio)

        # Progress report with stage
        click.echo(f"  [{index+1}/{segment_count}] Stage: {stage_id}")

    return self._assemble_segments(segments)
```

---

## Testing

1. **Stage mapping:** Test `_get_stage_for_segment()` returns correct stage for various segment counts and positions
2. **Modifier parsing:** Test `_parse_effects_modifiers()` with valid and invalid strings
3. **Interpolation:** Test `interpolate_effects()` applies correct values to base preset
4. **End-to-end:** Generate short mix (3 segments) with modifiers, verify smooth transitions

---

## Error Handling

- Invalid modifier syntax → Skip silently, warn in logs
- Unknown stage name → Use nearest valid stage
- Invalid parameter name → Skip modifier
- Out-of-range effects values → Clamp to reasonable bounds

---

## Success Criteria

- All 10 stages map correctly across different segment counts
- Modifiers parse and apply without errors
- Per-segment effects values differ nontrivially with modifiers
- Prompts vary per stage
- Short test mix (3 segments) generates without errors

---

## Potential Future Enhancements

- Interpolate smoothly between modifier stages (currently discrete)
- More granular modifiers (oscillating values, LFO-like)
- Stage transitions with crossfade effects
- User-defined prompt templates per stage