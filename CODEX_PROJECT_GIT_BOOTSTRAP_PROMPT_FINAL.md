# Codex Bootstrap Prompt — Git, Governance, Skills, Private GitHub Repository

## Purpose

Bootstrap the existing `AIvideocenter` workspace as a clean, governed OpenAI Codex project.

This task creates:

- the minimal repository-level Codex configuration;
- the minimal project governance files;
- two repo-local Codex skills;
- a local Git repository;
- the first baseline commit;
- one private GitHub remote repository;
- the first push to `main`.

This task **does not implement Foundation F0**.

---

# 1. Fixed bootstrap parameters

Use these values unless the owner has already supplied different values in the current thread:

```text
REMOTE_REPOSITORY_NAME = ai-newsroom-os
REMOTE_VISIBILITY = private
REMOTE_NAME = origin
DEFAULT_BRANCH = main
INITIAL_COMMIT_MESSAGE = chore: establish owner-reviewed F0 foundation
REPOSITORY_DESCRIPTION = Proof-first AI newsroom automation system
```

Create **one repository only**:

- one local Git repository in the current project root;
- one corresponding private GitHub remote.

Do not create separate repositories for documentation, skills, backend, video, or future phases.

---

# 2. Authority and scope

Read these files completely before editing:

- `F0_TECHNICAL_SPEC.md`
- `PROJECT_VISION.md`
- `docs/f0-minimal-scope.md`
- `docs/open-decisions.md`
- `docs/f0-risk-register.md`
- `docs/foundation-owner-review.md`

Treat:

1. `F0_TECHNICAL_SPEC.md` as the sole normative F0 specification;
2. `docs/f0-minimal-scope.md` as a derived checklist;
3. `PROJECT_VISION.md` as non-normative product context;
4. audit, vNext and original Foundation files as historical context.

Do not modify the existing foundation documents during this bootstrap unless a file is corrupted or missing. Report such a problem instead of silently rewriting it.

---

# 3. Hard constraints

During this task, MUST NOT:

- implement F0 application code;
- create `src/`, `tests/`, `pyproject.toml`, `uv.lock`, a database, fixtures or exports;
- add Python dependencies;
- install packages;
- add CI workflows;
- add Docker files;
- add an API, UI, LLM provider, video or publishing code;
- add placeholder modules or empty architecture directories;
- create multiple GitHub repositories;
- create a public repository;
- create a license without an owner decision;
- create GitHub secrets;
- create releases, tags, issues or pull requests;
- enable automatic merge;
- modify GitHub repository settings beyond repository creation and optional wiki disablement;
- use Chrome, browser automation or Computer Use for GitHub;
- print credentials, tokens or suspected secret values;
- use destructive Git commands;
- force-push;
- rewrite existing history;
- commit if the staged diff contains an unresolved secret or unexpected binary file.

---

# 4. Preflight

Before creating or modifying files, inspect the current directory.

## 4.1. Confirm project root

Confirm that the current directory contains:

- `F0_TECHNICAL_SPEC.md`;
- `PROJECT_VISION.md`;
- `docs/`.

If not, stop and report that the wrong directory is open.

## 4.2. Check Git state

Run read-only checks:

```powershell
git --version
git rev-parse --show-toplevel
git status --short
git remote -v
```

Expected behavior:

- if the directory is not yet a Git repository, continue;
- if it is already a Git repository, do not reinitialize it;
- if an `origin` remote already exists, stop and report its URL;
- if there are unexpected uncommitted files outside the known project documents, list them and continue only if they are safe and belong to this project.

Do not delete or move unknown user files.

## 4.3. Check Git identity

Run:

```powershell
git config --get user.name
git config --get user.email
```

If either value is missing:

- do not invent it;
- do not change global Git configuration;
- stop before commit;
- report the exact local commands the owner can run:

```powershell
git config user.name "OWNER NAME"
git config user.email "OWNER EMAIL"
```

## 4.4. Check GitHub CLI and authentication

Prefer GitHub CLI for deterministic local-to-remote publishing.

Run:

```powershell
gh --version
gh auth status
```

If authenticated, obtain the current owner safely:

```powershell
gh api user --jq .login
```

Do not print tokens.

If `gh` is missing or unauthenticated:

- continue through local file creation and local commit;
- do not use Chrome or browser automation;
- use the connected GitHub plugin only if it explicitly supports creating a private repository from the existing local history;
- otherwise stop before remote creation and report the missing prerequisite.

## 4.5. Check remote-name collision

