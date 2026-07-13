# AI Newsroom OS — Codex Instructions

## Authority

- `F0_TECHNICAL_SPEC.md` is the sole normative F0 specification.
- `docs/f0-minimal-scope.md` is a derived checklist.
- `PROJECT_VISION.md` is non-normative product context.
- Historical foundation and audit files are non-normative.
- If documents conflict, `F0_TECHNICAL_SPEC.md` wins.

## Scope

Implement Foundation F0 only when explicitly requested.

Do not create:

- live network ingestion;
- clustering or multi-source merge;
- real LLM providers;
- UI or API;
- Docker;
- TTS, video or publishing;
- future placeholders or speculative abstractions.

## Environment

- Windows 11
- Python 3.12.x
- `uv`
- Ryzen 3 5300U
- 16 GB RAM
- no GPU requirement
- no Docker
- no network in runtime, tests or F0 demo

## Dependencies

Direct runtime dependencies:

- Typer
- Pydantic v2

Direct development dependencies:

- pytest
- Ruff
- mypy

Ask before adding another direct dependency.

## Working method

1. Read `F0_TECHNICAL_SPEC.md` completely.
2. Inspect the repository before editing.
3. Present a short file-level plan.
4. Implement the smallest compliant vertical slice.
5. Add tests with each behavior.
6. Run Ruff, mypy and pytest.
7. Run the full Definition of Done twice.
8. Report exact results and deviations.

## Safety

- Never use network in tests.
- Never run destructive Git commands.
- Never recreate or repair an existing database automatically.
- Never overwrite differing exports without explicit `--force`.
- Never expose secrets or raw fixture bodies in logs.
- Never commit or push unless explicitly requested.

## Stop conditions

Stop and report instead of guessing when:

- the specification conflicts with itself;
- completion requires a non-goal;
- a new direct dependency appears necessary;
- a destructive action would be required;
- deterministic behavior cannot be achieved.
