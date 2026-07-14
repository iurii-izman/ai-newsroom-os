Status: historical audit artifact.
Superseded for F0 implementation by F0_TECHNICAL_SPEC.md.
Do not use this file as the normative Cursor implementation specification.
Owner-review summary: docs/foundation-owner-review.md.

# Executive Comparison

| Область | Было | Стало | Причина | Finding IDs |
|---|---|---|---|---|
| F0 purpose | Technical slice mixed with editorial/product promises | Explicit technical-hypothesis test only | Prevent false PMF/readiness claims | AUD-013, AUD-019 |
| F0 entities | Source, Story, Claim, Score, Angle, Script, ProductionPlan, enums/transitions | SourceSnapshot, Story, StoryPackageSnapshot; embedded MockClaim | Minimum traceable slice | AUD-001, AUD-014 |
| Ingestion | Fixture plus one live RSS | Local bounded RSS 2.0 fixture only | Offline reproducibility | AUD-002 |
| Story formation | Cluster/manual merge unclear in DoD | One Story per immutable SourceSnapshot | Executable F0 flow | AUD-003, AUD-004 |
| Workflow | Full state machine through publishing/learning; F0 to production-ready | No F0 state machine; package is `MOCK`, nonpublishable | Human gates have no F0 consumer | AUD-005, AUD-006, AUD-018 |
| Data identity | Prefix examples only | Content hashes, deterministic IDs, exact revision rules | Idempotency and lineage | AUD-004, AUD-010 |
| Identity preimages | Hash intent, then incomplete vNext draft | Byte-exact serialization; lowercase digest; raw date; independent full vector | Prevent self-consistent but incompatible tests | AUD-R2-001, AUD-R2-002, AUD-R2-011 |
| Persistence | SQLite/repositories/UTC in prose | Exact schema/checks, semantic read validation, transactions, timeout, no auto-repair | Data integrity and tamper detection | AUD-009, AUD-027, AUD-R2-003, AUD-R2-012 |
| Mock claim | Source-linked shape | Exactly one deterministically derived claim with fixed semantics | Arbitrary unsupported claim cannot pass | AUD-R2-004 |
| Package | Central concept, no model/source of truth | Persisted canonical versioned payload with source fingerprints | Rebuild/explainability | AUD-005, AUD-010 |
| CLI | Nine broad commands plus inconsistent DoD | Five exact commands and global data-dir | Agent precision | AUD-003, AUD-029 |
| Exports | Two in goal, five in CLI/task | Exactly canonical JSON + derived Markdown | Remove duplication/future scope | AUD-007 |
| Export failure boundary | Atomicity unspecified | Per-file atomicity, detectable partial pair, reviewed force recovery | Honest crash semantics | AUD-R2-005 |
| Determinism | Intent only | Exact encoding/order/clock/path/overwrite behavior | Stable golden and repeat runs | AUD-007, AUD-011, AUD-026 |
| Dependencies | Alternatives and optional stack | Exact small allowlist; stdlib for core I/O | Cost and scope control | AUD-008, AUD-023, AUD-025, AUD-032 |
| Tests | Minimum 15 + broad list | Behavior matrix, network guard, failure paths, byte goldens, repeated E2E | Objective DoD | AUD-011 |
| Security/data retention | General principles | F0 file/XML/URL/path/log limits and bounded stored fields | Proportional concrete controls | AUD-015, AUD-016 |
| Product plan | Mixed hypotheses and go/no-go | Hypothesis/evidence/non-evidence table; pilot deferred | Avoid false learning | AUD-013, AUD-020, AUD-021, AUD-030 |
| External facts | Platform thresholds, prices and licenses in core | No numeric mutable assumptions in normative Foundation; dated audit snapshot | Prevent staleness/misleading regional inference | AUD-012 |
| Agent prompt | Two prompts plus full backlog | One operative execution prompt and exclusions-wins rule | Avoid convenient interpretation | AUD-001, AUD-024, AUD-029 |
| Error contract | “Understandable/actionable” prose | Stable domain/usage codes, sanitized resource and safe next action | Binary recovery-path tests | AUD-R2-009, AUD-R2-013 |
| Audit trace | Existing IDs but occasional wrong target | Registry-resolved and semantically mapped references | Reviewers reach the real rationale | AUD-R2-008, AUD-R2-014 |

# Removed Requirements

