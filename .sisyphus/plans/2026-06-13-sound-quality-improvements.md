# Sound Quality Improvements — 3-Tier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 17 targeted improvements across effects wiring, dub techno production techniques, and technical quality to significantly improve mix sound quality.

**Architecture:** Three independent tiers executed in order. Tier 1 wires existing dead code (highest impact/effort). Tier 2 adds professional dub techniques to the DSP pipeline. Tier 3 fixes technical quality issues. Each task produces testable, verifiable changes.

**Tech Stack:** Python 3.12+, numpy, soundfile, pedalboard, pytest

---

## Tier 1: Wire What We Have (High Impact, Low Effort)

### Task 1.1: Wire SidechainCompression into PythonDSPBridge

**Files:**
- Modify: `packages/core/src/openmusic/bridge/pedalboard_bridge.py`
- Test: `packages/core/tests/test_bridge/test_pedalboard_bridge.py`

- [ ] **Step 1: Add sidechain compression to PythonDSPBridge.process()**

After the main Pedalboard chain processing and before mastering, add SidechainCompression as an additional processing step. Add `sidechain` parameter to `__init__`:

```python
def __init__(
    self,
    preset: str = "deep_dub",
    apply_mastering: bool = True,
    target_lufs: float = -16.0,
    sidechain_enabled: bool = True,
    sidechain_threshold_db: float = -24,
    sidechain_ratio: float = 4.0,
    sidechain_release_ms: float = 300,
):
    self.preset_name = preset
    self.apply_mastering = apply_mastering
    self.target_lufs = target_lufs
    self.sidechain_enabled = sidechain_enabled
    self.sidechain_threshold_db = sidechain_threshold_db
    self.sidechain_ratio = sidechain_ratio
    self.sidechain_release_ms = sidechain_release_ms
```

In `process()`, after `processed = chain.board(audio, sample_rate)`:

```python
# Apply sidechain compression (internal envelope follower, no external sidechain input)
if self.sidechain_enabled:
    from openmusic.effects.compression import SidechainCompression
    sc = SidechainCompression()
    processed = sc.process(processed, {
        "threshold_db": self.sidechain_threshold_db,
        "ratio": self.sidechain_ratio,
        "release_ms": self.sidechain_release_ms,
        "attack_ms": 10,
        "knee_db": 3,
        "wet_dry_mix": 80,
        "sample_rate": sample_rate,
    })
```

- [ ] **Step 2: Run existing tests to verify no regressions**

```bash
cd packages/core && uv run pytest tests/test_bridge/test_pedalboard_bridge.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/bridge/pedalboard_bridge.py
git commit -m "feat(effects): wire SidechainCompression into PythonDSPBridge"
```

### Task 1.2: Wire MidSideStereoWidener into PythonDSPBridge (with mono-below-150Hz)

**Files:**
- Modify: `packages/core/src/openmusic/bridge/pedalboard_bridge.py`
- Test: `packages/core/tests/test_bridge/test_pedalboard_bridge.py`

- [ ] **Step 1: Add M/S processing after sidechain but before mastering**

Add `ms_enabled` parameter to `__init__` (default `True`). In `process()`, after sidechain compression:

```python
# Apply mid-side stereo processing with mono sub-bass
if self.ms_enabled:
    from openmusic.effects.stereo import MidSideStereoWidener
    ms = MidSideStereoWidener()
    processed = ms.process(processed, {
        "stereo_width": 1.0,
        "sample_rate": sample_rate,
    })
```

This also fulfills Tier 2 item #9 (mono below 150Hz) since the M/S encode/decode naturally gives us control. For explicit mono-below-150, we'll also add a brickwall lowpass → mono sum for <150Hz as a separate step. Add:

```python
# Mono sub-bass below 150Hz (club compatibility)
# Sum L+R below 150Hz to mono, keep stereo above
from scipy import signal
if hasattr(processed, 'shape') and processed.shape[0] == 2:
    sos = signal.butter(4, 150, 'lowpass', fs=sample_rate, output='sos')
    sub_l = signal.sosfilt(sos, processed[0])
    sub_r = signal.sosfilt(sos, processed[1])
    sub_mono = (sub_l + sub_r) / 2
    processed[0] = processed[0] - sub_l + sub_mono
    processed[1] = processed[1] - sub_r + sub_mono
```

Note: if scipy isn't available, use simpler approach: FFT-based split at 150Hz.

- [ ] **Step 2: Run tests**

```bash
cd packages/core && uv run pytest tests/test_bridge/test_pedalboard_bridge.py tests/test_effects/test_stereo.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/bridge/pedalboard_bridge.py
git commit -m "feat(effects): wire MidSideStereoWidener + mono-below-150Hz into PythonDSPBridge"
```

