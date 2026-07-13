# Codex Prompt — F0 Planning, Scope Review, Plan Commit and Push

## Purpose

Prepare an approved implementation plan for Foundation F0 in a new feature branch.

This task must:

1. verify the repository baseline;
2. create branch `feat/f0-foundation`;
3. inspect the normative F0 specification;
4. create a minimal file-level implementation plan;
5. run `$f0-scope-guardian` against that plan;
6. revise the plan until the guardian returns `PASS`;
7. commit the approved plan;
8. push the branch to `origin`;
9. stop before implementing any F0 code.

This task **does not implement F0**.

---

# 1. Project context

Expected project root:

```text
C:\Dev\ai-newsroom-os
```

Expected baseline:

```text
branch: main
remote: origin
remote repository: iurii-izman/ai-newsroom-os
visibility: private
baseline commit:
728f73dbbf2cdd2b9326e4a5cc855ea597db86af
```

The repository already contains:

- `F0_TECHNICAL_SPEC.md`;
- `PROJECT_VISION.md`;
- `AGENTS.md`;
- `.codex/config.toml`;
- `docs/f0-minimal-scope.md`;
- repo-local skill `$f0-scope-guardian`;
- repo-local skill `$f0-quality-gate`.

---

# 2. Authority

Read completely before planning:

1. `AGENTS.md`;
2. `F0_TECHNICAL_SPEC.md`;
3. `docs/f0-minimal-scope.md`;
4. `PROJECT_VISION.md`;
5. `docs/open-decisions.md`;
6. `docs/f0-risk-register.md`.

Authority order:

1. `F0_TECHNICAL_SPEC.md` — sole normative F0 specification;
2. `docs/f0-minimal-scope.md` — derived non-normative checklist;
3. `PROJECT_VISION.md` — non-normative product context;
4. historical Foundation and audit files — historical context only.

If documents conflict, `F0_TECHNICAL_SPEC.md` wins.

---

# 3. Hard constraints

During this task, MUST NOT:

- implement application code;
- create `src/`;
- create `tests/`;
- create `pyproject.toml`;
- create `uv.lock`;
- install dependencies;
- create a database;
- create RSS fixtures;
- create exports;
- create CI;
- create Docker files;
- add UI, API, LLM, TTS, video or publishing code;
- add placeholders for future phases;
- modify normative or historical Foundation documents;
- modify `AGENTS.md`;
- modify `.codex/config.toml`;
- run `$f0-quality-gate`;
- merge into `main`;
- create a pull request;
- force-push;
- rewrite Git history;
- use network except for the explicit final Git push;
- add a direct dependency;
- silently expand F0 scope.

Only the implementation plan and Git branch metadata may change.

---

# 4. Preflight

Run:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git log -1 --oneline
```

Verify:

- repository root is `C:\Dev\ai-newsroom-os`;
- current branch is `main`;
- working tree is clean;
- `origin` points to `iurii-izman/ai-newsroom-os`;
- current `HEAD` is the approved baseline or a documented descendant of it;
- no unexpected local changes exist.

If any condition fails:

- do not create a branch;
- do not modify files;
- return `BLOCKED` with exact evidence.

---

# 5. Confirm active Codex instructions

Before editing, summarize:

- the sole normative F0 document;
- F0 objective;
- F0 non-goals;
- direct dependency policy;
- offline/network policy;
- disposable F0 data policy;
- expected CLI surface;
- Definition of Done;
- 2–4 focused working day timebox.

Do not modify files during this confirmation.

If the summary conflicts with `F0_TECHNICAL_SPEC.md`, stop and report the conflict.

---

# 6. Create the feature branch

Create:

```powershell
git switch -c feat/f0-foundation
```

Then verify:

```powershell
git branch --show-current
git status --short
```

Expected:

```text
feat/f0-foundation
clean working tree
```

If the branch already exists:

- do not delete or recreate it;
- inspect whether it is based on the current `main`;
- if clean and safe, switch to it;
- otherwise stop and report the branch state.

---

# 7. Inspect the repository

Inspect:

- current file tree;
- active documentation;
- `.gitignore`;
- `.gitattributes`;
- `.editorconfig`;
- Codex skills;
- existing code or runtime artifacts, if any.

Do not treat historical audit files as implementation instructions.

Identify:

- files that must remain untouched;
- files that will be created during F0 implementation;
- direct dependencies allowed by the spec;
- F0 behavior groups;
- risk-sensitive boundaries:
  - text normalization;
  - date normalization;
  - URL canonicalization;
  - deterministic identity;
  - SQLite persistence;
  - canonical package generation;
  - export collision and partial-pair handling;
  - CLI errors;
  - offline operation.

---

# 8. Create the implementation plan

Create exactly one new file:

```text
docs/f0-implementation-plan.md
```

Do not create any implementation file in this task.

The plan must be concise, executable and proportional to the F0 timebox.

Use this structure.

---

## `docs/f0-implementation-plan.md`

```markdown
# Foundation F0 Implementation Plan

