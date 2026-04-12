# Contributing to OpenMusic

- Prerequisites: Node.js (20.x), Python (3.12), uv, and a modern shell.
- Package management: pnpm for TypeScript, uv for Python.
- Testing: pytest for Python, vitest for JavaScript/TypeScript.

Getting started

- Install uv: https://docs.astral.sh/uv/getting-started/installation/
- Install dependencies: pnpm install && uv sync
- Run TypeScript tests: pnpm test
- Run Python tests: uv run pytest
- For development: ensure Python and Node tools are in PATH and accessible.

Workflow

- Create a feature branch per task
- Keep tests green locally before opening a PR
- Provide clear, concise PR descriptions focusing on the problem and the fix
- Run the project's verification steps before merging

Code of conduct

- Be respectful and collaborative. Follow project guidelines.