### Task 1.3: Wire LFO Modulation Engine (stop being pass-through)

**Files:**
- Modify: `packages/core/src/openmusic/effects/lfo.py`
- Test: `packages/core/tests/test_effects/test_lfo.py`

- [ ] **Step 1: Update LFOModulationEngine.process() to apply modulation to audio**

The LFO generates the correct modulation_curve, then returns audio.copy(). Change it to apply the modulation as gain modulation:

```python
def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """Process audio with LFO modulation.
    
    Applies amplitude modulation using the LFO curve. The modulation
    creates a tremolo effect that can be subtle or extreme.
    """
    waveform = str(params.get("waveform", "sine"))
    rate_hz = float(params.get("rate_hz", 1.0))
    depth = float(params.get("depth", 50.0))
    phase_offset = float(params.get("phase_offset", 0.0))
    sample_rate = int(params.get("sample_rate", 48000))
    
    rate_hz = np.clip(rate_hz, 0.1, 20.0)
    depth = np.clip(depth, 0.0, 100.0)
    phase_offset = np.clip(phase_offset, 0.0, 1.0)
    
    valid_waveforms = {"sine", "triangle", "square", "random"}
    if waveform not in valid_waveforms:
        raise ValueError(...)
    
    modulation_curve = self._generate_lfo_curve(
        len(audio), waveform, rate_hz, phase_offset, sample_rate
    )
    
    # Map modulation_curve from [-1, 1] to [1-depth, 1+depth] range
    depth_decimal = depth / 100.0
    # Center around 1.0, oscillate by depth_decimal
    gain_mod = 1.0 + modulation_curve * depth_decimal
    
    # Apply gain modulation to audio
    if len(audio.shape) > 1 and audio.shape[0] == 2:
        # Stereo: apply same modulation to both channels
        return audio * gain_mod[np.newaxis, :]
    else:
        return audio * gain_mod
```

- [ ] **Step 2: Update LFO tests to reflect new behavior**

Update the test assertions that check "returns audio unchanged" — they should now verify that the output IS modulated. Add tests for different depths:

```python
def test_process_applies_amplitude_modulation(self):
    """Test that LFO actually modulates audio amplitude."""
    params = {"waveform": "sine", "rate_hz": 1.0, "depth": 100.0, "sample_rate": 48000}
    output = self.effect.process(self.audio_1s.copy(), params)
    # Should NOT be identical anymore
    assert not np.allclose(output, self.audio_1s, atol=1e-6)
    # Output should have same length
    assert output.shape == self.audio_1s.shape
    # At peak of sine (0.25 cycle), gain should be ~1.0 + 1.0 * 1.0 = 2.0 max
    # At trough, gain should be ~1.0 - 1.0 = 0.0
    max_abs = np.max(np.abs(output))
    assert max_abs <= np.max(np.abs(self.audio_1s)) * 2.0
```

```python
def test_zero_depth_passthrough(self):
    """Test that 0% depth leaves audio unchanged."""
    params = {"waveform": "sine", "rate_hz": 1.0, "depth": 0.0, "sample_rate": 48000}
    output = self.effect.process(self.audio_1s.copy(), params)
    np.testing.assert_allclose(output, self.audio_1s, atol=1e-10)
```

- [ ] **Step 3: Actually run tests to verify**

```bash
cd packages/core && uv run pytest tests/test_effects/test_lfo.py -v
```

Expected: Old pass-through tests fail, new tests pass.

Wait — we need to UPDATE not ADD. The old tests assert pass-through behavior. We must update them. The existing `test_process_returns_audio_unchanged` at line 22-34 asserts `np.testing.assert_allclose(output, self.audio_1s)`. Change it to:

```python
def test_process_modulates_at_100_percent_depth(self):
    """Test that LFO modulates audio at 100% depth."""
    params = {
        "waveform": "sine",
        "rate_hz": 1.0,
        "depth": 100.0,
        "sample_rate": 48000,
    }
    output = self.effect.process(self.audio_1s.copy(), params)
    # Should be modulated, not identical
    assert output.shape == self.audio_1s.shape
    assert not np.allclose(output, self.audio_1s, atol=1e-6)
```

Also update `test_sine_waveform_generates_curve`, `test_triangle_waveform_generates_curve`, etc. to not assert pass-through.

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/openmusic/effects/lfo.py packages/core/tests/test_effects/test_lfo.py
git commit -m "feat(effects): wire LFO modulation engine to actually modulate audio"
```

### Task 1.4: Use GenerationParams dataclass in generator.py

**Files:**
- Modify: `packages/core/src/openmusic/acestep/generator.py`
- Modify: `packages/core/src/openmusic/acestep/config.py` (extend GenerationParams)

- [ ] **Step 1: Extend GenerationParams with inference_steps field**

In `config.py`, add `inference_steps` to GenerationParams:

```python
@dataclass
class GenerationParams:
    """Parameters for a single audio generation request."""
    prompt: str = ""
    bpm: int | None = None
    key: str | None = None
    duration: int = 30
    instrumental: bool = True
    inference_steps: int | None = None
