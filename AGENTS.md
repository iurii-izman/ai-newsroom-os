# AI Newsroom OS — Codex Instructions

## Authority

- `F0_TECHNICAL_SPEC.md` is the sole normative F0 specification.
- `F1_F2_VERTICAL_MVP_SPEC.md` is authoritative only for the F1/F2 vertical slice.
- `docs/f0-minimal-scope.md` is a derived checklist.
- `PROJECT_VISION.md` is non-normative product context.
- Historical foundation and audit files are non-normative.
- If documents conflict, `F0_TECHNICAL_SPEC.md` wins.

## Scope

Implement only the explicitly requested phase. Preserve every existing F0 behavior when working on
the F1/F2 vertical slice.

Outside an explicitly approved phase specification, do not create:

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
- no network in tests or the F0 runtime/demo

## Dependencies

Direct runtime dependencies:

- Typer
- Pydantic v2
- `openai>=2,<3` for the concrete DeepSeek-compatible integration

Direct development dependencies:

- pytest
- Ruff
- mypy

Direct build-system dependency:

- `uv_build>=0.9.30,<0.10.0` (build-time only)

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
- Runtime network is permitted only in `harvest live` and
  `package build --generator deepseek`; the F0 demo remains offline.
- `DEEPSEEK_API_KEY` is the only approved provider credential.
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
