Status: historical audit artifact.
Superseded for F0 implementation by F0_TECHNICAL_SPEC.md.
Do not use this file as the normative Cursor implementation specification.
Owner-review summary: docs/foundation-owner-review.md.

# Must Change Before F0

| Finding ID | Раздел исходника | Предлагаемое изменение | Причина | Ожидаемый эффект | Риск изменения | Acceptance criterion |
|---|---|---|---|---|---|---|
| AUD-001, AUD-014, AUD-029 | §6, §7.4, §8, §19–20 | Сделать vNext единственным normative F0; оставить Source, Story, Mock Package и явные non-goals. | Три несовместимых scope. | Один разработчик/agent реализует один и тот же срез. | Можно слишком ослабить editorial intent. | Lineage и непубликуемость сохранены; future principles остаются кратко. |
| AUD-002 | §7.2, §18–20 | Удалить live RSS/HTTP из F0; принимать только local fixture. | Offline requirement сейчас нарушается. | Воспроизводимый demo/tests без внешнего состояния. | Real-feed issues не проявятся. | Network guard + offline full demo; live ingestion явно F1. |
| AUD-003, AUD-006 | §7.4, §12, §19 DoD | Создавать одну Story на Source при harvest; убрать cluster/merge/review/state machine; добавить способ получить ID. | Текущий DoD не исполним. | Полный CLI flow без скрытых шагов. | Временная one-source Story semantics. | Fresh-data-dir DoD проходит; `--ids-only` возвращает один stable ID. |
| AUD-004, AUD-009, AUD-010 | §8–9, §19.4–5 | Определить content-derived IDs, immutable snapshots, constraints, schema version and fingerprint. | Нет identity/lineage/data-integrity contract. | Идемпотентность и объяснимый rebuild. | Feed metadata edit создаёт новую Story. | Revision/repeat tests дают documented counts and IDs. |
| AUD-005, AUD-017, AUD-018 | §1.2, §5, §10, §19.7–8 | Определить persisted mock package; только embedded `VENDOR_CLAIM/UNVERIFIED`; `publishable=false`. | Mock можно принять за verified placeholder. | Schema-complete demo с честной provenance. | Package не демонстрирует full editorial value. | Golden/schema/manual review подтверждают source link and warning. |
| AUD-007 | §12, §19.8 | Оставить два exports; canonical JSON, derived Markdown, exact bytes/collision/per-file atomic replacement. | Контракт противоречив и недетерминирован. | Stable golden outputs, no silent overwrite. | Не покрывает future production artifacts. | Repeat SHA-256 equal; edit fails without force; pre-replace failure preserves pair. |
| AUD-008, AUD-023, AUD-025, AUD-032 | §7.2, §10–13, §19 | Exact dependency allowlist; stdlib SQLite/XML/JSON; no YAML/provider/repository abstraction. | Alternative choices invite bloat. | Меньше кода, lockfile и RAM footprint. | Controlled RSS subset narrower. | Dependency audit matches allowlist; unsupported format fails clearly. |
| AUD-011 | §18–20 | Behavior matrix, network guard, lint/type/test, repeated E2E; remove test-count proxy. | 15 trivial tests can pass broken slice. | Evidence-backed DoD. | More precise tests take time. | Every named behavior has passing test or binary manual check. |
| AUD-012 | §2, §21 | Remove mutable platform/pricing facts from normative foundation; keep dated audit snapshot. | Regional YPP context is misleading and values decay. | Stable F0 spec. | Strategic context becomes less visible. | vNext contains no numeric platform/tool assumption; external table has URL/date/status. |
| AUD-013, AUD-019 | §1, §14–16, §22 | Separate hypothesis classes and phase evidence. | Code completion can be mistaken for market evidence. | Correct interpretation of F0 and safer roadmap. | Adds a small product table. | F0 is explicitly technical-only; non-evidence is named. |
| AUD-015, AUD-016 | §5.5, §8, §17 | Define bounded retained fields and untrusted local-input controls. | Copyright/resource/path/log risks. | Minimal data exposure and deterministic Windows behavior. | Strict fixture rejection. | Limits, DTD, URL, Markdown, log and no-write failure tests pass. |
| AUD-R2-001, AUD-R2-002, AUD-R2-011 | vNext §7 | Fix canonical bytes/preimages/digest representation; hash raw date; publish an independent vector. | Implementation-authored identities can agree with their own tests while evidence collapses. | Reproducible compatible snapshot/package IDs. | Schema-v1 identity is intentionally rigid. | Audit vector asserts exact preimages, lowercase full hashes and IDs; raw-date change creates a revision. |
| AUD-R2-003, AUD-R2-004, AUD-R2-012 | vNext §7, §9–10 | Add enforceable ID/hash/JSON checks, semantic read validation and one exact claim. | Structural prose allowed tampered rows or arbitrary claims. | Enforceable lineage rather than schema-shaped output. | Reads do extra bounded hashing/validation. | Direct-SQL tampering and zero/extra/modified claims fail without export/repair. |
| AUD-R2-005, AUD-R2-007 | vNext §10, §12–13 | State per-file—not group—atomicity; detect partial pair; require literal mock markers in both formats. | Crash semantics and human interpretation were ambiguous. | No truncated file and no silently complete-looking mixed set. | Recovery needs an explicit reviewed force. | Injected stop yields `E_EXPORT_PARTIAL`; force restores exact pair; golden markers match. |
| AUD-R2-006 | vNext §8, §10 | Remove `--provider` and provider-shaped export vocabulary from F0. | One concrete generator has no abstraction consumer. | CLI/schema match the non-goal. | Future F2 may introduce a new adapter boundary. | Help has no provider option/protocol; payload uses `generator`. |
| AUD-R2-008, AUD-R2-009, AUD-R2-010, AUD-R2-013, AUD-R2-014 | Audit trace, vNext §8, AUD-025 | Repair reference/semantic mapping/phase label; define stable domain and CLI-usage errors. | Formal trace and framework-default errors were gameable. | Machine-checkable rationale and recovery behavior. | Symbolic codes become compatibility surface. | References map correctly; AUD-025 is Later/F2; domain and usage tests assert code/action. |

