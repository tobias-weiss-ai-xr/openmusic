=== Decisions from Task 05: Dub Techno Theory Spec ===

Date: Fri 27 Mar 22:12:52 CET 2026

## Parameterization Decisions ===
### BPM Range Decision
- Range: 120-130 BPM (±2 BPM tolerance for variation)
- Default: 125 BPM (sweet spot for Rob Jenkins style)
- Rationale: Balance between groove and atmosphere

### Key Signature Decision
- Primary keys: D minor, E minor, A minor (80% of use)
- Scale types: Natural minor (80%), Dorian (15%), Harmonic minor (5%)
- Rationale: Minor keys provide dark, atmospheric mood

### Chord Quality Decision
- Preferred: m9 chords (40%), m7 chords (35%), m triads (15%), m11 chords (10%)
- Rationale: Extended chords provide atmospheric depth

### Effect Chain Architecture ===
- Primary delay: dotted 1/8 or 1/4 note, 40% feedback, 50% mix
- Secondary delay: 3/16 or 1/8 note, 30% feedback, 40% mix
- Reverb: 3.0s decay, 40% mix, bandpass input filter
- Filter: Bandpass 800 Hz center, LFO 0.2 Hz, 100 Hz depth
- Rationale: Dual delays + reverb create dub techno signature space

### Mix Length Decision
- Target: 60-120 minute continuous mixes
- Structure: intro (3 min) + development (60 min) + climax (6 min) + outro (3 min)
- Rationale: Rob Jenkins mixes emphasize long-form evolution

### Dynamic Range Decision
- RMS target: -16 dB (range: -18 to -14 dB)
- Peak/RMS ratio: 15 dB (preserved headroom)
- Rationale: Controlled dynamics allow space for atmospheric elements

## Implementation Notes ===
- All parameters are measurable and implementable in code
- Randomization should occur within defined ranges (e.g., filter LFO rate: 0.1-0.5 Hz)
- Key changes only at section boundaries (not within sections)
- Transitions: 16-32 bars with filter sweeps or crossfades