## Status

- Phase: Foundation F0
- Branch: `feat/f0-foundation`
- Normative source: `F0_TECHNICAL_SPEC.md`
- Plan status: `PROPOSED` or `SCOPE_APPROVED`
- Implementation started: `NO`

## Objective

State the exact offline vertical slice.

## Preconditions

List the verified repository, environment and governance assumptions.

## Non-goals

List the relevant F0 exclusions. Do not copy every historical exclusion.

## Direct dependencies

### Runtime

### Development

State that transitive dependencies are allowed and no other direct dependency is planned.

## Proposed file tree

List every file expected to be created or modified during F0 implementation.

For each file include:

- responsibility;
- normative requirements served;
- why the file is needed now.

Do not include speculative files.

## Module responsibilities

Describe the smallest practical module boundaries.

## Implementation sequence

Use numbered vertical steps.

Each step must:

- produce observable behavior;
- name files changed;
- name tests added;
- state the verification command;
- avoid leaving empty architecture placeholders.

## Requirement-to-test mapping

Use a table:

| Requirement area | Planned behavior | Planned test type | Planned test file |
|---|---|---|---|

Cover at minimum:

- text normalization;
- date normalization;
- URL canonicalization;
- identity reference vector;
- RSS validation and limits;
- SQLite initialization and transactions;
- immutable source revisions;
- Story creation;
- deterministic mock package;
- canonical JSON export;
- Markdown export;
- collision/force behavior;
- partial-pair detection;
- CLI behavior;
- offline network guard;
- repeated end-to-end determinism;
- Windows Unicode and spaces in paths.

## CLI implementation plan

Map exactly the five allowed commands and their responsibilities.

Do not add placeholder commands.

## Persistence plan

Describe exactly the four F0 tables and transaction boundaries.

Do not introduce ORM, migrations or repository abstractions.

## Determinism plan

Explain how the implementation will avoid dependency on:

- current time in identities/exports;
- row order;
- absolute paths;
- randomness;
- locale;
- platform newline differences.

## Error-handling plan

Map expected project error codes to implementation boundaries.

Typer/Click syntax errors remain framework-standard.

## Security and resource plan

Cover:

- DTD/entity rejection;
- fixture size and item limits;
- control characters;
- path safety;
- log sanitization;
- no network;
- no destructive DB fallback;
- 16 GB target;
- optional manual memory sanity observation.

## Commit strategy

Propose 3–6 logical implementation commits.

Do not commit generated runtime data.

## Verification strategy

List:

- iterative checks;
- final Ruff/mypy/pytest;
- complete Definition of Done;
- repeated E2E;
- `$f0-scope-guardian`;
- `$f0-quality-gate`;
- independent diff review;
- Codex Security diff scan.

## Definition of Done commands

Copy the executable commands from the current normative specification accurately.

## Risks and stop conditions

List only implementation-relevant risks.

Explicitly state when Codex must stop rather than expand scope.

## Planned deviations

State `NONE`.

If a deviation appears necessary, the plan must remain `PROPOSED` and implementation must not begin.
```

---

# 9. File-tree quality rules

The proposed tree must be minimal.

A reasonable design may use a compact structure such as:

```text
pyproject.toml
uv.lock
src/
└── ai_newsroom/
    ├── __init__.py
    ├── cli.py
    ├── models.py
    ├── normalization.py
    ├── rss.py
    ├── database.py
    ├── package_builder.py
    └── exporters.py