# Should Change During F0

| Finding ID | Раздел исходника | Предлагаемое изменение | Причина | Ожидаемый эффект | Риск изменения | Acceptance criterion |
|---|---|---|---|---|---|---|
| AUD-026 | §7.1, §8, §18 | Implement aware UTC/RFC3339, null+raw naive dates, NFC, UTF-8 no BOM/LF and Unicode/spaces paths. | Cross-platform determinism is otherwise fragile. | Stable IDs/exports on Windows. | Over-normalization can alter intended text. | Golden Cyrillic/path/date vectors match vNext exactly. |
| AUD-027 | §19.4 | Enable FK, explicit transactions, busy timeout and non-destructive errors. | SQLite failures are undefined. | No partial/orphan writes and actionable recovery. | Timeout value may need later tuning. | Rollback/locked/incompatible/corrupt error paths preserve data. |
| AUD-004, AUD-011 | §9, §18 | Record repeat-run summaries and test all identity edge cases. | Idempotency needs observable evidence. | Easier debugging and audit. | Slight CLI-output commitment. | Mutations print counts/IDs; assertions cover same/different URL/content. |

# Defer to F1

| Finding ID | Раздел исходника | Предлагаемое изменение | Причина | Ожидаемый эффект | Риск изменения | Acceptance criterion |
|---|---|---|---|---|---|---|
| AUD-020 | §3, §14 | Owner chooses beachhead audience, primary platform and principal JTBD. | Technical F0 does not need it; pilot does. | Interpretable pilot. | A narrower wedge may miss adjacent demand. | Decision record names one segment/platform/job before pilot. |
| AUD-021, AUD-030 | §14–15 | Design exploratory pilot, metric dictionary and provisional Lesson lifecycle. | Current experiment cannot support causal claims. | Reduced false learning/survivorship bias. | Slower go/no-go. | One primary metric/variable; formulas/windows/source; lesson evidence and review state. |
| AUD-017 | §5.1–5.2 | Add evidence locator/common-origin rules, verification actor/method and claim invariants. | Full fact-checking requires human workflow. | Defensible claim ledger. | Additional editorial labor. | A reviewer traces every material claim to exact source/artifact location. |
| AUD-003, AUD-004 | §9, §16 F1 | Decide stable Story identity and manual multi-source merge. | F0 intentionally has one Story per snapshot. | Multi-source context without fuzzy automation. | Wrong merge semantics cause migration. | DEC-001 accepted and merge tests preserve Story identity. |
| AUD-002, AUD-015 | §19.5, §16 F1 | Add small allowlisted real-source ingestion only after source/retention decisions. | Network and content rights enter together. | Controlled real-data learning. | Source variability/failures. | DEC-002/003 accepted; per-source failures and retention tests exist. |
| AUD-031 | §1.1, §5.3 | Make action/visual/originality gates format-sensitive with human rationale. | Universal gate can force invented value. | Honest editorial decisions. | Review consistency. | `NOT_APPLICABLE` requires actor/reason; core evidence gate remains mandatory. |

# Defer to Later

| Finding ID | Раздел исходника | Предлагаемое изменение | Причина | Ожидаемый эффект | Риск изменения | Acceptance criterion |
|---|---|---|---|---|---|---|
| AUD-025 | §10, §13, §16 F2 | Design one real LLM adapter, prompt/version, retry/cost/raw-response rules with first provider. | Interface needs real constraints. | Smaller, evidence-driven adapter. | Later refactor of mock generator. | Provider evaluation passes on human-reviewed stories with explicit budget/data policy. |
| AUD-014 | §8.3–8.7, §16 F2/F3 | Introduce Brief/Score/Angle/Script/ProductionPlan only when manual artifacts/consumer exist. | Avoid speculative schemas and false score precision. | Models match real workflow. | Migration later. | Every new entity has owner, lifecycle, storage, use case and test. |
| AUD-028 | §5.4, §17, §16 F3/P1 | Implement rights, disclosure, correction and takedown lifecycle before production/publishing. | No assets/publication exist in F0. | Controls arrive with real risk. | Must not be forgotten. | Phase readiness blocks without owner/evidence/status transitions. |
| AUD-012 | §2, §21, §16 V1/P1 | Reverify tool licenses/prices/platform rules at decision time. | Values and policies change. | Current integration decisions. | External docs may be inaccessible. | Official URL/date/status; otherwise `EXTERNAL_VERIFICATION_REQUIRED`. |