If GitHub authentication is available, check whether:

```text
<authenticated-owner>/ai-newsroom-os
```

already exists.

If it exists:

- do not overwrite or reuse it automatically;
- do not create a suffixed repository;
- stop before remote creation and report the existing repository URL.

---

# 5. Create the minimal governance structure

Create exactly the following new files and directories when absent:

```text
README.md
AGENTS.md
.gitignore
.gitattributes
.editorconfig
.codex/
└── config.toml
.agents/
└── skills/
    ├── f0-scope-guardian/
    │   ├── SKILL.md
    │   └── agents/
    │       └── openai.yaml
    └── f0-quality-gate/
        ├── SKILL.md
        └── agents/
            └── openai.yaml
docs/
└── codex-tooling-registry.md
```

Do not create empty code directories.

---

# 6. README.md requirements

Create a concise repository README containing:

1. project name: `AI Newsroom OS`;
2. one-paragraph product purpose;
3. status: `Foundation F0 ready for implementation`;
4. a clear statement that implementation has not started;
5. authoritative document order;
6. current phase boundaries;
7. target environment:
   - Windows 11;
   - Python 3.12.x;
   - Ryzen 3 5300U;
   - 16 GB RAM;
   - no GPU requirement;
   - no Docker;
8. repository governance summary;
9. next step:
   - implement F0 from `F0_TECHNICAL_SPEC.md` in a feature branch;
10. links to:
   - `PROJECT_VISION.md`;
   - `F0_TECHNICAL_SPEC.md`;
   - `docs/f0-minimal-scope.md`;
   - `docs/open-decisions.md`;
   - `docs/f0-risk-register.md`.

Do not copy the full specification into the README.

---

# 7. AGENTS.md requirements

Create a short root `AGENTS.md`.

It must contain the following intent without duplicating the full specification.

```markdown
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
```

Keep `AGENTS.md` compact and below 16 KiB.

---

# 8. Project Codex configuration

Create `.codex/config.toml`:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "disabled"
model_reasoning_effort = "high"
model_verbosity = "medium"
project_doc_max_bytes = 32768

[sandbox_workspace_write]
network_access = false
```

Rules:

- no model-provider override;
- no API keys;
- no absolute machine-specific paths;
- no MCP servers;
- no hooks;
- no danger-full-access;
- no automatic commit or push configuration.

This configuration is intended for subsequent F0 sessions. The temporary GitHub network actions in this bootstrap require explicit approval if the current sandbox blocks them.

---

# 9. Repo-local skill: f0-scope-guardian

Create:

```text
.agents/skills/f0-scope-guardian/SKILL.md
```

Use this metadata:

```yaml
---
name: f0-scope-guardian
description: Review an F0 implementation plan or Git diff against F0_TECHNICAL_SPEC.md for scope violations. Use only for explicit F0 scope-compliance review; do not use for implementation, automatic fixes, general review, or F1 planning.
---
```

Instructions must require:

1. reading `F0_TECHNICAL_SPEC.md`, `AGENTS.md` and the proposed plan or current diff;
2. treating `F0_TECHNICAL_SPEC.md` as sole normative source;
3. checking the F0 whitelist and every non-goal;
4. checking direct dependencies separately from transitive dependencies;
5. detecting:
   - network access;
   - Docker;
   - UI/API;
   - real LLM providers;
   - live ingestion;
   - clustering/merge;
   - video/publishing;
   - future placeholder abstractions;
   - extra CLI commands;
   - historical documents used as normative sources;
6. reporting exact file paths and evidence;
7. making no file edits;
8. returning:

```markdown
## Verdict
PASS | FAIL

## Blocking violations

## Warnings

## Requirement coverage
```

Create:

```text
.agents/skills/f0-scope-guardian/agents/openai.yaml
```

with:

```yaml
interface:
  display_name: "F0 Scope Guardian"
  short_description: "Check F0 plans and diffs for scope violations"

policy:
  allow_implicit_invocation: false
