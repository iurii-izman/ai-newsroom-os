# Foundation F0 Implementation Plan

## Status

- Phase: Foundation F0
- Branch: `feat/f0-foundation`
- Normative source: `F0_TECHNICAL_SPEC.md`
- Plan status: `SCOPE_APPROVED`
- Implementation started: `NO`

## Scope review

- Review date: 2026-07-14
- Guardian verdict: `PASS`
- Review rounds: 1
- Corrections applied: none; the initial draft passed without scope changes

## Objective

Implement the exact offline vertical slice defined by the normative specification:

```text
local RSS 2.0 fixture
→ normalized immutable SourceSnapshot
→ SQLite schema v1
→ one Story per SourceSnapshot
→ deterministic Mock StoryPackageSnapshot
→ story-package.json + story-package.md
```

The slice proves repeatability, determinism, lineage, safe failure behavior, and fit on the target machine. It does not validate product, editorial, audience, format, monetization, or production readiness.

## Preconditions

- Repository: `C:\Dev\ai-newsroom-os`, with `origin` pointing to `iurii-izman/ai-newsroom-os`.
- Implementation branch: `feat/f0-foundation`, created from clean `main` at `ea89a5ab9d6dbda665cb7cfbd0ad82595d7aba89`, a descendant of approved baseline `728f73dbbf2cdd2b9326e4a5cc855ea597db86af`.
- Authority: `F0_TECHNICAL_SPEC.md` is sole normative F0 source; derived and historical documents cannot override it.
- Target: Windows 11, Python 3.12.x, Ryzen 3 5300U, 16 GB RAM, no GPU, no Docker, one synchronous process.
- Runtime, tests, and demo remain offline. Dependency installation is outside that runtime boundary.
- Delivery is timeboxed to 2–4 focused working days. After core Definition of Done passes, hardening stops unless an observed failure or owner-approved finding justifies it.
- `AGENTS.md`, `.codex/config.toml`, normative documents, and historical Foundation documents remain untouched.

## Non-goals

- HTTP, live RSS, manual URL ingestion, or any runtime network client.
- Fuzzy deduplication, clustering, multi-source merge, review queues, or F1 identity/migration semantics.
- A Claim table, ledger, state machine, approval workflow, or future editorial/production entities.
- Real LLM providers, provider interfaces, prompt packs, retry/cost subsystems, or file-fixture provider abstractions.
- UI, API, workers, Docker, n8n, TTS, video, publishing, cloud, or platform adapters.
- YAML configuration, ORM, migration framework, generic repository, compatibility layer, or speculative ports/adapters/services.
- Product, editorial, audience, format, monetization, lead-generation, or production-readiness claims.

## Direct dependencies

### Runtime

- Typer
- Pydantic v2

### Development

- pytest
- Ruff
- mypy

Transitive dependencies resolved from these direct dependencies are allowed. `uv` manages the environment and lock. No other direct dependency, including a build/runtime helper, is planned; if the exact `ai-newsroom` entry point cannot be packaged without another direct dependency, implementation stops for an owner-approved specification decision.

## Proposed file tree

The implementation creates or modifies exactly the following 21 files. No empty package or architecture directory is planned.

