# Codex Prompt — Foundation F0 Implementation

## Purpose

Implement Foundation F0 for **AI Newsroom OS** from the already approved specification and implementation plan.

This task must:

1. verify that Codex is running from the repository root;
2. verify the approved feature branch and clean baseline;
3. read the normative specification and approved plan completely;
4. implement the five approved F0 steps without expanding scope;
5. add only the approved direct dependencies;
6. run tests and static checks after each logical step;
7. create a small, reviewable Git history;
8. run the complete F0 scope and quality gates;
9. push the completed feature branch;
10. stop before pull request, security review, merge or release.

This prompt is executed from:

```text
C:\Dev\ai-newsroom-os
```

All commands, paths and repository operations must be relative to this repository root unless a tool inherently reports an absolute path.

---

# 1. Expected repository state

Expected repository:

```text
root: C:\Dev\ai-newsroom-os
remote: origin
remote repository: iurii-izman/ai-newsroom-os
visibility: private
branch: feat/f0-foundation
```

Approved plan commit:

```text
4d8fb4b29e6500af75aac76d0b8c4e8e371e43d1
docs: define approved F0 implementation plan
```

Approved baseline on `main`:

```text
ea89a5ab9d6dbda665cb7cfbd0ad82595d7aba89
```

The current `HEAD` may be a documented descendant of the approved plan commit if it contains only prompt or governance documentation added after plan approval.

---

# 2. Authority

Read completely before editing:

1. `AGENTS.md`;
2. `F0_TECHNICAL_SPEC.md`;
3. `docs/f0-implementation-plan.md`;
4. `docs/f0-minimal-scope.md`;
5. `PROJECT_VISION.md`;
6. `docs/open-decisions.md`;
7. `docs/f0-risk-register.md`.

Authority order:

1. `F0_TECHNICAL_SPEC.md` — sole normative F0 source;
2. `docs/f0-implementation-plan.md` — scope-approved implementation plan;
3. `docs/f0-minimal-scope.md` — derived checklist;
4. `PROJECT_VISION.md` — non-normative product context;
5. historical Foundation and audit files — historical context only.

Rules:

- if the approved plan conflicts with `F0_TECHNICAL_SPEC.md`, the specification wins;
- do not reinterpret historical documents as active requirements;
- do not change the normative specification to make implementation easier;
- do not silently change the approved plan;
- when the plan is incomplete but the normative specification is clear, follow the specification with the smallest compliant implementation;
- when a required decision is genuinely absent, stop instead of inventing architecture.

---

# 3. Required execution profile

Use:

```text
Model: 5.6 Sol
Reasoning effort: High
Sandbox: workspace-write
Approval policy: on-request
Default network access: disabled
```

Network may be requested only for:

1. resolving the explicitly approved project dependencies if they are not already available;
2. the final `git push`.

Network must remain unavailable to:

- application runtime;
- tests;
- CLI demo;
- fixture processing;
- quality-gate execution.

Do not enable unrestricted network globally.

---

# 4. Hard constraints

During this task, MUST NOT:

- work outside `C:\Dev\ai-newsroom-os`;
- switch to or modify `main`;
- rewrite or amend existing commits;
- force-push;
- merge;
- create a pull request;
- create a tag or release;
- modify GitHub repository settings;
- modify `F0_TECHNICAL_SPEC.md`;
- modify historical Foundation or audit documents;
- expand F0 into F1 or later phases;
- add live RSS or HTTP ingestion;
- add browser automation;
- add a real LLM provider;
- add clustering or multi-source merge;
- add UI or API;
- add Docker;
- add TTS, video rendering or publishing;
- add background workers or schedulers;
- add state machines;
- add provider, port, adapter or repository abstractions without an immediate F0 consumer;
- add placeholder modules for future phases;
- add ORM or migration framework;
- add YAML configuration;
- add telemetry, analytics or external observability;
- create or commit runtime databases, exports, caches or logs;
- expose secrets;
- run destructive Git commands;
- repair or recreate an existing database automatically;
- overwrite a differing export without explicit `--force`;
- use current time, randomness, absolute paths or database row order in deterministic identities or canonical exports.

---

# 5. Dependency policy

Approved direct runtime dependencies:

```text
Typer
Pydantic v2
```

Approved direct development dependencies:

```text
pytest
Ruff
mypy
```

Transitive dependencies are allowed.

Core file, XML, URL, hashing, JSON, datetime and SQLite I/O must use the Python standard library unless the normative specification explicitly says otherwise.

