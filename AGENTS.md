# AI Newsroom OS — Codex Instructions

## Working directory

Always work from `C:\Dev\ai-newsroom-os`.
Verify repository root, branch, status, remote, and base SHA before changes.

## Authority

- The active specification for the requested phase is the primary authority.
- `F0_TECHNICAL_SPEC.md` remains authoritative for existing F0 behavior.
- `F1_F2_VERTICAL_MVP_SPEC.md` is authoritative for the F1/F2 slice when present.
- `F3_SCRIPT_VIDEO_MVP_SPEC.md` is authoritative for the F3 script/video slice when present.
- `PROJECT_VISION.md` is non-normative product context.
- Historical Foundation, audit, vNext, and old prompt files are non-normative.
- Do not reread historical documents unless the task explicitly needs them.

## Delivery mode

Default to one bounded vertical delivery:

preflight → short inline plan → implementation → targeted tests →
one final quality gate → one focused review/security check →
at most one remediation cycle → Git delivery when requested.

Do not create separate planning or audit documents unless a public contract,
database schema, direct dependency, major subsystem, irreversible decision,
or real requirement conflict requires one.

## Architecture

Prefer a minimal modular monolith and concrete code.

Do not add without a current consumer:
ports/adapters, generic repositories, provider frameworks, plugin systems,
state machines, workers, queues, event buses, Docker, ORM, migration frameworks,
UI/API placeholders, future modules, or empty directories.

## Dependencies

Use the existing stack.
A new direct dependency requires a brief owner-approved reason.
Normal transitive dependencies do not require separate approval.

## Local secrets

- Local `.env` and `.env.local` files are allowed and must remain ignored.
- Track only `.env.example` with empty placeholders.
- Prefer `uv run --env-file .env -- <command>`.
- Application code reads environment variables; do not add dotenv loaders without need.
- Never print, persist, commit, or expose secrets.

## Quality

During implementation, run targeted tests for changed behavior.

Before delivery, run once:
- `uv sync --frozen`;
- Ruff;
- mypy;
- pytest;
- one relevant end-to-end smoke.

Run a security diff scan only for security-sensitive changes.
Do not run repeated full DoD cycles unless a normative phase spec requires them.

## Tests and network

- Automated tests are offline and deterministic.
- Use fakes for live feeds and providers.
- Runtime network is allowed only for explicitly approved commands, including explicit Edge TTS
  execution by `video render` in F3.
- One real live smoke may be used for an integration slice.

## Git

- Do not perform feature work directly on `main`.
- No force-push, destructive Git commands, or amend of reviewed commits.
- Prefer 3–5 logical commits for a large vertical slice.
- Verify exact reviewed HEAD before merge.
- Commit/push/PR/merge only when included in the task.

## Findings

Block only on Blocker, High, material Medium, failed checks,
data-loss/corruption, secret exposure, security-boundary violation,
public-contract violation, unapproved dependency, or scope expansion.

Do not block on style, naming, speculative refactoring,
future-phase suggestions, or harmless Low findings.

Maximum one remediation cycle.

## Stop conditions

Stop and report when:
- active requirements materially conflict;
- a destructive or irreversible action lacks approval;
- a new direct dependency lacks approval;
- data could be lost or corrupted;
- a secret may be exposed;
- a Blocker/High remains after one remediation cycle.

## Reporting

Return only:
- verdict;
- what changed;
- checks;
- commits/push/PR/merge;
- genuine deviations;
- blockers;
- one next step.
