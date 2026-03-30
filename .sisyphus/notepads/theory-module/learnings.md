
## Music Theory Module - Learnings

### Note Naming System
- Used `degreeNoteName(root, degree, chromaticOffset)` algorithm: each scale degree maps to a letter (C-D-E-F-G-A-B cycling), and the accidental is computed from `targetChromaticIndex - naturalPositionOfLetter`
- This handles enharmonic spelling correctly across all keys (e.g., D harmonic minor: C# not Db)
- Key insight: the letter name is determined by the scale degree, NOT by the chromatic index

### Diatonic Chord Qualities
- Natural minor VII = dominant 7th (not major 7th) — e.g., in D minor, C7 not Cmaj7
- Dorian vi = half-diminished (m7b5), not major — e.g., in D dorian, Bm7b5 not Bbmaj7
- Harmonic minor: V = dominant 7th (A7 in D harmonic minor), vii° = dim7 (C#dim7)

### Parallel Movement API Design
- `parallel()` uses ABSOLUTE offsets from root (each interval maps to one chord)
- Negative intervals supported via `-` prefix (e.g., `-m2` = down minor 2nd)
- For negative intervals, degree = `(7 - positiveDegree) % 7`

### Descending Parallel Motion
- For `parallel-descent` template, degree formula: `6 - Math.floor((-offset - 1) / 2)`
- Descending convention uses flats (Gb not F#) — this is theoretically correct
- The degree computation for descending is tricky because E-F and B-C are only 1 semitone apart

### TDD Process
- Vitest test files go in `__tests__/` subdirectory (matching vitest config pattern)
- Test command: `npx vitest run packages/patterns` (to avoid effects package failures)
