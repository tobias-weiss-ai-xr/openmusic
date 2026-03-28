# OpenMusic: AI-Powered Dub Techno Framework

## TL;DR

> **Quick Summary**: Build an open-source framework that generates 2-hour dub techno mixes using ACE-Step 1.5 (AI), Strudel (patterns), and Tone.js (effects). CLI-first, studio production focus, with Ableton/Live DJ on the roadmap.
> 
> **Deliverables**:
> - CLI tool: `openmusic generate --length 2h --style dub_techno --output mix.flac`
> - Python package: ACE-Step integration + orchestration
> - TypeScript package: Strudel patterns + Tone.js effects + dub techno theory
> - GitHub repo with full documentation and CI/CD
> 
> **Estimated Effort**: XL (Large)
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Project Setup → ACE-Step Validation → Architecture → Core Modules → Integration → Export Pipeline

---

## Context

### Original Request
Create an open-source framework for AI-powered dub techno creation to generate mixes like Rob Jenkins (https://www.youtube.com/watch?v=7CywAKcUKDw) - atmospheric, deep, minimal, long-form dub techno.

### Interview Summary
**Key Discussions**:
- Tech Stack: Python + TypeScript (Python for AI, TypeScript for patterns/effects)
- Output: 2-hour full mixes (studio production focus)
- AI: ACE-Step 1.5 integration
- Pattern Layer: Strudel (TidalCycles port) - hybrid REPL + library
- Audio Engine: Tone.js + WebAudio
- Export: WAV + FLAC + MP3
- Music Theory: Tonal.js + custom dub techno theory module
- Testing: TDD with Vitest + Pytest
- Publishing: git@github.com:tobias-weiss-ai-xr/openmusic.git

**Roadmap (Out of Scope for v1)**:
- Ableton Live integration
- Live DJ performance mode
- Real-time parameter control

### Metis Review - Key Gaps Addressed
- **Architecture**: Python (orchestrator) ↔ TypeScript (audio engine) via file-based bridge
- **ACE-Step**: Must validate dub techno capability before full implementation
- **Scope**: Studio production only (no live performance in v1)
- **Guardrails**: No DAW integration, no MIDI controllers, no modular effects
- **Acceptance Criteria**: Defined as executable commands with expected outputs

---

## Work Objectives

### Core Objective
Build a CLI tool that generates 2-hour professional-quality dub techno mixes by combining AI-generated textures (ACE-Step), algorithmic patterns (Strudel), and genre-specific effects chains (Tone.js).

### Concrete Deliverables
- `@openmusic/core` - Python package for orchestration and ACE-Step integration
- `@openmusic/patterns` - TypeScript package for Strudel patterns and dub techno theory
- `@openmusic/effects` - TypeScript package for Tone.js dub techno effects chain
- `openmusic` CLI - Unified command-line interface
- GitHub repository with README, CONTRIBUTING, LICENSE, CI/CD

### Definition of Done
- [ ] `openmusic generate --length 2h --output mix.flac` produces valid 2-hour FLAC file
- [ ] Generated mix contains recognizable dub techno elements (chord stabs, delays, reverb)
- [ ] All tests pass: `pytest && npm test`
- [ ] Documentation complete: README with usage examples
- [ ] Published to GitHub: git@github.com:tobias-weiss-ai-xr/openmusic.git

### Must Have
- ACE-Step 1.5 integration for AI-generated textures
- Strudel pattern layer for algorithmic composition
- Tone.js effects chain (delay, reverb, filter, saturation, vinyl noise)
- Dub techno theory module (parallel minor chords, scales, extensions)
- CLI with config file support
- WAV/FLAC/MP3 export
- TDD test coverage

### Must NOT Have (Guardrails - v1)
- NO DAW integration (Ableton, Reaper, etc.)
- NO MIDI controller support
- NO VST/AU plugin hosting
- NO web interface
- NO live performance features
- NO real-time generation (offline only)
- NO multi-model AI support
- NO fine-tuning or training

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (fresh project)
- **Automated tests**: YES (TDD)
- **Framework**: Vitest (TypeScript) + Pytest (Python)
- **TDD Workflow**: Each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task includes agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI**: Bash — Run commands, check exit codes, validate output files
- **Audio**: Bash (ffmpeg/sox) — Verify duration, sample rate, bit depth
- **Python**: Bash (pytest) — Run unit tests, check coverage
- **TypeScript**: Bash (npm test) — Run unit tests, check coverage

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation + validation):
├── Task 1: Project scaffolding (monorepo setup) [quick]
├── Task 2: GitHub setup (README, LICENSE, CI/CD, templates) [quick]
├── Task 3: ACE-Step validation (test dub techno capability) [deep]
├── Task 4: Strudel + Tone.js research (integration patterns) [deep]
└── Task 5: Dub techno theory spec (measurable parameters) [writing]

Wave 2 (After Wave 1 — architecture + proof of concept):
├── Task 6: Architecture design (Python ↔ TypeScript bridge) [deep]
├── Task 7: Test infrastructure setup (Vitest + Pytest) [quick]
├── Task 8: 5-minute PoC (minimal end-to-end pipeline) [deep]
└── Task 9: Acceptance criteria document [writing]

Wave 3 (After Wave 2 — core modules, MAX PARALLEL):
├── Task 10: Dub techno theory module (TypeScript) [deep]
├── Task 11: ACE-Step integration (Python) [deep]
├── Task 12: Strudel pattern library (TypeScript) [deep]
├── Task 13: Tone.js effects chain (TypeScript) [deep]
├── Task 14: Python orchestrator core [deep]
├── Task 15: TypeScript audio engine [deep]
└── Task 16: Bridge layer (file-based communication) [deep]

Wave 4 (After Wave 3 — CLI + integration):
├── Task 17: CLI interface (command structure) [quick]
├── Task 18: Config file parser (YAML/JSON) [quick]
├── Task 19: Mix arrangement engine [deep]
├── Task 20: Export pipeline (WAV/FLAC/MP3) [deep]
├── Task 21: End-to-end integration tests [deep]
└── Task 22: 2-hour mix generation test [deep]

