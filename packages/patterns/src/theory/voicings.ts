import { getChordTones, type ChordQuality } from './scales'

export type VoicingExtension = ChordQuality

/**
 * Creates a voicing for a root note with the specified extension.
 * @param root - Root note of the chord
 * @param extension - Voicing extension (m, m7, m9, m11)
 * @returns Array of note names in the voicing
 */
export function voice(root: string, extension: VoicingExtension): string[] {
  return getChordTones(root, extension)
}

/**
 * Applies inversion to a voicing.
 * @param voicing - Array of note names
 * @param inversion - Inversion number (0 = root position, 1 = 1st inversion, etc.)
 * @returns Array of note names in the new voicing
 */
export function invert(voicing: string[], inversion: number): string[] {
  if (inversion <= 0) return [...voicing]
  const n = voicing.length
  const idx = inversion % n
  return [...voicing.slice(idx), ...voicing.slice(0, idx)]
}