| File | Responsibility | Normative requirements served and why needed now |
|---|---|---|
| `pyproject.toml` | Python 3.12 project metadata, exact direct dependencies, `ai-newsroom` entry point, and Ruff/mypy/pytest settings | DEP-01/02, CLI §11, DoD §17; required to install and run the specified CLI and checks |
| `uv.lock` | Frozen transitive dependency graph | Reproducible `uv sync --frozen`; required by the DoD |
| `src/ai_newsroom/cli.py` | Typer composition root, five commands, safe error mapping, and operational timestamps | ARCH-01, CLI §11; the only framework-facing orchestration module |
| `src/ai_newsroom/models.py` | Immutable domain values and Pydantic schema-v1 package/claim validation | Domain §9, payload §12, integrity §13; provides concrete validation consumers |
| `src/ai_newsroom/normalization.py` | Text/date/URL normalization, canonical JSON, hashes, and exact IDs | §§7–9; isolates deterministic pure behavior and normative vectors |
| `src/ai_newsroom/rss.py` | Bounded local-byte read, pre-parse safety checks, RSS subset parsing, and whole-fixture validation | RSS §6, security §16; concrete local fixture ingestion only |
| `src/ai_newsroom/database.py` | Exact schema-v1 DDL and concrete stdlib `sqlite3` reads/writes with validation | ARCH-02, persistence §10, integrity §13; no repository abstraction or migration layer |
| `src/ai_newsroom/package_builder.py` | Recompute lineage/identities and build or validate the deterministic mock package | §§9, 12, 13; concrete `package build` behavior |
| `src/ai_newsroom/exporters.py` | Canonical JSON/Markdown rendering, collision checks, temporary files, and per-file replacement | §§12, 14; concrete `package export` behavior |
| `tests/conftest.py` | Autouse socket guard and shared temporary-path helpers | ENV-02 and offline test evidence from the first test run |
| `tests/fixtures/feeds/sample.xml` | One valid Cyrillic RSS item used by the official demo | DoD §17; the single committed runtime fixture |
| `tests/golden/story-package.json` | Exact expected JSON export bytes for the official fixture | Output §12 and byte-level determinism |
| `tests/golden/story-package.md` | Exact expected Markdown export bytes for the official fixture | Output §12 and nonpublishability markers |
| `tests/test_normalization.py` | Text/date/URL vectors and independent identity vector | §§7–9, ID-01/02 |
| `tests/test_rss.py` | Encoding, RSS subset, limits, DTD/ENTITY, mixed validity, and no-write preconditions | §6, RSS-01/02, security §16 |
| `tests/test_database.py` | Schema, init, transactions, revisions, constraints, lock/corruption, and targeted SQL tamper cases | §§10, 13; exact persistence behavior |
| `tests/test_package.py` | Mock package, lineage, Pydantic validation, repeat build, and integrity recomputation | §§9, 12, 13 |
| `tests/test_export.py` | JSON/Markdown goldens, no-op/conflict/force, atomic replacement, and partial-pair recovery | §§12, 14 |
| `tests/test_cli_e2e.py` | Exact CLI surface, usage behavior, Unicode/space paths, full demo, and repeated isolated runs | CLI §11, DoD §17, Windows evidence |
| `tests/test_project_contracts.py` | Direct dependency audit, import boundaries, exact command/table surface, and forbidden-artifact scan | DEP-01/02, ARCH-01/02, explicit non-goals |
| `docs/f0-implementation-report.md` | Exact check results, elapsed focused days, resource evidence status, manual lineage review, and any justified post-DoD hardening trigger | PROC-01/02, ENV-03, DoD §17; required acceptance evidence rather than product documentation |

Boundary and invalid fixtures other than `sample.xml` are generated as bounded bytes inside tests, avoiding a fixture-file matrix and keeping the tree proportional.

## Module responsibilities

- `normalization.py` and `rss.py` are pure domain/input modules and import neither Typer nor SQLite.
- `models.py` defines only F0 values and the persisted/exported schema-v1 package; it contains no future entities.
- `database.py` is the single concrete `sqlite3` boundary. It exposes task-specific functions rather than a repository interface.
- `package_builder.py` performs the exact build-time integrity checks and mock derivation without provider seams.
- `exporters.py` renders from validated persisted payload and owns only the specified filesystem recovery behavior.
- `cli.py` wires paths, operational timestamps, database functions, builder, exporters, and stable errors. It remains the sole Typer import site and composition root.

## Implementation sequence

The five steps fit the 2–4 day timebox. Each step lands observable behavior and tests; no step creates unused modules.

1. **Normalize and validate the local RSS boundary.**
   - Change: `pyproject.toml`, `uv.lock`, `models.py`, `normalization.py`, `rss.py`, `tests/conftest.py`, `tests/fixtures/feeds/sample.xml`, `tests/test_normalization.py`, `tests/test_rss.py`, and the initial dependency/import checks in `tests/test_project_contracts.py`.
   - Behavior: strict UTF-8/BOM RSS validation produces normalized immutable values and exact reference-vector IDs without network access.
   - Verification: `uv run pytest tests/test_normalization.py tests/test_rss.py tests/test_project_contracts.py` and `uv run ruff check .`.
2. **Persist sources and stories and expose init/harvest/list.**
   - Change: `database.py`, `cli.py`, `models.py`, `tests/test_database.py`, and initial cases in `tests/test_cli_e2e.py`.
   - Behavior: schema initialization is safe/idempotent; a wholly validated fixture atomically creates immutable Source/Story rows; listing is stable.
   - Verification: `uv run pytest tests/test_database.py tests/test_cli_e2e.py -k "init or harvest or list"`.