Wave FINAL (After ALL tasks — verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Full QA - generate 2-hour mix (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: 1 → 3 → 6 → 8 → 11 → 14 → 16 → 19 → 20 → 22 → F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 7 (Wave 3)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1 | — | 6, 7, 17, 18 |
| 2 | 1 | — |
| 3 | — | 6, 8, 11 |
| 4 | — | 6, 8, 12, 13 |
| 5 | — | 9, 10 |
| 6 | 1, 3, 4 | 8, 14, 15, 16 |
| 7 | 1 | 10, 11, 12, 13, 14, 15, 16 |
| 8 | 3, 4, 6, 7 | 19, 20 |
| 9 | 5, 6 | 21, 22 |
| 10 | 5, 7 | 12, 19 |
| 11 | 3, 7 | 14, 16, 19 |
| 12 | 4, 7, 10 | 15, 19 |
| 13 | 4, 7 | 15, 19 |
| 14 | 6, 7, 11 | 16, 17, 19 |
| 15 | 6, 7, 12, 13 | 16, 19, 20 |
| 16 | 6, 11, 14, 15 | 19, 20 |
| 17 | 1, 14 | 21, 22 |
| 18 | 1, 14 | 17, 21 |
| 19 | 8, 10, 11, 12, 13, 14, 15, 16 | 20, 21, 22 |
| 20 | 15, 19 | 21, 22 |
| 21 | 9, 17, 18, 19, 20 | 22 |
| 22 | 19, 20, 21 | F3 |
| F1 | ALL | — |
| F2 | ALL | — |
| F3 | 22 | — |
| F4 | ALL | — |

### Agent Dispatch Summary

- **Wave 1**: **5** — T1-T2 → `quick`, T3-T4 → `deep`, T5 → `writing`
- **Wave 2**: **4** — T6 → `deep`, T7 → `quick`, T8 → `deep`, T9 → `writing`
- **Wave 3**: **7** — T10-T16 → `deep`
- **Wave 4**: **6** — T17-T18 → `quick`, T19-T22 → `deep`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.

- [x] 1. Project Scaffolding (Monorepo Setup)

  **What to do**:
  - Create monorepo structure with pnpm workspaces
  - Initialize packages: `@openmusic/core` (Python), `@openmusic/patterns`, `@openmusic/effects`, `@openmusic/cli` (TypeScript)
  - Add root `package.json`, `pyproject.toml`, `pnpm-workspace.yaml`
  - Configure TypeScript with strict mode
  - Set up Python virtual environment structure
  - Add `.gitignore` for Python, Node, audio files

  **Must NOT do**:
  - Do NOT install ACE-Step yet (separate task)
  - Do NOT configure CI/CD yet (separate task)
  - Do NOT add any business logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard project scaffolding, well-defined structure
  - **Skills**: []
    - No special skills needed for boilerplate setup

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: 6, 7, 17, 18
  - **Blocked By**: None (can start immediately)

  **References**:
  - `https://pnpm.io/workspaces` - pnpm monorepo configuration
  - `https://python-poetry.org/docs/pyproject/` - Python project structure

  **Acceptance Criteria**:
  - [ ] `pnpm install` runs successfully in root
  - [ ] `packages/core/pyproject.toml` exists
  - [ ] `packages/patterns/package.json` exists
  - [ ] `packages/effects/package.json` exists
  - [ ] `packages/cli/package.json` exists
  - [ ] `tsconfig.json` has `"strict": true`
  - [ ] `.gitignore` includes `node_modules/`, `__pycache__/`, `*.wav`, `*.flac`

  **QA Scenarios**:

  ```
  Scenario: Verify monorepo structure
    Tool: Bash
    Preconditions: Fresh project directory
    Steps:
      1. Run `ls -la packages/`
      2. Assert output contains: core, patterns, effects, cli
      3. Run `pnpm list --depth 0`
      4. Assert exit code 0
    Expected Result: All package directories exist, pnpm workspace configured
    Evidence: .sisyphus/evidence/task-01-structure.txt

  Scenario: TypeScript configuration valid
    Tool: Bash
    Preconditions: packages/ directories exist
    Steps:
      1. Run `npx tsc --version`
      2. Run `cat tsconfig.json | grep '"strict"'`
      3. Assert output contains `"strict": true`
    Expected Result: TypeScript configured with strict mode
    Evidence: .sisyphus/evidence/task-01-typescript.txt
  ```

  **Commit**: YES
  - Message: `chore: initial project scaffolding`
  - Files: `package.json, pnpm-workspace.yaml, tsconfig.json, .gitignore, packages/*/package.json, packages/core/pyproject.toml`

---

- [ ] 2. GitHub Setup (README, LICENSE, CI/CD, Templates)

  **What to do**:
  - Create `README.md` with project overview, installation, usage examples
  - Add `LICENSE` file (MIT)
  - Create `.github/workflows/ci.yml` for linting and testing
  - Add `.github/ISSUE_TEMPLATE/bug_report.md`
  - Add `.github/ISSUE_TEMPLATE/feature_request.md`
  - Add `.github/PULL_REQUEST_TEMPLATE.md`
  - Add `CONTRIBUTING.md` with development setup instructions
  - Add `CHANGELOG.md` placeholder
  - Set up git remote: `git@github.com:tobias-weiss-ai-xr/openmusic.git`

  **Must NOT do**:
  - Do NOT push to GitHub yet (wait until working code exists)
  - Do NOT add badges that don't work yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard GitHub boilerplate, documentation
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: None
  - **Blocked By**: Task 1 (needs project structure)

  **References**:
  - `https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests` - GitHub templates

  **Acceptance Criteria**:
  - [ ] `README.md` exists with sections: Overview, Installation, Usage, Roadmap, License
  - [ ] `LICENSE` contains MIT license text
  - [ ] `.github/workflows/ci.yml` exists with test/lint jobs
  - [ ] `.github/ISSUE_TEMPLATE/bug_report.md` exists
  - [ ] `.github/ISSUE_TEMPLATE/feature_request.md` exists
  - [ ] `.github/PULL_REQUEST_TEMPLATE.md` exists
  - [ ] `CONTRIBUTING.md` exists with dev setup instructions
  - [ ] `git remote -v` shows `origin git@github.com:tobias-weiss-ai-xr/openmusic.git`

  **QA Scenarios**:

  ```
  Scenario: Verify GitHub templates exist
    Tool: Bash
    Preconditions: Task 1 completed
    Steps:
      1. Run `ls -la .github/ISSUE_TEMPLATE/`
      2. Assert output contains: bug_report.md, feature_request.md
      3. Run `ls -la .github/workflows/`
      4. Assert output contains: ci.yml
    Expected Result: All GitHub templates and workflows exist
    Evidence: .sisyphus/evidence/task-02-github-templates.txt

  Scenario: Verify README structure
    Tool: Bash
    Preconditions: README.md exists
    Steps:
      1. Run `grep -E "^## (Overview|Installation|Usage|Roadmap|License)" README.md`
      2. Assert output contains all 5 section headers
    Expected Result: README has required sections
    Evidence: .sisyphus/evidence/task-02-readme.txt

  Scenario: Verify git remote configured
    Tool: Bash
    Preconditions: git remote added
    Steps:
      1. Run `git remote -v`
      2. Assert output contains `git@github.com:tobias-weiss-ai-xr/openmusic.git`
    Expected Result: Git remote points to correct repository
    Evidence: .sisyphus/evidence/task-02-git-remote.txt
  ```

  **Commit**: YES
  - Message: `docs: add README, LICENSE, and GitHub templates`
  - Files: `README.md, LICENSE, CONTRIBUTING.md, CHANGELOG.md, .github/**`

---

- [x] 3. ACE-Step Validation (Test Dub Techno Capability)

  **What to do**:
  - Install ACE-Step 1.5 in `packages/core`
  - Create test script to generate 30-second dub techno samples
  - Test with prompts: "deep dub techno chord stabs", "atmospheric dub techno bass", "dub techno delay textures"
  - Document output format (WAV? MIDI? Token sequences?)
  - Document generation latency (seconds per 30s of audio)
  - Document hardware requirements (GPU VRAM, RAM)
  - Save test outputs to `tests/fixtures/acestep/`

  **Must NOT do**:
  - Do NOT integrate into main pipeline yet
  - Do NOT optimize for performance yet
  - Do NOT fine-tune the model

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Research task requiring experimentation and documentation
  - **Skills**: [`superpowers/verification-before-completion`]
    - Need to verify ACE-Step output quality before proceeding

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: 6, 8, 11
  - **Blocked By**: None (can start immediately)

  **References**:
  - `https://github.com/ace-step/ACE-Step-1.5` - ACE-Step repository
  - `https://huggingface.co/ace-step/ACE-Step-1.5` - Model weights

  **Acceptance Criteria**:
  - [ ] ACE-Step 1.5 installed in `packages/core`
  - [ ] Test script `tests/acestep_validation.py` generates 30-second samples
  - [ ] `docs/acestep_validation.md` documents: output format, latency, hardware requirements
  - [ ] At least 3 test samples saved to `tests/fixtures/acestep/`
  - [ ] Samples contain recognizable dub techno elements (verified by listening)

  **QA Scenarios**:

  ```
  Scenario: ACE-Step generates dub techno audio
    Tool: Bash
    Preconditions: ACE-Step installed
    Steps:
      1. Run `cd packages/core && python tests/acestep_validation.py --prompt "dub techno chord stabs" --output test.wav`
      2. Run `ffprobe -show_format -show_streams tests/fixtures/acestep/dub_techno_stabs.wav`
      3. Assert duration ≈ 30 seconds (±5s)
      4. Assert sample_rate = 44100 or 48000
    Expected Result: Valid audio file with dub techno characteristics
    Evidence: .sisyphus/evidence/task-03-acestep-output.wav

  Scenario: Document ACE-Step requirements
    Tool: Bash
    Preconditions: Validation complete
    Steps:
      1. Run `cat docs/acestep_validation.md`
      2. Assert file contains sections: "Output Format", "Latency", "Hardware Requirements"
    Expected Result: Documentation exists with required sections
    Evidence: .sisyphus/evidence/task-03-acestep-docs.txt
  ```

  **Commit**: YES
  - Message: `test: add ACE-Step validation tests and documentation`
  - Files: `packages/core/requirements.txt, tests/acestep_validation.py, tests/fixtures/acestep/*.wav, docs/acestep_validation.md`

---

- [x] 4. Strudel + Tone.js Research (Integration Patterns)

  **What to do**:
  - Research Strudel's API for pattern generation
  - Research Tone.js effects chain configuration
  - Create proof-of-concept: Strudel pattern → Tone.js effects → audio output
  - Document how to run Strudel/Tone.js in Node.js (not browser)
  - Document available effects: delay, reverb, filter, distortion, phaser
  - Test audio output quality (is it release-ready?)
  - Save PoC to `poc/strudel-tonejs/`

  **Must NOT do**:
  - Do NOT build full dub techno effects chain yet
  - Do NOT integrate with ACE-Step yet
  - Do NOT create CLI wrapper yet

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Research task requiring experimentation with audio frameworks
  - **Skills**: [`superpowers/verification-before-completion`]
    - Need to verify Tone.js output quality

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: 6, 8, 12, 13
  - **Blocked By**: None (can start immediately)

  **References**:
  - `https://strudel.cc/` - Strudel documentation
  - `https://tonejs.github.io/` - Tone.js documentation
  - `https://github.com/tidalcycles/strudel` - Strudel repository

  **Acceptance Criteria**:
  - [ ] `poc/strudel-tonejs/` contains working Node.js script
  - [ ] Script generates 30-second audio with Strudel pattern + Tone.js effects
  - [ ] `docs/strudel_tonejs_integration.md` documents: Node.js setup, effect chain config, output quality
  - [ ] Test output `poc/strudel-tonejs/output.wav` exists and plays correctly

  **QA Scenarios**:

  ```
  Scenario: Strudel + Tone.js generates audio in Node.js
    Tool: Bash
    Preconditions: Node.js environment set up
    Steps:
      1. Run `cd poc/strudel-tonejs && npm install && node index.js`
      2. Run `ffprobe poc/strudel-tonejs/output.wav`
      3. Assert duration ≈ 30 seconds
      4. Assert no errors in script output
    Expected Result: Valid audio file generated from Strudel + Tone.js
    Evidence: .sisyphus/evidence/task-04-strudel-tonejs-output.wav

  Scenario: Documentation complete
    Tool: Bash
    Preconditions: Research complete
    Steps:
      1. Run `cat docs/strudel_tonejs_integration.md`
      2. Assert file contains sections: "Setup", "Effect Chain", "Output Quality Assessment"
    Expected Result: Integration documentation exists
    Evidence: .sisyphus/evidence/task-04-integration-docs.txt
  ```

  **Commit**: YES
  - Message: `research: add Strudel + Tone.js integration PoC`
  - Files: `poc/strudel-tonejs/**, docs/strudel_tonejs_integration.md`

---

- [x] 5. Dub Techno Theory Spec (Measurable Parameters)

  **What to do**:
  - Define "Rob Jenkins style" as measurable parameters
  - Document BPM range (120-130? 125 fixed?)
  - Document key signatures (D minor, E minor, etc.)
  - Document chord progressions (parallel minor movements, common sequences)
  - Document structural patterns (intro, development, climax, outro sections)
  - Document effect parameters (delay times, reverb decay, filter cutoff ranges)
  - Document transition types (crossfades, filter sweeps, drops)
  - Save to `docs/dub_techno_theory.md`

  **Must NOT do**:
  - Do NOT implement the theory module yet
  - Do NOT create overly complex theory (keep it practical)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Documentation and specification task
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: 9, 10
  - **Blocked By**: None (can start immediately)

  **References**:
  - `https://www.attackmagazine.com/technique/tutorials/the-theory-of-techno-parallel-chord-stabs/` - Parallel chord theory
  - `https://www.studiobrootle.com/dub-techno-effects-chains/` - Dub techno effects

  **Acceptance Criteria**:
  - [ ] `docs/dub_techno_theory.md` exists
  - [ ] Contains at least 15 measurable parameters
  - [ ] BPM range defined (e.g., "120-130 BPM, default 125")
  - [ ] At least 5 chord progressions documented
  - [ ] Effect parameter ranges defined (delay time, reverb decay, filter cutoff)
  - [ ] Structural template defined (section durations, transitions)

  **QA Scenarios**:

  ```
  Scenario: Theory spec contains required parameters
    Tool: Bash
    Preconditions: docs/dub_techno_theory.md exists
    Steps:
      1. Run `grep -E "^- (BPM|Key|Chord|Effect|Structure)" docs/dub_techno_theory.md | wc -l`
      2. Assert count >= 15
      3. Run `grep -i "bpm" docs/dub_techno_theory.md`
      4. Assert output contains specific BPM range (e.g., "120-130")
    Expected Result: Theory spec has 15+ measurable parameters
    Evidence: .sisyphus/evidence/task-05-theory-spec.txt

  Scenario: Chord progressions documented
    Tool: Bash
    Preconditions: docs/dub_techno_theory.md exists
    Steps:
      1. Run `grep -A 5 "## Chord Progressions" docs/dub_techno_theory.md`
      2. Assert output contains at least 5 progression examples
    Expected Result: Chord progressions section has 5+ examples
    Evidence: .sisyphus/evidence/task-05-chord-progressions.txt
  ```

  **Commit**: YES
  - Message: `docs: add dub techno theory specification`
  - Files: `docs/dub_techno_theory.md`

---

- [ ] 6. Architecture Design (Python ↔ TypeScript Bridge)

  **What to do**:
  - Design the communication mechanism between Python (ACE-Step) and TypeScript (Strudel/Tone.js)
  - Choose bridge approach: file-based (temp WAV stems) vs IPC vs WebSocket
  - Create sequence diagram showing data flow
  - Define file formats for inter-process communication
  - Define error handling and timeout strategies
  - Document which layer is the orchestrator (Python calls TypeScript)
  - Save to `docs/architecture.md`

  **Must NOT do**:
  - Do NOT implement the bridge yet
  - Do NOT over-engineer (keep it simple for v1)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Critical architectural decision affecting entire project
  - **Skills**: [`superpowers/writing-plans`]
    - Need to document architecture properly

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 1, 3, 4 results)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9)
  - **Blocks**: 8, 14, 15, 16
  - **Blocked By**: Task 1 (project structure), Task 3 (ACE-Step format), Task 4 (Strudel/Tone.js)

  **References**:
  - `docs/acestep_validation.md` - ACE-Step output format (from Task 3)
  - `docs/strudel_tonejs_integration.md` - Tone.js input requirements (from Task 4)

  **Acceptance Criteria**:
  - [ ] `docs/architecture.md` exists
  - [ ] Contains sequence diagram (Mermaid or ASCII)
  - [ ] Bridge mechanism documented (recommended: file-based with temp directory)
  - [ ] File format specs: ACE-Step output → TypeScript input
  - [ ] Error handling strategy defined
  - [ ] Orchestrator layer identified (Python main process)

  **QA Scenarios**:

  ```
  Scenario: Architecture document complete
    Tool: Bash
    Preconditions: docs/architecture.md exists
    Steps:
      1. Run `cat docs/architecture.md`
      2. Assert contains section "## Data Flow"
      3. Assert contains section "## Bridge Mechanism"
      4. Assert contains sequence diagram (```mermaid or ASCII art)
    Expected Result: Complete architecture documentation
    Evidence: .sisyphus/evidence/task-06-architecture.txt
  ```

  **Commit**: YES
  - Message: `docs: add system architecture design`
  - Files: `docs/architecture.md`

---

- [ ] 7. Test Infrastructure Setup (Vitest + Pytest)

  **What to do**:
  - Configure Vitest for TypeScript packages (`vitest.config.ts`)
  - Configure Pytest for Python package (`pytest.ini`, `conftest.py`)
  - Add test scripts to `package.json` and `pyproject.toml`
  - Create test directory structure:
    - `packages/core/tests/`
    - `packages/patterns/tests/`
    - `packages/effects/tests/`
    - `packages/cli/tests/`
  - Add placeholder test files for each package
  - Configure coverage reporting

  **Must NOT do**:
  - Do NOT write actual tests yet (just infrastructure)
  - Do NOT add complex test utilities yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard test framework setup
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD workflow knowledge for proper setup

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 8, 9)
  - **Blocks**: 10, 11, 12, 13, 14, 15, 16
  - **Blocked By**: Task 1 (project structure)

  **References**:
  - `https://vitest.dev/config/` - Vitest configuration
  - `https://docs.pytest.org/en/stable/reference/reference.html#configuration-options` - Pytest configuration

  **Acceptance Criteria**:
  - [ ] `vitest.config.ts` exists in root
  - [ ] `pytest.ini` exists in `packages/core/`
  - [ ] `pnpm test` runs successfully (even with placeholder tests)
  - [ ] `pytest` runs successfully (even with placeholder tests)
  - [ ] Coverage reporting configured

  **QA Scenarios**:

  ```
  Scenario: Vitest configured correctly
    Tool: Bash
    Preconditions: vitest.config.ts exists
    Steps:
      1. Run `pnpm test`
      2. Assert exit code 0
      3. Assert output contains "passed" or "skipped" (no failures)
    Expected Result: Vitest runs without errors
    Evidence: .sisyphus/evidence/task-07-vitest.txt

  Scenario: Pytest configured correctly
    Tool: Bash
    Preconditions: pytest.ini exists
    Steps:
      1. Run `cd packages/core && pytest`
      2. Assert exit code 0
      3. Assert output contains "passed" or "collected"
    Expected Result: Pytest runs without errors
    Evidence: .sisyphus/evidence/task-07-pytest.txt
  ```

  **Commit**: YES
  - Message: `test: add test infrastructure (Vitest + Pytest)`
  - Files: `vitest.config.ts, packages/core/pytest.ini, packages/*/tests/*.test.ts, packages/core/tests/test_*.py`

