# F0 Minimal Scope

Status: active, derived, non-normative checklist.  
Normative source: `F0_TECHNICAL_SPEC.md`.

## Authority

1. `F0_TECHNICAL_SPEC.md` — sole normative F0 source;
2. this file — derived checklist;
3. `PROJECT_VISION.md` — product context;
4. `docs/open-decisions.md` — future decisions;
5. `docs/f0-risk-register.md` — operational risks;
6. original Foundation, vNext and Ultra-audit docs — historical context.

On conflict, the technical spec wins.

# Objective

```text
local RSS 2.0 fixture → SourceSnapshot → SQLite → Story
→ Mock StoryPackageSnapshot → JSON/Markdown
```

F0 is offline, deterministic and idempotent. It validates technical behavior only.

# Parallel Track and Timebox

```text
Track A — Content Validation:
manual research → manual script → manual production → publish → measure

Track B — Technical Foundation:
F0 → F1 → F2 → F3
```

- [ ] Technical F0 does not block the manual content pilot.
- [ ] F0 targets 2–4 focused working days.
- [ ] After core DoD, further hardening cites an observed failure or owner-approved finding.

# Target and Dependencies

- Windows 11, Python 3.12.x, Ryzen 3 5300U, 16 GB RAM.
- No GPU requirement, no Docker, one synchronous process.
- Direct runtime: Typer, Pydantic v2.
- Direct development: pytest, Ruff, mypy.
- [ ] `pyproject.toml` uses `uv_build>=0.9.30,<0.10.0` as the only approved direct build-system dependency.
- Transitively resolved packages are allowed.
- Core I/O uses the standard library.
- [ ] Dependency audit checks direct declarations, not every transitive lock entry.
- [ ] Resource report says measured, estimated or not measured; 512 MB is manual sanity only.

# Inputs

- Local regular UTF-8 or UTF-8-with-BOM RSS 2.0 fixture only.
- BOM removed before strict UTF-8 parse; other encoding fails.
- Maximum 5 MiB and 500 direct items.
- Exact `rss` → `channel` → `item` subset; Atom, DTD and ENTITY rejected before writes.
- No network, manual URL, API, secrets or YAML.
- [ ] Text/date cases reproduce every vector in spec §7.
- [ ] URL cases reproduce every vector in spec §8, including meaningful query order.

# Domain and Persistence

1. `SourceSnapshot` — immutable normalized item.
2. `Story` — exactly `id` and `primary_source_id`; no stored title.
3. `StoryPackageSnapshot` — persisted canonical mock payload.
4. `MockClaim` — exactly one embedded derived claim.

- Exactly four tables: `schema_meta`, `sources`, `stories`, `story_packages`.
- Story title is read from its immutable SourceSnapshot.
- `payload_json` uses bounded `TEXT`; SQLite JSON1 is not required.
- FK ON, explicit transactions, 5-second busy timeout.
- Whole fixture validates before writes; source revisions are immutable.
- F0 schema/data are disposable; F1 migration is not guaranteed or predesigned.
- [ ] Package build/export recompute identities and validate JSON/Pydantic/lineage.
- [ ] `stories list` does not validate the whole package graph.

# Required CLI

```text
ai-newsroom --data-dir PATH db init
ai-newsroom --data-dir PATH harvest run --fixture FILE
ai-newsroom --data-dir PATH stories list [--ids-only]
ai-newsroom --data-dir PATH package build STORY_ID
ai-newsroom --data-dir PATH package export STORY_ID --format json|markdown|all [--force]
```

- [ ] No future placeholder commands.
- [ ] Project-domain errors use the stable codes in spec §11.
- [ ] Standard Typer usage errors are non-zero, concise and traceback-free; help exits 0.

# Outputs

- `<data-dir>/exports/<story-id>/story-package.json`.
- `<data-dir>/exports/<story-id>/story-package.md`.
- JSON source object uses `canonical_url`, not `url`.
- `published_at_raw` is always present in JSON and shown in Markdown when non-null.
- Both files expose exact package/source/claim lineage.
- Markdown contains the exact MOCK, nonpublishability and warning lines.
- No runtime example or output contains a fake hash placeholder.

# Required Tests

- [ ] Text/date and URL vectors.
- [ ] Independent identity/hash reference vector: `UNCHANGED` after owner review.
- [ ] Invalid encoding/RSS/Atom/DTD/ENTITY/oversized fixture writes nothing.
- [ ] Init, harvest, build and export repeated.
- [ ] Same URL changed content; different URLs same content.
- [ ] Rollback, DB version mismatch, lock and corruption.
- [ ] Source → Story → package → sole claim lineage.
- [ ] JSON/Markdown byte goldens, Cyrillic, combining Unicode and path with spaces.
- [ ] No-network socket guard.
- [ ] Manual edit conflict/no-op/force.
- [ ] Targeted direct-SQL tamper cases at build/export.
- [ ] Deterministic injected partial-export test should pass; real process kill is not required.
- [ ] Direct dependency audit, Ruff, mypy and pytest.
- [ ] Repeated end-to-end flow has equal IDs/counts/file hashes.

# Non-Goals

- Live RSS/HTTP/manual URL.
- Clustering, merge, review queue or Claim table.
- State machine, approvals, Brief, Score, Angle, Script or ProductionPlan.
- Real LLM/provider layer, retries, costs or prompt pack.
- Migration framework, compatibility layer, YAML or ORM.
- UI/API/Docker/n8n/TTS/video/publishing/platform adapters.
- Product, editorial, audience, format or monetization validation.

# Demo Scenario

1. Use a fresh data directory and the one-item Cyrillic fixture.
2. Init, harvest and obtain Story ID with `--ids-only`.
3. Build the mock package and export both formats.
4. Confirm computed Story title, canonical URL, both date fields, hashes and sole claim lineage.
5. Confirm exact nonpublishability markers.
6. Repeat harvest/build/export and compare rows, IDs and both SHA-256 files.
7. Repeat with network blocked.

# Definition of Done

- [ ] Every command in spec §17 exits as specified on Windows 11/16 GB.
- [ ] No network, Docker or GPU requirement.
- [ ] All required behavior evidence passes; test count alone is irrelevant.
- [ ] Manual lineage/nonpublishability review passes.
- [ ] No product hypothesis is marked validated.
- [ ] Work stops after core DoD unless evidence or owner approval justifies more hardening.
