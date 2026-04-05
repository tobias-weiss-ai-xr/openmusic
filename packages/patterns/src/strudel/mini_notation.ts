export interface MiniNotationNote {
  type: 'note'
  value: string
}

export interface MiniNotationRest {
  type: 'rest'
  value: '.'
}

export interface MiniNotationGroup {
  type: 'group'
  elements: (MiniNotationNote | MiniNotationRest)[]
}

export type MiniNotationElement = MiniNotationNote | MiniNotationRest | MiniNotationGroup

/**
 * Parses a single token into a note or rest.
 * @param token - Token string ('.' for rest, note name otherwise)
 * @returns MiniNotationNote or MiniNotationRest
 */
export function parseNote(token: string): MiniNotationNote | MiniNotationRest {
  if (token === '.') {
    return { type: 'rest', value: '.' }
  }
  return { type: 'note', value: token }
}

/**
 * Parses a bracketed group of elements (e.g., '[c,e,g]').
 * @param input - String with brackets (e.g., '[c,e,g]')
 * @returns MiniNotationGroup with parsed elements
 */
export function parseGroup(input: string): MiniNotationGroup {
  const inner = input.slice(1, -1)
  const elements: (MiniNotationNote | MiniNotationRest)[] = []

  for (const token of inner.split(',')) {
    const trimmed = token.trim()
    if (trimmed === '') continue
    elements.push(parseNote(trimmed))
  }

  return { type: 'group', elements }
}

/**
 * Parses a mini-notation string into an array of elements.
 * Supports: notes ('c', 'd#'), rests ('.'), and groups ('[c,e,g]').
 * @param input - Mini-notation string (e.g., 'c d . e [f,a]')
 * @returns Array of parsed MiniNotationElement
 */
export function parseMiniNotation(input: string): MiniNotationElement[] {
  const trimmed = input.trim()
  if (trimmed === '') return []

  const tokens: string[] = []
  let current = ''
  let depth = 0

  for (const char of trimmed) {
    if (char === '[') {
      depth++
      if (depth === 1) {
        if (current.trim()) tokens.push(current.trim())
        current = '['
        continue
      }
    }
    if (char === ']') {
      depth--
      if (depth === 0) {
        current += ']'
        tokens.push(current)
        current = ''
        continue
      }
    }
    if (char === ' ' && depth === 0) {
      if (current.trim()) tokens.push(current.trim())
      current = ''
      continue
    }
    current += char
  }
  if (current.trim()) tokens.push(current.trim())

  return tokens.map(token => {
    if (token.startsWith('[') && token.endsWith(']')) {
      return parseGroup(token)
    }
    return parseNote(token)
  })
}