---

- [ ] 8. 5-Minute PoC (Minimal End-to-End Pipeline)

  **What to do**:
  - Build minimal working pipeline: ACE-Step → Strudel → Tone.js → WAV export
  - Python script generates 30s texture with ACE-Step
  - TypeScript script applies Strudel pattern and Tone.js effects
  - Bridge via temp WAV file
  - Export 5-minute mix (loop 30s texture with variations)
  - Save to `poc/5min-mix/`
  - Validate: duration ≈ 5:00, no artifacts, dub techno characteristics

  **Must NOT do**:
  - Do NOT build full CLI yet
  - Do NOT implement all effects (just basic delay + reverb)
  - Do NOT add configuration parsing

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Proof of concept integrating multiple components
  - **Skills**: [`superpowers/test-driven-development`, `superpowers/verification-before-completion`]
    - TDD for code quality, verification for audio output

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Tasks 3, 4, 6, 7)
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 9)
  - **Blocks**: 19, 20
  - **Blocked By**: Task 3 (ACE-Step), Task 4 (Strudel/Tone.js), Task 6 (architecture), Task 7 (tests)

  **References**:
  - `docs/architecture.md` - Bridge mechanism (from Task 6)
  - `docs/acestep_validation.md` - ACE-Step usage (from Task 3)
  - `docs/strudel_tonejs_integration.md` - Tone.js setup (from Task 4)

  **Acceptance Criteria**:
  - [ ] `poc/5min-mix/generate.py` generates 30s ACE-Step texture
  - [ ] `poc/5min-mix/process.ts` applies Strudel + Tone.js
  - [ ] `poc/5min-mix/output.wav` exists
  - [ ] `ffprobe` shows duration 5:00 ± 0:05
  - [ ] No audible artifacts (clicks, pops, distortion)
  - [ ] Contains recognizable dub techno elements

  **QA Scenarios**:

  ```
  Scenario: 5-minute mix generates successfully
    Tool: Bash
    Preconditions: PoC scripts complete
    Steps:
      1. Run `cd poc/5min-mix && python generate.py && npx ts-node process.ts`
      2. Run `ffprobe -show_format poc/5min-mix/output.wav | grep duration`
      3. Assert duration is 300 ± 5 seconds
      4. Run `ffprobe poc/5min-mix/output.wav`
      5. Assert sample_rate = 44100, channels = 2
    Expected Result: Valid 5-minute audio file
    Evidence: .sisyphus/evidence/task-08-poc-output.wav

  Scenario: Audio contains dub techno elements
    Tool: Bash (ffprobe/sox analysis)
    Preconditions: output.wav exists
    Steps:
      1. Run `sox poc/5min-mix/output.wav -n stat` (check for clipping)
      2. Assert no "clipping detected" warning
      3. Run `ffprobe -show_streams poc/5min-mix/output.wav | grep sample_rate`
      4. Assert sample_rate is 44100 or 48000
    Expected Result: No clipping, valid sample rate
    Evidence: .sisyphus/evidence/task-08-audio-quality.txt
  ```

  **Commit**: YES
  - Message: `feat: add 5-minute mix PoC`
  - Files: `poc/5min-mix/**`

