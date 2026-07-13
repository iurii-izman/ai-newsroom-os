# F0 Risk Register

Status: active operational risk register. Normative controls live in `F0_TECHNICAL_SPEC.md`.

Probability and Impact use `LOW`, `MEDIUM`, `HIGH`.

| ID | Risk | Probability | Impact | Early Signal | Mitigation | Owner | Phase |
|---|---|---:|---:|---|---|---|---|
| RSK-001 | Scope creep reintroduces future entities, commands or abstractions | HIGH | HIGH | New placeholder modules/tables or direct dependency outside whitelist | Treat `F0_TECHNICAL_SPEC.md` scope/non-goals as acceptance gates; stop on conflict | Project owner + developer | Before/during F0 |
| RSK-002 | Hidden network call enters parser, test or demo | MEDIUM | HIGH | Test hangs/fails offline; HTTP client/import appears | Local-path-only parser; socket-blocking test guard; dependency audit | Developer | During F0 |
| RSK-003 | Ambiguous identity causes duplicates or overwritten evidence | MEDIUM | HIGH | Row counts grow on repeat; malformed/naive raw date changes without a new identity | Exact canonical preimages including `published_at_raw`, immutable IDs, constraints and revision vectors | Developer | During F0 |
| RSK-004 | Nondeterministic package/export creates flaky tests and unreproducible demo | HIGH | HIGH | SHA-256 differs between isolated/repeated runs | Exclude time/path/order/randomness; canonical JSON; golden bytes | Developer | During F0 |
| RSK-005 | Mock output is mistaken for verified or publishable content | MEDIUM | HIGH | `VERIFIED`, `APPROVED` or production-ready language appears | Fixed `MOCK`, `publishable=false`, warning and manual binary review | Editorial owner | F0 handoff |
| RSK-006 | Invalid fixture, crash or SQLite lock leaves partial data | MEDIUM | HIGH | Orphan rows, mismatched counts, truncated file or mixed JSON/Markdown pair | Validate before transaction; FK/rollback/timeout; per-file temp+replace; detect `E_EXPORT_PARTIAL` and require reviewed force recovery | Developer | During F0 |
| RSK-007 | Unsafe/unbounded XML/text/path violates 16 GB or Windows constraints | LOW | HIGH | Large memory spike, invalid path, Markdown/control-char artifacts | 5 MiB/500-item limits, reject DTD/entities, hash paths, escaping | Developer | During F0 |
| RSK-008 | Dependency/environment inflation breaks low-cost target | MEDIUM | MEDIUM | Project declares an unapproved direct dependency; startup/working set grows | Audit direct dependencies only; allow their transitives; 512 MB is a manual sanity target with honest measurement status | Developer | F0 verification |
| RSK-009 | Manual export edit or incompatible DB is silently overwritten/recreated | LOW | HIGH | Lost edit/data after rerun or version change | Refuse differing export without force; no auto-migrate/repair/recreate | Developer + owner | During F0 |
| RSK-010 | Passing tests creates false product-readiness confidence | MEDIUM | HIGH | Report says format/audience validated after mock demo | Technical-only hypothesis statement and nonpublishability checklist | Project owner | F0 acceptance |
| RSK-011 | Specification drift between historical artifacts, spec and checklist | MEDIUM | HIGH | Implementation cites original/vNext instead of the final spec | One normative source; banners on historical docs; derived-checklist consistency QA | Project owner | Before F0 |
| RSK-012 | Self-authored tests or shape-only reads accept incompatible/tampered identity data | MEDIUM | HIGH | Digest differs, generator changes claim, or direct-SQL edit still exports | Audit-owned vector, DDL shape checks and targeted recomputation before package build/export | Developer + editorial owner | During F0 |
| RSK-013 | CLI framework usage output becomes overengineered or opaque | MEDIUM | MEDIUM | Custom parser/error layer appears, or syntax errors show traceback/no guidance | Keep standard Typer/Click usage; test non-zero, concise guidance, no traceback and help exit 0 | Developer | During F0 |
| RSK-014 | Engineering F0 delays manual content validation | HIGH | HIGH | No pilot videos are published while F0 expands beyond the whitelist or continues hardening after DoD passes | Timebox F0 to 2–4 focused working days; run Track A in parallel; stop hardening after DoD unless an observed failure or owner-approved finding exists | Project owner | F0 and content pilot |
