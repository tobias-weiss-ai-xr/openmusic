# Audio Engine Implementation Learnings

## WAV Format
- Format code 3 = IEEE 32-bit float PCM (not the common 1 = PCM)
- WAV header is 44 bytes: RIFF(12) + fmt(24) + data(8)
- Data is interleaved: sample[frame*channels + channel]
- web-audio-api's OfflineAudioContext.decodeAudioData handles WAV natively

## web-audio-api
- Float32Array<ArrayBufferLike> vs Float32Array<ArrayBuffer> type mismatch is a known issue
- chain.ts already uses `as any` to work around it
- Not a runtime issue, only TypeScript strictness

## Testing
- Generated test WAV files (sine wave buffers) - no real file dependencies
- All tests use tmpdir for isolation
- Tests: 10 decoder, 7 encoder, 11 audio_engine = 28 new tests

## Architecture
- AudioEngine mixes multiple stems by summing with gain = 1/N
- Effects chain processes the mixed buffer via DubTechnoEffectsChain
- Bridge config matches docs/architecture.md JSON format exactly
- FLAC/MP3 are stubs (throw) - WAV is the primary export for v1