---

- [ ] 9. Acceptance Criteria Document

  **What to do**:
  - Convert all functional/quality/integration requirements to executable test commands
  - Document expected outputs for each CLI command
  - Define audio quality tests as spectral analysis commands
  - Create `docs/acceptance_criteria.md`
  - Include validation methods for each criterion

  **Must NOT do**:
  - Do NOT include subjective criteria ("sounds good")
  - Do NOT create criteria that require human listening tests

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Documentation task
  - **Skills**: [`superpowers/writing-plans`]
    - Proper planning documentation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8)
  - **Blocks**: 21, 22
  - **Blocked By**: Task 5 (theory spec), Task 6 (architecture)

  **References**:
  - `docs/dub_techno_theory.md` - Theory parameters (from Task 5)
  - `docs/architecture.md` - System design (from Task 6)

  **Acceptance Criteria**:
  - [ ] `docs/acceptance_criteria.md` exists
  - [ ] Each criterion has: command, expected output, validation method
  - [ ] No subjective criteria (all machine-verifiable)
  - [ ] Covers: CLI commands, audio quality, integration tests

  **QA Scenarios**:

  ```
  Scenario: Acceptance criteria are executable
    Tool: Bash
    Preconditions: docs/acceptance_criteria.md exists
    Steps:
      1. Run `grep -c "Expected:" docs/acceptance_criteria.md`
      2. Assert count >= 10 (at least 10 executable criteria)
      3. Run `grep -c "Validation:" docs/acceptance_criteria.md`
      4. Assert count >= 10
    Expected Result: Document has 10+ executable criteria
    Evidence: .sisyphus/evidence/task-09-acceptance-criteria.txt
  ```

  **Commit**: YES
  - Message: `docs: add acceptance criteria document`
  - Files: `docs/acceptance_criteria.md`

---

