import { noteToIndex, degreeNoteName, getScale, type ScaleType } from './scales'

const INTERVAL_SEMITONES: Record<string, number> = {
  'P1': 0, 'd2': 1, 'm2': 1, 'M2': 2, 'm3': 3, 'M3': 4,
  'P4': 5, 'TT': 6, 'A4': 6, 'd5': 6, 'P5': 7, 'm6': 8,
  'M6': 9, 'm7': 10, 'M7': 11, 'P8': 12,
}

const INTERVAL_DEGREE: Record<string, number> = {
  'P1': 0, 'd2': 1, 'm2': 1, 'M2': 1, 'm3': 2, 'M3': 2,
  'P4': 3, 'TT': 3, 'A4': 3, 'd5': 4, 'P5': 4, 'm6': 5,
  'M6': 5, 'm7': 6, 'M7': 6, 'P8': 7,
}

// i-VII-VI-v: scale degrees [0, 6, 5, 4]
const TEMPLATE_I_VII_VI_V = [0, 6, 5, 4]
// i-iv-VII-III: scale degrees [0, 3, 6, 2]
const TEMPLATE_I_IV_VII_III = [0, 3, 6, 2]

// Diatonic 7th chord quality by scale degree (0-indexed) for each scale type:
// Natural minor: i=m7, ii°=m7b5, III=maj7, iv=m7, v=m7, VI=maj7, VII=7
// Harmonic minor: i=m7, ii°=m7b5, III=maj7, iv=m7, V=7, VI=maj7, vii°=dim7
// Dorian: i=m7, ii=m7, III=maj7, iv=m7, v=m7, vi°=m7b5, VII=maj7
const DIATONIC_QUALITIES: Record<string, string[]> = {
  'natural-minor':  ['m7', 'm7b5', 'maj7', 'm7', 'm7', 'maj7', '7'],
  'harmonic-minor': ['m7', 'm7b5', 'maj7', 'm7', '7',  'maj7', 'dim7'],
  'dorian':         ['m7', 'm7',   'maj7', 'm7', 'm7', 'm7b5', 'maj7'],
}

function chordQualityForDegree(degree: number, scaleType: ScaleType): string {
  return DIATONIC_QUALITIES[scaleType][degree % 7]
}

function buildChordName(root: string, quality: string): string {
  return root + quality
}

function parseInterval(interval: string): { semitones: number; degree: number; negative: boolean } {
  const negative = interval.startsWith('-')
  const name = negative ? interval.slice(1) : interval
  const semitones = (INTERVAL_SEMITONES[name] ?? 0) * (negative ? -1 : 1)
  const positiveDegree = INTERVAL_DEGREE[name] ?? 0
  const degree = negative ? (7 - positiveDegree) % 7 : positiveDegree
  return { semitones, degree, negative }
}

export class ChordProgression {
  static parallel(rootChord: string, intervals: string[]): string[] {
    const { root, suffix } = parseChordName(rootChord)
    return intervals.map(interval => {
      const { semitones, degree } = parseInterval(interval)
      const newRoot = degreeNoteName(root, degree, semitones)
      return newRoot + suffix
    })
  }

  static generate(key: string, scaleType: ScaleType, length: number): string[] {
    const scale = getScale(key, scaleType)
    const degrees = TEMPLATE_I_VII_VI_V
    const chords: string[] = []
    for (let i = 0; i < length; i++) {
      const degree = degrees[i % degrees.length]
      const root = scale[degree]
      const quality = chordQualityForDegree(degree, scaleType)
      chords.push(buildChordName(root, quality))
    }
    return chords
  }

  static fromTemplate(
    template: string,
    key: string,
    scaleType: ScaleType,
  ): string[] {
    if (template === 'parallel-descent') {
      const offsets = [0, -1, -2, -3, -4, -5, -6]
      return offsets.map(offset => {
        const degree = offset === 0 ? 0 : (6 - Math.floor((-offset - 1) / 2))
        const root = degreeNoteName(key, degree, offset)
        return root + 'm9'
      })
    }

    const degrees = template === 'i-iv-VII-III'
      ? TEMPLATE_I_IV_VII_III
      : TEMPLATE_I_VII_VI_V

    const scale = getScale(key, scaleType)
    return degrees.map(degree => {
      const root = scale[degree]
      const quality = chordQualityForDegree(degree, scaleType)
      return buildChordName(root, quality)
    })
  }
}

function parseChordName(chord: string): { root: string; suffix: string } {
  const match = chord.match(/^([A-G][#b]?)(.+)$/)
  if (!match) return { root: chord, suffix: '' }
  return { root: match[1], suffix: match[2] }
}