```

- [ ] **Step 2: Update generate_texture() to use GenerationParams**

Change `generate_texture()` in `generator.py` to accept `GenerationParams` as an alternative to individual kwargs (maintain backward compat):

```python
def generate_texture(
    self,
    prompt: str,
    duration: int = 60,
    bpm: int = 125,
    key: str = "Am",
    inference_steps: int | None = None,
    params: GenerationParams | None = None,
) -> Path:
    if params is not None:
        params_dict = {
            "bpm": params.bpm or bpm,
            "key": params.key or key,
            "duration": params.duration or duration,
            "instrumental": params.instrumental,
        }
        if params.inference_steps is not None:
            params_dict["inference_steps"] = params.inference_steps
    else:
        params_dict = {
            "bpm": bpm,
            "key": key,
            "duration": duration,
            "instrumental": True,
        }
        if inference_steps is not None:
            params_dict["inference_steps"] = inference_steps
    ...
```

- [ ] **Step 3: Run existing tests**

```bash
cd packages/core && uv run pytest tests/ -k "acestep" -v
```

Expected: PASS (or skip if ACE-Step not installed)

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/openmusic/acestep/ packages/core/src/openmusic/acestep/config.py
git commit -m "feat(acestep): use GenerationParams dataclass in generate_texture()"
```

### Task 1.5: Wire Quality Feedback in MixOrchestrator

**Files:**
- Modify: `packages/core/src/openmusic/orchestrator/mix.py`

- [ ] **Step 1: Add quality telemetry after segment processing**

In `MixOrchestrator.generate_mix()`, after processing each segment, store the segment path and call `set_quality_feedback` with a preliminary score based on RMS level:

```python
def generate_mix(self) -> Path:
    segments: list[Path] = []
    for i in range(self.segment_count):
        raw = self._generate_segment(i, self.segment_count)
        processed = self._process_segment(raw, i, self.segment_count)
        segments.append(processed)
        
        # Provide quality feedback to Bayesian selector
        if (self._pattern_selector is not None 
            and self.config.use_bayesian_markov
            and hasattr(self._pattern_selector, 'set_quality_feedback')):
            try:
                audio, sr = sf.read(str(processed))
                # Simple quality metric: RMS level relative to peak
                rms = np.sqrt(np.mean(audio ** 2))
                peak = np.max(np.abs(audio))
                if peak > 0:
                    crest_factor = peak / rms
                    # Lower crest factor = more consistent level = "better" for dub
                    # Map to 0-1 range: crest factor ~3-12 typical, invert so 3→1.0, 12→0.0
                    quality = max(0.0, min(1.0, 1.0 - (crest_factor - 3.0) / 9.0))
                    self._pattern_selector.set_quality_feedback(str(processed), quality)
            except Exception:
                pass  # Non-critical feedback — don't break generation
    ...
```

- [ ] **Step 2: Run tests**

```bash
cd packages/core && uv run pytest tests/test_patterns/test_bayesian.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/orchestrator/mix.py
git commit -m "feat(orchestrator): wire quality feedback for Bayesian pattern selector"
```

---

## Tier 2: Professional Dub Techniques (High Impact, Medium Effort)

### Task 2.1: Fix Effects Chain Order - Saturation First

**Files:**
- Modify: `packages/core/src/openmusic/effects/pedalboard_chain.py`
- Modify: `packages/core/src/openmusic/effects/__init__.py` (export TapeSaturation)
- Test: `packages/core/tests/test_effects/test_saturation.py`

- [ ] **Step 1: Add TapeSaturation to the Pedalboard chain**

Dub techno canonical order: Source → Saturation → Filter → Delay → Reverb → Chorus → Gain

Current order: HPF → LPF → Delay → Reverb → Chorus → Distortion → Gain

The Distortion pedalboard effect works differently from our TapeSaturation (tanh soft-clip). The Pedalboard Pedalboard-based chain should use the built-in Distortion at a very low drive (more like saturation), but we can't easily inject our numpy TapeSaturation into the middle of a Pedalboard chain (Pedalboard operates on buffered audio, not numpy arrays mid-chain).

**Solution:** Add TapeSaturation as a standalone pre-processing step in PythonDSPBridge BEFORE feeding into the Pedalboard chain. Update the Pedalboard chain to remove Distortion (since we handle saturation externally).

Modify `pedalboard_chain.py`:

```python
def _build_chain(self, p: dict) -> Pedalboard:
    """Build a Pedalboard chain from preset parameters."""
    return Pedalboard(
        [
            # No HPF here — we handle pre-filter + saturation in PythonDSPBridge
            LowpassFilter(cutoff_frequency_hz=p["filter_cutoff_hz"]),
            Delay(
                delay_seconds=p["delay_seconds"],
                feedback=p["delay_feedback"],
                mix=p["delay_mix"],
            ),
            Reverb(
                room_size=p["reverb_room_size"],
                damping=p["reverb_damping"],
                wet_level=p["reverb_wet"],
                dry_level=p["reverb_dry"],
            ),
            Chorus(rate_hz=p["chorus_rate_hz"], depth=p["chorus_depth"]),
            Gain(gain_db=p["output_gain_db"]),
        ]
    )
```

Note: Removed HighpassFilter (moved to PythonDSPBridge), removed Distortion (replaced by TapeSaturation in PythonDSPBridge).

- [ ] **Step 2: Update PythonDSPBridge.process() to add pre-saturation + HPF**

In `pedalboard_bridge.py`, before `processed = chain.board(audio, sample_rate)`:

```python
# Pre-processing: HPF + Tape Saturation (before Pedalboard chain)
# Canonical dub chain: Source → Saturation → Filter → Delay → Reverb
from openmusic.effects.saturation import TapeSaturation

# Add TapeSaturation (light, 20-30% wet)
sat = TapeSaturation()
audio = sat.process(audio, {
    "drive": 20,
    "wet_dry_mix": 30,
})

# Also apply gentle highpass before the chain (removes subsonic rumble)
from scipy import signal
sos = signal.butter(4, 30, 'highpass', fs=sample_rate, output='sos')
if audio.ndim == 1:
    audio = signal.sosfilt(sos, audio)
else:
    for ch in range(audio.shape[1]):
        audio[:, ch] = signal.sosfilt(sos, audio[:, ch])
```

Note: Add import guard for scipy (fallback to simple DC blocking if unavailable).

- [ ] **Step 3: Run tests**

```bash
cd packages/core && uv run pytest tests/test_effects/test_saturation.py tests/test_bridge/test_pedalboard_bridge.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/openmusic/effects/pedalboard_chain.py packages/core/src/openmusic/bridge/pedalboard_bridge.py
git commit -m "feat(effects): fix chain order - saturation before filter/delay/reverb"
```

### Task 2.2: Add Bandpass Filter in Delay Feedback Path

**Files:**
- Modify: `packages/core/src/openmusic/effects/delay.py`
- Test: `packages/core/tests/test_effects/test_delay.py`

- [ ] **Step 1: Add filtered feedback option to MultiTapDelay**

The Basic Channel signature sound involves a bandpass filter (~450Hz) in the delay feedback path. The feedback signal gets filtered before being fed back into the delay line.

Add new parameters: `feedback_filter_freq`, `feedback_filter_q`, `feedback_filter_enabled` to `process()`:

```python
feedback_filter_enabled = bool(params.get("feedback_filter_enabled", False))
feedback_filter_freq = float(params.get("feedback_filter_freq", 450.0))
feedback_filter_q = float(params.get("feedback_filter_q", 2.0))
```

In the feedback loop (around line 102-104 in delay.py), add filtering:

```python
if feedback > 0:
    for i in range(delay_samples, len(left)):
        delayed[i] += delayed[i - delay_samples] * feedback
    # Apply bandpass filter to feedback if enabled
    if feedback_filter_enabled:
        # Simple IIR bandpass using difference equation
        # 2nd-order bandpass: center freq = feedback_filter_freq, Q = feedback_filter_q
        # Use biquad coefficients
        w0 = 2 * np.pi * feedback_filter_freq / sample_rate
        alpha = np.sin(w0) / (2 * feedback_filter_q)
        b0 = alpha
        b1 = 0
        b2 = -alpha
        a0 = 1 + alpha
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha
        # Normalize
        b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0
        # Apply filter to delayed signal
        filtered = np.zeros_like(delayed)
        for i in range(2, len(delayed)):
            filtered[i] = (b0 * delayed[i] + b1 * delayed[i-1] + b2 * delayed[i-2]
                          - a1 * filtered[i-1] - a2 * filtered[i-2])
        delayed = filtered
```

Note: The biquad is applied per-tap to the feedback signal only. This creates the signature "filtered echo" sound.

- [ ] **Step 2: Add tests**