- [ ] 10. Dub Techno Theory Module (TypeScript)

  **What to do**:
  - Create `packages/patterns/src/theory/` directory
  - Implement `ChordProgression` class with parallel minor chord generation
  - Implement `Scale` utilities for minor scales (natural, harmonic, dorian)
  - Implement `Voicing` helpers for chord extensions (m7, m9, m11)
  - Create progression templates: i-VII-VI-v, parallel movements
  - Add unit tests for all theory functions
  - Export from `@openmusic/patterns`

  **Must NOT do**:
  - Do NOT add advanced theory (jazz harmony, microtonal, etc.)
  - Do NOT create complex generative algorithms

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core domain logic requiring music theory knowledge
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for theory module

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11, 12, 13, 14, 15, 16)
  - **Blocks**: 12, 19
  - **Blocked By**: Task 5 (theory spec), Task 7 (test infrastructure)

  **References**:
  - `docs/dub_techno_theory.md` - Theory specification (from Task 5)
  - `https://tonaljs.github.io/tonal/docs` - Tonal.js API
  - `https://strudel.cc/learn/tonal/` - Strudel tonal functions

  **Acceptance Criteria**:
  - [ ] `packages/patterns/src/theory/progressions.ts` exists
  - [ ] `packages/patterns/src/theory/scales.ts` exists
  - [ ] `packages/patterns/src/theory/voicings.ts` exists
  - [ ] `pnpm test packages/patterns` passes with >80% coverage
  - [ ] `ChordProgression.parallel('Cm', ['P1', 'M2', 'm3'])` returns ['Cm', 'Dm', 'Ebm']

  **QA Scenarios**:

  ```
  Scenario: Parallel chord progression generates correctly
    Tool: Bash
    Preconditions: theory module implemented
    Steps:
      1. Run `cd packages/patterns && pnpm test -- --grep "parallel progression"`
      2. Assert all tests pass
      3. Run `node -e "const {ChordProgression} = require('./src/theory'); console.log(ChordProgression.parallel('Cm', ['P1', 'M2']))"`
      4. Assert output contains "Cm" and "Dm"
    Expected Result: Parallel progressions work correctly
    Evidence: .sisyphus/evidence/task-10-theory-tests.txt

  Scenario: Scale utilities return correct notes
    Tool: Bash
    Preconditions: scales.ts implemented
    Steps:
      1. Run `pnpm test packages/patterns -- --grep "scale"`
      2. Assert all scale tests pass
    Expected Result: Scale utilities tested and passing
    Evidence: .sisyphus/evidence/task-10-scale-tests.txt
  ```

  **Commit**: YES
  - Message: `feat(patterns): add dub techno theory module`
  - Files: `packages/patterns/src/theory/**, packages/patterns/tests/theory/**`

---

- [ ] 11. ACE-Step Integration (Python)

  **What to do**:
  - Create `packages/core/src/acestep/` directory
  - Implement `ACEStepGenerator` class with model loading
  - Add methods: `generate_texture(prompt, duration)`, `generate_chord_stab(key, quality)`
  - Implement output caching to avoid regenerating same prompts
  - Add configuration for GPU vs CPU mode
  - Add error handling for model loading failures
  - Add unit tests with mocked model (for CI)
  - Export from `@openmusic/core`

  **Must NOT do**:
  - Do NOT fine-tune the model
  - Do NOT add multi-model support
  - Do NOT implement real-time generation (offline only)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex ML integration requiring PyTorch knowledge
  - **Skills**: [`superpowers/test-driven-development`, `superpowers/verification-before-completion`]
    - TDD for reliability, verification for model output

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 12, 13, 14, 15, 16)
  - **Blocks**: 14, 16, 19
  - **Blocked By**: Task 3 (ACE-Step validation), Task 7 (test infrastructure)

  **References**:
  - `docs/acestep_validation.md` - Usage patterns (from Task 3)
  - `https://github.com/ace-step/ACE-Step-1.5` - ACE-Step API

  **Acceptance Criteria**:
  - [ ] `packages/core/src/acestep/generator.py` exists
  - [ ] `pytest packages/core/tests/acestep/` passes
  - [ ] `ACEStepGenerator.generate_texture("dub techno pad", 30)` returns path to WAV file
  - [ ] Caching works: same prompt returns cached file
  - [ ] GPU fallback to CPU works when no GPU available

  **QA Scenarios**:

  ```
  Scenario: ACE-Step generator creates texture
    Tool: Bash
    Preconditions: ACE-Step model available
    Steps:
      1. Run `cd packages/core && python -c "from src.acestep import ACEStepGenerator; g = ACEStepGenerator(); print(g.generate_texture('dub techno pad', 30))"`
      2. Assert output is a file path ending in .wav
      3. Run `ffprobe <output_path>`
      4. Assert duration ≈ 30 seconds
    Expected Result: Generator produces valid audio file
    Evidence: .sisyphus/evidence/task-11-acestep-gen.wav

  Scenario: Caching prevents regeneration
    Tool: Bash
    Preconditions: Generator implemented with caching
    Steps:
      1. Run generation twice with same prompt
      2. Assert second call returns in <1 second (cached)
      3. Assert same file path returned
    Expected Result: Caching works correctly
    Evidence: .sisyphus/evidence/task-11-caching.txt
  ```

  **Commit**: YES
  - Message: `feat(core): add ACE-Step integration`
  - Files: `packages/core/src/acestep/**, packages/core/tests/acestep/**`

---

- [ ] 12. Strudel Pattern Library (TypeScript)

  **What to do**:
  - Create `packages/patterns/src/strudel/` directory
  - Implement `DubTechnoPatterns` class with common pattern templates
  - Add patterns: chord stabs, bass pulses, hi-hat patterns, atmospheric textures
  - Integrate with theory module for chord progressions
  - Implement pattern variations (randomization, humanization)
  - Add unit tests for pattern generation
  - Export from `@openmusic/patterns`

  **Must NOT do**:
  - Do NOT create overly complex patterns
  - Do NOT add patterns for other genres

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Domain-specific pattern programming
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for pattern correctness

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 13, 14, 15, 16)
  - **Blocks**: 15, 19
  - **Blocked By**: Task 4 (Strudel research), Task 7 (tests), Task 10 (theory)

  **References**:
  - `docs/strudel_tonejs_integration.md` - Strudel setup (from Task 4)
  - `https://strudel.cc/learn/` - Strudel tutorials

  **Acceptance Criteria**:
  - [ ] `packages/patterns/src/strudel/patterns.ts` exists
  - [ ] `DubTechnoPatterns.chordStab('Cm9', { duration: '16n' })` returns Strudel pattern
  - [ ] `DubTechnoPatterns.bassPulse('C2', { rate: '1/4' })` returns Strudel pattern
  - [ ] `pnpm test packages/patterns` passes with pattern tests

  **QA Scenarios**:

  ```
  Scenario: Chord stab pattern generates correctly
    Tool: Bash
    Preconditions: pattern library implemented
    Steps:
      1. Run `pnpm test packages/patterns -- --grep "chordStab"`
      2. Assert all tests pass
      3. Run `node -e "const p = require('./src/strudel'); console.log(p.DubTechnoPatterns.chordStab('Cm9'))"`
      4. Assert output contains valid Strudel pattern string
    Expected Result: Chord stab patterns work
    Evidence: .sisyphus/evidence/task-12-pattern-tests.txt
  ```

  **Commit**: YES
  - Message: `feat(patterns): add Strudel pattern library`
  - Files: `packages/patterns/src/strudel/**, packages/patterns/tests/strudel/**`

---

- [ ] 13. Tone.js Effects Chain (TypeScript)

  **What to do**:
  - Create `packages/effects/src/` directory
  - Implement `DubTechnoEffectsChain` class
  - Add effects: Delay (tape echo style), Reverb (long decay), Filter (bandpass with LFO), Distortion (subtle saturation), VinylNoise (crackle/hiss)
  - Implement effect parameter randomization for variation
  - Create preset configurations for different dub techno styles
  - Add unit tests for effect chain
  - Export from `@openmusic/effects`

  **Must NOT do**:
  - Do NOT create modular effect graph system
  - Do NOT add effects outside dub techno scope (chorus, flanger, etc. - keep minimal)
  - Do NOT load external VSTs

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Audio DSP programming with Tone.js
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for effect correctness

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12, 14, 15, 16)
  - **Blocks**: 15, 19
  - **Blocked By**: Task 4 (Tone.js research), Task 7 (tests)

  **References**:
  - `docs/dub_techno_theory.md` - Effect parameters (from Task 5)
  - `https://tonejs.github.io/docs/` - Tone.js API

  **Acceptance Criteria**:
  - [ ] `packages/effects/src/chain.ts` exists
  - [ ] `DubTechnoEffectsChain.apply(input, { delay: 0.5, reverb: 0.8 })` returns processed audio
  - [ ] VinylNoise effect adds subtle crackle without overwhelming audio
  - [ ] `pnpm test packages/effects` passes

  **QA Scenarios**:

  ```
  Scenario: Effects chain processes audio
    Tool: Bash
    Preconditions: effects package implemented
    Steps:
      1. Run `pnpm test packages/effects -- --grep "effects chain"`
      2. Assert all tests pass
      3. Create test: input audio → effects chain → output audio
      4. Assert output duration equals input duration
      5. Assert output RMS level is different from input (processing occurred)
    Expected Result: Effects chain processes audio correctly
    Evidence: .sisyphus/evidence/task-13-effects-tests.txt
  ```

  **Commit**: YES
  - Message: `feat(effects): add dub techno effects chain`
  - Files: `packages/effects/src/**, packages/effects/tests/**`

