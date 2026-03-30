import { getChordTones, type ChordQuality } from './scales'

export type VoicingExtension = ChordQuality

export function voice(root: string, extension: VoicingExtension): string[] {
  return getChordTones(root, extension)
}

export function invert(voicing: string[], inversion: number): string[] {
  if (inversion <= 0) return [...voicing]
  const n = voicing.length
  const idx = inversion % n
  return [...voicing.slice(idx), ...voicing.slice(0, idx)]
}
