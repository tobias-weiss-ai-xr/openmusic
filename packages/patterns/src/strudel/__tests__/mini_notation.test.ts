import { test, expect, describe } from 'vitest'
import { parseMiniNotation, parseNote, parseGroup, type MiniNotationElement, type MiniNotationGroup } from '../mini_notation'

describe('parseNote', () => {
  test('parses a single note name', () => {
    const result = parseNote('Cm9')
    expect(result).toEqual({ type: 'note', value: 'Cm9' })
  })

  test('parses a note with accidentals', () => {
    const result = parseNote('Ebm9')
    expect(result).toEqual({ type: 'note', value: 'Ebm9' })
  })

  test('parses a simple note', () => {
    const result = parseNote('C')
    expect(result).toEqual({ type: 'note', value: 'C' })
  })

  test('parses a rest as note type with rest value', () => {
    const result = parseNote('.')
    expect(result).toEqual({ type: 'rest', value: '.' })
  })
})

describe('parseGroup', () => {
  test('parses a bracketed group', () => {
    const result = parseGroup('[Cm9, Ebm9, Gm9]')
    expect(result).toEqual({
      type: 'group',
      elements: [
        { type: 'note', value: 'Cm9' },
        { type: 'note', value: 'Ebm9' },
        { type: 'note', value: 'Gm9' },
      ],
    })
  })

  test('parses a group with spaces around commas', () => {
    const result = parseGroup('[Cm9,Ebm9]')
    expect(result).toEqual({
      type: 'group',
      elements: [
        { type: 'note', value: 'Cm9' },
        { type: 'note', value: 'Ebm9' },
      ],
    })
  })

  test('parses a group with rests', () => {
    const result = parseGroup('[Cm9, ., Ebm9]')
    expect(result).toEqual({
      type: 'group',
      elements: [
        { type: 'note', value: 'Cm9' },
        { type: 'rest', value: '.' },
        { type: 'note', value: 'Ebm9' },
      ],
    })
  })

  test('parses a single-element group', () => {
    const result = parseGroup('[Cm9]')
    expect(result).toEqual({
      type: 'group',
      elements: [{ type: 'note', value: 'Cm9' }],
    })
  })
})

describe('parseMiniNotation', () => {
  test('parses a single chord', () => {
    const result = parseMiniNotation('Cm9')
    expect(result).toEqual([{ type: 'note', value: 'Cm9' }])
  })

  test('parses space-separated elements', () => {
    const result = parseMiniNotation('Cm9 Ebm9')
    expect(result).toEqual([
      { type: 'note', value: 'Cm9' },
      { type: 'note', value: 'Ebm9' },
    ])
  })

  test('parses a note followed by a group', () => {
    const result = parseMiniNotation('Cm9 [Cm9, Ebm9, Gm9]')
    expect(result).toEqual([
      { type: 'note', value: 'Cm9' },
      {
        type: 'group',
        elements: [
          { type: 'note', value: 'Cm9' },
          { type: 'note', value: 'Ebm9' },
          { type: 'note', value: 'Gm9' },
        ],
      },
    ])
  })

  test('parses rests in sequence', () => {
    const result = parseMiniNotation('Cm9 . Ebm9')
    expect(result).toEqual([
      { type: 'note', value: 'Cm9' },
      { type: 'rest', value: '.' },
      { type: 'note', value: 'Ebm9' },
    ])
  })

  test('parses multiple groups', () => {
    const result = parseMiniNotation('[Cm9, Ebm9] [Gm9, Am9]')
    expect(result).toEqual([
      {
        type: 'group',
        elements: [
          { type: 'note', value: 'Cm9' },
          { type: 'note', value: 'Ebm9' },
        ],
      },
      {
        type: 'group',
        elements: [
          { type: 'note', value: 'Gm9' },
          { type: 'note', value: 'Am9' },
        ],
      },
    ])
  })

  test('parses complex pattern with mixed elements', () => {
    const result = parseMiniNotation('Cm9 [Ebm9, .] Gm9 .')
    expect(result).toEqual([
      { type: 'note', value: 'Cm9' },
      {
        type: 'group',
        elements: [
          { type: 'note', value: 'Ebm9' },
          { type: 'rest', value: '.' },
        ],
      },
      { type: 'note', value: 'Gm9' },
      { type: 'rest', value: '.' },
    ])
  })

  test('parses empty string as empty array', () => {
    const result = parseMiniNotation('')
    expect(result).toEqual([])
  })

  test('parses whitespace-only string as empty array', () => {
    const result = parseMiniNotation('   ')
    expect(result).toEqual([])
  })

  test('parses note with octave number', () => {
    const result = parseMiniNotation('C4')
    expect(result).toEqual([{ type: 'note', value: 'C4' }])
  })

  test('parses sharp and flat notes', () => {
    const result = parseMiniNotation('F#m7 Bbm9')
    expect(result).toEqual([
      { type: 'note', value: 'F#m7' },
      { type: 'note', value: 'Bbm9' },
    ])
  })
})