---

- [ ] 14. Python Orchestrator Core

  **What to do**:
  - Create `packages/core/src/orchestrator/` directory
  - Implement `MixOrchestrator` class as main entry point
  - Add methods: `generate_mix(config)` → coordinates ACE-Step, calls TypeScript
  - Implement config parsing (YAML/JSON)
  - Implement progress reporting (console output)
  - Implement error handling and recovery
  - Add unit tests for orchestrator
  - Export from `@openmusic/core`

  **Must NOT do**:
  - Do NOT add CLI parsing (separate task)
  - Do NOT implement parallel generation yet (sequential for v1)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core orchestration logic
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for reliability

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12, 13, 15, 16)
  - **Blocks**: 16, 17, 19
  - **Blocked By**: Task 6 (architecture), Task 7 (tests), Task 11 (ACE-Step)

  **References**:
  - `docs/architecture.md` - Orchestration flow (from Task 6)

  **Acceptance Criteria**:
  - [ ] `packages/core/src/orchestrator/mix.py` exists
  - [ ] `MixOrchestrator(config)` initializes correctly
  - [ ] `orchestrator.generate_mix()` returns path to final mix
  - [ ] `pytest packages/core/tests/orchestrator/` passes

  **QA Scenarios**:

  ```
  Scenario: Orchestrator coordinates generation
    Tool: Bash
    Preconditions: orchestrator implemented
    Steps:
      1. Run `cd packages/core && python -c "from src.orchestrator import MixOrchestrator; o = MixOrchestrator({'length': 300}); print(o.generate_mix())"`
      2. Assert output is a file path ending in .wav
    Expected Result: Orchestrator produces valid mix
    Evidence: .sisyphus/evidence/task-14-orchestrator.txt
  ```

  **Commit**: YES
  - Message: `feat(core): add mix orchestrator`
  - Files: `packages/core/src/orchestrator/**, packages/core/tests/orchestrator/**`

---

- [ ] 15. TypeScript Audio Engine

  **What to do**:
  - Create `packages/effects/src/engine/` directory
  - Implement `AudioEngine` class that:
    - Loads audio files (from ACE-Step output)
    - Applies Strudel patterns (from pattern library)
    - Processes through Tone.js effects chain
    - Exports to WAV/FLAC/MP3
  - Implement offline rendering (Node.js compatible, no browser required)
  - Add unit tests for audio engine
  - Export from `@openmusic/effects`

  **Must NOT do**:
  - Do NOT require browser environment
  - Do NOT add real-time streaming

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core audio processing pipeline
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for audio correctness

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12, 13, 14, 16)
  - **Blocks**: 16, 19, 20
  - **Blocked By**: Task 6 (architecture), Task 7 (tests), Task 12 (patterns), Task 13 (effects)

  **References**:
  - `docs/architecture.md` - Audio engine role (from Task 6)
  - `poc/5min-mix/` - Reference implementation (from Task 8)

  **Acceptance Criteria**:
  - [ ] `packages/effects/src/engine/audio_engine.ts` exists
  - [ ] `AudioEngine.render(input_files, patterns, effects)` returns audio buffer
  - [ ] `AudioEngine.export(buffer, 'output.wav', format='wav')` writes file
  - [ ] `pnpm test packages/effects` passes with engine tests

  **QA Scenarios**:

  ```
  Scenario: Audio engine renders mix
    Tool: Bash
    Preconditions: audio engine implemented
    Steps:
      1. Run `pnpm test packages/effects -- --grep "AudioEngine render"`
      2. Assert all tests pass
      3. Run `node -e "const e = require('./src/engine'); console.log(typeof e.AudioEngine.render)"`
      4. Assert output is "function"
    Expected Result: Audio engine works correctly
    Evidence: .sisyphus/evidence/task-15-engine-tests.txt
  ```

  **Commit**: YES
  - Message: `feat(effects): add audio engine`
  - Files: `packages/effects/src/engine/**, packages/effects/tests/engine/**`

---

- [ ] 16. Bridge Layer (File-Based Communication)

  **What to do**:
  - Create `packages/core/src/bridge/` directory
  - Implement `TypeScriptBridge` class:
    - `call_audio_engine(input_files, output_path, config)` → spawns Node process
    - Passes config as JSON file
    - Returns output audio path
  - Implement temp file management (create, cleanup)
  - Implement timeout handling (max 10 minutes per call)
  - Add error handling for subprocess failures
  - Add unit tests with mocked subprocess
  - Export from `@openmusic/core`

  **Must NOT do**:
  - Do NOT use IPC/WebSocket (keep file-based for simplicity)
  - Do NOT add real-time communication

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Critical integration layer
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for reliability

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12, 13, 14, 15)
  - **Blocks**: 19, 20
  - **Blocked By**: Task 6 (architecture), Task 11 (ACE-Step), Task 14 (orchestrator), Task 15 (audio engine)

  **References**:
  - `docs/architecture.md` - Bridge design (from Task 6)

  **Acceptance Criteria**:
  - [ ] `packages/core/src/bridge/typescript_bridge.py` exists
  - [ ] `TypeScriptBridge.call_audio_engine(...)` spawns Node.js and returns output
  - [ ] Temp files cleaned up after successful generation
  - [ ] Timeout kills hung processes
  - [ ] `pytest packages/core/tests/bridge/` passes

  **QA Scenarios**:

  ```
  Scenario: Bridge calls TypeScript audio engine
    Tool: Bash
    Preconditions: bridge implemented
    Steps:
      1. Run `cd packages/core && python -c "from src.bridge import TypeScriptBridge; b = TypeScriptBridge(); print(b.call_audio_engine([], 'test.wav', {}))"`
      2. Assert output is a file path
      3. Assert file exists at output path
    Expected Result: Bridge communicates with TypeScript correctly
    Evidence: .sisyphus/evidence/task-16-bridge.txt

  Scenario: Temp files cleaned up
    Tool: Bash
    Preconditions: bridge with cleanup
    Steps:
      1. Run bridge call that succeeds
      2. Check temp directory for leftover files
      3. Assert temp directory is empty or contains only expected files
    Expected Result: No temp file leaks
    Evidence: .sisyphus/evidence/task-16-cleanup.txt
  ```

  **Commit**: YES
  - Message: `feat(core): add TypeScript bridge layer`
  - Files: `packages/core/src/bridge/**, packages/core/tests/bridge/**`

---

- [ ] 17. CLI Interface (Command Structure)

  **What to do**:
  - Create `packages/cli/` directory
  - Implement `openmusic` command with subcommands:
    - `openmusic generate --length 2h --bpm 125 --key d_minor --output mix.flac`
    - `openmusic validate <config.yaml>` - validate config file
    - `openmusic version` - show version
  - Use `click` for Python CLI (or `typer`)
  - Add help text and examples for each command
  - Add progress indicators during generation
  - Add unit tests for CLI commands
  - Install as entry point in `pyproject.toml`

  **Must NOT do**:
  - Do NOT add interactive prompts (keep pure CLI)
  - Do NOT add web interface commands

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard CLI implementation
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 18, 19, 20, 21, 22)
  - **Blocks**: 21, 22
  - **Blocked By**: Task 1 (project structure), Task 14 (orchestrator)

  **References**:
  - `https://click.palletsprojects.com/` - Click CLI library
  - `https://typer.tiangolo.com/` - Typer CLI library

  **Acceptance Criteria**:
  - [ ] `openmusic --help` shows usage information
  - [ ] `openmusic generate --help` shows generate options
  - [ ] `openmusic version` outputs version number
  - [ ] CLI entry point configured in `pyproject.toml`
  - [ ] `pytest packages/cli/tests/` passes

  **QA Scenarios**:

  ```
  Scenario: CLI help works
    Tool: Bash
    Preconditions: CLI installed
    Steps:
      1. Run `openmusic --help`
      2. Assert exit code 0
      3. Assert output contains "generate" and "validate"
    Expected Result: CLI shows help
    Evidence: .sisyphus/evidence/task-17-cli-help.txt

  Scenario: Generate command validates arguments
    Tool: Bash
    Preconditions: generate command implemented
    Steps:
      1. Run `openmusic generate --length invalid --output test.wav`
      2. Assert exit code non-zero
      3. Assert error message about invalid length
    Expected Result: CLI validates arguments
    Evidence: .sisyphus/evidence/task-17-cli-validation.txt
  ```

  **Commit**: YES
  - Message: `feat(cli): add CLI interface`
  - Files: `packages/cli/**`