```python
def test_feedback_filter_applies_bandpass(self):
    """Test that feedback filter modifies delay signal."""
    audio = np.sin(np.linspace(0, 4 * np.pi, 48000))
    params = {
        "num_taps": 1,
        "tap_times_ms": [100],
        "tap_feedback": [0.5],
        "master_feedback": 0.5,
        "wet_dry": 100,
        "sample_rate": 48000,
        "feedback_filter_enabled": True,
        "feedback_filter_freq": 450.0,
        "feedback_filter_q": 2.0,
    }
    filtered = self.effect.process(audio.copy(), params)
    
    params_no_filter = dict(params)
    params_no_filter["feedback_filter_enabled"] = False
    unfiltered = self.effect.process(audio.copy(), params_no_filter)
    
    # Filtered should differ from unfiltered
    assert not np.allclose(filtered, unfiltered, atol=1e-6)
```

- [ ] **Step 3: Run tests**

```bash
cd packages/core && uv run pytest tests/test_effects/test_delay.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/openmusic/effects/delay.py packages/core/tests/test_effects/test_delay.py
git commit -m "feat(effects): add bandpass filter in delay feedback path (Basic Channel style)"
```

### Task 2.3: Dual Delay with Detune

**Files:**
- Add: `packages/core/src/openmusic/effects/dual_delay.py`
- Add: `packages/core/tests/test_effects/test_dual_delay.py`
- Modify: `packages/core/src/openmusic/effects/__init__.py`

- [ ] **Step 1: Create DualDelay effect with pitch detune**

Create a new effect that runs two parallel delay lines with slightly detuned pitch:

```python
"""Dual delay with pitch detune for dub techno width."""
from typing import Any, Dict
import numpy as np
from .base import Effect

class DualDelay(Effect):
    """Parallel dual delay with pitch detune.
    
    Two delays: one at dotted-8th (75% of quarter), one at quarter note.
    Each is hard-panned opposite and slightly pitch-detuned (±X cents).
    Creates the wide, spatial echo signature of dub techno.
    """
    
    def __init__(self):
        self.name = "dual_delay"
    
    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        delay1_ms = float(params.get("delay1_ms", 375))      # Dotted 8th at 125 BPM
        delay2_ms = float(params.get("delay2_ms", 500))      # Quarter note
        feedback1 = float(params.get("feedback1", 0.4))
        feedback2 = float(params.get("feedback2", 0.3))
        mix = float(params.get("mix", 0.5))
        detune_cents = float(params.get("detune_cents", 3.0))
        sample_rate = int(params.get("sample_rate", 48000))
        
        is_stereo = len(audio.shape) > 1 and audio.shape[0] == 2
        
        if is_stereo:
            left = audio[0].copy()
            right = audio[1].copy()
        else:
            left = audio.copy()
            right = audio.copy()
        
        def _delay_line(signal: np.ndarray, delay_ms: float, fb: float, detune: float) -> np.ndarray:
            delay_samples = int(delay_ms / 1000.0 * sample_rate)
            out = np.zeros_like(signal)
            if delay_samples >= len(signal):
                return out
            out[delay_samples:] = signal[:-delay_samples]
            if fb > 0:
                for i in range(delay_samples, len(signal)):
                    out[i] += out[i - delay_samples] * fb
            # Simple pitch detune via linear interpolation (resampling)
            if abs(detune) > 0.01:
                # Detune ratio: 1 cent = 2^(1/1200)
                ratio = 2 ** (detune / 1200.0)
                # Create stretched/compressed version
                orig_indices = np.arange(len(out))
                new_indices = orig_indices * ratio
                new_indices = np.clip(new_indices, 0, len(out) - 1)
                # Linear interpolation
                idx_floor = np.floor(new_indices).astype(int)
                idx_ceil = np.minimum(idx_floor + 1, len(out) - 1)
                frac = new_indices - idx_floor
                out = out[idx_floor] * (1 - frac) + out[idx_ceil] * frac
            return out
        
        # Tap 1: panned left, -detune
        tap1_left = _delay_line(left, delay1_ms, feedback1, -detune_cents)
        tap1_right = _delay_line(right, delay1_ms, feedback1, -detune_cents) * 0.3  # bleed
        
        # Tap 2: panned right, +detune  
        tap2_left = _delay_line(left, delay2_ms, feedback2, detune_cents) * 0.3
        tap2_right = _delay_line(right, delay2_ms, feedback2, detune_cents)
        
        # Mix
        wet = np.zeros_like(audio)
        if is_stereo:
            wet[0] = tap1_left * 0.707 + tap2_left * 0.707
            wet[1] = tap1_right * 0.707 + tap2_right * 0.707
        else:
            wet = tap1_left * 0.5 + tap2_right * 0.5
        
        return audio * (1 - mix) + wet * mix
```

- [ ] **Step 2: Add tests at tests/test_effects/test_dual_delay.py**