```

Do not add scripts, assets, references or MCP dependencies.

---

# 10. Repo-local skill: f0-quality-gate

Create:

```text
.agents/skills/f0-quality-gate/SKILL.md
```

Use this metadata:

```yaml
---
name: f0-quality-gate
description: Run and report the complete Foundation F0 quality gate from F0_TECHNICAL_SPEC.md. Use only when explicitly requested after F0 implementation; do not implement fixes or change files during the gate.
---
```

Instructions must require:

1. reading the normative Definition of Done;
2. checking that implementation prerequisites exist;
3. if implementation is absent, returning `NOT_READY` without creating it;
4. running, when available:
   - `uv sync --frozen`;
   - Ruff;
   - mypy;
   - pytest;
   - the complete documented CLI demo;
   - repeated harvest/build/export;
   - ID, row-count and SHA-256 comparisons;
5. no network;
6. no code edits;
7. no dependency edits;
8. no automatic repair;
9. distinguishing:
   - passed;
   - failed;
   - not executed;
   - not applicable;
10. returning:

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

Create:

```text
.agents/skills/f0-quality-gate/agents/openai.yaml
```

with:

```yaml
interface:
  display_name: "F0 Quality Gate"
  short_description: "Run the complete F0 verification without making fixes"

policy:
  allow_implicit_invocation: false
```

Do not create scripts yet.

---

# 11. Git ignore policy

Create `.gitignore` that excludes at minimum:

```gitignore
# Secrets
.env
.env.*
!.env.example
*.pem
*.key

# Python
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/

# Runtime data
*.db
*.sqlite
*.sqlite3
.demo-f0/
data/
exports/
tmp/
temp/

# Logs
*.log
.codex-log/

# OS and editors
.DS_Store
Thumbs.db
.idea/
.vscode/

# Build artifacts
build/
dist/
*.egg-info/
```

Do not ignore:

- `.codex/`;
- `.agents/`;
- `uv.lock`;
- project documentation.

---

# 12. Git attributes and editor configuration

Create `.gitattributes`:

```gitattributes
* text=auto eol=lf

*.ps1 text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf

*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.webp binary
*.pdf binary
*.db binary
*.sqlite binary
*.sqlite3 binary
```

Create `.editorconfig`:

```editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 4
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false

[*.{json,yaml,yml,toml}]
indent_size = 2

[*.ps1]
end_of_line = crlf
indent_size = 4
```

---

# 13. Codex tooling registry

Create `docs/codex-tooling-registry.md`.

Record only tools that are actually installed or enabled now:

| Tool | Type | Purpose | Permissions posture | Enabled phase | Removal/disable condition |
|---|---|---|---|---|---|
| Context7 | Plugin/App | Version-sensitive documentation | Network read only; no project writes expected | F0+ | Disable when not needed |
| GitHub | Plugin/App | Repository, PR, issue and CI access | Read-first; external writes require confirmation | Bootstrap/F0+ | Disable when no remote work |
| Codex Security | Plugin | Security scans and diff review | Read/review by default; fixes require explicit task | Post-F0 | Disable outside security tasks |
| Plugin Management | App | Inspect/manage plugin permissions | Administrative | As needed | Keep only while plugin management is useful |

Also record:

- custom MCP servers: none;
- browser automation: disabled;
- project runtime network: disabled.

Do not include tokens, account names or secret identifiers.

---

# 14. Validate the new governance files

Before Git initialization or staging:

1. parse `.codex/config.toml` if a TOML parser is available in the standard environment; otherwise inspect it structurally;
2. verify each `SKILL.md` has valid frontmatter with:
   - `name`;
   - `description`;
3. verify each `openai.yaml` contains:
   - display metadata;
   - `allow_implicit_invocation: false`;
4. confirm no skill contains scripts or external tool dependencies;
5. confirm `AGENTS.md` points to `F0_TECHNICAL_SPEC.md`;
6. confirm no existing foundation document was modified;
7. confirm no code directory or implementation artifact was created;
8. confirm all new text files use UTF-8 and expected line endings.

Do not rely on the newly created skills being reloaded in the current session.

---

# 15. Secret and artifact pre-commit review

Before staging, inspect:

- file names;
- file types;
- file sizes;
- likely secret markers.

Look for patterns such as:

```text
BEGIN PRIVATE KEY
github_pat_
ghp_
gho_
sk-
API_KEY=
ACCESS_TOKEN=
SECRET=
PASSWORD=
```

Do not print suspected secret values.

If a likely real secret is found:

- stop;
- report the file and line only;
- do not stage or commit.

Confirm that no files matching these categories are staged:

- `.env`;
- DB files;
- generated exports;
- logs;
- caches;
- unknown binaries.

Historical PDFs or user-provided binary assets must not be committed unless they are already an intentional part of the project and explicitly approved. If such files exist, stop and list them.

---

# 16. Initialize the local Git repository

If `.git` does not exist:

```powershell
git init
git branch -M main
```

Do not use a nested repository.

If `.git` already exists:

- do not reinitialize;
- confirm the current root and branch;
- continue only when there is no remote conflict and no prior history requiring preservation decisions.

Run:

```powershell
git status --short
```

---

# 17. Stage and review the baseline

Stage the intended project files:

```powershell
git add .
```

Then run:

```powershell
git diff --cached --check
git diff --cached --stat
git status --short
```

Review the staged file list.

The baseline should include:

- existing owner-reviewed foundation documents;
- README;
- AGENTS;
- Codex config;
- two repo-local skills;
- Git/editor hygiene files;
- tooling registry.

It must not include:

- application code;
- runtime data;
- secrets;
- database;
- exports;
- caches;
- logs;
- environment folders.

If unexpected files are staged:

- unstage them without deleting them;
- report them;
- continue only if the intended baseline remains coherent.

---

# 18. Create the initial commit

Only after every validation passes:

```powershell
git commit -m "chore: establish owner-reviewed F0 foundation"
```

Do not amend an existing commit.

Capture:

```powershell
git rev-parse HEAD
git log -1 --oneline
git status --short
```

The working tree must be clean after the commit.

---

# 19. Create the private GitHub repository and push

## 19.1. Preferred route: GitHub CLI

When `gh` is available and authenticated, create the remote from the existing local repository:

```powershell
gh repo create ai-newsroom-os `
  --private `
  --source=. `
  --remote=origin `
  --push `
  --description "Proof-first AI newsroom automation system" `
  --disable-wiki