---

- [ ] 18. Config File Parser (YAML/JSON)

  **What to do**:
  - Create `packages/core/src/config/` directory
  - Implement `ConfigParser` class:
    - Supports YAML and JSON formats
    - Validates required fields: length, bpm, key, output
    - Provides sensible defaults for optional fields
    - Validates value ranges (BPM 60-200, length 1m-4h)
  - Create example config files in `examples/` directory
  - Add unit tests for config parsing
  - Export from `@openmusic/core`

  **Must NOT do**:
  - Do NOT add advanced config features (inheritance, includes)
  - Do NOT add TOML support (YAML + JSON only)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard configuration parsing
  - **Skills**: []
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 19, 20, 21, 22)
  - **Blocks**: 17, 21
  - **Blocked By**: Task 1 (project structure), Task 14 (orchestrator)

  **References**:
  - `https://pyyaml.org/wiki/PyYAMLDocumentation` - PyYAML

  **Acceptance Criteria**:
  - [ ] `packages/core/src/config/parser.py` exists
  - [ ] `ConfigParser.parse('config.yaml')` returns validated config dict
  - [ ] `examples/basic_config.yaml` exists with all required fields
  - [ ] `pytest packages/core/tests/config/` passes

  **QA Scenarios**:

  ```
  Scenario: Config parser handles YAML
    Tool: Bash
    Preconditions: parser implemented
    Steps:
      1. Create test YAML file with required fields
      2. Run `python -c "from src.config import ConfigParser; print(ConfigParser.parse('test.yaml'))"`
      3. Assert output contains parsed values
    Expected Result: YAML config parses correctly
    Evidence: .sisyphus/evidence/task-18-yaml-parse.txt

  Scenario: Config parser rejects invalid values
    Tool: Bash
    Preconditions: parser with validation
    Steps:
      1. Create test YAML with BPM=500 (invalid)
      2. Run parser
      3. Assert raises ValidationError
    Expected Result: Invalid values rejected
    Evidence: .sisyphus/evidence/task-18-validation.txt
  ```

  **Commit**: YES
  - Message: `feat(core): add config file parser`
  - Files: `packages/core/src/config/**, packages/core/tests/config/**, examples/*.yaml`

---

- [ ] 19. Mix Arrangement Engine

  **What to do**:
  - Create `packages/core/src/arrangement/` directory
  - Implement `ArrangementEngine` class:
    - Generates mix structure (intro, development, climax, outro sections)
    - Determines section durations based on total length
    - Assigns chord progressions to sections
    - Creates transitions between sections (crossfades, filter sweeps)
    - Outputs arrangement as timeline structure
  - Implement section templates for dub techno
  - Add unit tests for arrangement logic
  - Export from `@openmusic/core`

  **Must NOT do**:
  - Do NOT generate audio yet (just arrangement structure)
  - Do NOT add complex AI-based arrangement

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core domain logic for mix structure
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for arrangement correctness

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on many Wave 3 tasks)
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 20, 21, 22)
  - **Blocks**: 20, 21, 22
  - **Blocked By**: Task 8 (PoC), Task 10 (theory), Task 11 (ACE-Step), Task 12 (patterns), Task 13 (effects), Task 14 (orchestrator), Task 15 (audio engine), Task 16 (bridge)

  **References**:
  - `docs/dub_techno_theory.md` - Structural patterns (from Task 5)
  - `poc/5min-mix/` - Reference arrangement (from Task 8)

  **Acceptance Criteria**:
  - [ ] `packages/core/src/arrangement/engine.py` exists
  - [ ] `ArrangementEngine.generate(120)` returns arrangement for 2-hour mix
  - [ ] Arrangement contains: intro, at least 4 development sections, climax, outro
  - [ ] Each section has: duration, chord progression, intensity level
  - [ ] `pytest packages/core/tests/arrangement/` passes

  **QA Scenarios**:

  ```
  Scenario: Arrangement engine creates valid structure
    Tool: Bash
    Preconditions: arrangement engine implemented
    Steps:
      1. Run `python -c "from src.arrangement import ArrangementEngine; e = ArrangementEngine(); a = e.generate(120); print(len(a.sections))"`
      2. Assert section count >= 6 (intro + 4 development + outro)
      3. Assert total duration ≈ 7200 seconds (2 hours)
    Expected Result: Valid arrangement structure
    Evidence: .sisyphus/evidence/task-19-arrangement.txt

  Scenario: Sections have required attributes
    Tool: Bash
    Preconditions: arrangement structure defined
    Steps:
      1. Generate arrangement
      2. For each section, assert it has: duration, chords, intensity
      3. Assert intensity values are in range [0, 1]
    Expected Result: All sections have required attributes
    Evidence: .sisyphus/evidence/task-19-sections.txt
  ```

  **Commit**: YES
  - Message: `feat(core): add mix arrangement engine`
  - Files: `packages/core/src/arrangement/**, packages/core/tests/arrangement/**`

---

- [ ] 20. Export Pipeline (WAV/FLAC/MP3)

  **What to do**:
  - Create `packages/effects/src/export/` directory
  - Implement `AudioExporter` class:
    - Export to WAV (16-bit, 24-bit)
    - Export to FLAC (lossless compression)
    - Export to MP3 (320kbps)
    - Add metadata: title, artist, date, genre
  - Implement sample rate conversion (if needed)
  - Implement normalization (peak level to -1dB)
  - Add unit tests for export formats
  - Export from `@openmusic/effects`

  **Must NOT do**:
  - Do NOT add stem export (separate tracks)
  - Do NOT add other formats (OGG, AAC, etc.)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Audio encoding with multiple format support
  - **Skills**: [`superpowers/test-driven-development`]
    - TDD for format correctness

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 19, 21, 22)
  - **Blocks**: 21, 22
  - **Blocked By**: Task 15 (audio engine), Task 19 (arrangement)

  **References**:
  - `https://ffmpeg.org/ffmpeg.html` - FFmpeg for encoding
  - `https://github.com/ffflorian/wav` - WAV encoding in Node.js

  **Acceptance Criteria**:
  - [ ] `packages/effects/src/export/audio_exporter.ts` exists
  - [ ] `AudioExporter.export(buffer, 'output.wav', { format: 'wav', bitDepth: 16 })` writes file
  - [ ] `AudioExporter.export(buffer, 'output.flac', { format: 'flac' })` writes FLAC
  - [ ] `AudioExporter.export(buffer, 'output.mp3', { format: 'mp3', bitrate: 320 })` writes MP3
  - [ ] `ffprobe` confirms format and metadata for each export type
  - [ ] `pnpm test packages/effects` passes with export tests

  **QA Scenarios**:

  ```
  Scenario: Export to WAV works
    Tool: Bash
    Preconditions: exporter implemented
    Steps:
      1. Generate test audio buffer
      2. Export to WAV
      3. Run `ffprobe output.wav`
      4. Assert sample_rate = 44100, channels = 2, bits_per_sample = 16
    Expected Result: Valid WAV file created
    Evidence: .sisyphus/evidence/task-20-wav-export.wav

  Scenario: Export to FLAC works
    Tool: Bash
    Preconditions: exporter implemented
    Steps:
      1. Generate test audio buffer
      2. Export to FLAC
      3. Run `ffprobe output.flac`
      4. Assert format_name contains "flac"
    Expected Result: Valid FLAC file created
    Evidence: .sisyphus/evidence/task-20-flac-export.flac

  Scenario: Export to MP3 works
    Tool: Bash
    Preconditions: exporter implemented
    Steps:
      1. Generate test audio buffer
      2. Export to MP3
      3. Run `ffprobe output.mp3`
      4. Assert format_name contains "mp3", bit_rate ≈ 320000
    Expected Result: Valid MP3 file created
    Evidence: .sisyphus/evidence/task-20-mp3-export.mp3
  ```

  **Commit**: YES
  - Message: `feat(effects): add export pipeline`
  - Files: `packages/effects/src/export/**, packages/effects/tests/export/**`

