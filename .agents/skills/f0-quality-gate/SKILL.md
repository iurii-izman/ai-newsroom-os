---
name: f0-quality-gate
description: Run and report the complete Foundation F0 quality gate from F0_TECHNICAL_SPEC.md. Use only when explicitly requested after F0 implementation; do not implement fixes or change files during the gate.
---

# F0 Quality Gate

Run the complete Foundation F0 verification without changing project files or repairing failures.

## Gate procedure

1. Read `F0_TECHNICAL_SPEC.md`, especially the complete normative Definition of Done, and read `AGENTS.md`.
2. Check that F0 implementation prerequisites exist, including `pyproject.toml`, `uv.lock`, `src/`, tests, the documented fixture, and the `ai-newsroom` entry point.
3. If implementation or required prerequisites are absent, return `NOT_READY`. Do not create them.
4. When prerequisites and commands are available, run and record:
   - `uv sync --frozen`;
   - `uv run ruff check .`;
   - `uv run mypy src`;
   - `uv run pytest`;
   - the complete CLI demo documented in the Definition of Done;
   - repeated harvest, package build, and export operations;
   - comparisons of IDs, database row counts, and JSON/Markdown SHA-256 values across repeated runs.
5. Keep runtime, tests, and the F0 demo offline. Make no project network calls. If a command cannot run without network, mark it not executed and record the deviation.
6. Make no code, test, fixture, configuration, export, or dependency edits.
7. Perform no dependency updates, automatic repairs, database repairs, or forced export recovery.
8. Classify each check explicitly as passed, failed, not executed, or not applicable.
9. Return `FAIL` if an executed required check fails or a required ready-state check cannot be completed. Return `PASS` only when the complete normative gate passes.

Return exactly these sections:

```markdown
## Status
PASS | FAIL | NOT_READY

## Environment

## Commands executed

## Results

## Repeated-run determinism

## Deviations

## Next safe action
```
