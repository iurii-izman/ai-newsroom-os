# Foundation Owner Review

Status: active, non-normative owner-review summary.  
Date: 13 July 2026.

## Outcome

Owner review converted the Ultra-audit candidate into one final implementation contract: `F0_TECHNICAL_SPEC.md` version `0.6-owner-reviewed`, status `READY_FOR_F0`. This task changed Markdown only; F0 was not implemented.

## Authoritative Document Order

1. `F0_TECHNICAL_SPEC.md` — sole normative source for F0;
2. `docs/f0-minimal-scope.md` — derived non-normative checklist;
3. `PROJECT_VISION.md` — non-normative product context;
4. `docs/open-decisions.md` — future owner decisions;
5. `docs/f0-risk-register.md` — operational risks;
6. original Foundation, vNext and Ultra-audit documents — historical context.

If documents conflict, `F0_TECHNICAL_SPEC.md` wins for F0.

## Owner Corrections Applied

| ID | Final correction |
|---|---|
| OWN-001 | Fixed Windows 11/Python 3.12.x/Ryzen 3 5300U/16 GB/no GPU/no Docker/single-process target. The 512 MB value is a manual sanity target, never a flaky gate; reports label resource evidence measured, estimated or not measured. |
| OWN-002 | Dependency rules now distinguish project-declared direct dependencies from allowed transitives; core I/O is standard library. |
| OWN-003 | F0 schema/data are disposable; no F1 migration, aliases or compatibility layer are predesigned. |
| OWN-004 | Encoding, controlled RSS subset, XML text extraction, title/summary normalization, forbidden controls and date behavior now have exact order and vectors. |
| OWN-005 | URL validation/canonicalization now fixes IDNA, IPv6, ports, path, tracking removal, duplicate/blank query values and preservation of meaningful query order. |
| OWN-006 | `Story` stores only `id` and `primary_source_id`; title is always derived from immutable SourceSnapshot. |
| OWN-007 | Export source uses `canonical_url`, always includes `published_at_raw`, avoids fake runtime hashes and makes Markdown fields/markers explicit. |
| OWN-008 | SQLite DDL has no JSON1 dependency; application code owns JSON/Pydantic/semantic validation. |
| OWN-009 | Stable codes remain for project-domain failures; Typer/Click syntax errors use proportional framework usage behavior without a custom parser layer. |
| OWN-010 | Full identity/payload recomputation is limited to package build/export; `stories list` does not validate the entire package graph. |
| OWN-011 | Export promises per-file atomic replacement and obvious partial-pair recovery, not group atomicity or mandatory process-kill simulation. |
| OWN-012 | Manual content validation runs in parallel; F0 is timeboxed to 2–4 focused days and post-DoD hardening requires evidence or owner approval. |

## Active Documents

- `PROJECT_VISION.md`;
- `F0_TECHNICAL_SPEC.md`;
- `docs/f0-minimal-scope.md`;
- `docs/open-decisions.md`;
- `docs/f0-risk-register.md`;
- this owner-review summary.

## Historical Evidence

Retained without content rewrite:

- `PROJECT_FOUNDATION.md` — original product foundation;
- `PROJECT_FOUNDATION.vNext.md` — Ultra-audit candidate;
- `docs/foundation-audit.md`;
- `docs/foundation-change-plan.md`;
- `docs/foundation-diff-summary.md`.

Historical files are not F0 implementation instructions.

## Reference Vector

Disposition: `UNCHANGED`.

All dependent values remain identical:

- content hash: `e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d`;
- source ID: `src_58343a9a5ffae3037a3f73bf`;
- Story ID: `story_55c2bc7f60628d20cb9acd4c`;
- claim ID: `claim_11806810946d69ba4de2ccd4`;
- input fingerprint: `bd9e982b780c713eaad078c3129e6ddebec56fcc6b5cba0bf951547ae31fda8f`;
- package ID: `pkg_17e9b7502f7bc00db437b993`.

Reason: vector strings were already normalized under the clarified rules, the canonical URL is unchanged, `Story.title` was never an identity input, and no identity algorithm changed.