---

- [ ] 21. End-to-End Integration Tests

  **What to do**:
  - Create `tests/integration/` directory
  - Implement end-to-end tests:
    - `test_5min_mix.py` - Generate 5-minute mix, verify output
    - `test_30min_mix.py` - Generate 30-minute mix, verify output
    - `test_cli_full_pipeline.py` - Test CLI from command to output file
  - Tests should verify:
    - Output file exists
    - Duration matches expected (±5%)
    - No audio artifacts (clipping, silence)
    - All sections present in arrangement
  - Add to CI/CD pipeline

  **Must NOT do**:
  - Do NOT run 2-hour tests in CI (too slow, use shorter tests)
  - Do NOT add performance benchmarks (separate concern)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex integration testing
  - **Skills**: [`superpowers/test-driven-development`, `superpowers/verification-before-completion`]
    - TDD and verification for integration tests

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all previous tasks)
  - **Parallel Group**: Wave 4 (with Tasks 17, 18, 19, 20, 22)
  - **Blocks**: 22
  - **Blocked By**: Task 9 (acceptance criteria), Task 17 (CLI), Task 18 (config), Task 19 (arrangement), Task 20 (export)

  **References**:
  - `docs/acceptance_criteria.md` - Acceptance criteria (from Task 9)

  **Acceptance Criteria**:
  - [ ] `tests/integration/test_5min_mix.py` exists
  - [ ] `tests/integration/test_30min_mix.py` exists
  - [ ] `tests/integration/test_cli_full_pipeline.py` exists
  - [ ] `pytest tests/integration/` passes
  - [ ] Integration tests added to `.github/workflows/ci.yml`

  **QA Scenarios**:

  ```
  Scenario: 5-minute mix integration test passes
    Tool: Bash
    Preconditions: integration tests implemented
    Steps:
      1. Run `pytest tests/integration/test_5min_mix.py -v`
      2. Assert exit code 0
      3. Assert output contains "PASSED"
    Expected Result: Integration test passes
    Evidence: .sisyphus/evidence/task-21-5min-test.txt

  Scenario: CLI pipeline test passes
    Tool: Bash
    Preconditions: CLI integration test implemented
    Steps:
      1. Run `pytest tests/integration/test_cli_full_pipeline.py -v`
      2. Assert exit code 0
      3. Assert output file exists and has correct duration
    Expected Result: Full CLI pipeline works
    Evidence: .sisyphus/evidence/task-21-cli-test.txt
  ```

  **Commit**: YES
  - Message: `test: add end-to-end integration tests`
  - Files: `tests/integration/**, .github/workflows/ci.yml`

---

- [ ] 22. 2-Hour Mix Generation Test

  **What to do**:
  - Create `tests/full_mix/` directory
  - Implement `test_2hour_mix.py`:
    - Generates full 2-hour mix
    - Verifies duration ≈ 2:00:00 (±1 minute)
    - Verifies file size reasonable (FLAC ~500MB-1GB)
    - Verifies no artifacts using spectral analysis
    - Checks for dub techno characteristics (low-mid frequency emphasis)
  - Save output to `tests/full_mix/output/` (gitignored)
  - Document generation time in `docs/performance.md`

  **Must NOT do**:
  - Do NOT run in CI (too slow, manual test only)
  - Do NOT commit output files to git

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Final validation of full system
  - **Skills**: [`superpowers/verification-before-completion`]
    - Verification for final output quality

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all previous tasks)
  - **Parallel Group**: Wave 4 (after Tasks 17, 18, 19, 20, 21)
  - **Blocks**: F3 (Final QA)
  - **Blocked By**: Task 19 (arrangement), Task 20 (export), Task 21 (integration tests)

  **References**:
  - `docs/acceptance_criteria.md` - Final acceptance criteria (from Task 9)

  **Acceptance Criteria**:
  - [ ] `tests/full_mix/test_2hour_mix.py` exists
  - [ ] Test generates 2-hour mix successfully
  - [ ] Duration verified: 2:00:00 ± 0:01:00
  - [ ] File size verified: 500MB-1.5GB for FLAC
  - [ ] Spectral analysis shows dub techno characteristics
  - [ ] `docs/performance.md` documents generation time

  **QA Scenarios**:

  ```
  Scenario: 2-hour mix generates successfully
    Tool: Bash
    Preconditions: all components implemented
    Steps:
      1. Run `pytest tests/full_mix/test_2hour_mix.py -v`
      2. Assert exit code 0
      3. Run `ffprobe tests/full_mix/output/mix.flac | grep duration`
      4. Assert duration ≈ 7200 seconds (±60)
    Expected Result: Full 2-hour mix generated
    Evidence: .sisyphus/evidence/task-22-2hour-mix.txt

  Scenario: Mix has dub techno characteristics
    Tool: Bash (sox/spectral analysis)
    Preconditions: mix generated
    Steps:
      1. Run `sox tests/full_mix/output/mix.flac -n stat 2>&1 | grep -E "(RMS|Peak)"`
      2. Assert RMS level in expected range for dub techno
      3. Run spectral analysis (freq balance check)
      4. Assert low-mid frequencies (100-500Hz) are emphasized
    Expected Result: Mix sounds like dub techno
    Evidence: .sisyphus/evidence/task-22-spectral-analysis.txt
  ```

  **Commit**: YES
  - Message: `test: add 2-hour mix generation test`
  - Files: `tests/full_mix/**, docs/performance.md`

---

## Final Verification Wave (MANDATORY)

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify all "Must Have" implemented, all "Must NOT Have" absent, evidence files exist.

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run linters, type checks, tests. Review for AI slop patterns.

- [ ] F3. **Full QA - Generate 2-Hour Mix** — `unspecified-high`
  Run full pipeline: `openmusic generate --length 2h --output final_mix.flac`
  Validate: duration ≈ 2h, no artifacts, dub techno characteristics present.

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify no scope creep: no DAW integration, no live features, no extra AI models.

---

## Commit Strategy

- **Initial**: `feat: initial commit - project scaffolding` — package.json, pyproject.toml, .gitignore
- **After Wave 1**: `feat: add GitHub templates and CI/CD` — .github/, README.md, LICENSE
- **After Wave 2**: `feat: add architecture docs and PoC` — docs/, poc/
- **After Wave 3**: `feat: implement core modules` — packages/core, packages/patterns, packages/effects
- **After Wave 4**: `feat: add CLI and export pipeline` — packages/cli, src/export/
- **Final**: `release: v0.1.0 - first working version` — all components integrated

---

## Success Criteria

### Verification Commands
```bash
# Project structure
ls -la packages/  # Expected: core, patterns, effects, cli directories

# Tests pass
pytest && npm test  # Expected: all tests pass, coverage > 80%

# Generate mix
openmusic generate --length 2h --bpm 125 --key d_minor --output mix.flac
# Expected: Exit code 0, mix.flac exists, duration ≈ 2:00:00

# Audio validation
ffprobe mix.flac  # Expected: 44.1kHz, 16-bit, stereo, ~2h duration

# Publish to GitHub
git remote -v  # Expected: origin git@github.com:tobias-weiss-ai-xr/openmusic.git
git push origin main  # Expected: successful push
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] 2-hour mix generates successfully
- [ ] README with usage examples
- [ ] Published to GitHub
