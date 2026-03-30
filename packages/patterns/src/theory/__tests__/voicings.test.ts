import { test, expect, describe } from 'vitest'
import { voice, invert } from '../voicings'

describe('voice', () => {
  test('voices a minor triad', () => {
    const result = voice('D', 'm')
    expect(result).toEqual(['D', 'F', 'A'])
  })

  test('voices a minor 7th chord', () => {
    const result = voice('D', 'm7')
    expect(result).toEqual(['D', 'F', 'A', 'C'])
  })

  test('voices a minor 9th chord', () => {
    const result = voice('D', 'm9')
    expect(result).toEqual(['D', 'F', 'A', 'C', 'E'])
  })

  test('voices a minor 11th chord', () => {
    const result = voice('D', 'm11')
    expect(result).toEqual(['D', 'F', 'A', 'C', 'E', 'G'])
  })

  test('voices C minor 7th with correct flats', () => {
    const result = voice('C', 'm7')
    expect(result).toEqual(['C', 'Eb', 'G', 'Bb'])
  })

  test('voices A minor 9th', () => {
    const result = voice('A', 'm9')
    expect(result).toEqual(['A', 'C', 'E', 'G', 'B'])
  })
})

describe('invert', () => {
  test('first inversion moves root to top', () => {
    const result = invert(['D', 'F', 'A'], 1)
    expect(result).toEqual(['F', 'A', 'D'])
  })

  test('second inversion moves root and third to top', () => {
    const result = invert(['D', 'F', 'A'], 2)
    expect(result).toEqual(['A', 'D', 'F'])
  })

  test('third inversion for 7th chord', () => {
    const result = invert(['D', 'F', 'A', 'C'], 3)
    expect(result).toEqual(['C', 'D', 'F', 'A'])
  })

  test('zero inversion returns original', () => {
    const result = invert(['D', 'F', 'A', 'C'], 0)
    expect(result).toEqual(['D', 'F', 'A', 'C'])
  })

  test('handles 5-note voicing inversion', () => {
    const result = invert(['D', 'F', 'A', 'C', 'E'], 2)
    expect(result).toEqual(['A', 'C', 'E', 'D', 'F'])
  })
})
