import { test, expect, describe } from 'vitest'
import { getScale, getChordTones, type ScaleType } from '../scales'

describe('getScale', () => {
  test('returns C natural minor scale', () => {
    const result = getScale('C', 'natural-minor')
    expect(result).toEqual(['C', 'D', 'Eb', 'F', 'G', 'Ab', 'Bb'])
  })

  test('returns D natural minor scale', () => {
    const result = getScale('D', 'natural-minor')
    expect(result).toEqual(['D', 'E', 'F', 'G', 'A', 'Bb', 'C'])
  })

  test('returns A natural minor scale', () => {
    const result = getScale('A', 'natural-minor')
    expect(result).toEqual(['A', 'B', 'C', 'D', 'E', 'F', 'G'])
  })

  test('returns E natural minor scale', () => {
    const result = getScale('E', 'natural-minor')
    expect(result).toEqual(['E', 'F#', 'G', 'A', 'B', 'C', 'D'])
  })

  test('returns F natural minor scale', () => {
    const result = getScale('F', 'natural-minor')
    expect(result).toEqual(['F', 'G', 'Ab', 'Bb', 'C', 'Db', 'Eb'])
  })

  test('returns D harmonic minor scale', () => {
    const result = getScale('D', 'harmonic-minor')
    expect(result).toEqual(['D', 'E', 'F', 'G', 'A', 'Bb', 'C#'])
  })

  test('returns D dorian scale', () => {
    const result = getScale('D', 'dorian')
    expect(result).toEqual(['D', 'E', 'F', 'G', 'A', 'B', 'C'])
  })

  test('handles sharp keys correctly (B minor)', () => {
    const result = getScale('B', 'natural-minor')
    expect(result).toEqual(['B', 'C#', 'D', 'E', 'F#', 'G', 'A'])
  })

  test('handles flat keys correctly (Bb minor)', () => {
    const result = getScale('Bb', 'natural-minor')
    expect(result).toEqual(['Bb', 'C', 'Db', 'Eb', 'F', 'Gb', 'Ab'])
  })
})

describe('getChordTones', () => {
  test('returns minor triad tones', () => {
    const result = getChordTones('D', 'm')
    expect(result).toEqual(['D', 'F', 'A'])
  })

  test('returns minor 7th chord tones', () => {
    const result = getChordTones('D', 'm7')
    expect(result).toEqual(['D', 'F', 'A', 'C'])
  })

  test('returns minor 9th chord tones (with octave)', () => {
    const result = getChordTones('D', 'm9')
    expect(result).toEqual(['D', 'F', 'A', 'C', 'E'])
  })

  test('returns minor 11th chord tones (with octave)', () => {
    const result = getChordTones('D', 'm11')
    expect(result).toEqual(['D', 'F', 'A', 'C', 'E', 'G'])
  })

  test('returns C minor 7th tones', () => {
    const result = getChordTones('C', 'm7')
    expect(result).toEqual(['C', 'Eb', 'G', 'Bb'])
  })

  test('returns A minor triad tones', () => {
    const result = getChordTones('A', 'm')
    expect(result).toEqual(['A', 'C', 'E'])
  })
})
