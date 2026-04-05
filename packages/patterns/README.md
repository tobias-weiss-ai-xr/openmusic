# @openmusic/patterns

Dub techno pattern library with music theory utilities and Strudel-inspired mini-notation.

## Installation

```bash
npm install @openmusic/patterns
```

## Usage

```typescript
import { DubTechnoPatterns } from '@openmusic/patterns';

// Generate full pattern
const pattern = DubTechnoPatterns.fullPattern('Am', 125, { variation: 0.3 });

// Single tracks
const chordStab = DubTechnoPatterns.chordStab('Am9');
const bass = DubTechnoPatterns.bassPulse('A');
const hihat = DubTechnoPatterns.hiHatPattern();
const pad = DubTechnoPatterns.padTexture('Am9');
```

## Music Theory

```typescript
import { getScale, getChordTones, voice, invert } from '@openmusic/patterns';

// Scales
const scale = getScale('Am', 'natural-minor'); // ['A', 'B', 'C', 'D', 'E', 'F', 'G']

// Chords
const chord = getChordTones('Am', 'm9'); // ['A', 'C', 'E', 'G', 'B']

// Voicings
const voicing = voice('A', 'm7');
const inverted = invert(voicing, 1);
```

## Mini-Notation

```typescript
import { parseMiniNotation } from '@openmusic/patterns';

const pattern = parseMiniNotation('c d . e [f,a] g');
// Parses into notes, rests, and groups
```