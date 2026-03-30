# Test Audit - Identified Gaps

## Non-Blocking Gaps

### Python
1. `acestep/generator.py` lines 114-161: `_generate()` method (actual model call) untested - requires real ACE-Step GPU model
2. `acestep/generator.py` lines 77-86: `_classify_gpu_tier` tiers 5-8 (16GB+ VRAM) untested
3. `cli/main.py` lines 19-35: `_parse_length_to_seconds` error path for invalid strings like "abc"
4. `config/parser.py` line 54: YAML unavailable RuntimeError untested
5. `config/parser.py` lines 72-78: Unknown extension YAML→JSON fallback untested

### TypeScript
6. `effects/config.ts`: No dedicated unit test for preset values (DEEP_DUB, MINIMAL_DUB, CLUB_DUB) - tested indirectly
7. `theory/scales.ts` line 29: `noteToIndex` error path for unknown note strings untested
8. LSP type errors in effect test files: `AudioBuffer` type mismatch between `web-audio-api` and native - tests still pass at runtime

### Missing Coverage Tool
9. `@vitest/coverage-v8` not installed - cannot measure TS line coverage numerically