```python
import numpy as np
import pytest
from openmusic.effects.dual_delay import DualDelay

class TestDualDelay:
    def setup_method(self):
        self.effect = DualDelay()
    
    def test_initialization(self):
        assert self.effect.name == "dual_delay"
    
    def test_process_stereo(self):
        audio = np.random.randn(2, 48000) * 0.5
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
    
    def test_mono_passthrough(self):
        audio = np.random.randn(48000) * 0.5
        params = {"sample_rate": 48000}
        output = self.effect.process(audio, params)
        assert output.shape == audio.shape
    
    def test_detune_changes_signal(self):
        audio = np.sin(np.linspace(0, 8 * np.pi, 48000))
        params_no = {"sample_rate": 48000, "detune_cents": 0.0}
        params_yes = {"sample_rate": 48000, "detune_cents": 5.0}
        out_no = self.effect.process(audio.copy(), params_no)
        out_yes = self.effect.process(audio.copy(), params_yes)
        # With different detune, results should differ
        assert not np.allclose(out_no, out_yes, atol=1e-6)
    
    def test_zero_mix_identity(self):
        audio = np.random.randn(2, 48000) * 0.5
        params = {"sample_rate": 48000, "mix": 0.0}
        output = self.effect.process(audio, params)
        np.testing.assert_allclose(output, audio, atol=1e-10)
```

- [ ] **Step 3: Update __init__.py to export DualDelay**

```python
from .dual_delay import DualDelay
```

And add to `__all__`.

- [ ] **Step 4: Run tests**

```bash
cd packages/core && uv run pytest tests/test_effects/test_dual_delay.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/effects/dual_delay.py packages/core/tests/test_effects/test_dual_delay.py packages/core/src/openmusic/effects/__init__.py
git commit -m "feat(effects): add DualDelay with pitch detune for spatial dub echoes"
```

### Task 2.4: Parameter Automation - Connect automation.py primitives

**Files:**
- Create: `packages/core/src/openmusic/effects/parameter_automation.py`
- Add tests at `tests/test_effects/test_parameter_automation.py`

- [ ] **Step 1: Create ParameterAutomation effect**

Since the existing `automation.py` has Envelope, LFO, RandomWalk but they're not connected to any real parameter modulation, create a new effect that modulates audio using these primitives:

```python
"""Parameter automation effect - applies envelopes and LFOs to audio parameters."""
from typing import Any, Dict, Optional
import numpy as np
from .base import Effect
from .automation import Envelope, LFO, RandomWalk

class ParameterAutomation(Effect):
    """Modulates audio using parameter automation primitives.
    
    Applies gain/pan/filter envelopes to create evolving sound over time.
    """
    
    def __init__(self):
        self.name = "parameter_automation"
    
    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        auto_type = str(params.get("auto_type", "gain_envelope"))
        sample_rate = int(params.get("sample_rate", 48000))
        
        if auto_type == "gain_envelope":
            start = float(params.get("start", 0.0))
            end = float(params.get("end", 1.0))
            curve = str(params.get("curve", "linear"))
            env = Envelope(start, end, len(audio) if audio.ndim == 1 else audio.shape[-1], curve)
            curve_vals = env.generate()
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals
        
        elif auto_type == "tremolo":
            rate_hz = float(params.get("rate_hz", 2.0))
            depth = float(params.get("depth", 0.5))
            lfo = LFO(rate_hz=rate_hz, depth=depth, center=1.0, sample_rate=sample_rate)
            curve_vals = lfo.generate(len(audio) if audio.ndim == 1 else audio.shape[-1])
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals
        
        elif auto_type == "random_walk_gain":
            center = float(params.get("center", 1.0))
            max_dev = float(params.get("max_deviation", 0.2))
            step = float(params.get("step_size", 0.01))
            rw = RandomWalk(center=center, max_deviation=max_dev, step_size=step)
            curve_vals = rw.generate(len(audio) if audio.ndim == 1 else audio.shape[-1])
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals
        
        return audio.copy()
```

- [ ] **Step 2: Add tests**

- [ ] **Step 3: Update __init__.py**

- [ ] **Step 4: Run tests and commit**

---

## Tier 3: Technical Quality

### Task 3.1: Add Brickwall Limiter + Fix LUFS in MasteringChain

