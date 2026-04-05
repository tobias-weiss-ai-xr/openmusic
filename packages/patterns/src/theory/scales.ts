const CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] as const

const FLAT_TO_INDEX: Record<string, number> = {
  'Cb': 11, 'Db': 1, 'Eb': 3, 'Fb': 4, 'Gb': 6, 'Ab': 8, 'Bb': 10,
}

const LETTERS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
const NATURAL_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

export type ScaleType = 'natural-minor' | 'harmonic-minor' | 'dorian'

const SCALE_INTERVALS: Record<ScaleType, number[]> = {
  'natural-minor':  [0, 2, 3, 5, 7, 8, 10],
  'harmonic-minor': [0, 2, 3, 5, 7, 8, 11],
  'dorian':         [0, 2, 3, 5, 7, 9, 10],
}

/** Converts a note name to its chromatic index (0-11). */
export function noteToIndex(note: string): number {
  if (note.length === 2 && note[1] === '#') {
    const idx = CHROMATIC.indexOf(note as typeof CHROMATIC[number])
    if (idx !== -1) return idx
  }
  if (note.length === 2 && note[1] === 'b') {
    const idx = FLAT_TO_INDEX[note]
    if (idx !== undefined) return idx
  }
  const idx = CHROMATIC.indexOf(note as typeof CHROMATIC[number])
  if (idx !== -1) return idx
  throw new Error(`Unknown note: ${note}`)
}

/** Converts a chromatic index (0-11) to a note name. */
export function indexToNote(index: number): string {
  return CHROMATIC[((index % 12) + 12) % 12]
}

/**
 * Derives a note name from a root key, scale degree, and chromatic target.
 * Uses music theory convention: each degree gets a letter name (cycling C-D-E-F-G-A-B),
 * and the accidental is computed from the difference between the target chromatic index
 * and the natural position of that letter.
 */
export function degreeNoteName(root: string, degree: number, chromaticOffset: number): string {
  const rootLetterIdx = LETTERS.indexOf(root[0])
  const letterIdx = (rootLetterIdx + degree) % 7
  const letter = LETTERS[letterIdx]
  const rootIdx = noteToIndex(root)
  const targetIdx = ((rootIdx + chromaticOffset) % 12 + 12) % 12
  const naturalIdx = NATURAL_SEMITONES[letterIdx]
  let diff = ((targetIdx - naturalIdx) % 12 + 12) % 12
  if (diff > 6) diff -= 12

  if (diff === 0) return letter
  if (diff === 1) return letter + '#'
  if (diff === -1) return letter + 'b'
  if (diff === 2) return letter + '##'
  if (diff === -2) return letter + 'bb'
  return indexToNote(targetIdx)
}

/**
 * Returns an array of note names forming the specified scale.
 * @param key - Root note (e.g., 'C', 'Am')
 * @param scaleType - Type of scale
 * @returns Array of note names in the scale
 */
export function getScale(key: string, scaleType: ScaleType): string[] {
  return SCALE_INTERVALS[scaleType].map((semitones, degree) =>
    degreeNoteName(key, degree, semitones),
  )
}

export type ChordQuality = 'm' | 'm7' | 'm9' | 'm11'

const CHORD_INTERVALS: Record<ChordQuality, number[]> = {
  'm':   [0, 3, 7],
  'm7':  [0, 3, 7, 10],
  'm9':  [0, 3, 7, 10, 14],
  'm11': [0, 3, 7, 10, 14, 17],
}

// Map chord semitone offsets to scale degrees for proper letter naming:
// root(0)→0, m3(3)→2, P5(7)→4, m7(10)→6, M9(14)→1, P11(17)→3
const CHORD_SEMITONE_TO_DEGREE: Record<number, number> = {
  0: 0, 3: 2, 7: 4, 10: 6, 14: 1, 17: 3,
}

/**
 * Returns chord tones for a root note and quality.
 * @param root - Root note of the chord
 * @param quality - Chord quality (m, m7, m9, m11)
 * @returns Array of note names in the chord
 */
export function getChordTones(root: string, quality: ChordQuality): string[] {
  return CHORD_INTERVALS[quality].map(semitones => {
    const degree = CHORD_SEMITONE_TO_DEGREE[semitones] ?? Math.round(semitones * 7 / 12)
    return degreeNoteName(root, degree, semitones)
  })
}
