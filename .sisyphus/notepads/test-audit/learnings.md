# Test Audit Learnings

## Project Structure
- 4 packages: core (Python), effects (TS), patterns (TS), cli (TS)
- 499 tests total: 326 Python + 173 TypeScript
- Python uses pytest, TS uses vitest
- Python coverage tool: `--cov` flag works; TS coverage requires `@vitest/coverage-v8` (not installed)

## Coverage Patterns
- Hardware-dependent code (ACE-Step model invocation) intentionally left untested
- Bridge tests use subprocess mocking extensively with `side_effect` interceptors
- Config validation uses regex-based key patterns (`_MINOR_KEY_REGEX`)
- Integration tests in `test_integration/` cover CLI→Config→Orchestrator→Bridge flow

## Test Quality Observations
- Error paths well covered: BridgeError, EncodingError, EmbeddingError, ValueError all tested
- Boundary conditions covered: tolerance bounds, peak thresholds, exact start/end times
- Music theory edge cases covered: enharmonics (B minor, Bb minor), all 3 scale types, negative intervals
- Barrel export tests exist for most Python modules (`test_barrel_exports.py`)