3. **Build the deterministic mock package.**
   - Change: `models.py`, `database.py`, `package_builder.py`, `cli.py`, and `tests/test_package.py`.
   - Behavior: `package build` recomputes source/story/package/claim lineage, persists one canonical mock payload, and detects targeted tampering.
   - Verification: `uv run pytest tests/test_package.py tests/test_database.py`.
4. **Export canonical JSON and Markdown safely.**
   - Change: `exporters.py`, `cli.py`, `tests/golden/story-package.json`, `tests/golden/story-package.md`, and `tests/test_export.py`.
   - Behavior: `package export` writes exact bytes, refuses differing files without `--force`, preserves identical files, and supports specified partial-pair recovery.
   - Verification: `uv run pytest tests/test_export.py tests/test_package.py`.
5. **Close the end-to-end and governance gate.**
   - Change: complete `tests/test_cli_e2e.py` and `tests/test_project_contracts.py`; create `docs/f0-implementation-report.md` after evidence exists.
   - Behavior: exact CLI usage, full offline demo, two isolated/repeated runs, equal rows/IDs/file hashes, import/dependency/non-goal scans, and honest resource reporting all pass.
   - Verification: final Ruff, mypy, pytest, the complete Definition of Done twice, explicit skills/reviews, and the report checks listed below.

## Requirement-to-test mapping

| Requirement area | Planned behavior | Planned test type | Planned test file |
|---|---|---|---|
| Text normalization | Exact newline, Unicode whitespace, NFC, length, and forbidden-control rules | Normative-vector unit tests | `tests/test_normalization.py` |
| Date normalization | Absent, aware UTC, naive, malformed, raw-date preservation | Normative-vector unit tests | `tests/test_normalization.py` |
| URL canonicalization | Exact validation/order/IDNA/IPv6/port/query/tracking behavior | Normative-vector unit tests | `tests/test_normalization.py` |
| Identity reference vector | Exact item JSON, content hash, source/story/claim/package values | Independent fixed-vector unit test | `tests/test_normalization.py` |
| RSS validation and limits | UTF-8/BOM, exact structure, duplicate fields, DTD/ENTITY, 5 MiB/500 item boundaries, whole-fixture failure | Unit and boundary integration tests | `tests/test_rss.py` |
| SQLite initialization and transactions | Four-table schema, metadata/version validation, FK/timeout, idempotence, rollback, lock, corruption | Integration tests | `tests/test_database.py` |
| Immutable source revisions | Repeat unchanged item, same URL changed content, different URLs same content | Integration tests | `tests/test_database.py` |
| Story creation | Exactly `id`/`primary_source_id`, one Story per SourceSnapshot, computed title | Integration tests | `tests/test_database.py` |
| Deterministic mock package | Exact generator, one MockClaim, lineage, repeat no-op, no operational fields in payload | Unit/integration tests | `tests/test_package.py` |
| Integrity validation | Recompute IDs/hashes/fingerprint/payload/claim before build/export; reject direct-SQL tampering | Targeted integration tests | `tests/test_database.py`, `tests/test_package.py`, `tests/test_export.py` |
| Canonical JSON export | Exact fields/order/Unicode/indent/LF/final LF and golden SHA-256 | Byte-golden integration test | `tests/test_export.py` |
| Markdown export | Exact lineage, escaping, raw date, MOCK/nonpublishability/warning lines, LF | Byte-golden integration test | `tests/test_export.py` |
| Collision and force behavior | Identical no-op, differing refusal, reviewed forced replacement | Filesystem integration tests | `tests/test_export.py` |
| Partial-pair detection | Injected failure and obvious mixed pair yield `E_EXPORT_PARTIAL`; per-file atomicity | Deterministic failure-injection test | `tests/test_export.py` |
| CLI behavior | Exactly five commands, stable project errors, standard concise Typer usage, help/list sorting | CLI runner/subprocess tests | `tests/test_cli_e2e.py`, `tests/test_project_contracts.py` |
| Offline network guard | Any socket attempt fails; full demo passes with guard active | Autouse guard plus E2E test | `tests/conftest.py`, `tests/test_cli_e2e.py` |
| Repeated end-to-end determinism | Two isolated data directories and repeated harvest/build/export keep IDs, counts, JSON/Markdown SHA-256 | E2E integration test | `tests/test_cli_e2e.py` |
| Windows Unicode and spaces | CLI accepts Cyrillic content and a data/fixture path containing spaces and Unicode | Windows-path E2E test | `tests/test_cli_e2e.py` |
| Dependency/architecture scope | Only allowed direct declarations; no Typer/SQLite domain imports, Docker, network client, extra tables/commands | Static contract tests | `tests/test_project_contracts.py` |

