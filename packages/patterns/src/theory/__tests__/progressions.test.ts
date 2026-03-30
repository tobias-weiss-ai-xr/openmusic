import { test, expect, describe } from 'vitest'
import { ChordProgression } from '../progressions'

describe('ChordProgression.parallel', () => {
  test('shifts root by intervals preserving quality', () => {
    const result = ChordProgression.parallel('Cm', ['P1', 'M2', 'm3'])
    expect(result).toEqual(['Cm', 'Dm', 'Ebm'])
  })

  test('handles m7 quality', () => {
    const result = ChordProgression.parallel('Dm7', ['P1', 'm2', 'M2'])
    expect(result).toEqual(['Dm7', 'Ebm7', 'Em7'])
  })

  test('handles m9 quality', () => {
    const result = ChordProgression.parallel('Am9', ['P1', 'P4', 'P5'])
    expect(result).toEqual(['Am9', 'Dm9', 'Em9'])
  })

  test('parallel descent using negative intervals', () => {
    const result = ChordProgression.parallel('Cm9', ['P1', '-m2', '-M2', '-m3'])
    expect(result).toEqual(['Cm9', 'Bm9', 'Bbm9', 'Am9'])
  })

  test('handles sharp keys', () => {
    const result = ChordProgression.parallel('F#m', ['P1', 'M2', 'm3'])
    expect(result).toEqual(['F#m', 'G#m', 'Am'])
  })

  test('handles flat keys', () => {
    const result = ChordProgression.parallel('Bbm', ['P1', 'P4', 'P5'])
    expect(result).toEqual(['Bbm', 'Ebm', 'Fm'])
  })
})

describe('ChordProgression.generate', () => {
  test('generates i-VII-VI-v in D natural minor', () => {
    const result = ChordProgression.generate('D', 'natural-minor', 4)
    expect(result).toEqual(['Dm7', 'C7', 'Bbmaj7', 'Am7'])
  })

  test('generates progression in A natural minor', () => {
    const result = ChordProgression.generate('A', 'natural-minor', 4)
    expect(result).toEqual(['Am7', 'G7', 'Fmaj7', 'Em7'])
  })

  test('generates progression in E natural minor', () => {
    const result = ChordProgression.generate('E', 'natural-minor', 4)
    expect(result).toEqual(['Em7', 'D7', 'Cmaj7', 'Bm7'])
  })

  test('respects length parameter', () => {
    const result = ChordProgression.generate('D', 'natural-minor', 3)
    expect(result).toEqual(['Dm7', 'C7', 'Bbmaj7'])
  })

  test('generates with dorian scale', () => {
    const result = ChordProgression.generate('D', 'dorian', 4)
    expect(result).toEqual(['Dm7', 'Cmaj7', 'Bm7b5', 'Am7'])
  })

  test('generates with harmonic minor scale', () => {
    const result = ChordProgression.generate('D', 'harmonic-minor', 4)
    expect(result).toEqual(['Dm7', 'C#dim7', 'Bbmaj7', 'A7'])
  })
})

describe('ChordProgression templates', () => {
  test('i-VII-VI-v template in D minor', () => {
    const result = ChordProgression.fromTemplate('i-VII-VI-v', 'D', 'natural-minor')
    expect(result).toEqual(['Dm7', 'C7', 'Bbmaj7', 'Am7'])
  })

  test('i-iv-VII-III template in D minor', () => {
    const result = ChordProgression.fromTemplate('i-iv-VII-III', 'D', 'natural-minor')
    expect(result).toEqual(['Dm7', 'Gm7', 'C7', 'Fmaj7'])
  })

  test('parallel-descent template in C minor', () => {
    const result = ChordProgression.fromTemplate('parallel-descent', 'C', 'natural-minor')
    expect(result).toEqual(['Cm9', 'Bm9', 'Bbm9', 'Am9', 'Abm9', 'Gm9', 'Gbm9'])
  })

  test('parallel-descent template in D minor', () => {
    const result = ChordProgression.fromTemplate('parallel-descent', 'D', 'natural-minor')
    expect(result).toEqual(['Dm9', 'C#m9', 'Cm9', 'Bm9', 'Bbm9', 'Am9', 'Abm9'])
  })
})
