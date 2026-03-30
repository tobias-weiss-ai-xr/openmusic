# Learnings - Effects Chain Implementation

## web-audio-api in Node.js
- `web-audio-api` npm package provides pure JS Web Audio API implementation for Node.js
- Use `OfflineAudioContext` for faster-than-realtime rendering
- `import { OfflineAudioContext } from 'web-audio-api'` (value import, NOT `import type`)
- `import type` causes "cannot be used as a value" runtime errors

## Type Conflicts: web-audio-api vs DOM lib
- `web-audio-api` types conflict with DOM's `AudioBuffer`, `AudioNode`, `GainNode`, etc.
- LSP shows many errors but `skipLibCheck: true` in tsconfig handles compilation
- Fix: Use `ReturnType<OfflineAudioContext['createGain']>` for field types
- Fix: Use `as any` for `source.buffer = inputBuffer` assignments
- Fix: Don't explicitly annotate `process()` return types — let TS infer
- Fix: In tests, import `AudioBuffer` from `web-audio-api` (it's not a global in Node.js)

## Vitest + ESM .js extensions
- Test files use `.js` extension in imports: `import { X } from './delay.js'`
- Vitest resolves `.ts` files for `.js` extension imports automatically
- chain.test.ts was in `src/` alongside `chain.ts`, so import should be `./chain.js` not `../chain.js`

## Effect Implementation Patterns
- Each effect class has `input` and `output` GainNodes for chaining
- `process()` creates a fresh OfflineAudioContext, builds the effect graph, renders, returns buffer
- Disabled effects bypass processing by connecting input directly to output
- Feedback clamped to 0.94 to prevent runaway
- Reverb impulse response: exponential decay noise (`Math.pow(1 - i/length, decay)`)
- Distortion: soft-clip curve using atan-like formula with `k = amount * 100`
- Vinyl: separate crackle (random spikes) and hiss (continuous noise) buffers

## Performance
- Reverb with 4s decay is slow (~2-3s render for 1s audio) — DEEP_DUB preset excluded from loop test
- 1s audio buffer at 44100Hz stereo = sufficient for testing all effects
- Set test timeouts to 15s for chain tests with multiple presets

## TDD Flow
- Write all tests first (RED), verify they fail for the right reasons
- Implement all effects, fix import/type issues
- GREEN: all 32 effects tests pass
- Pre-existing patterns package failures (8 tests) are unrelated — enharmonic naming bugs