## CLI implementation plan

The CLI contains all and only these five command paths:

| Command | Responsibility |
|---|---|
| `ai-newsroom --data-dir PATH db init` | Create or validate exact schema v1 without repair, migration, deletion, or recreation |
| `ai-newsroom --data-dir PATH harvest run --fixture FILE` | Read and wholly validate one local RSS fixture, then atomically persist Source/Story rows |
| `ai-newsroom --data-dir PATH stories list [--ids-only]` | List Stories sorted by ID; compute title from the primary Source; avoid package-graph recomputation |
| `ai-newsroom --data-dir PATH package build STORY_ID` | Validate source/story integrity and persist or validate the deterministic mock package |
| `ai-newsroom --data-dir PATH package export STORY_ID --format json\|markdown\|all [--force]` | Validate the persisted package and render requested canonical files with collision/partial recovery |

`--data-dir` defaults to `data`. Mutating commands report created/unchanged counts or the resulting ID. Project errors are concise, sanitized, traceback-free non-zero results; Typer/Click owns syntax usage output.

## Persistence plan

Use one concrete stdlib `sqlite3` module and exactly four tables:

1. `schema_meta` — one row with version `1`.
2. `sources` — immutable normalized SourceSnapshots with exact ID/hash/length constraints and `UNIQUE(canonical_url, content_hash)`.
3. `stories` — exactly `id` and unique FK `primary_source_id`.
4. `story_packages` — one package per Story with exact mock generator/fingerprint/payload/operational timestamp fields.

Every connection enables foreign keys and a 5-second busy timeout. `db init` uses an explicit transaction and validates existing DDL shape plus the singleton metadata row; it never migrates or repairs. Harvest normalizes and validates every item before opening an explicit write transaction, then commits Source and Story inserts together or rolls back both. Package build validates immutable inputs before its explicit write transaction and treats an identical existing package as unchanged. Export is read-only to SQLite and completes render/validation/preflight before any per-file `os.replace`. There is no ORM, JSON1 dependency, generic repository, migration, compatibility, or filesystem-transaction abstraction.

## Determinism plan

- Current time is used only for aware UTC operational `discovered_at`/`built_at` values. It is excluded from IDs, payload, and exports; tests pass explicit operational timestamps to concrete functions rather than add a clock abstraction.
- Canonical compact JSON uses UTF-8, `ensure_ascii=False`, sorted object keys, compact separators, and no final LF for identity/persisted payload bytes.
- IDs and hashes use only the exact normative preimages and full SHA-256/first-24 rules.
- Database reads used for outputs have explicit ID ordering; no SQLite row order is trusted.
- Paths are `pathlib` inputs only and never enter identities or exported content.
- No randomness is used.
- Date handling uses explicit timezone awareness and UTC; local timezone and locale are never guessed.
- Export renderers emit explicit LF bytes and one final LF where specified, independent of Windows platform newlines.

## Error-handling plan

| Error code | Boundary and behavior |
|---|---|
| `E_FIXTURE_INVALID` | Local path/size/encoding/XML/item/text/date/URL validation fails before database writes |
| `E_DB_SCHEMA` | Existing schema/metadata or recomputed source/story/package/payload/claim integrity is incompatible; no repair/export |
| `E_DB_LOCKED` | SQLite remains busy after the configured 5-second timeout; close other writer and retry |
| `E_DB_CORRUPT` | SQLite reports corruption; preserve original and diagnose or restore a copy |
| `E_STORY_NOT_FOUND` | Requested Story is absent at build |
| `E_PACKAGE_NOT_BUILT` | Requested persisted package is absent at export |
| `E_EXPORT_CONFLICT` | An existing requested file differs and `--force` is absent |
| `E_EXPORT_PARTIAL` | An obvious expected/missing-or-differing JSON/Markdown pair is detected for `--format all` |
| `E_UNEXPECTED` | Unmapped failure produces sanitized diagnostics without fixture bodies, summaries, secrets, or traceback |

