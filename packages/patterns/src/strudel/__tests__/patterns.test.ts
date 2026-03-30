import { test, expect, describe } from 'vitest'
import { DubTechnoPatterns, type PatternOptions, type TimingInfo, type Pattern } from '../patterns'

describe('DubTechnoPatterns', () => {
  describe('chordStab', () => {
    test('returns pattern with correct type', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      expect(result.type).toBe('chord-stab')
    })

    test('uses getChordTones for voicings', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      // Cm9 chord tones: root, m3, P5, m7, M9
      expect(result.notes).toContain('C')
      expect(result.notes).toContain('Eb')
      expect(result.notes).toContain('G')
      expect(result.notes).toContain('Bb')
      expect(result.notes).toContain('D')
    })

    test('includes timing info with default bpm', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      expect(result.timing.bpm).toBe(125)
      expect(result.timing.subdivision).toBe('1/4')
    })

    test('includes pattern array for rhythm', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      expect(Array.isArray(result.timing.pattern)).toBe(true)
      expect(result.timing.pattern.length).toBeGreaterThan(0)
    })

    test('respects rate option', () => {
      const result = DubTechnoPatterns.chordStab('Cm9', { rate: '1/8' })
      expect(result.timing.subdivision).toBe('1/8')
    })

    test('respects velocity option', () => {
      const result = DubTechnoPatterns.chordStab('Cm9', { velocity: 90 })
      expect(result.velocity).toBe(90)
    })

    test('defaults velocity to 80', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      expect(result.velocity).toBe(80)
    })

    test('respects duration option', () => {
      const result = DubTechnoPatterns.chordStab('Cm9', { duration: 8 })
      expect(result.duration).toBe(8)
    })

    test('defaults duration to 4 beats', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      expect(result.duration).toBe(4)
    })

    test('pattern array contains only 0s and 1s (on/off)', () => {
      const result = DubTechnoPatterns.chordStab('Cm9')
      for (const step of result.timing.pattern) {
        expect([0, 1]).toContain(step)
      }
    })

    test('works with minor triad', () => {
      const result = DubTechnoPatterns.chordStab('Dm')
      expect(result.notes).toContain('D')
      expect(result.notes).toContain('F')
      expect(result.notes).toContain('A')
    })

    test('works with minor 7th', () => {
      const result = DubTechnoPatterns.chordStab('Ebm7')
      expect(result.notes).toContain('Eb')
      expect(result.notes).toContain('Gb')
    })

    test('respects bpm option', () => {
      const result = DubTechnoPatterns.chordStab('Cm9', { bpm: 130 })
      expect(result.timing.bpm).toBe(130)
    })
  })

  describe('bassPulse', () => {
    test('returns pattern with correct type', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.type).toBe('bass-pulse')
    })

    test('returns root note', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.notes).toContain('D')
    })

    test('has quarter note default subdivision', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.timing.subdivision).toBe('1/4')
    })

    test('supports dotted quarter rate', () => {
      const result = DubTechnoPatterns.bassPulse('D', { rate: '1/4.' })
      expect(result.timing.subdivision).toBe('1/4.')
    })

    test('defaults velocity to 100', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.velocity).toBe(100)
    })

    test('defaults duration to 4 beats', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.duration).toBe(4)
    })

    test('defaults bpm to 125', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.timing.bpm).toBe(125)
    })

    test('pattern has 4/4 kick-like rhythm', () => {
      const result = DubTechnoPatterns.bassPulse('D')
      expect(result.timing.pattern[0]).toBe(1)
    })

    test('respects bpm option', () => {
      const result = DubTechnoPatterns.bassPulse('D', { bpm: 120 })
      expect(result.timing.bpm).toBe(120)
    })
  })

  describe('hiHatPattern', () => {
    test('returns pattern with correct type', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.type).toBe('hihat')
    })

    test('returns empty notes array (percussion, no pitch)', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.notes).toEqual([])
    })

    test('has 1/8 note default subdivision', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.timing.subdivision).toBe('1/8')
    })

    test('defaults bpm to 125', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.timing.bpm).toBe(125)
    })

    test('defaults velocity to 60', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.velocity).toBe(60)
    })

    test('defaults duration to 1 bar (4 beats)', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      expect(result.duration).toBe(4)
    })

    test('pattern density is 2-6 events per bar', () => {
      const result = DubTechnoPatterns.hiHatPattern()
      const hits = result.timing.pattern.filter(v => v === 1).length
      expect(hits).toBeGreaterThanOrEqual(2)
      expect(hits).toBeLessThanOrEqual(6)
    })

    test('respects velocity option', () => {
      const result = DubTechnoPatterns.hiHatPattern({ velocity: 45 })
      expect(result.velocity).toBe(45)
    })

    test('respects bpm option', () => {
      const result = DubTechnoPatterns.hiHatPattern({ bpm: 128 })
      expect(result.timing.bpm).toBe(128)
    })
  })

  describe('padTexture', () => {
    test('returns pattern with correct type', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.type).toBe('pad')
    })

    test('uses chord tones for voicing', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.notes.length).toBeGreaterThan(0)
      expect(result.notes).toContain('C')
      expect(result.notes).toContain('Eb')
    })

    test('has 1/4 note subdivision', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.timing.subdivision).toBe('1/4')
    })

    test('defaults velocity to 50 (soft)', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.velocity).toBe(50)
    })

    test('defaults duration to 4 beats', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.duration).toBe(4)
    })

    test('defaults bpm to 125', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.timing.bpm).toBe(125)
    })

    test('pattern is sustained (single long event)', () => {
      const result = DubTechnoPatterns.padTexture('Cm9')
      expect(result.timing.pattern[0]).toBe(1)
    })

    test('respects velocity option', () => {
      const result = DubTechnoPatterns.padTexture('Cm9', { velocity: 70 })
      expect(result.velocity).toBe(70)
    })

    test('respects bpm option', () => {
      const result = DubTechnoPatterns.padTexture('Cm9', { bpm: 122 })
      expect(result.timing.bpm).toBe(122)
    })
  })

  describe('fullPattern', () => {
    test('returns combined pattern with all elements', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125)
      expect(result).toHaveProperty('chordStab')
      expect(result).toHaveProperty('bass')
      expect(result).toHaveProperty('hihat')
      expect(result).toHaveProperty('pad')
    })

    test('chord stab uses m9 quality by default', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125)
      expect(result.chordStab.notes).toContain('D')
      expect(result.chordStab.notes).toContain('F')
      expect(result.chordStab.notes).toContain('A')
      expect(result.chordStab.notes).toContain('C')
      expect(result.chordStab.notes).toContain('E')
    })

    test('bass uses the key root', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125)
      expect(result.bass.notes).toContain('D')
    })

    test('all sub-patterns share the same bpm', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125)
      expect(result.chordStab.timing.bpm).toBe(125)
      expect(result.bass.timing.bpm).toBe(125)
      expect(result.hihat.timing.bpm).toBe(125)
      expect(result.pad.timing.bpm).toBe(125)
    })

    test('all sub-patterns share the same duration', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125, { duration: 8 })
      expect(result.chordStab.duration).toBe(8)
      expect(result.bass.duration).toBe(8)
      expect(result.hihat.duration).toBe(8)
      expect(result.pad.duration).toBe(8)
    })

    test('hihat has no notes (percussion)', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125)
      expect(result.hihat.notes).toEqual([])
    })

    test('pad uses the key root with m9 quality', () => {
      const result = DubTechnoPatterns.fullPattern('C', 125)
      expect(result.pad.notes).toContain('C')
    })

    test('respects bpm parameter', () => {
      const result = DubTechnoPatterns.fullPattern('D', 128)
      expect(result.chordStab.timing.bpm).toBe(128)
    })

    test('respects options passed through', () => {
      const result = DubTechnoPatterns.fullPattern('D', 125, { velocity: 70 })
      expect(result.chordStab.velocity).toBe(70)
    })
  })
})
