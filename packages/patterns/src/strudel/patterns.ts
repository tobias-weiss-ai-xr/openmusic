import { getChordTones, type ChordQuality } from '../theory/scales'

export interface TimingInfo {
  bpm: number
  subdivision: string
  pattern: number[]
}

export interface Pattern {
  type: string
  notes: string[]
  timing: TimingInfo
  duration: number
  velocity: number
}

export interface PatternOptions {
  rate?: string
  variation?: number
  velocity?: number
  duration?: number
  bpm?: number
}

export interface FullPattern {
  chordStab: Pattern
  bass: Pattern
  hihat: Pattern
  pad: Pattern
}

const DEFAULT_BPM = 125

function parseChordName(chord: string): { root: string; quality: ChordQuality } {
  const match = chord.match(/^([A-G][#b]?)(m(?:7|9|11)?|)$/)
  if (!match) return { root: chord, quality: 'm' }

  const root = match[1]
  const suffix = match[2]
  const quality: ChordQuality = suffix === 'm11' ? 'm11' : suffix === 'm9' ? 'm9' : suffix === 'm7' ? 'm7' : 'm'
  return { root, quality }
}

function chordStabRhythm(subdivision: string): number[] {
  const steps = subdivision === '1/4' ? 4 : subdivision === '1/8' ? 8 : subdivision === '1/16' ? 16 : 4
  const pattern = new Array(steps).fill(0)
  const positions = [0, Math.floor(steps / 2)]
  for (const pos of positions) {
    if (pos < steps) pattern[pos] = 1
  }
  return pattern
}

function bassRhythm(subdivision: string): number[] {
  const steps = subdivision === '1/4' ? 4 : subdivision === '1/8' ? 8 : 4
  const pattern = new Array(steps).fill(0)
  pattern[0] = 1
  if (steps >= 4) pattern[2] = 1
  return pattern
}

function hiHatRhythm(): number[] {
  return [1, 0, 0, 1, 0, 0, 1, 0]
}

function padRhythm(): number[] {
  return [1, 0, 0, 0]
}

/**
 * Generates dub techno patterns for all instrument tracks.
 */
export class DubTechnoPatterns {
  /**
   * Generates a chord stab pattern for the given chord.
   * @param chord - Chord name (e.g., 'Am', 'Dm7')
   * @param options - Pattern options (bpm, rate, velocity, duration)
   * @returns Pattern object with timing and notes
   */
  static chordStab(chord: string, options: PatternOptions = {}): Pattern {
    const { root, quality } = parseChordName(chord)
    const notes = getChordTones(root, quality)
    const bpm = options.bpm ?? DEFAULT_BPM
    const subdivision = options.rate ?? '1/4'

    return {
      type: 'chord-stab',
      notes,
      timing: {
        bpm,
        subdivision,
        pattern: chordStabRhythm(subdivision),
      },
      duration: options.duration ?? 4,
      velocity: options.velocity ?? 80,
    }
  }

  /**
   * Generates a bass pulse pattern for the given root note.
   * @param root - Root note (e.g., 'C', 'A')
   * @param options - Pattern options (bpm, rate, velocity, duration)
   * @returns Pattern object with timing and notes
   */
  static bassPulse(root: string, options: PatternOptions = {}): Pattern {
    const bpm = options.bpm ?? DEFAULT_BPM
    const subdivision = options.rate ?? '1/4'

    return {
      type: 'bass-pulse',
      notes: [root],
      timing: {
        bpm,
        subdivision,
        pattern: bassRhythm(subdivision),
      },
      duration: options.duration ?? 4,
      velocity: options.velocity ?? 100,
    }
  }

  /**
   * Generates a hi-hat pattern.
   * @param options - Pattern options (bpm, velocity, duration)
   * @returns Pattern object with timing and notes
   */
  static hiHatPattern(options: PatternOptions = {}): Pattern {
    const bpm = options.bpm ?? DEFAULT_BPM

    return {
      type: 'hihat',
      notes: [],
      timing: {
        bpm,
        subdivision: '1/8',
        pattern: hiHatRhythm(),
      },
      duration: options.duration ?? 4,
      velocity: options.velocity ?? 60,
    }
  }

  /**
   * Generates a pad texture pattern for the given chord.
   * @param chord - Chord name (e.g., 'Am', 'Dm7')
   * @param options - Pattern options (bpm, velocity, duration)
   * @returns Pattern object with timing and notes
   */
  static padTexture(chord: string, options: PatternOptions = {}): Pattern {
    const { root, quality } = parseChordName(chord)
    const notes = getChordTones(root, quality)
    const bpm = options.bpm ?? DEFAULT_BPM

    return {
      type: 'pad',
      notes,
      timing: {
        bpm,
        subdivision: '1/4',
        pattern: padRhythm(),
      },
      duration: options.duration ?? 4,
      velocity: options.velocity ?? 50,
    }
  }

  /**
   * Generates a complete dub techno pattern with all tracks.
   * @param key - Musical key (e.g., 'Am')
   * @param bpm - Tempo in beats per minute
   * @param options - Pattern options for all tracks
   * @returns FullPattern object with all instrument tracks
   */
  static fullPattern(key: string, bpm: number, options: PatternOptions = {}): FullPattern {
    const chordName = key + 'm9'

    return {
      chordStab: DubTechnoPatterns.chordStab(chordName, { ...options, bpm }),
      bass: DubTechnoPatterns.bassPulse(key, { ...options, bpm }),
      hihat: DubTechnoPatterns.hiHatPattern({ ...options, bpm }),
      pad: DubTechnoPatterns.padTexture(chordName, { ...options, bpm }),
    }
  }
}