```

Do not pass:

- `--add-readme`;
- `--gitignore`;
- `--license`;
- `--template`;
- `--public`.

The remote must use the existing local commit history.

If the current shell does not support PowerShell line continuation, run the equivalent command on one line.

## 19.2. Fallback route

If `gh` cannot perform the operation:

- use the connected GitHub plugin only if it can create a private repository and attach the existing local repository without generating a second history;
- otherwise stop after the local commit;
- report the exact owner action required;
- do not use browser automation.

## 19.3. Network and approval

Remote creation and push are external write actions.

If the sandbox requests approval:

- request approval only for GitHub authentication check, repository creation and push;
- do not enable unrestricted network globally;
- do not alter `.codex/config.toml`;
- do not use network for any project runtime or test.

---

# 20. Verify the remote

After successful creation and push, run:

```powershell
git remote -v
git branch --show-current
git status -sb
git log -1 --oneline
gh repo view --json nameWithOwner,url,visibility,defaultBranchRef
```

Verify:

- remote name is `origin`;
- visibility is `PRIVATE`;
- default branch is `main`;
- local `main` tracks `origin/main`;
- remote commit equals local `HEAD`;
- working tree is clean;
- no second remote exists;
- no extra repository was created.

Do not create a feature branch in this task. The separate F0 implementation task will create:

```text
feat/f0-foundation
```

from the pushed baseline.

---

# 21. Final report

Return exactly:

## Verdict

- `BOOTSTRAP_COMPLETE`
- `LOCAL_COMMIT_ONLY`
- or `BLOCKED`

## Project root

## Created files

## Existing files preserved

## Validation results

Include:

- authority check;
- skill metadata check;
- secret/artifact check;
- staged diff check;
- line-ending check.

## Git result

Include:

- repository root;
- branch;
- commit hash;
- commit subject;
- working-tree status.

## GitHub result

Include:

- repository name;
- owner;
- visibility;
- remote URL;
- default branch;
- push status.

Do not expose credentials.

## Deviations

List every skipped or changed step.

## Constraints confirmed

Confirm:

- F0 code not implemented;
- no dependencies installed;
- no database created;
- no Docker;
- no API/LLM/video/publishing code;
- one local repository;
- one private GitHub remote;
- original Foundation preserved.

## Next step

Only:

> Start a new Codex thread, create branch `feat/f0-foundation`, run `$f0-scope-guardian` on the implementation plan, then implement F0 from `F0_TECHNICAL_SPEC.md`.

---

# 22. Success criterion

The bootstrap succeeds only if:

1. the current project root becomes the sole Git root;
2. existing owner-reviewed documents remain intact;
3. Codex governance is minimal and repo-local;
4. both skills are explicit-only;
5. no implementation code is created;
6. the initial commit is clean and reviewable;
7. one private GitHub repository is created from local history;
8. `main` is pushed and tracks `origin/main`;
9. no secrets, runtime data or generated artifacts are committed;
10. the project is ready for a separate F0 implementation branch.
