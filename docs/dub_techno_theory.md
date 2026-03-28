# Dub Techno Music Theory Specification

This document defines measurable parameters for generating dub techno music in the style of Rob Jenkins, characterized by atmospheric, deep, and minimal aesthetics with long-form structures.

---

## Overview

Dub techno is defined by:
- Deep, atmospheric chord stabs with extended reverb
- Tape-style delay echoes creating space and depth
- Filter modulation and LFO-driven movement
- Long, evolving arrangements (typically 60-120 minutes)
- Dark, moody harmonic content in minor keys
- Vinyl crackle and subtle saturation for warmth

**Key Reference**: Rob Jenkins mixes (https://www.youtube.com/@RobJenkinsDubTechno) exemplify the target aesthetic with long-form, dark atmospheric dub techno.

---

## 1. Measurable Parameters

### Rhythmic Parameters

#### 1.1 BPM Range
- **Range**: 120-130 BPM
- **Default**: 125 BPM
- **Tolerance**: ±2 BPM for subtle variation within sections
- **Typical**: 122-128 BPM for Rob Jenkins style

#### 1.2 Rhythmic Density
- **Kick Pattern**: 4/4 on-beat, sparse syncopation
- **Hi-Hat Density**: 2-6 events per bar (quarter to sixteenth notes)
- **Chord Stab Density**: 2-8 events per 4-bar phrase
- **Bass Pulse Rate**: Quarter notes or dotted eighths typical

---

### Harmonic Parameters

#### 1.3 Key Signatures
**Preferred Minor Keys** (in order of typicality):
- D minor (most common)
- E minor
- A minor
- C minor
- F minor
- B minor

**Scale Types**:
- Natural Minor (Aeolian) - 80% of use
- Dorian - 15% of use (for brighter moments)
- Harmonic Minor - 5% of use (for tension/release)

#### 1.4 Chord Qualities
**Primary Chords** (90% of harmony):
- Minor triads (m): Root + m3 + P5
- Minor 7th chords (m7): Root + m3 + P5 + m7
- Minor 9th chords (m9): Root + m3 + P5 + m7 + M9

**Secondary Chords** (10% of harmony):
- Minor 11th chords (m11) - for depth
- Suspended chords (sus2, sus4) - for transitional moments

**Chord Voicing Rules**:
- Close voicing preferred (within one octave)
- Root in bass for bass tones
- Root doubled or omitted in chord stabs
- Extensions (7, 9, 11) preferred over triads

---

### Structural Parameters

#### 1.5 Mix Structure (60-120 minute mixes)
```
Total Duration: 60-120 minutes (typical for Rob Jenkins style)

┌────────────────────────────────────────────────────────────┐
│ INTRO (2-4 minutes)                                 │
│ - Minimal elements, filtered down                       │
│ - Atmospheric pads, no chords initially                  │
│ - Gradual filter opening                               │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ DEVELOPMENT 1 (8-12 minutes)                         │
│ - First chord stabs introduced                          │
│ - Delay tails building                                 │
│ - Sub-bass establishes groove                          │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ DEVELOPMENT 2-5 (40-80 minutes)                     │
│ - Multiple thematic variations                           │
│ - Chord progression shifts                             │
│ - Intensity gradually increases                         │
│ - Filter sweeps and LFO modulation                     │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ CLIMAX/PEAK (4-8 minutes)                           │
│ - Maximum chord density                                 │
│ - Full frequency range engaged                          │
│ - Peak reverb and delay feedback                       │
│ - Often includes minor key shift (up minor 3rd)        │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ OUTRO (2-4 minutes)                                  │
│ - Elements gradually removed                            │
│ - Filter closing                                      │
│ - Fading to atmospheric noise                          │
└────────────────────────────────────────────────────────────┘
```

#### 1.6 Section Durations
- **Phrase Length**: 4-8 bars (most common)
- **Loop Duration**: 8-32 bars before variation
- **Section Length**: 8-32 minutes between harmonic shifts
- **Transition Duration**: 16-64 bars (8-32 seconds at 125 BPM)

---

### Effect Parameters

#### 1.7 Delay Settings (Tape Echo Style)

**Primary Delay (Delay 1)**:
- **Time**: 1/8 note (dotted) or 1/4 note
- **Feedback**: 30-50%
- **Mix**: 40-60% wet
- **Error/Motor Wobble**: 5-15% (for tape drift)
- **Stereo Mode**: Ping-pong (for width)
- **Reverb in Delay**: 20-30% (integrated ambience)

**Secondary Delay (Delay 2)**:
- **Time**: 3/16 note or 1/8 note
- **Feedback**: 20-40%
- **Mix**: 30-50% wet
- **Error/Motor Wobble**: 8-18%
- **Stereo Mode**: Stereo
- **Reverb in Delay**: 15-25%

#### 1.8 Reverb Parameters
- **Decay Time**: 2.0-4.0 seconds (default: 3.0s)
- **Pre-Delay**: 20-50 ms
- **Diffusion**: High (80-90%)
- **High Cut**: 4-8 kHz (to tame harshness)
- **Mix**: 30-50% for chord stabs, 15-30% for bass
- **Input Filter**: Bandpass 200-2000 Hz for chord stabs

#### 1.9 Filter Parameters
- **Bandpass Center Freq**: 200-2000 Hz (default: 800 Hz)
- **Bandwidth/Q Factor**: 2.0-4.0 (moderate width)
- **LFO Rate**: 0.1-0.5 Hz (6-30 BPM modulation)
- **LFO Depth**: 50-200 Hz frequency sweep
- **Filter Envelope Attack**: 5-20 ms
- **Filter Envelope Decay**: 100-500 ms (tight stabs)

#### 1.10 Saturation/Distortion
- **Saturation Amount**: 10-30% (subtle warmth)
- **Overdrive Drive**: 5-15% (mild crunch)
- **Frequency Focus**: Low-mid (200-800 Hz)
- **Clipping Threshold**: -3 to -6 dB (dynamic control)
- **Tube/Console Emulation**: Preferred for harmonic richness

#### 1.11 Vinyl Noise Characteristics
- **Crackle Volume**: 10-25% (subtle, not overwhelming)
- **Hiss Level**: 5-15% (background texture)
- **Wow/Flutter**: 3-8% (slight pitch drift)
- **Click/Pop Reduction**: Active (to avoid sudden artifacts)
- **Frequency Range**: Full spectrum, tilted high

---

### Dynamic Parameters

#### 1.12 Dynamic Range Targets
- **Overall RMS**: -18 to -14 dB (typical mix level)
- **Peak/RMS Ratio**: 12-18 dB (dynamic headroom)
- **Kick Peak**: -6 to -3 dB
- **Chord Stab Peak**: -12 to -8 dB
- **Reverb Tail Level**: -24 to -18 dB
- **Noise Floor**: -60 dB or below

#### 1.13 Frequency Balance
- **Sub-Bass (20-60 Hz)**: -3 to 0 dB relative to reference
- **Bass (60-250 Hz)**: -2 to 0 dB
- **Low-Mid (250-500 Hz)**: -4 to -2 dB
- **Mid (500-2000 Hz)**: -6 to -4 dB
- **High-Mid (2-8 kHz)**: -8 to -6 dB
- **High (8-20 kHz)**: -10 to -8 dB (gentle roll-off)

#### 1.14 Stereo Width
- **Overall Width**: 120-150% (enhanced width)
- **Low Frequencies (<200 Hz)**: Mono (centered)
- **Mid Frequencies (200-2000 Hz)**: 100-120% width
- **High Frequencies (>2 kHz)**: 140-180% width (airy feel)
- **Delay Pan Width**: 50-100 L/R spread

---

### Textural Parameters

#### 1.15 Sub-Bass Characteristics
- **Frequency Range**: 25-55 Hz
- **Waveform**: Sine or soft triangle (minimal harmonics)
- **Attack**: 5-15 ms (tight punch)
- **Release**: 100-300 ms (smooth decay)
- **Filter**: Low-pass at 80-120 Hz
- **Layering**: Optional second layer at 1 octave up for definition

#### 1.16 High Frequency Rolloff
- **Slope**: -12 to -24 dB/octave
- **Cutoff**: 14-16 kHz (natural roll-off)
- **Shelving**: Optional -3 to -6 dB above 10 kHz
- **Purpose**: Prevent harshness, maintain warmth

---

## 2. Chord Progressions

### 2.1 Parallel Minor Movements

**Progression 1: Descending Parallel Minor (Classic Dub Techno)**
```
Cm9 → Bm9 → B♭m9 → Am9 → Gm9 → F♯m9 → Fm9
Root movement: Down by semitone
Duration: 4-8 bars per chord
Variation: Omit chords for tension (e.g., Cm9 → (rest) → B♭m9)
```

**Progression 2: Whole-Step Parallel Movement**
```
Em7 → D♯m7 → Dm7 → C♯m7 → Cm7 → Bm7 → B♭m7
Root movement: Down by whole tone
Duration: 2-4 bars per chord
Usage: Development sections for forward momentum
```

**Progression 3: Minor Third Parallel Shifts**
```
Dm9 → Bm9 → Gm9 → Em9 → Cm9 → Am9
Root movement: Down by minor third
Duration: 4-8 bars per chord
Usage: Climax sections for dramatic movement
```

### 2.2 Natural Minor Diatonic Progressions

**Progression 4: i - VII - VI - v (Natural Minor)**
```
Key: D minor
Dm7 → C7 → B♭m7 → Am7
Degrees: i - VII - VI - v
Duration: 8-16 bars per chord
Usage: Foundation sections, stable harmonic center
```

**Progression 5: iim - iiim - IV - v (Emotional Tension)**
```
Key: E minor
F♯m7 → Gm7 → Am7 → Bm7
Degrees: iim - iiim - IV - v
Duration: 6-12 bars per chord
Usage: Development sections for gradual tension build
```

**Progression 6: Parallel i - VI - iv - V (Chromatic)**
```
Key: A minor
Am7 → Fm7 → Dm7 → E7alt
Degrees: i - VI - iv - V
Duration: 4-8 bars per chord
Usage: Climax sections for chromatic tension
```

### 2.3 Modal Interchange Progressions

**Progression 7: i - ♭VI - ♭VII - i (Andalusian Cadence)**
```
Key: C minor
Cm9 → A♭maj7 → B♭maj7 → Cm9
Degrees: i - ♭VI - ♭VII - i
Duration: 8-16 bars per chord
Usage: Dramatic sections, emotional peaks
```

**Progression 8: i - iv - i - ♭VII (Suspension)**
```
Key: D minor
Dm9 → Gm7 → Dm9 → C7
Degrees: i - iv - i - ♭VII
Duration: 4-8 bars per chord
Usage: Intro/outro sections, resolving tension
```

---

## 3. Arrangement Patterns

### 3.1 Layer Entrance Order (Typical)
```
1. Atmospheric Noise (vinyl crackle, pad texture)
2. Sub-Bass ( establishes foundation)
3. Kick Drum (4/4 pulse)
4. Hi-Hats (rhythmic texture)
5. Chord Stabs (harmonic content, filtered)
6. Delays (space and ambience)
7. Reverb (depth)
8. Additional Percussion (claps, rim, shaker - optional)
```

### 3.2 Layer Exit Order (Outro)
```
1. Chord Stabs (remove or filter down)
2. Additional Percussion
3. Hi-Hats
4. Delays (reduce feedback)
5. Kick Drum
6. Sub-Bass
7. Reverb (fade out)
8. Atmospheric Noise (fade last)
```

### 3.3 Filter Automation Patterns

**Pattern 1: Slow Opening**
- Duration: 32-64 bars
- Start: Bandpass 200 Hz
- End: Bandpass 2000 Hz
- Curve: Exponential (slow start, faster opening)
- LFO: Yes (0.1-0.2 Hz, 50-100 Hz depth)

**Pattern 2: Breathing Movement**
- Duration: 8-16 bars repeating
- Range: 400-1200 Hz
- Rate: 0.3-0.5 Hz LFO
- Shape: Sine wave
- Randomization: ±50 Hz per cycle

**Pattern 3: Filter Drop (Transition)**
- Duration: 16-32 bars
- Start: Full frequency range
- End: Bandpass 150-300 Hz
- Curve: Linear drop
- Followed by: Reopening to new harmonic content

---

## 4. Transition Techniques

### 4.1 Crossfade Transitions
- **Duration**: 16-32 bars (8-16 seconds at 125 BPM)
- **Crossfade Curve**: Equal-power or S-curve
- **Overlap**: 2-4 bars of both sections audible
- **Filter State**: One section filtering down, next filtering up
- **Reverb Tail**: Allow 2-4 seconds of previous section to decay

### 4.2 Filter Sweep Transitions
- **Duration**: 16-32 bars
- **Technique**: Both sections filter to bandpass 300-500 Hz, then open to new section
- **LFO Increase**: Boost to 0.5-1.0 Hz during sweep
- **Delay Feedback**: Increase to 50-60% during transition

### 4.3 Drop/Build Transitions
- **Drop Phase**: 8-16 bars - filter down, reduce elements
- **Silence/Void**: 1-2 bars - minimal elements only
- **Build Phase**: 8-16 bars - filter opens, new elements enter
- **Chord Change**: Occurs at build peak or in void

### 4.4 Harmonic Shift Transitions
- **Duration**: 16-32 bars
- **Technique**: Gradual chord quality shift or root movement
- **Parallel Motion**: Maintain chord quality, shift root
- **Overlap**: Both harmonic areas audible for 4-8 bars
- **Resolution**: New key center establishes by end of transition

---

## 5. "Rob Jenkins Style" Definition

Rob Jenkins dub techno is characterized by:

**Aesthetic Qualities**:
- Dark, atmospheric mood (minor keys, spacious reverb)
- Deep, submerged chord stabs
- Long, evolving structures (60-120+ minutes)
- Minimal but effective rhythmic elements
- Vinyl warmth and subtle noise

**Technical Implementation**:
- BPM: 120-130 (typically 122-128)
- Keys: D minor, E minor, A minor (natural minor preferred)
- Chords: Extended minor chords (m9, m11) with parallel movement
- Effects: Dual tape delays (1/8 and 3/16), long reverb (3-4s)
- Filter: Bandpass with LFO modulation (0.1-0.5 Hz)
- Dynamics: Controlled RMS (-18 to -14 dB), preserved headroom
- Structure: Long intro (2-4 min), extended development (40-80 min), gradual peak (4-8 min), smooth outro (2-4 min)

**Emotional Arc**:
- Intro: Subtle, mysterious, filtered down
- Development: Gradual buildup, evolving tension
- Climax: Maximum intensity, emotional peak, key shift optional
- Outro: Fading, resolving, returning to atmospheric

**Mix Characteristics**:
- Wide stereo image (120-150% overall)
- Sub-bass centered (mono), chords wide
- Saturation subtle (10-30%) for analog warmth
- Vinyl crackle present (10-25%) but not overwhelming
- Transitions smooth (16-32 bars) with filter sweeps

---

## 6. Implementation Guidelines

### 6.1 Randomization vs. Control
**Randomize**:
- Chord stab timing (within rhythmic density range)
- Filter LFO phase and rate (within defined range)
- Delay error amount (5-15% per instance)
- Velocity of MIDI notes (for filter modulation)
- Occasional chord omission (for tension)

**Control**:
- BPM stability (±2 BPM max)
- Key signature consistency within sections
- Chord quality preservation in parallel movements
- Section durations (within defined ranges)
- Peak levels (-6 dB max)

### 6.2 Variation Techniques
**Melodic/Rhythmic Variation**:
- Occasional added notes (9th, 11th) to existing chords
- Subtle rhythmic syncopation (2-8% of chord stabs)
- Chord inversion changes (for textural interest)
- Octave doublings for emphasis

**Timbral Variation**:
- Filter cutoff automation per chord event
- Velocity-dependent filter envelope
- Subtle LFO rate changes
- Delay feedback modulation per phrase

**Structural Variation**:
- Phrase length variation (4, 8, 16, 32 bars)
- Section duration variation (8, 16, 24, 32 minutes)
- Occasional micro-sections (2-4 bars) for surprise
- Key changes at section boundaries (minor third or perfect fifth)

---

## 7. Parameter Summary Table

| Parameter | Range | Default | Unit |
|-----------|--------|----------|-------|
| BPM | 120-130 | 125 | beats/minute |
| Kick Pattern | 4/4 on-beat | - | - |
| Hi-Hat Density | 2-6 | 4 | events/bar |
| Chord Stab Density | 2-8 | 4 | events/4 bars |
| Key Signature | Minor keys | D minor | - |
| Scale Type | Natural/Dorian/Harmonic | Natural | - |
| Chord Quality | m, m7, m9, m11 | m9 | - |
| Intro Duration | 2-4 | 3 | minutes |
| Development Duration | 40-80 | 60 | minutes |
| Climax Duration | 4-8 | 6 | minutes |
| Outro Duration | 2-4 | 3 | minutes |
| Delay 1 Time | 1/8 or 1/4 | dotted 1/8 | note |
| Delay 1 Feedback | 30-50 | 40 | % |
| Delay 1 Mix | 40-60 | 50 | % |
| Delay 1 Error | 5-15 | 10 | % |
| Delay 2 Time | 3/16 or 1/8 | 3/16 | note |
| Delay 2 Feedback | 20-40 | 30 | % |
| Reverb Decay | 2.0-4.0 | 3.0 | seconds |
| Reverb Mix | 30-50 | 40 | % |
| Filter Center Freq | 200-2000 | 800 | Hz |
| Filter LFO Rate | 0.1-0.5 | 0.2 | Hz |
| Filter LFO Depth | 50-200 | 100 | Hz |
| Saturation | 10-30 | 20 | % |
| Vinyl Crackle | 10-25 | 18 | % |
| Overall RMS | -18 to -14 | -16 | dB |
| Stereo Width | 120-150 | 135 | % |
| Sub-Bass Freq | 25-55 | 35 | Hz |
| High Rolloff Cutoff | 14-16 | 15 | kHz |

---

## 8. References

### Theoretical Foundations
- Attack Magazine: "The Theory of Techno Parallel Chord Stabs" - Parallel chord movement in techno
- Studio Brootle: "Dub Techno Effects Chains" - Practical effects implementation
- Rob Jenkins: Deep atmospheric dub techno mixes - Reference aesthetic and structure

### Recommended Listening
- Deep Chord: Ethereal dub techno aesthetics
- Basic Channel: Minimal dub techno production techniques
- Echospace: Extended dub techno arrangements
- Rod Modell: Atmospheric dub techno textures

---

## 9. Implementation Notes

This specification is designed for:
- **Generation**: AI-driven audio generation (ACE-Step)
- **Pattern Layering**: Algorithmic composition (Strudel)
- **Effects Processing**: WebAudio/Tone.js implementation
- **Mix Length**: 60-120 minute continuous mixes
- **Style**: Rob Jenkins-inspired atmospheric dub techno

All parameters are measurable and implementable in code. For audio generation, prioritize:
1. Stable BPM within defined range
2. Consistent minor key tonality
3. Parallel chord movements
4. Extended reverb and delay effects
5. Filter modulation and LFO movement
6. Gradual structural evolution over long durations