Typer/Click syntax errors remain framework-standard. Error mapping is narrow: it does not hide programming failures behind domain codes during tests.

## Security and resource plan

- Read a local regular file as bounded bytes; enforce 5 MiB and 500 direct-item limits before unbounded work.
- Reject case-insensitive `DOCTYPE`/`ENTITY` declarations before `ElementTree` parsing and before writes.
- Strictly reject forbidden controls and non-UTF-8/unsupported encoding without logging raw body or summary.
- Validate URLs as data only; never fetch, shell, evaluate, import, or send fixture text to an LLM.
- Derive export paths only from validated hash IDs; escape untrusted Markdown labels.
- Install an autouse socket guard for all tests and run the complete demo offline.
- Preserve incompatible/corrupt DBs; never auto-repair, migrate, delete, or recreate them.
- Bound payload/text and use a synchronous single process suitable for 16 GB RAM; report peak memory only if actually measured, otherwise `not measured`. The optional 512 MB observation is not an automated gate.

## Commit strategy

Use five logical implementation commits; each includes its behavior tests and excludes `.demo-f0`, databases, exports, caches, and other generated runtime data.

1. `feat: normalize and validate local RSS fixtures`
2. `feat: persist immutable sources and stories`
3. `feat: build deterministic mock story packages`
4. `feat: export canonical story packages safely`
5. `test: prove offline F0 determinism and document verification`

## Verification strategy

- During each vertical step, run its focused pytest files plus Ruff; run mypy once the source boundary exists.
- Keep the socket guard active for every test and for the documented demo.
- Audit direct declarations, import boundaries, exact four-table schema, exact five-command CLI, and forbidden artifacts.
- Reproduce the independent §9.5 vector exactly.
- Run the final Ruff, mypy, and pytest checks from the frozen environment.
- Run the complete Definition of Done twice, including repeated harvest/build/export, and compare IDs, row counts, and JSON/Markdown SHA-256 values across repeated and isolated data directories.
- Manually inspect exported lineage and exact MOCK/nonpublishability markers.
- Run `$f0-scope-guardian` explicitly on the final implementation diff.
- Run `$f0-quality-gate` explicitly after implementation; it must not fix files.
- Perform an independent diff review and a Codex Security diff scan before handoff. Any fixes require their own explicit task and rerun of affected gates.
- Record exact commands/results, elapsed focused days, deviations, resource evidence status, and any justified post-DoD hardening trigger in `docs/f0-implementation-report.md` without claiming product hypotheses were validated.

## Definition of Done commands

Run these exact commands from the repository root on the target environment:

```powershell
uv sync --frozen
uv run ruff check .
uv run mypy src
uv run pytest
uv run ai-newsroom --data-dir .demo-f0 db init
uv run ai-newsroom --data-dir .demo-f0 harvest run --fixture tests/fixtures/feeds/sample.xml
$storyId = uv run ai-newsroom --data-dir .demo-f0 stories list --ids-only | Select-Object -First 1
uv run ai-newsroom --data-dir .demo-f0 package build $storyId
uv run ai-newsroom --data-dir .demo-f0 package export $storyId --format all
```

Repeat harvest, build, and export and confirm the same IDs, row counts, JSON SHA-256, and Markdown SHA-256. Repeat the end-to-end flow in an isolated data directory with network blocked. Confirm no Docker/GPU requirement and record the 16 GB target plus honest memory evidence status.

## Risks and stop conditions

- Stop if `F0_TECHNICAL_SPEC.md` conflicts with itself or required acceptance cannot be mapped to F0 without guessing.
- Stop before adding any direct dependency or packaging helper outside the whitelist; request an approved specification decision.
- Stop if a required behavior needs network access, a future entity/command/abstraction, ORM/migration, Docker, or other explicit non-goal.
- Stop rather than repair, recreate, delete, or migrate an incompatible/corrupt database.
- Stop and diagnose if the reference vector or repeated IDs/counts/export hashes are nondeterministic.
- Stop and report if export safety appears to require a manifest, group transaction, workflow engine, or real process-kill framework.
- Stop post-DoD hardening after the 2–4 day target unless an observed failure or owner-approved finding is recorded.
- Preserve Track A independence; technical F0 must not block the manual content pilot.

## Planned deviations

NONE