# Remove

| Finding ID | Раздел исходника | Предлагаемое изменение | Причина | Ожидаемый эффект | Риск изменения | Acceptance criterion |
|---|---|---|---|---|---|---|
| AUD-006 | §7.4 F0 | Full state machine and transition history. | No F0 workflow consumer. | Less code and fewer contradictions. | Future migration. | No status/transition table or placeholder. |
| AUD-014 | §8.3–8.7, §19.2 | Separate future domain models and precise scoring weights in F0. | Premature policy/schema. | Smaller vertical slice. | Less impressive demo. | F0 schema has only four infrastructure/domain tables. |
| AUD-022 | §4.2, §14 | Fixed content mix and multi-output commitment as current rules. | Taxonomies conflict and demand unproven. | Pilot flexibility. | Less prescriptive roadmap. | vNext treats formats as hypotheses only. |
| AUD-023 | §11 configs, §19.3 | F0 YAML files and `doctor` optional-dependency validation. | No consumer/schema/parser. | No config framework. | Constants require code change. | No YAML runtime dependency/files required by DoD. |
| AUD-024 | §0, §11, §20 | Mandatory ADR for accepted decisions, duplicate implementation docs, wrapper directory. | Documentation overhead and path risk. | Direct implementation from vNext. | Fewer design records. | ADR only for material deviation; files remain at current root. |
| AUD-025 | §10 F0 | Generic provider Protocol and FileFixture provider. | One mock implementation. | No speculative seam. | Later extraction. | One concrete generator and no provider interface. |
| AUD-007 | §12 export | Claims/script/production YAML/MD files in F0. | Duplicate sources and future scope. | Two coherent files. | Consumers may later need migration. | Exactly JSON + Markdown under fixed export path. |
| AUD-008 | §7.2 | SQLAlchemy, Alembic, httpx, feedparser, trafilatura, RapidFuzz, Jinja2 in F0. | No required consumer. | Lower cost/startup/lockfile. | Narrow RSS support. | Dependency audit passes. |

# Preserve

| Finding ID | Раздел исходника | Решение, которое сохранить | Причина | Ожидаемый эффект | Риск | Acceptance criterion |
|---|---|---|---|---|---|---|
| — | §1, §22 | Anti-slop proof-first vision and «automate only proven process». | Core product moat. | Technical work stays tied to editorial purpose. | Could become slogan only. | vNext vision and future gates retain it. |
| AUD-013 | §3 | JTBD and author expertise in CRM/integrations/automation. | Plausible differentiation. | Better future wedge selection. | Audience still broad. | Present in vNext vision/open decision. |
| AUD-017 | §5.1–5.2 | Source hierarchy, claim types and qualifiers as future principles. | Editorial integrity. | Traceable claims later. | Over-modeling in F0. | Preserved as principles, not tables/workflow. |
| AUD-018 | §6.3 | Human gates before real editorial/publishing decisions. | Prevent unsafe automation. | Human accountability. | Gate overload. | Deferred to first real consumer, not bypassed. |
| — | §7.1–7.3 | Windows/16 GB/no GPU/no Docker, Python-first, modular monolith, SQLite. | Proportional to owner constraints. | Low operational cost. | Local limits. | vNext F0-01/architecture checks. |
| AUD-002, AUD-011 | §10, §18 | Mock-first and no network in tests. | Reproducibility and budget control. | Stable CI/demo. | Real integration issues deferred. | Network guard and offline target run. |
| — | §16 | Phase separation and no auto-publishing. | Scope safety. | Incremental learning. | Future phases still need owner discipline. | Each phase requires new approved scope. |

# Implementation Order

1. Owner accepts `PROJECT_FOUNDATION.vNext.md` as the sole F0 specification.
2. Bootstrap locked Python 3.12.x project using the dependency allowlist.
3. Implement canonicalization, normalized fixture parser and domain schemas with unit vectors.
4. Implement schema v1, transactions and deterministic Source/Story persistence.
5. Implement the five-command CLI flow and stable output summaries.
6. Implement deterministic mock package persistence and exact JSON/Markdown renderers.
7. Add failure, golden, network, Unicode/Windows and repeated E2E tests.
8. Run the complete DoD twice on the target machine and perform the binary lineage/nonpublishability review.

This order is a plan only. This audit task does not implement it.