**Files:**
- Modify: `packages/core/src/openmusic/effects/mastering.py`
- Test: `packages/core/tests/test_effects/test_mastering.py` (create if doesn't exist)

- [ ] **Step 1: Add brickwall limiter and proper LUFS to MasteringChain**

Replace the RMS approximation with a two-stage approach: soft-clip limiter + proper LUFS calculation:

```python
class Limiter:
    """Simple brickwall limiter with lookahead."""
    
    def __init__(self, threshold_db: float = -1.0, release_ms: float = 100.0, sample_rate: int = 48000):
        self.threshold_linear = 10 ** (threshold_db / 20.0)
        self.release_coeff = np.exp(-1.0 / (release_ms / 1000.0 * sample_rate))
        self.envelope = 0.0
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        output = np.zeros_like(audio)
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        for ch in range(audio.shape[0]):
            self.envelope = 0.0
            for i in range(audio.shape[1]):
                abs_val = abs(audio[ch, i])
                if abs_val > self.envelope:
                    self.envelope = abs_val
                else:
                    self.envelope += (abs_val - self.envelope) * self.release_coeff
                if self.envelope > self.threshold_linear:
                    gain = self.threshold_linear / self.envelope
                    output[ch, i] = audio[ch, i] * gain
                else:
                    output[ch, i] = audio[ch, i]
        return output if audio.shape[0] > 1 else output[0]
```

Update `MasteringChain.__init__` to accept limiter params and add it to the processing chain:

```python
def __init__(
    self,
    target_lufs: float = -16.0,
    compressor_threshold_db: float = -20.0,
    compressor_ratio: float = 3.0,
    bass_gain_db: float = 2.0,
    treble_gain_db: float = -1.0,
    limiter_threshold_db: float = -1.0,
    limiter_enabled: bool = True,
):
    ...
    self.limiter_threshold_db = limiter_threshold_db
    self.limiter_enabled = limiter_enabled

def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
    processed = self.board(audio, sample_rate)
    
    # Improved LUFS approximation (ITU-R BS.1770-4 style)
    # Pre-filter: apply Leq(RLB) highpass
    from scipy import signal
    sos = signal.butter(4, 38, 'highpass', fs=sample_rate, output='sos')
    if processed.ndim == 1:
        filtered = signal.sosfilt(sos, processed)
    else:
        filtered = np.zeros_like(processed)
        for ch in range(processed.shape[-1] if processed.ndim > 1 else 1):
            filtered[..., ch] = signal.sosfilt(sos, processed[..., ch])
    
    # Mean square per channel (with gating - simplified: -70dB threshold)
    if filtered.ndim == 1:
        mean_sq = np.mean(filtered ** 2)
        # Simple gating: compute mean only where signal > -70dB
        gate_threshold = 10 ** (-70 / 20.0)
        above_gate = np.abs(filtered) > gate_threshold
        if np.any(above_gate):
            mean_sq = np.mean(filtered[above_gate] ** 2)
    else:
        ch_powers = []
        for ch in range(filtered.shape[-1]):
            ch_data = filtered[..., ch]
            gate_threshold = 10 ** (-70 / 20.0)
            above_gate = np.abs(ch_data) > gate_threshold
            if np.any(above_gate):
                ch_powers.append(np.mean(ch_data[above_gate] ** 2))
            else:
                ch_powers.append(np.mean(ch_data ** 2))
        # For stereo: apply 0dB (L) and -1.5dB (R) weighting per BS.1770
        if len(ch_powers) >= 2:
            mean_sq = ch_powers[0] + 10**(-1.5/10) * ch_powers[1]
        else:
            mean_sq = ch_powers[0]
    
    # LUFS = -0.691 + 10*log10(mean_sq)
    lufs = -0.691 + 10 * np.log10(max(mean_sq, 1e-20))
    
    # Apply gain to reach target LUFS
    gain_db = self.target_lufs - lufs
    gain_db = min(gain_db, 6.0)  # Limit boost
    processed = processed * (10 ** (gain_db / 20.0))
    
    # Apply brickwall limiter
    if self.limiter_enabled:
        limiter = Limiter(threshold_db=self.limiter_threshold_db, sample_rate=sample_rate)
        processed = limiter.process(processed)
    
    return processed
```

- [ ] **Step 2: Run tests**

```bash
cd packages/core && uv run pytest tests/ -k "mastering" -v
```

Expected: PASS (existing tests that use MasteringChain continue to work)

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/effects/mastering.py
git commit -m "feat(effects): add brickwall limiter and improved LUFS normalization to MasteringChain"
```

### Task 3.2: Fix/Delete Broken Spectral Masking Files

**Files:**
- Delete or fix: `packages/core/src/openmusic/effects/frequency_masking.py`
- Delete or fix: `packages/core/src/openmusic/effects/spectral_masking.py`
- Delete or fix: `packages/core/src/openmusic/effects/frequency_masking_avoidance.py`

- [ ] **Step 1: Check if any of these are imported anywhere**

```bash
cd packages/core && grep -r "frequency_masking\|spectral_masking" src/ --include="*.py"
```

If not imported (expected: they're not in __init__.py and never wired), **delete** them. They are dead code with syntax errors.

- [ ] **Step 2: Verify deletion doesn't break tests**

```bash
cd packages/core && uv run pytest tests/ -v 2>&1 | tail -20
```

Expected: No test failures related to frequency/spectral masking.

- [ ] **Step 3: Commit**

```bash
git rm packages/core/src/openmusic/effects/frequency_masking.py \
      packages/core/src/openmusic/effects/spectral_masking.py \
      packages/core/src/openmusic/effects/frequency_masking_avoidance.py
git commit -m "chore: remove broken, unwired spectral masking files"
```

### Task 3.3: Add Seed Parameter to ACEStepGenerator

**Files:**
- Modify: `packages/core/src/openmusic/acestep/generator.py`
- Modify: `packages/core/src/openmusic/acestep/config.py`

- [ ] **Step 1: Add seed to GenerationParams and generator**

In `config.py`, add `seed: int | None = None` to `GenerationParams`.

In `generator.py`, add `seed` parameter to `generate_texture()`:

```python
def generate_texture(
    self,
    prompt: str,
    duration: int = 60,
    bpm: int = 125,
    key: str = "Am",
    inference_steps: int | None = None,
    params: GenerationParams | None = None,
    seed: int | None = None,
) -> Path:
```

If `seed` is set (either directly or via `params.seed`), pass it to ACE-Step's `GenerationParams`. ACE-Step's `AceParams` may or may not support seed — add it as a dictionary key if their API allows.

```python
ace_params = AceParams(
    caption=prompt,
    bpm=params_dict.get("bpm"),
    duration=params_dict.get("duration", 30),
    instrumental=params_dict.get("instrumental", True),
    inference_steps=params_dict.get("inference_steps", self.config.inference_steps),
    keyscale=params_dict.get("key", ""),
)
# Add seed if provided (ACE-Step may or may not support it)
if seed is not None:
    try:
        ace_params.seed = seed
    except (AttributeError, TypeError):
        logger.warning(f"ACE-Step does not support seed parameter, ignoring seed={seed}")
```

- [ ] **Step 2: Run tests**

- [ ] **Step 3: Commit**

### Task 3.4: Add TPDF Dithering to Export

**Files:**
- Modify: `packages/core/src/openmusic/export/encoder.py`

- [ ] **Step 1: Add dithering option to AudioEncoder**

Before writing FLAC output, apply Triangular Probability Density Function (TPDF) dithering to reduce quantization distortion:

```python
def _apply_tpdf_dither(self, audio: np.ndarray, bit_depth: int = 24) -> np.ndarray:
    """Apply TPDF dithering to reduce quantization distortion.
    
    Args:
        audio: Float audio in [-1, 1] range
        bit_depth: Target bit depth (16 or 24)
    Returns:
        Dithered audio
    """
    if bit_depth == 24:
        quant_level = 2 ** 23
    elif bit_depth == 16:
        quant_level = 2 ** 15
    else:
        return audio
    
    # TPDF noise: sum of two uniform random distributions
    noise = (np.random.uniform(-1, 1, audio.shape) + 
             np.random.uniform(-1, 1, audio.shape)) * 0.5
    noise = noise / quant_level
    
    return audio + noise
```

Add `dither` parameter to `encode_flac()`:

```python
def encode_flac(
    self,
    input_path: str | Path,
    output_path: str | Path,
    metadata: TrackMetadata | None = None,
    dither: bool = True,
    dither_bit_depth: int = 24,
) -> Path:
    ...
    # Read input
    import soundfile as sf
    audio, sr = sf.read(str(input_path))
    
    # Apply dithering
    if dither:
        audio = self._apply_tpdf_dither(audio, dither_bit_depth)
        # Write dithered audio to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        sf.write(temp_path, audio, sr, format='WAV')
        input_path = temp_path
    ...
```

Note: This adds soundfile dependency to encoder.py. If it's not already imported there, it needs to be. Or use ffmpeg's dither option instead:

```bash
# ffmpeg can do dithering natively
ffmpeg -i input.wav -c:a flac -sample_fmt s32 -dither_method triangular_hp output.flac
```

Actually, the FFMPEG dither method is cleaner. Just add `-dither_method triangular_hp` to the ffmpeg command in `encode_flac()`:

```python
cmd = [
    self.ffmpeg_path,
    "-y",
    "-i",
    str(input_path),
    "-c:a",
    "flac",
    "-sample_fmt",
    "s32",  # 24-bit encoding in s32 container
    "-dither_method",
    "triangular_hp",  # TPDF dithering
    "-ar",
    "48000",
]
```

- [ ] **Step 2: Run tests**

```bash
cd packages/core && uv run pytest tests/test_export/ -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/export/encoder.py
git commit -m "feat(export): add TPDF dithering to FLAC encoder via ffmpeg"
```

---

## Verification (Run After All Tasks)

- [ ] **Final: Run full test suite**

```bash
cd packages/core && uv run pytest tests/ -v --tb=short 2>&1 | tail -60
```

Expected: All tests pass (or unchanged count of pre-existing failures)