## Packaging and build stop condition

Do not silently add a direct packaging or build dependency such as:

- hatchling;
- setuptools;
- wheel;
- build;
- Poetry;
- Flit;
- PDM backend.

Before creating `pyproject.toml`, inspect the exact packaging approach approved in `docs/f0-implementation-plan.md`.

Proceed only when the approved plan supports a working CLI installation without adding an unapproved direct dependency.

If an additional direct build dependency is technically required but not explicitly approved:

1. stop before adding it;
2. leave the working tree clean or limited to already verified changes;
3. return `PACKAGING_DECISION_REQUIRED`;
4. explain the minimal viable options;
5. do not continue implementation by improvisation.

Do not classify an explicitly configured build-system requirement as “transitive” merely to bypass this rule.

---

# 6. Preflight

Run:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git log -5 --oneline
git merge-base --is-ancestor 4d8fb4b29e6500af75aac76d0b8c4e8e371e43d1 HEAD
python --version
uv --version
```

Verify:

- repository root is exactly `C:\Dev\ai-newsroom-os`;
- current branch is `feat/f0-foundation`;
- working tree is clean;
- `origin` points to `iurii-izman/ai-newsroom-os`;
- approved plan commit is an ancestor of `HEAD`;
- Python is 3.12.x;
- `uv` is available.

If the branch is wrong:

- do not change `main`;
- if the working tree is clean, switch to `feat/f0-foundation`;
- if switching is unsafe, return `BLOCKED`.

If the working tree is not clean:

- inspect changes;
- do not discard user changes;
- continue only if changes are clearly part of this task and explicitly expected;
- otherwise return `BLOCKED`.

If Python 3.12.x or `uv` is missing:

- do not install tools automatically;
- return `ENVIRONMENT_BLOCKED` with the exact missing prerequisite.

---

# 7. Confirm the approved contract

Before writing code, report a compact internal checklist covering:

- exact F0 offline vertical slice;
- five allowed CLI commands;
- direct dependencies;
- four F0 tables;
- deterministic identity rules;
- normalization order;
- URL canonicalization rules;
- package and export contracts;
- error-code boundaries;
- atomic export behavior;
- full Definition of Done;
- F0 non-goals.

Then compare this checklist with:

```text
docs/f0-implementation-plan.md
```

If there is a material conflict:

- do not edit either document;
- return `SPEC_PLAN_CONFLICT`;
- cite the exact sections.

Do not spend tokens re-auditing the entire product vision.

---

# 8. Implementation discipline

Follow the five approved implementation steps in `docs/f0-implementation-plan.md`.

For each step:

1. state the step being implemented;
2. identify the exact files to create or modify;
3. implement the smallest compliant behavior;
4. add or update tests in the same step;
5. run the targeted tests;
6. run Ruff and mypy on affected code when practical;
7. inspect the diff;
8. commit only when the step is coherent and passing.

Do not create all files first as empty placeholders.

Do not create modules that have no immediate behavior or test.

Prefer:

- pure functions for normalization and identity;
- explicit transaction boundaries;
- straightforward standard-library code;
- small Pydantic models;
- direct SQLite access;
- deterministic serialization;
- clear CLI orchestration.

Avoid:

- architecture layers;
- dependency injection frameworks;
- generic registries;
- plugin systems;
- async code without need;
- hidden global mutable state;
- over-generalized base classes;
- speculative configuration systems.

---

# 9. Project bootstrap

Create only the bootstrap files approved by the implementation plan.

Typical approved artifacts may include:

```text
pyproject.toml
uv.lock
src/ai_newsroom/
tests/
```

The exact tree is controlled by the approved plan, not this illustrative list.

## `pyproject.toml`

It must:

- target Python 3.12;
- declare only approved direct dependencies;
- expose the exact required CLI entry point;
- configure pytest, Ruff and mypy proportionally;
- avoid unrelated metadata and optional groups;
- avoid unapproved build dependencies.

Do not add:

- coverage plugins;
- pre-commit;
- tox;
- nox;
- task runners;
- release tools;
- type-stub packages unless the approved tests prove they are necessary and owner approval is obtained.

## Lockfile

Create `uv.lock` using the approved dependency set.

If dependency resolution requires network approval:

- request approval only for `uv lock` or `uv sync`;
- do not enable project runtime network;
- record the exact command used.

## Initial verification

Run the exact bootstrap commands from the approved plan.

At minimum, verify:

```powershell
uv sync --frozen
```

after the lockfile exists.

If the normative specification uses another exact command sequence, follow it.

---

# 10. Domain contracts

Implement the exact F0 entities and enums from `F0_TECHNICAL_SPEC.md`.

Rules include:

- `Story` stores only its required identity and `primary_source_id`;
- do not persist `Story.title`;
- derive title from the referenced `SourceSnapshot`;
- immutable source revisions remain immutable;
- package claims use the exact required type and verification status;
- no future workflow state machine;
- no F1 merge identity;
- no provider abstraction.

Pydantic models must:

- use Pydantic v2 APIs;
- reject invalid normative values;
- avoid silently coercing values where the specification requires strictness;
- serialize deterministically where they contribute to exports or fingerprints.

Do not duplicate normative constants across many files when one small, direct definition is sufficient.

---

# 11. Text and date normalization

Implement the exact normative sequence from `F0_TECHNICAL_SPEC.md`.

Do not reorder operations.

Cover at minimum:

- UTF-8 decoding;
- BOM handling;
- newline normalization;
- Unicode NFC;
- title normalization;
- summary normalization;
- prohibited control characters;
- empty or invalid values;
- raw publication date preservation;
- normalized publication timestamp behavior;
- deterministic handling of missing or invalid dates.

Tests must include:

- valid Unicode;
- decomposed/composed Unicode equivalence where required;
- Windows line endings;
- BOM;
- tabs and controls;
- whitespace boundaries;
- invalid UTF-8 behavior if specified;
- missing and invalid dates;
- exact reference vectors from the specification.

Do not use locale-dependent parsing.

---

# 12. URL validation and canonicalization

Implement the normative URL algorithm exactly.

Cover:

- supported scheme validation;
- host validation;
- IDNA handling;
- IPv6 handling;
- credentials rejection;
- default-port behavior;
- path normalization only where specified;
- fragment handling;
- removal of specified tracking parameters;
- preservation of meaningful query-pair order;
- repeated query keys;
- empty query values;
- canonical string generation.

Do not:

- sort meaningful query pairs;
- remove unknown query parameters;
- infer tracking parameters not listed by the specification;
- fetch the URL;
- resolve redirects;
- normalize in a way that changes resource semantics.

Add table-driven tests for positive and negative cases.

---

# 13. Deterministic identities

Implement every identity and hash contract from the normative specification.

Use:

- exact canonical inputs;
- exact separators;
- exact encodings;
- exact SHA-256 handling;
- exact prefixes;
- exact truncation lengths.

Verify the complete normative reference vector:

```text
content_hash=e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d
source_id=src_58343a9a5ffae3037a3f73bf
story_id=story_55c2bc7f60628d20cb9acd4c
claim_id=claim_11806810946d69ba4de2ccd4
input_fingerprint=bd9e982b780c713eaad078c3129e6ddebec56fcc6b5cba0bf951547ae31fda8f
package_id=pkg_17e9b7502f7bc00db437b993
```

A mismatch is a blocker.

Do not modify the specification’s expected values.

Do not use current timestamps, random UUIDs or database row IDs for deterministic identities.

---

# 14. Offline RSS fixture ingestion

Implement only local fixture ingestion.

Requirements:

- read a local file;
- enforce normative size limits;
- reject prohibited XML constructs such as DTD/entities according to the specification;
- enforce item-count limits;
- parse only the supported F0 feed shape;
- normalize fields before identity generation;
- preserve raw publication date;
- create immutable `SourceSnapshot` records;
- create associated `Story` records;
- handle duplicates idempotently;
- perform writes in the required transaction boundary;
- never access network.

Use standard-library XML parsing only as approved.

Tests must prove:

- valid fixture ingestion;
- duplicate ingestion;
- malformed XML;
- DTD/entity rejection;
- oversized fixture;
- too many items;
- invalid required fields;
- transaction rollback on failure;
- no network calls.

Do not add live RSS URLs, HTTP clients or retry logic.

---

# 15. SQLite persistence

Implement exactly the four normative F0 tables.

Requirements:

- direct `sqlite3` usage;
- exact required columns;
- exact keys and constraints;
- no `json_valid()` dependency;
- no ORM;
- no migration framework;
- no automatic destructive repair;
- no hidden schema upgrades;
- F0 schema/data treated as disposable for future F1;
- deterministic queries use explicit `ORDER BY`;
- foreign keys enabled where required;
- transaction boundaries follow the specification.

Database initialization must:

- create a new valid F0 database;
- be idempotent where specified;
- refuse incompatible or unexpected existing state as required;
- not silently delete, rebuild or mutate unknown data.

Tests must use isolated temporary paths.

Do not commit database files.

---

# 16. Deterministic mock package

Implement the exact F0 deterministic package builder.

Requirements:

- read the selected Story and its primary SourceSnapshot;
- perform the normative integrity validation at package build;
- produce the exact required package model;
- produce the exact mock claim type/status;
- compute the exact input fingerprint;
- compute the exact package identity;
- remain deterministic across repeated runs;
- not call an LLM;
- not introduce provider interfaces;
- not use current time unless the specification defines a deterministic source for a non-identity field.

Tests must cover:

- normative reference vector;
- missing Story;
- missing or tampered SourceSnapshot;
- integrity mismatch;
- repeated build;
- package upsert/idempotence if required;
- no network.

---

# 17. Canonical JSON and Markdown export

Implement the exact export contract.

JSON source fields must use the normative names, including:

- `canonical_url`;
- `published_at`;
- `published_at_raw`;
- exact IDs and hashes required by the specification.

Do not output a generic `url` field when `canonical_url` is required.

Do not use fake hash placeholders.

Canonical JSON must be deterministic with:

- exact encoding;
- exact key policy;
- exact separators/indentation policy;
- exact newline policy;
- stable list ordering;
- no absolute paths;
- no current-time noise.

Markdown must be deterministic and derived from the same validated package.

## Collision behavior

Implement:

- no overwrite when existing output differs and `--force` is absent;
- no unnecessary replacement when existing output is byte-identical;
- explicit `--force` behavior;
- per-file atomic replacement;
- proportional partial-pair detection and recovery exactly as specified;
- no requirement for a real process-kill simulation.

Tests must use an injected deterministic failure where the plan/spec calls for it.

Do not commit generated exports.

---

# 18. CLI surface

Implement exactly these command forms:

```text
ai-newsroom --data-dir PATH db init
ai-newsroom --data-dir PATH harvest run --fixture FILE
ai-newsroom --data-dir PATH stories list [--ids-only]
ai-newsroom --data-dir PATH package build STORY_ID
ai-newsroom --data-dir PATH package export STORY_ID --format json|markdown|all [--force]
```

Rules:

- no additional placeholder commands;
- no hidden network mode;
- no F1 flags;
- standard Typer/Click behavior for syntax and usage errors;
- project error codes only where normatively defined;
- deterministic stdout/stderr where specified;
- non-zero exits on required failures;
- no traceback leakage for expected user errors;
- paths with spaces and Unicode must work on Windows.

CLI tests should invoke the real command surface, not only internal functions.

---

# 19. Error handling and logging

Implement only the normative error taxonomy.

Requirements:

- map expected domain/application failures to the required project error codes;
- leave command syntax errors to Typer/Click;
- do not invent `E_USAGE`;
- do not expose secrets;
- do not print raw fixture bodies;
- do not print SQL statements with user content;
- do not catch `BaseException`;
- do not convert unexpected programming errors into false success;
- keep logs proportional.

Expected errors must be testable without brittle full-message matching unless exact text is normative.

---

# 20. Network isolation

Tests and F0 demo must prove offline behavior.

Implement a test guard that fails if application code attempts outbound socket access.

The guard must:

- apply to relevant test paths;
- not depend on a third-party plugin;
- not block normal local filesystem or SQLite use;
- make attempted network access visible as a failure.

Do not add HTTP libraries.

Do not use Context7, GitHub or any external connector from application code or tests.

Development-time documentation lookup is separate from runtime behavior.

---

# 21. Windows and resource behavior

Verify:

- paths containing spaces;
- paths containing Unicode;
- CRLF fixture handling where relevant;
- no dependence on POSIX-only shell behavior;
- no hard-coded `/tmp`;
- no symlink assumptions;
- no Docker requirement.

Resource target:

```text
Windows 11
Ryzen 3 5300U
16 GB RAM
no GPU
```

Perform the manual 512 MB sanity observation exactly as required by the specification.

Do not add a memory-profiling dependency.

---

# 22. Testing strategy

Implement the tests mapped in the approved plan.

Tests must be:

- deterministic;
- isolated;
- offline;
- safe to repeat;
- independent of current date/time;
- independent of repository absolute path;
- independent of test execution order;
- compatible with Windows.

Use fixtures and golden files only where approved.

Do not create excessive snapshots for behavior better asserted structurally.

At minimum, the suite must cover every requirement area listed in `docs/f0-implementation-plan.md`.

---

# 23. Iterative verification

After each approved implementation step, run the targeted commands from the plan.

Also run:

```powershell
uv run ruff check .
uv run mypy .
uv run pytest
```

Use the exact command form from the normative spec when it differs.

Do not hide failures with:

- `|| true`;
- PowerShell equivalents that discard exit codes;
- selective test omission;
- marks that skip required tests;
- loosening Ruff or mypy configuration merely to pass.

Fix root causes within F0 scope.

If a fix requires scope expansion or a new direct dependency, stop.

---

# 24. Commit strategy

Follow the approved plan’s commit strategy.

Create between 3 and 6 logical implementation commits.

A reasonable pattern is:

```text
chore: bootstrap F0 Python project
feat: implement normalization and deterministic identities
feat: persist offline source snapshots and stories
feat: build deterministic mock story packages
feat: export canonical JSON and Markdown
test: complete F0 determinism and CLI coverage
```

This is illustrative. Use commit boundaries matching the actual five approved steps.

Commit rules:

- all targeted tests for the step pass;
- staged diff reviewed;
- no generated data;
- no secrets;
- no unrelated documentation rewrites;
- no `--no-verify`;
- no amend of prior approved commits;
- no automated push after each commit.

Before each commit:

```powershell
git diff --check
git diff --stat
git status --short
```

After each commit:

```powershell
git log -1 --oneline
git status --short
```

Working tree should be clean before beginning the next logical step.

---

# 25. Scope verification before final gate

After implementation and before the final quality gate, run explicitly:

```text
$f0-scope-guardian
```

Review the complete branch diff from `main`:

```powershell
git diff --stat main...HEAD
git diff main...HEAD
```

The guardian must verify:

- only F0 implementation exists;
- no non-goal was introduced;
- only approved direct dependencies exist;
- exactly five CLI commands exist;
- no network implementation exists;
- no future placeholders exist;
- normative documents were not modified.

## If guardian returns FAIL

- fix only confirmed implementation violations;
- do not change the normative specification;
- rerun targeted tests;
- rerun guardian;
- maximum two remediation rounds.

If still failing after two rounds:

- do not push;
- return `SCOPE_GATE_FAILED`.

---

# 26. Full verification before quality gate

Run all normative static and test commands.

At minimum:

```powershell
uv sync --frozen
uv run ruff check .
uv run mypy .
uv run pytest
```

Then execute the complete Definition of Done from `F0_TECHNICAL_SPEC.md`, including:

- clean demo directory;
- database initialization;
- fixture harvest;
- story listing;
- package build;
- JSON export;
- Markdown export;
- all-format export where required;
- repeated harvest;
- repeated package build;
- repeated export;
- ID comparison;
- database row-count comparison;
- SHA-256 comparison;
- collision behavior;
- force behavior;
- partial-pair behavior;
- offline proof;
- Windows path cases;
- reference-vector verification.

Do not substitute an approximate demo for the normative one.

Do not commit demo data.

---

# 27. Run F0 Quality Gate

After normal checks pass, invoke explicitly:

```text
$f0-quality-gate
```

The skill must not edit files.

Expected final status:

```text
PASS
```

## If quality gate returns FAIL

1. preserve the report;
2. fix only verified F0 defects outside the skill;
3. run targeted checks;
4. rerun the complete normal verification;
5. rerun `$f0-quality-gate`.

Maximum remediation rounds:

```text
2
```

If still failing:

- do not push;
- return `QUALITY_GATE_FAILED`.

Do not weaken tests or gates.

---

# 28. Final implementation report

Create one concise implementation report only if the approved plan or normative specification requires it.

Preferred path when needed:

```text
docs/f0-implementation-results.md
```

The report must contain:

- implemented steps;
- final file tree;
- direct dependencies;
- static-check results;
- test count and result;
- Definition of Done result;
- reference-vector result;
- repeated-run determinism result;
- scope guardian result;
- quality-gate result;
- deviations;
- remaining work before merge.

Do not duplicate test logs in full.

If the approved plan does not call for this file, do not create it merely for ceremony; include the information in the final Codex response instead.

---

# 29. Final diff review within the implementation thread

Run:

```powershell
git status --short
git diff --check
git diff --stat main...HEAD
git log --oneline --decorate main..HEAD
```

Verify:

- branch is `feat/f0-foundation`;
- `main` was not changed;
- no normative or historical document changed;
- no runtime DB/export/cache/log is tracked;
- no secret candidate is tracked;
- no unexpected binary exists;
- all implementation changes belong to F0;
- working tree is clean after final commit.

Perform a secret-name and content-pattern scan without printing secret values.

If an implementation-results file was created, commit it separately with an appropriate documentation commit.

---

# 30. Push

Push only after:

- all implementation commits exist;
- scope guardian returns `PASS`;
- all static checks pass;
- all tests pass;
- complete DoD passes;
- quality gate returns `PASS`;
- working tree is clean.

Run:

```powershell
git push origin feat/f0-foundation
```

If upstream is missing:

```powershell
git push -u origin feat/f0-foundation
```

This is the only permitted final network action besides approved dependency resolution.

Do not:

- push to `main`;
- force-push;
- create a PR;
- merge;
- create tags;
- change GitHub settings.

Verify:

```powershell
git status -sb
git rev-parse HEAD
git rev-parse origin/feat/f0-foundation
git remote -v
```

Local and remote SHAs must match.

---

# 31. Stop boundary

After the successful push, STOP.

Do not perform:

- independent review in the same thread;
- Codex Security scan;
- PR creation;
- merge;
- release;
- F1 planning.

Those require fresh, independent threads.

---

# 32. Final response format

Return exactly the following sections.

## Verdict

One of:

- `F0_IMPLEMENTED_AND_PUSHED`
- `F0_IMPLEMENTED_LOCAL_ONLY`
- `PACKAGING_DECISION_REQUIRED`
- `ENVIRONMENT_BLOCKED`
- `SPEC_PLAN_CONFLICT`
- `SCOPE_GATE_FAILED`
- `QUALITY_GATE_FAILED`
- `BLOCKED`

## Repository state

Include:

- root;
- branch;
- starting commit;
- final commit;
- working-tree status;
- remote tracking state.

## Implementation summary

Include:

- five approved steps and result;
- created/modified files;
- final file count;
- exact direct dependencies;
- CLI commands implemented;
- database tables implemented.

## Commits

List each new commit:

```text
<short SHA> <subject>
```

## Static checks

Report exact result for:

- `uv sync --frozen`;
- Ruff;
- mypy;
- pytest.

Include test count if available.

## Reference vector

Report expected versus actual for:

- `content_hash`;
- `source_id`;
- `story_id`;
- `claim_id`;
- `input_fingerprint`;
- `package_id`.

## Definition of Done

Report every normative DoD group as:

- `PASS`;
- `FAIL`;
- `NOT_EXECUTED`.

## Determinism

Include:

- repeated harvest result;
- repeated package build result;
- repeated export result;
- row-count comparison;
- SHA-256 comparison.

## Scope Guardian

Include:

- rounds;
- final verdict;
- violations corrected;
- unresolved findings.

## Quality Gate

Include:

- rounds;
- final status;
- failures corrected;
- unresolved failures.

## Security and offline checks

Include:

- network guard;
- XML DTD/entity rejection;
- path safety;
- collision/force behavior;
- partial-pair behavior;
- secret/artifact scan.

## Git push

Include:

- remote branch;
- push result;
- local SHA;
- remote SHA;
- SHA match.

## Deviations

State:

```text
NONE
```

or list every deviation from:

- normative specification;
- approved plan;
- dependency policy;
- commit strategy.

## Constraints confirmed

Confirm:

- normative documents unchanged;
- `main` unchanged;
- no live network ingestion;
- no real LLM;
- no UI/API;
- no Docker;
- no video/publishing;
- no ORM/migrations;
- no generated runtime data committed;
- no PR or merge created.

## Next step

Only:

> Start a new read-only Codex thread for an independent review of `main...feat/f0-foundation`. After that review passes, run Codex Security in a separate security-review thread.

---

# 33. Success criterion

The task succeeds only if:

1. Codex works from `C:\Dev\ai-newsroom-os`;
2. implementation remains on `feat/f0-foundation`;
3. the normative specification remains unchanged;
4. all five approved plan steps are implemented;
5. only approved direct dependencies are used;
6. the reference vector matches exactly;
7. the complete test suite passes offline;
8. the full Definition of Done passes;
9. `$f0-scope-guardian` returns `PASS`;
10. `$f0-quality-gate` returns `PASS`;
11. the Git history contains small logical commits;
12. the feature branch is pushed and synchronized;
13. `main` remains unchanged;
14. the task stops before independent review, security scan, PR or merge.
