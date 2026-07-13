# Foundation F0 Implementation Report

Date: 2026-07-14
Branch: `feat/f0-foundation`
Normative source: `F0_TECHNICAL_SPEC.md`
Result: `PASS`

## Scope and process

Foundation F0 was completed in one focused working day inside the 2–4 day target. Track A remains independent and can proceed without F0 software. F0 validates only technical repeatability, determinism, lineage, safe failure behavior, offline operation and resource fit; it does not validate product, editorial, audience, format, monetization, lead-generation or production-readiness hypotheses.

No post-Definition-of-Done hardening was performed. Corrections before the final DoD were triggered by observed build, Ruff, mypy, integrity and test failures.

## Implemented steps

1. Strictly decode, bound, parse, normalize and validate a local RSS 2.0 fixture; reproduce all text/date/URL and identity vectors.
2. Initialize and validate SQLite schema v1; atomically persist immutable SourceSnapshots and one Story per SourceSnapshot; expose init, harvest and list commands.
3. Recompute lineage and build one deterministic mock StoryPackageSnapshot with one exact MockClaim.
4. Revalidate persisted payload and export canonical JSON and escaped Markdown with collision, force, atomic replacement and partial-pair recovery behavior.
5. Prove the exact CLI/schema/dependency/import surface, offline behavior, tamper rejection and repeated/isolated end-to-end determinism.

## Files

The packaging decision modified only:

- `F0_TECHNICAL_SPEC.md`
- `AGENTS.md`
- `docs/f0-implementation-plan.md`
- `docs/f0-minimal-scope.md`

Implementation created 22 files:

```text
pyproject.toml
uv.lock
src/ai_newsroom/__init__.py
src/ai_newsroom/cli.py
src/ai_newsroom/database.py
src/ai_newsroom/exporters.py
src/ai_newsroom/models.py
src/ai_newsroom/normalization.py
src/ai_newsroom/package_builder.py
src/ai_newsroom/rss.py
tests/conftest.py
tests/fixtures/feeds/sample.xml
tests/golden/story-package.json
tests/golden/story-package.md
tests/test_cli_e2e.py
tests/test_database.py
tests/test_export.py
tests/test_normalization.py
tests/test_package.py
tests/test_project_contracts.py
tests/test_rss.py
docs/f0-implementation-report.md
```

`src/ai_newsroom/__init__.py` is the one-file addition to the approved 21-file plan because `uv_build` refuses to install the package without that module marker. It contains no future behavior or abstraction.

## Dependencies and packaging

- Direct runtime: `pydantic>=2.12,<3`, `typer>=0.20,<1`
- Direct development: `mypy>=1.19,<2`, `pytest>=9,<10`, `ruff>=0.14,<1`
- Direct build system: `uv_build>=0.9.30,<0.10.0`
- Build backend: `uv_build`
- Console entry point: `ai-newsroom = ai_newsroom.cli:main`

The installed `uv 0.9.30` generator produced the exact bounded `uv_build>=0.9.30,<0.10.0` range. `uv_build` is build-time only. No other direct dependency was added.

## CLI and database

The CLI contains exactly:

```text
ai-newsroom --data-dir PATH db init
ai-newsroom --data-dir PATH harvest run --fixture FILE
ai-newsroom --data-dir PATH stories list [--ids-only]
ai-newsroom --data-dir PATH package build STORY_ID
ai-newsroom --data-dir PATH package export STORY_ID --format json|markdown|all [--force]
```

SQLite contains exactly `schema_meta`, `sources`, `stories` and `story_packages`. Every application connection enables foreign keys and a 5-second busy timeout. Writes use explicit transactions. Initialization does not migrate, repair, delete or recreate an incompatible or corrupt database.

## Verification

Both complete Definition-of-Done runs passed from the frozen environment:

- `uv sync --frozen`: `PASS` (`23` packages audited)
- `uv run ruff check .`: `PASS`
- `uv run mypy src`: `PASS` (`8` source files)
- `uv run pytest`: `PASS` (`82 passed`, no skips)
- CLI init/harvest/list/build/export: `PASS`
- repeated harvest/build/export: `PASS`
- isolated second data directory: `PASS`

Reference vector actual values matched the normative expected values exactly:

```text
content_hash=e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d
source_id=src_58343a9a5ffae3037a3f73bf
story_id=story_55c2bc7f60628d20cb9acd4c
claim_id=claim_11806810946d69ba4de2ccd4
input_fingerprint=bd9e982b780c713eaad078c3129e6ddebec56fcc6b5cba0bf951547ae31fda8f
package_id=pkg_17e9b7502f7bc00db437b993
```

Repeated and isolated results:

```text
row_counts sources,stories,story_packages = 1,1,1
JSON_SHA256 = ba6459b16162859ed8499985aaeb08d43c112391024e9262ebced40b171b87ce
Markdown_SHA256 = b77cc21cf74b262e810781ff7798ddbca2234a9598ae0d5bc77ec72588eb3a6b
```

The socket guard, DTD/ENTITY rejection, strict UTF-8 and bounds, Windows Unicode/space paths, rollback, lock, corruption, direct-SQL tampering, collision/no-op/force, pre-replace preservation and injected partial-pair recovery all passed.

Manual payload/export review confirmed exact Source → Story → package → sole claim lineage and the exact `MOCK`, `publishable=false` and do-not-publish warning. JSON is UTF-8 without BOM with LF and one final LF; Markdown is UTF-8 without BOM and LF-only.

## Resource evidence

- OS: Windows 11 Pro `10.0.26200`
- CPU: AMD Ryzen 3 5300U
- Installed RAM: `16,456,474,624` bytes (`15.33 GiB`, marketed 16 GB)
- Python: `3.12.10`
- GPU requirement: none
- Docker requirement: none
- Measured peak working set for a single-process direct F0 init/harvest/list/build/export flow: `31,350,784` bytes (`29.90 MiB`)
- Optional 512 MiB manual sanity target: `PASS`

The first attempted process-wrapper measurement returned no peak value and was discarded; the reported value comes from Windows `GetProcessMemoryInfo` in the process that executed the complete direct F0 flow.

## Gates

- Packaging scope review: `PASS`, round 1
- Final scope guardian criteria over `main...HEAD`: `PASS`, round 1; no corrections or unresolved findings
- Final quality-gate criteria: `PASS`, round 1; no corrections or unresolved failures

The named `$f0-scope-guardian` and `$f0-quality-gate` skills were not available in this Codex session. Their documented criteria were executed manually using the complete Git diff, contract tests, frozen static/test commands, repeated DoD, independent reference/golden/determinism tests and manual lineage review.

## Commits before this report

```text
85c10b7 docs: approve uv_build for F0 packaging
a7e0a42 feat: normalize and validate local RSS fixtures
b097441 feat: persist immutable sources and stories
59cd446 feat: build deterministic mock story packages
8f6d70d feat: export canonical story packages safely
d89a4f5 test: prove offline F0 determinism and integrity
```

## Deviations

Normative specification: none.

Approved plan and procedure:

- The exact probe command rejected `.tmp-uv-build-probe` as an invalid package name under `uv 0.9.30`; the local generator was rerun with `--name uv-build-probe` and produced the approved exact range.
- The approved 21-file plan omitted the `__init__.py` required by `uv_build`; the minimal module marker makes the installed console entry point work and raises the implementation file count to 22.
- Named F0 scope/quality skills were unavailable; equivalent read-only manual gates passed as documented above.
- The task input `CODEX_F0_APPROVE_UV_BUILD_AND_RESUME_FINAL.md` and separately created `docs/TRACK_A/` remain untracked and were intentionally excluded from every commit.

Dependency policy: no deviation.
Implementation commit strategy: five logical implementation commits, plus the required packaging-decision and implementation-report documentation commits.

## Constraints confirmed

- `main` remains at `ea89a5ab9d6dbda665cb7cfbd0ad82595d7aba89`.
- Historical Foundation/audit documents and `PROJECT_VISION.md` are unchanged.
- No F1 functionality, live/network ingestion, real LLM, provider seam, clustering, merge, UI, API, Docker, workers, ORM, migrations, YAML, TTS, video, publishing or future placeholder was added.
- No runtime database, export, cache, log, secret or unexpected binary is tracked.
- No pull request, merge, tag or release was created.

## Remaining work before merge

Start a new read-only Codex thread for an independent diff review of `main...feat/f0-foundation`, then run Codex Security in a separate thread.
