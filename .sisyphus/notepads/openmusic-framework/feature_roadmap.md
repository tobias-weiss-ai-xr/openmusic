# OpenMusic Feature Roadmap

**Date**: 2026-04-01  
**Focus**: Dub Techno Generation Enhancement  
**Constraints**: CLI-only, no DAW/MIDI/real-time/web UI, no model training

---

## Prioritized Features

### Phase 1: Quick Wins (High Impact, Low Effort)

#### 1. Tape Saturation
- **Description**: Add tape saturation emulation effect module with drive, wet/dry, and bias controls. Uses soft-clipping (tanh) algorithm to add harmonic warmth.
- **Parameters**: `drive (0-100%)`, `wet_dry_mix`, `bias_tone`
- **Effort**: S (Small)
- **Impact**: 9/10
- **Implementation**: Use audiomentations TanhDistortion or implement simple tanh soft-clipping. Integrate into existing effects chain in `mixer.py`.

#### 2. Multi-Tap Delay
- **Description**: Multi-tap delay with programmable delay times per tap, individual feedback, and pan controls. Creates complex rhythmic patterns.
- **Parameters**: `num_taps`, `tap_times_ms`, `tap_feedback`, `tap_pan`, `master_feedback`, `wet_dry`
- **Effort**: S (Small)
- **Impact**: 7/10
- **Implementation**: Multiple delay buffers with independent parameters. Simple array-based implementation.

---

### Phase 2: Core Features (High Impact, Medium Effort)

#### 3. Granular Delay
- **Description**: Granular delay effect with grain_size, density, and randomization controls. Creates signature dub techno echo with textured, evolving repeats.
- **Parameters**: `grain_size_ms`, `grain_density`, `randomization_amount`, `feedback`, `wet_dry_mix`
- **Effort**: M (Medium)
- **Impact**: 10/10
- **Implementation**: Build on numpy array slicing and interpolation. Reference Red Panda's granular delay implementation.

#### 4. Mid-Side Stereo Widener
- **Description**: Mid-side processing module for stereo imaging control. Allows independent EQ/compression of mid (center) and side (stereo) channels.
- **Parameters**: `stereo_width`, `mid_eq`, `side_eq`, `side_compression`
- **Effort**: M (Medium)
- **Impact**: 8/10
- **Implementation**: M/S encoding: M = (L+R)/√2, S = (L-R)/√2. Process separately, then decode.

#### 5. Sidechain Compression
- **Description**: Sidechain compression module with configurable source tracking. Duck pads/ambience when kick hits, creating classic dub techno pumping rhythm.
- **Parameters**: `threshold`, `ratio`, `attack_ms`, `release_ms`, `knee`, `source_track`
- **Effort**: M (Medium)
- **Impact**: 9/10
- **Implementation**: Implement envelope follower on kick track, apply gain reduction to target.

---

### Phase 3: Advanced (Medium Impact, High Effort)

#### 6. LFO Modulation Engine
- **Description**: LFO-based parameter modulation system for effects automation. Supports sine, triangle, square, and random waveforms.
- **Parameters**: `waveform`, `rate_hz`, `depth`, `target_parameter`, `phase_offset`
- **Effort**: M (Medium)
- **Impact**: 8/10
- **Implementation**: Create LFO class that generates modulation curves. Apply to effect parameters during processing.

#### 7. Spectral Gating
- **Description**: Adaptive spectral gate that removes noise floor and creates rhythmic gating effects. Can be synced to tempo.
- **Parameters**: `threshold`, `attack`, `release`, `hold`, `sync_to_tempo`, `frequency_bands`
- **Effort**: M (Medium)
- **Impact**: 6/10
- **Implementation**: FFT-based analysis with threshold detection. Apply gain reduction to frequency bins.

#### 8. Frequency Masking Avoidance
- **Description**: Automated frequency carving system that detects overlapping frequency content between layers and applies subtle EQ cuts.
- **Parameters**: `sensitivity`, `max_cut_db`, `frequency_range`, `auto_detect`
- **Effort**: L (Large)
- **Impact**: 7/10
- **Implementation**: Requires FFT analysis (numpy.fft) to detect spectral overlap. Apply narrow EQ cuts at conflict frequencies.

---

## Architecture Recommendations

### Effects Module Structure
```
openmusic/effects/
├── __init__.py
├── base.py          # Base Effect class
├── saturation.py    # Tape saturation
├── delay.py         # Multi-tap, granular delay
├── stereo.py        # Mid-side processing
├── compression.py   # Sidechain compression
├── modulation.py    # LFO engine
└── spectral.py      # Spectral gating, frequency masking
```

### Integration Point
- Insert effects chain in `pipeline.py` between `GENERATE` and `PROCESS` stages
- Or integrate in `MixArranger.arrange_segments()`

### Config Extension
Add `effects_chain` array to `MixConfig` dataclass:
```python
@dataclass
class MixConfig:
    # ... existing fields ...
    effects_chain: List[EffectConfig] = field(default_factory=list)

@dataclass
class EffectConfig:
    type: str
    params: Dict[str, Any]
```

### Suggested Libraries
- `pedalboard` (Spotify's audio effects)
- `audiomentations` (data augmentation)
- `numpy.fft` (spectral analysis)
