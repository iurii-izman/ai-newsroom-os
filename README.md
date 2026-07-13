# AI Newsroom OS

AI Newsroom OS is a proof-first automation system for a Russian-speaking AI newsroom. It is intended to preserve traceable relationships between sources, claims, editorial conclusions, and practical applications while avoiding unverified, low-value AI summaries.

**Status:** Foundation F0 ready for implementation.

Implementation has not started. This repository currently contains the owner-reviewed foundation, project governance, and Codex tooling instructions only.

## Document authority

1. [`F0_TECHNICAL_SPEC.md`](F0_TECHNICAL_SPEC.md) is the sole normative F0 specification.
2. [`docs/f0-minimal-scope.md`](docs/f0-minimal-scope.md) is a derived, non-normative checklist.
3. [`PROJECT_VISION.md`](PROJECT_VISION.md) is non-normative product context.
4. [`docs/open-decisions.md`](docs/open-decisions.md) records future owner decisions.
5. [`docs/f0-risk-register.md`](docs/f0-risk-register.md) records operational risks.
6. Foundation, vNext, audit, and related prompt files are historical context.

If documents conflict, `F0_TECHNICAL_SPEC.md` wins for F0.

## Current phase boundaries

The next phase is Foundation F0: an offline, deterministic local RSS-fixture-to-SQLite-to-mock-package vertical slice. F0 does not include live ingestion, clustering or multi-source merge, a real LLM provider, UI or API, Docker, TTS, video, publishing, or future placeholder abstractions. The independent manual content-validation track may proceed without F0 software.

## Target environment

- Windows 11
- Python 3.12.x
- Ryzen 3 5300U
- 16 GB RAM
- No GPU requirement
- No Docker

## Repository governance

Root Codex instructions define authority, scope, dependency limits, the working method, safety rules, and stop conditions. Project Codex settings keep runtime work offline and workspace-scoped. Repo-local skills provide explicit-only F0 scope review and quality-gate workflows. Git hygiene excludes secrets, runtime data, generated exports, caches, and build artifacts.

## Next step

Implement F0 from [`F0_TECHNICAL_SPEC.md`](F0_TECHNICAL_SPEC.md) in a feature branch.
