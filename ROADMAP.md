# OpenMusic Project Roadmap

> **Current Version**: 0.1.0
> **Status**: All pipeline features implemented, first YouTube release pipeline ready

---

## ✅ COMPLETED

### Framework Foundation

- [x] Monorepo scaffolding (pnpm workspace, Python package, TypeScript packages)
- [x] GitHub setup (README, LICENSE, CI/CD, issue/PR templates)
- [x] ACE-Step 1.5 validation and integration
- [x] Strudel + Tone.js integration research
- [x] Dub techno theory specification
- [x] Architecture design (Python ↔ TypeScript bridge)
- [x] Test infrastructure (Vitest + Pytest)
- [x] 5-minute PoC (end-to-end pipeline)
- [x] Acceptance criteria document

### Core Modules

- [x] Dub techno theory module (TypeScript) — chord progressions, scales, voicings
- [x] ACE-Step integration (Python) — texture generation with caching
- [x] Strudel pattern library (TypeScript) — chord stabs, bass pulses, hi-hats
- [x] Tone.js effects chain (TypeScript) — delay, reverb, filter, distortion, vinyl, tape saturation, granular delay
- [x] Python orchestrator core — MixOrchestrator, MixConfig, progress reporting
- [x] TypeScript audio engine — offline rendering, WAV/FLAC/MP3 export
- [x] Bridge layer — file-based Python ↔ TypeScript communication
- [x] Python DSP bridge — pedalboard-based effects (alternative to TypeScript)

### CLI & Export

- [x] CLI interface — `generate`, `validate`, `version`, `auth-youtube`
- [x] Config file parser — YAML/JSON with validation
- [x] Mix arrangement engine — intro, development, climax, outro sections
- [x] Export pipeline — WAV, FLAC, MP3 with metadata
- [x] End-to-end integration tests
- [x] 2-hour mix generation test

### Sound Quality Improvements (Tier 1-3)

- [x] Sidechain compression in PythonDSPBridge
- [x] Mid-side stereo widening + mono-below-150Hz
- [x] LFO modulation engine (non-pass-through)
- [x] GenerationParams dataclass usage
- [x] Quality feedback for Bayesian pattern selector
- [x] Saturation-first effects chain order (canonical dub chain)
- [x] Bandpass filter in delay feedback path (Basic Channel style)
- [x] Dual delay with pitch detune
- [x] Parameter automation (envelopes, LFO, random walk)
- [x] Brickwall limiter + proper LUFS normalization in MasteringChain
- [x] TPDF dithering in FLAC encoder
- [x] Seed parameter in ACE-Step generator
- [x] Cleaned up broken spectral masking files
- [x] Spectral gate effect

### Sprint 1 — "Ship the Pipeline"

- [x] P0: Fix openart dependency
- [x] P0: Lazy video module imports (fix 4 test collection errors)
- [x] P0: Push to origin, green CI
- [x] P1: `openmusic release` command (generate → render MP4 → upload YouTube)
- [x] P1: Batch short generation tooling
- [x] P2: Python test suite clean (708 passed, 9 skipped)
- [x] P2: Test coverage for publish/release
- [x] P2: E2E sound quality verification
- [x] P3: TypeScript build all packages
- [x] P3: Clean working tree
- [x] P3: README/AGENTS.md updates

### YouTube Upload

- [x] YouTube OAuth with localhost:18080 callback
- [x] Video upload with metadata (title, description, tags)
- [x] Playlist management (auto-create/append)
- [x] Thumbnail support
- [x] Scheduled publishing (ISO 8601 premiere)
- [x] Fallback upload via cookies.txt

### Shorts Pipeline

- [x] Short video generation (stoic quotes, animated visuals)
- [x] `openmusic short generate` command
- [x] `openmusic short batch` command (specified positions)
- [x] `openmusic short batch-auto` command (auto-staggered positions)
- [x] Content category rotation (stoic, meditation, devops)
- [x] Theme support for shorts
- [x] YouTube upload integration for shorts

---

## 📋 NEXT UP

### 1. Pattern Library Test Fixes — Update Tests to Match Current APIs

**Priority**: High | **Effort**: Small

36 Python test failures in the `patterns` subsystem due to test rot (tests written for APIs that have since changed):

- [ ] `test_pattern_library.py` — 20 failures: `PatternLibrary.__init__()` requires `path`; uses `add()`/`patterns`/`get_by_tags()`/`sample()` APIs
- [ ] `test_markov.py` — 15 failures: `PhaseTransitionMatrix` uses `StyleFactory.create()` not `create_style()`; phase enum values changed
- [ ] `test_bayesian.py` — 1 failure: `PatternLibrary` requires `path`; `PatternEntry` has no `name`/`description` fields

### 2. Scheduling System — Automated Mix Generation

**Priority**: Medium | **Effort**: Medium

Build infrastructure for scheduled, unattended mix generation:

- [ ] Cron job script for overnight mix generation
- [ ] Configuration for scheduled releases (day/time/template)
- [ ] Output rotation (archive old mixes)
- [ ] Notification on completion (email/webhook)
- [ ] Documentation for setting up scheduling

### 3. Analytics Tracking — Channel Performance

**Priority**: Low | **Effort**: Medium

Track YouTube channel performance and mix quality metrics:

- [ ] YouTube Analytics API integration (views, subs per content type)
- [ ] Local metrics tracking (generation time, file sizes, quality scores)
- [ ] Dashboard or report generation
- [ ] Alerting on anomalies (low performance, generation failures)

### 4. Content Expansion

**Priority**: Low | **Effort**: Ongoing

Scale content production per the 2026 release plan:

- [ ] DevOps tips expansion (Terraform, K8s, CI/CD, SRE)
- [ ] AI/ML tips expansion (LLMs, agents, RAG, fine-tuning)
- [ ] Graph tips expansion (Neo4j, GraphRAG, graph algorithms)
- [ ] Mix theme rotation (dark ambient, Detroit techno, hypnotic)

---

## 🗺️ STRETCH GOALS

- [ ] DAW integration (Ableton Live export)
- [ ] Live DJ performance mode
- [ ] Real-time parameter control (MIDI)
- [ ] Web interface for mix management
- [ ] Multi-model AI support
- [ ] Fine-tuning pipeline for custom sounds
- [ ] Mobile app for monitoring