- Full F0 state machine, transition history and production-ready status (AUD-006).
- F0 tables/workflows for Claim Ledger, Brief, Score, Angle, Script and Production Plan (AUD-014).
- Exact Editorial Score weights before calibration (AUD-014).
- F0 live RSS/manual URL/network calls (AUD-002).
- F0 fuzzy clustering, entity heuristics and manual merge (AUD-003, AUD-004).
- F0 YAML source/editorial/scoring configs and optional-dependency doctor (AUD-023).
- Generic LLM provider Protocol, FileFixture provider, prompts/retries/cost/raw-response subsystem (AUD-025).
- SQLAlchemy/Alembic/httpx/feedparser/trafilatura/RapidFuzz/Jinja2 from the F0 dependency surface (AUD-008).
- `sources list`, `stories show/cluster`, `review queue` and future placeholder CLI commands (AUD-003).
- `claims.yaml`, `script.md` and `production-plan.yaml` exports (AUD-007).
- Mandatory ADR for already accepted architecture and wrapper project directory (AUD-024).
- Numeric platform thresholds, regional implications, prices and license snapshots from normative Foundation (AUD-012).
- Arbitrary «minimum 15 tests» as a completion proxy (AUD-011).

# Simplified Requirements

- RSS scope is one controlled local RSS 2.0 subset; broad feed compatibility is F1.
- Story is one-to-one with a SourceSnapshot in F0; multi-source identity/merge is an owner decision before F1.
- Workflow is existence-based: Source → Story → Package. No status machine.
- Package generator is one concrete deterministic mock, not a provider framework.
- CLI and payload use generator terminology; the unused F0 provider seam is gone (AUD-R2-006).
- SQLite access is one concrete stdlib infrastructure module, not an abstract repository hierarchy.
- Configuration is CLI input/defaults, not three YAML files.
- Export is two coherent files with one canonical payload.
- Future phases are short evidence gates, not predesigned schemas/adapters.

# Strengthened Requirements

- Source identity, revisions, unique constraints and Story identity are deterministic (AUD-004, AUD-009, AUD-010).
- Identity serialization/preimages and one-claim derivation are byte-exact, with raw dates, lowercase digests and an independent vector (AUD-R2-001–AUD-R2-004, AUD-R2-011).
- Mock output is visibly nonpublishable and cannot emit a verified fact (AUD-005, AUD-017, AUD-018).
- Every claim demonstration links to an existing source ID and full content hash (AUD-005, AUD-017).
- JSON/Markdown bytes, ordering, Unicode, newlines, timestamps and absolute paths are specified (AUD-007, AUD-026).
- Markdown has literal mock/nonpublishability markers; multi-file interruption is detected without claiming group atomicity (AUD-R2-005, AUD-R2-007).
- SQLite transactions, FK, busy timeout, incompatible/corrupt behavior and no-destructive fallback are specified (AUD-009, AUD-027).
- DDL shape checks plus read-time recomputation reject direct tampering before export (AUD-R2-012).
- Fixture size/items/XML entities/URLs/control chars/paths/log data are bounded (AUD-015, AUD-016).
- Tests cover behavior, failures, network isolation, goldens, repeat runs and target machine constraints (AUD-011).
- Expected domain and Typer usage failures assert stable symbolic code and recovery action, not only non-zero (AUD-R2-009, AUD-R2-013).
- F0 evidence is explicitly prevented from validating audience/format/monetization hypotheses (AUD-013).

# Deferred Requirements

- F1: source allowlist/live ingestion, content retention decision, multi-source Story merge, evidence locators, Claim review and first human gate.
- Content pilot: beachhead audience, primary platform, metric dictionary, exploratory design and provisional lessons.
- F2: first real provider, prompt/evaluation, cost/retry/data boundary.
- F3: Brief/Score/Angle/Script/ProductionPlan, originality artifact, asset rights and AI disclosure.
- V1/P1: video and publishing adapters plus current policy re-verification.

# New Blocker-Level Requirements

- F0 runtime/demo/tests have no network connections.
- F0 implements only the explicit entity/command/dependency whitelist.
- Fresh-data-dir DoD produces a Story ID without an unlisted cluster/merge step.
- Same input twice yields identical IDs, row counts and export hashes.
- Invalid fixture fails before any database write.
- Mock package is `generation_mode=MOCK`, `publishable=false` and carries a fixed warning.

# Preserved Decisions

- Anti-AI-slop, proof-first product vision.
- Russian-language audience focused on practical AI for work/business.
- Author differentiation through CRM, integrations, automation and business processes.
- Source-backed claims, qualifiers and LLM-not-a-source principle.
- Human gates before any real verification/production/publishing decision.
- Python-first modular monolith, SQLite, one process.
- Windows 11 / 16 GB / no GPU / no Docker target.
- Mock-first and no network in tests.
- Manual publishing and staged automation.
- «Автоматизировать только доказанный процесс».