tests/
├── fixtures/
├── golden/
├── test_normalization.py
├── test_rss.py
├── test_database.py
├── test_package.py
├── test_export.py
└── test_cli_e2e.py
```

This is illustrative, not mandatory.

Reject or justify structures containing:

- `ports/`;
- `adapters/`;
- `providers/`;
- `services/` with no concrete need;
- `repositories/` abstractions;
- `use_cases/` wrappers with no value;
- `workflows/`;
- `agents/`;
- `api/`;
- `web/`;
- `frontend/`;
- `migrations/`;
- `docker/`;
- future placeholders;
- empty package trees.

Prefer a small modular monolith over architecture ceremony.

---

# 10. Run F0 Scope Guardian

After writing the first plan, invoke explicitly:

```text
$f0-scope-guardian
```

Ask it to review:

```text
docs/f0-implementation-plan.md
```

against:

```text
F0_TECHNICAL_SPEC.md
AGENTS.md
docs/f0-minimal-scope.md
```

The guardian must not edit files.

## If the guardian returns `FAIL`

1. inspect every blocking violation;
2. revise only `docs/f0-implementation-plan.md`;
3. do not change specifications;
4. rerun `$f0-scope-guardian`;
5. repeat until:
   - guardian returns `PASS`; or
   - a genuine specification conflict is found.

Maximum revision rounds:

```text
3
```

After three failed rounds:

- stop;
- do not commit;
- return `BLOCKED`.

## If the guardian returns `PASS`

Update plan status:

```text
Plan status: SCOPE_APPROVED
```

Record in the plan:

- review date;
- guardian verdict;
- number of review rounds;
- summary of corrections made.

Do not begin implementation.

---

# 11. Independent plan sanity check

After guardian `PASS`, independently verify:

1. only one plan file was created;
2. no code, tests, dependency files or runtime artifacts exist;
3. every proposed file has a current F0 consumer;
4. every planned direct dependency is permitted;
5. all five and only five CLI commands are planned;
6. no network implementation is planned;
7. no future phase entity is planned;
8. the plan covers the normative reference vector;
9. the plan includes a repeated end-to-end run;
10. the plan fits the 2–4 focused working day target;
11. the plan does not promise migration into F1;
12. historical documents are not treated as normative.

If any check fails, correct the plan and rerun the guardian.

---

# 12. Review the Git diff

Run:

```powershell
git status --short
git diff -- docs/f0-implementation-plan.md
git diff --check
```

Expected:

- only `docs/f0-implementation-plan.md` is untracked or modified;
- no other file changed;
- no whitespace errors in the new plan.

If another file changed:

- do not discard user changes;
- inspect and report;
- restore only changes made by this task when safe;
- stop if ownership is unclear.

---

# 13. Commit the approved plan

Stage only the plan:

```powershell
git add docs/f0-implementation-plan.md
```

Verify:

```powershell
git diff --cached --check
git diff --cached --stat
git status --short
```

Commit:

```powershell
git commit -m "docs: define approved F0 implementation plan"
```

Do not amend the baseline commit.

Capture:

```powershell
git rev-parse HEAD
git log -2 --oneline
git status --short
```

Expected working tree:

```text
clean
```

---

# 14. Push the feature branch

Push:

```powershell
git push -u origin feat/f0-foundation
```

This is the only allowed network action in this task.

If approval is required, request approval only for this push.

Do not:

- create a pull request;
- merge;
- push to `main`;
- create a tag;
- change GitHub settings.

After push, verify:

```powershell
git status -sb
git rev-parse HEAD
git rev-parse origin/feat/f0-foundation
git remote -v
```

Local and remote feature-branch SHAs must match.

If push fails:

- keep the local commit;
- do not retry with force;
- return `LOCAL_PLAN_COMMITTED` and the exact safe next action.

---

# 15. Final response

Return exactly:

## Verdict

One of:

- `PLAN_APPROVED_AND_PUSHED`
- `PLAN_APPROVED_LOCAL_ONLY`
- `BLOCKED`

## Repository state

Include:

- root;
- branch;
- clean/dirty status;
- remote.

## Plan

Include:

- path;
- status;
- proposed file count;
- proposed direct dependencies;
- proposed implementation steps;
- guardian rounds.

## F0 Scope Guardian

Include:

- final verdict;
- blocking violations found;
- corrections applied;
- unresolved findings.

## Validation

Report PASS/FAIL for:

- authority;
- preflight;
- branch;
- one-file-only change;
- non-goal compliance;
- dependency compliance;
- CLI compliance;
- test coverage plan;
- timebox proportionality;
- diff check.

## Git

Include:

- plan commit hash;
- commit subject;
- upstream branch;
- push result;
- local/remote SHA match.

## Constraints confirmed

Confirm:

- no F0 code implemented;
- no `src/`;
- no `tests/`;
- no dependencies installed;
- no `pyproject.toml`;
- no `uv.lock`;
- no database;
- no Docker;
- no API/LLM/video/publishing code;
- normative documents unchanged;
- `main` unchanged.

## Next step

Only:

> Start a new Codex implementation thread on `feat/f0-foundation`, read the approved plan, and implement F0 in small verified steps without changing the normative specification.

---

# 16. Success criterion

This task succeeds only if:

1. the project begins from a clean approved baseline;
2. implementation occurs on `feat/f0-foundation`;
3. the plan is derived from the sole normative specification;
4. `$f0-scope-guardian` returns `PASS`;
5. the plan remains proportional to F0;
6. no implementation artifact is created;
7. the approved plan is committed separately;
8. the feature branch is pushed without changing `main`;
9. the next implementation thread has a clear, reviewable contract.
