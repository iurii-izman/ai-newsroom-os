Status: historical audit artifact.
Superseded for F0 implementation by F0_TECHNICAL_SPEC.md.
Do not use this file as the normative Cursor implementation specification.
Owner-review summary: docs/foundation-owner-review.md.

# Executive Summary

`PROJECT_FOUNDATION.md` содержит сильное продуктовое и редакционное ядро, но не готов как однозначная инструкция для Foundation Sprint F0. Главная проблема — не отсутствие идей, а одновременное присутствие трёх разных scope: минимального offline vertical slice, полного editorial workflow до `PRODUCTION_READY` и будущей media/production платформы. Автономный coding agent может добросовестно выполнить любой из них и формально сослаться на документ.

Итог первого прохода девяти ролей: исходный F0 — `NO-GO` до исправления AUD-001–AUD-003. После синтеза выбран минимальный компромисс: сохранить proof-first lineage внутри явно непубликуемого mock package, но не создавать отдельные будущие сущности, workflow и abstractions. Независимый второй проход и его финальная consistency-проверка нашли ещё 14 дефектов контракта (`AUD-R2-001`–`AUD-R2-014`); все исправлены до рекомендации `READY_FOR_F0`.

## Карта документа

| Область | Где | Назначение | Нормативный? | F0? | Дубли/конфликт | Сократить? | Объективная проверка |
|---|---|---|---|---|---|---|---|
| 1. Vision | §1, §22 | Позиционирование и критерий успеха | Смешанный | Косвенно | Повторяется; не конфликтует | Да, объединить | Только через будущий pilot |
| 2. Product assumptions | §2, §14–15 | Платформенные допущения и learning | Смешанный | Нет | Изменчивые факты смешаны со стратегией | Сильно | Сейчас частично нет |
| 3. Audience | §3 | Target/JTBD/moat | Описательный | Нет | Beachhead не выбран | Умеренно | F1 pilot |
| 4. Content system | §4, §14–15 | Форматы, proof-first, experiments | Смешанный | Нет | Mix не совпадает с cohorts | Да | После metric dictionary |
| 5. Editorial rules | §5, §13, §17, §22 | Sources, claims, gates | Нормативный | Только lineage | Gates конфликтуют с mock F0 | Да, разделить по фазам | Частично |
| 6. Technical architecture | §7, §10–11 | Среда, stack, layers | Нормативный | Да | Альтернативы и лишние deps | Да | После выбора stack |
| 7. F0 scope | §6, §19–20 | Execution scope | Нормативный | Да | Три несовместимых версии | Критически | Нет до переписывания |
| 8. Future phases | §6.2, §16 | Roadmap | Описательный | Нет | Будущие модели уже обязательны в F0 | Да | Phase gate отсутствует |
| 9. Domain entities | §5.2, §8 | Data contracts | Пример выглядит нормативным | Частично | Story Package отсутствует; будущих сущностей много | Да | Нет constraints/lifecycle |
| 10. State machine | §7.4 | Workflow | Нормативный | Заявлено до production | Нет команд/preconditions | Удалить из F0 | Нет |
| 11. CLI | §12, §19 DoD, §20 | User contract | Нормативный | Да | 9 команд, 6 в DoD, missing merge/cluster step | Да | Текущий DoD не исполним |
| 12. Configuration | §11, §12, §19.3 | YAML/doctor | Нормативный | Заявлено | Нет schema/defaults/consumer | Удалить из F0 | Нет |
| 13. Testing | §18–20 | Quality gates | Нормативный | Да | Count proxy; commands неполны | Переписать | Частично |
| 14. Security | §0, §10, §17 | Secrets/untrusted/high risk | Нормативный | Частично | Future risks смешаны с fixture risks | Разделить | Частично |
| 15. External dependencies | §2.7, §7.2, §21 | Stack, prices, sources | Смешанный | Частично | Mutable facts в core | Сильно | Только датированный review |
| 16. Definition of Done | §19, §20 | Completion | Нормативный | Да | Missing cluster/ID; нет lint/type | Переписать | Сейчас нет |
| 17. Cursor instructions | §0, §20 | Agent execution | Нормативный | Да | Повторяются и конфликтуют | Один prompt | Сейчас нет |
| 18. Open decisions | Разбросаны | Owner choices | Отсутствует | Да/F1 | SQL layer/type checker/provider скрыты как alternatives | Создать реестр | Да, owner decision |

# Readiness Score

| Измерение | Исходник | vNext | Комментарий |
|---|---:|---:|---|
| Product clarity | 7.5 | 8.8 | Vision сильна; vNext разделяет гипотезы |
| F0 scope | 2.5 | 9.5 | В исходнике scope конфликтует; vNext имеет whitelist/non-goals |
| Editorial integrity | 8.0 | 8.8 | Сохранена lineage без ложного verification |
| Architecture proportionality | 4.0 | 9.2 | Убраны premature layers/dependencies |
| Data integrity | 3.0 | 9.1 | Определены snapshots, constraints, transactions |
| Determinism | 3.0 | 9.5 | Определены IDs, bytes, ordering, clock boundary |
| Testability | 4.5 | 9.1 | Behavior matrix вместо «15 тестов» |
| Security/legal proportionality | 6.0 | 8.7 | F0 risks отделены от future publishing |
| Cost/resource fit | 5.0 | 9.5 | Runtime allowlist и single-process target |
| AI-agent readiness | 3.0 | 9.3 | Один normative prompt и исполнимый DoD |
| **Итого** | **4.7 / 10** | **9.2 / 10** | vNext готов к F0 после owner acceptance документа |

# Главные сильные стороны

- Ясное анти-slop позиционирование и proof-first редакционная идея.
- JTBD «быть в курсе / применять / не попасться на хайп» связаны с реальной экспертизой автора.
- Source tiers, claim taxonomy, qualifiers, rights и human-review намерения создают хороший future foundation.
- Модульный монолит, SQLite, Python-first, Windows/16 GB и no-Docker — пропорциональные ограничения.
- Mock-first и no-network tests — правильное направление.
- Документ прямо признаёт: технический pipeline и один viral video не доказывают продукт.
- Future embeddings, video и publishing уже отложены до evidence.

# Blockers

| ID | Severity | Category | Location | Проблема | Реальный риск | Минимальное решение | Decision |
|---|---|---|---|---|---|---|---|
| AUD-001 | BLOCKER | AI_AGENT_INSTRUCTIONS | §6.1, §7.4, §8, §19.2, §20 | F0 одновременно минимальный slice, полный набор editorial entities и путь до `PRODUCTION_READY`. | Агент реализует почти весь roadmap, либо разные реализации будут несовместимы; высокий rework. | Один normative whitelist: Source, Story, Mock Story Package, SQLite, JSON/Markdown; всё остальное explicit non-goal. | FIX_BEFORE_F0 |
| AUD-002 | BLOCKER | IMPLEMENTATION | §7.2, §18, §19.5, §19 DoD, §20 | Offline/no-network конфликтует с «одним реальным RSS», httpx/feedparser и external verification формулировками. | Hidden network call ломает reproducibility, tests и demo без интернета. | F0 принимает только local RSS fixture bytes/path; live ingestion и HTTP deps перенести в F1. | FIX_BEFORE_F0 |
| AUD-003 | BLOCKER | AI_AGENT_INSTRUCTIONS | §12, §19.6, §19 DoD | DoD не вызывает clustering, manual merge command отсутствует, `STORY_ID` не получается формально, а review queue относится к F1. | Буквальный flow даёт пустой Story list или требует неописанные ручные действия; готовность объявляется формально. | Создавать одну Story на Source при harvest, дать `stories list --ids-only`, убрать merge/review и зафиксировать полный исполнимый flow. | FIX_BEFORE_F0 |

# High-Risk Findings

| ID | Severity | Category | Location | Проблема | Реальный риск | Минимальное решение | Decision |
|---|---|---|---|---|---|---|---|
| AUD-004 | HIGH | DATA | §8.1–8.2, §9, §19.4–5 | ID, unique keys, GUID fallback, same URL/changed content и Story identity не определены. | Дубли, silent overwrite evidence, нестабильные IDs и повреждённая lineage. | Content-addressed immutable SourceSnapshot; Story ID от source ID; documented F0 non-merge policy. | FIX_BEFORE_F0 |
| AUD-005 | HIGH | ARCHITECTURE | §1.2, §8, §10, §19.7–8 | Центральный Story Package не определён как stored contract; mock/file fixture/placeholder границы нет. | Одна статическая константа для любого Story формально проходит schema test; build/export используют разные truths. | Один persisted versioned package payload, привязанный к Story/source hashes; `MOCK`, `publishable=false`, warning. | FIX_BEFORE_F0 |
| AUD-006 | HIGH | ARCHITECTURE | §6.3, §7.4, §12, §19 | Full state machine и five human gates не имеют команд, actors, preconditions или обратных переходов. | Агент обходит approvals либо не может завершить demo; mock ошибочно становится production-ready. | Не реализовывать state machine/gates в F0; existence-based flow и nonpublishable package. | REMOVE |
| AUD-007 | HIGH | DATA | §12 export, §19.8 | F0 требует то два, то пять файлов; schema/encoding/order/current-time/atomicity/force semantics не определены. | Partial/mixed exports, golden flakiness, silent loss of manual edits. | Canonical persisted JSON + derived Markdown; exact bytes, stable order, preflight, temp+replace, collision rules. | FIX_BEFORE_F0 |
| AUD-008 | HIGH | COST | §7.2, §9–10, §19 | `SQLAlchemy или repository`, two type-checkers, httpx, trafilatura, RapidFuzz, Jinja2 и two mock providers оставляют случайный stack. | Dependency bloat и speculative abstractions без F0 consumer. | Exact allowlist; stdlib SQLite/XML/JSON; Typer/Pydantic runtime; pytest/ruff/mypy dev. | FIX_BEFORE_F0 |
| AUD-009 | HIGH | DATA | §8, §19.4 | Nullability, cardinality, FK/unique constraints, schema version и canonical source-of-truth отсутствуют. | Orphans, incompatible DB opened silently, impossible reproducibility. | Schema v1 with explicit tables/constraints, canonical package JSON and incompatible-version failure. | FIX_BEFORE_F0 |
| AUD-010 | HIGH | DATA | §8.1–8.2, §17 corrections, §19.7–8 | Source revision, package freshness and input fingerprint are undefined. | Package points to evidence that changed after build; old result cannot be explained. | Immutable snapshots plus full source hashes/input fingerprint; operational timestamps excluded from output. | FIX_BEFORE_F0 |
| AUD-011 | HIGH | TESTING | §18–20 | «15 meaningful tests» is gameable; no pass/fail outcomes for determinism, failures, content, lint/type or second run. | Trivial enum tests satisfy count while vertical slice is broken. | Behavior matrix, network guard, golden bytes, failure tests, repeated E2E, ruff/mypy/pytest. | FIX_BEFORE_F0 |
| AUD-012 | HIGH | PLATFORM | §2, §21 | Mutable platform rules/prices are embedded in Foundation. YPP 500 threshold is juxtaposed with Moldova general YPP availability, although Moldova is absent from expanded-YPP country list on 2026-07-13. | Owner may plan against an unavailable regional tier; document becomes stale and misleading. | Remove numeric external facts from normative core; maintain dated external snapshots and recheck immediately before integration. | REMOVE |
| AUD-013 | HIGH | PRODUCT | §1, §3, §14–15, §19, §22 | Technical, editorial, audience, format, monetization and lead-generation hypotheses are conflated. | Successful JSON/demo or noisy views are mistaken for PMF/business validation. | Hypothesis table: phase, evidence and explicit non-evidence; F0 validates only technical repeatability. | FIX_BEFORE_F0 |
| AUD-014 | HIGH | PRODUCT | §8.3–8.7, §19.2 | Brief/Score/Angle/Script/ProductionPlan and precise score weights are mandatory before process/data exist. | Schema locks untested editorial assumptions and causes rework after manual pilot. | Remove separate entities/score from F0; embed only one mock claim for lineage; revisit with real consumer. | REMOVE |
| AUD-015 | HIGH | LEGAL | §5.5, §8.1, §10, §17 | «Не хранить полный текст без необходимости» lacks retention limits, owner and exact F0 stored fields. | Copyright/privacy exposure and uncontrolled database growth. | F0 stores only normalized RSS metadata and bounded plain-text summary; no raw XML/HTML/PDF/LLM response. | FIX_BEFORE_F0 |
| AUD-016 | HIGH | SECURITY | §8–12, §17 | No limits or rules for XML entities, file size, invalid URLs, control chars, Markdown injection, unsafe filenames or error logging. | Memory abuse, path problems on Windows, malicious exports or sensitive/raw content in logs. | Local regular-file/size/item limits, reject DTD/entities, URL allowlist, fixed hash paths, escaped Markdown, bounded logs. | FIX_BEFORE_F0 |
| AUD-017 | HIGH | EDITORIAL | §5.1–5.2, §8.6, §13 | Tier A conflates primariness with truth; claim status/confidence/evidence locator semantics are undefined; mock may emit `VERIFIED`. | Vendor claim becomes «verified fact» and cannot be traced to exact evidence. | Mock emits only `VENDOR_CLAIM/UNVERIFIED` with source ID/hash; full verification model deferred to F1. | FIX_BEFORE_F0 |
| AUD-018 | HIGH | EDITORIAL | §2.4, §5.3, §6.3 | Publication/originality/visual gates apply to F0 mock, yet cannot be satisfied; «two own-value elements» is formally gameable. | Placeholder is mislabeled production-ready or decorative AI-slop passes a checkbox. | Mark F0 nonpublishable; move publication gates to first publishing consumer and require referenced original artifact + human verdict. | FIX_BEFORE_F0 |
| AUD-019 | HIGH | PRODUCT | §14–16 | Roadmap has code phases but no manual content-pilot gate; phase completion may be treated as evidence to automate next phase. | Technical momentum automates an unvalidated format. | State phase evidence: F0 technical only; manual F1/pilot before LLM/video; future work owner-approved anew. | FIX_BEFORE_F0 |

# Medium and Low Findings

| ID | Severity | Category | Location | Проблема | Реальный риск | Минимальное решение | Decision |
|---|---|---|---|---|---|---|---|
| AUD-020 | MEDIUM | PRODUCT | §3, §14 | Audience spans several professions; primary platform/beachhead are not selected. | Small pilot mixes audience/platform effects and cannot explain results. | Decide one initial wedge and platform before content pilot, not before technical F0. | DEFER_TO_F1 |
| AUD-021 | MEDIUM | CONTENT | §14–15 | 8–10 per format, own median, several metrics and seven factors do not support causal go/no-go. | Random winner becomes permanent automation rule; survivorship bias. | Label exploratory; one variable, one primary metric, comparable windows, qualitative review. | DEFER_TO_F1 |
| AUD-022 | MEDIUM | CONTENT | §4.1–4.2, §14, §1.2 | 40/30/20/10 category mix does not map to equal three-format cohorts; multi-output package is untested. | Planning and analysis taxonomies diverge; extra outputs add cost. | Remove fixed mix; pilot one video output plus at most one manual owned-channel derivative. | REMOVE |
| AUD-023 | MEDIUM | DOCUMENTATION | §11, §12 doctor, §19.3 | Three YAML configs and optional dependencies lack schema/defaults/real F0 consumer. | Generic config subsystem and accidental YAML dependency. | Use CLI fixture/data paths and code constants in F0; configs in F1 with consumer. | REMOVE |
| AUD-024 | MEDIUM | AI_AGENT_INSTRUCTIONS | §0, §11, §20 | Repository tree wrapper and mandatory ADR/implementation docs can create nested repo and paperwork for decided choices. | Time spent on duplicate documents; files placed under wrong root. | Existing root only; ADR only for material deviation/unresolved choice. | REMOVE |
| AUD-025 | MEDIUM | ARCHITECTURE | §10, §13, §19.7 | Generic LLM Protocol, FileFixture provider, prompt pack, retries/raw responses/cost appear before a real provider. | Placeholder architecture becomes a frozen API with no validated consumer. | One concrete mock generator; provider seam designed with first real provider in F2. | DEFER_TO_LATER |
| AUD-026 | MEDIUM | IMPLEMENTATION | §7.1, §8, §18 | UTC, naive dates, Windows paths, Unicode, BOM/LF and absolute-path effects are unspecified. | Platform-dependent IDs/golden files and datetime errors. | RFC3339 Z/null+raw policy, NFC, UTF-8 no BOM/LF, pathlib, Unicode/spaces tests. | FIX_DURING_F0 |
| AUD-027 | MEDIUM | OPERATIONS | §19.4, DoD | SQLite busy/corrupt/incompatible behaviors and recovery ownership are absent. | Silent recreate, partial data or confusing failures. | FK ON, busy timeout, explicit transactions; fail without auto-repair/migration. | FIX_DURING_F0 |
| AUD-028 | MEDIUM | LEGAL | §5.4, §17 | `rights_status=UNKNOWN` can coexist with `allowed_for_commercial_use=true`; correction/takedown owner/lifecycle absent. | Future publish gate can allow unknown-rights asset or fail to correct content. | Derive permission from evidence; design rights/correction lifecycle with first production/publish consumer. | DEFER_TO_LATER |
| AUD-029 | MEDIUM | DOCUMENTATION | §0, §6, §19–20 | MVP, Foundation, F0, editorial MVP and duplicated Cursor prompts have different implied scopes. | Agent chooses a convenient interpretation and expands scope. | One operative vNext, one F0 definition, one Cursor execution prompt. | FIX_BEFORE_F0 |
| AUD-030 | MEDIUM | DATA | §14–15 | Metrics lack definitions/denominators; Lesson lacks evidence set, scope, status, owner and review date. | Incomparable platform data becomes permanent «learning». | Metric dictionary and provisional/retired human lessons only in pilot phase. | DEFER_TO_F1 |
| AUD-031 | MEDIUM | EDITORIAL | §1.1, §5.3 | Every story requires action today and visual proof, even where honest answer is not applicable. | Editor invents action/decorative visual or discards important consequence story. | Format-sensitive gates with `NOT_APPLICABLE` + human rationale. | DEFER_TO_F1 |
| AUD-032 | LOW | IMPLEMENTATION | §7.2, §18–20 | `Python 3.12+` and «current compatible versions» are unbounded; install network and offline runtime are conflated. | Lockfile/environment differs between agents and future Python releases. | Pin F0 to Python 3.12.x; lock dependencies; explicitly separate installation from offline execution. | FIX_BEFORE_F0 |

# Second Independent Red-Team Review

| ID | Severity | Category | Location | Проблема | Реальный риск | Минимальное решение | Decision |
|---|---|---|---|---|---|---|---|
| AUD-R2-001 | HIGH | DATA | vNext §7.2–7.3 | Package fingerprint/ID and claim ID lacked byte-exact canonical preimages. | Self-authored tests could bless incompatible identities and hide nondeterminism. | Define canonical JSON bytes, every literal/preimage and fixed unit vectors. | FIX_BEFORE_F0 |
| AUD-R2-002 | HIGH | DATA | vNext §7.2–7.3 | `published_at_raw` was preserved but excluded from `content_hash`. | Two distinct malformed/naive source dates could collapse into one snapshot and lose evidence. | Include normalized raw date or null in canonical item content. | FIX_BEFORE_F0 |
| AUD-R2-003 | HIGH | DATA | vNext §9 | Named SQLite schema omitted enforceable nullability/check/singleton details. | Invalid or ambiguous rows could satisfy prose while breaking lineage. | Specify types, `NOT NULL`, `CHECK`, unique/FK constraints and singleton open validation. | FIX_BEFORE_F0 |
| AUD-R2-004 | HIGH | EDITORIAL | vNext §4, §7, §10 | Claim only had a source link; exact derivation and cardinality were open. | Arbitrary unsupported text could pass a structural lineage test. | Require exactly one fixed-text/type/status/qualifier claim linked only to the Story source. | FIX_BEFORE_F0 |
| AUD-R2-005 | HIGH | OPERATIONS | vNext §10, §12 | Per-file atomic replace was conflated with two-file group preservation. | Process termination between replaces can leave a mixed export set that appears complete. | Promise per-file atomicity only; detect mixed set as `E_EXPORT_PARTIAL`; reviewed force recovery. | FIX_BEFORE_F0 |
| AUD-R2-006 | MEDIUM | ARCHITECTURE | vNext §8, §10 | CLI/JSON exposed a provider seam while provider abstraction was forbidden. | Placeholder vocabulary freezes an API with one implementation and contradicts scope. | Remove CLI provider option; use one concrete generator and `generator` payload field. | FIX_BEFORE_F0 |
| AUD-R2-007 | MEDIUM | TESTING | vNext §10, §13 | Checklist required both exports to show mock flags, but Markdown exact literals were not normative. | A weak warning could pass while a reader misses nonpublishability. | Require and golden-test literal mode, publishability and warning lines in Markdown. | FIX_BEFORE_F0 |
| AUD-R2-008 | MEDIUM | DOCUMENTATION | vNext Audit Traceability | Traceability referenced a finding number absent from the audit registry. | Audit chain was formally broken and could conceal an unreviewed change. | Correct the reference and machine-check every `AUD-*` target. | FIX_BEFORE_F0 |
| AUD-R2-009 | MEDIUM | IMPLEMENTATION | vNext §8–§11 | “Actionable/understandable error” was tested only as non-zero. | Agent could emit unstable or useless errors and still pass DoD. | Stable symbolic codes plus sanitized resource and safe next action; assert them. | FIX_BEFORE_F0 |
| AUD-R2-010 | LOW | DOCUMENTATION | Audit AUD-025 | Decision said F1 while its own solution and roadmap place first real provider in F2. | Implementation planning receives contradictory timing. | Classify AUD-025 as `DEFER_TO_LATER` and keep F0 provider-free. | FIX_BEFORE_F0 |
| AUD-R2-011 | HIGH | DATA | vNext §7.3 | Digest case/length/prefix and an independent fixed vector were still unspecified. | Two incompatible hash representations could pass implementation-authored vectors. | Define 64 lowercase hex/no prefix, 24-char ID suffixes and publish one complete reference vector. | FIX_BEFORE_F0 |
| AUD-R2-012 | HIGH | DATA | vNext §9 | DDL allowed malformed IDs/hashes/JSON; tamper acceptance was promised but not enforceable. | Direct-SQL corruption could remain readable/exportable while tests pass. | Add format/JSON checks and recompute every identity/payload relation on read; fail `E_DB_SCHEMA`. | FIX_BEFORE_F0 |
| AUD-R2-013 | MEDIUM | IMPLEMENTATION | vNext §8 | Stable error registry omitted Typer usage errors. | Missing/unknown arguments could bypass `[CODE]` and safe-action contract. | Add `E_USAGE` and exact tests for missing argument, unknown command/option and invalid enum. | FIX_BEFORE_F0 |
| AUD-R2-014 | LOW | DOCUMENTATION | vNext trace references | Several valid finding IDs were attached to semantically unrelated changes. | Trace exists formally but sends reviewers to the wrong rationale. | Remap analytics, content-mix, workflow and rights findings to their actual sections. | FIX_BEFORE_F0 |

Second-pass disposition: all fourteen findings are reflected in vNext, F0 checklist, change plan and/or risk register; none remains an owner blocker for F0.

# Противоречия

| Finding IDs | Утверждение A | Утверждение B | Решение synthesis |
|---|---|---|---|
| AUD-001, AUD-014 | F0 is minimal fixture slice | F0 implements full entities/transitions to production-ready | Minimal three-object slice wins |
| AUD-002 | Tests/demo require no network | F0 harvests one real RSS and lists HTTP stack | Fixture-only F0; network F1 |
| AUD-003 | DoD goes harvest → list | Story requires cluster; merge has no CLI | One Story per Source in F0 |
| AUD-005, AUD-018 | Human gates never bypassed | Mock package must complete DoD | Mock is schema-complete but explicitly nonpublishable |
| AUD-007 | Goal names JSON/Markdown | CLI/export task names five files | Exactly two F0 files |
| AUD-008 | Minimal local stack | Alternatives/optional tools invite all dependencies | Exact allowlist |
| AUD-012 | 500-subscriber tier stated beside Moldova YPP availability | Official expanded-YPP list omits Moldova | Do not imply early tier; remove changing thresholds |
| AUD-022 | Fixed category mix | Equal format cohorts | Both become future exploratory choices |

# Избыточность и Scope Creep

| Компонент | F0 use | Решение | Причина |
|---|---|---|---|
| Source / Story | Да | Keep, minimal | Vertical slice and lineage |
| Mock claim | Да, embedded | Keep as value object | Proves evidence link without Claim workflow |
| Claim table/Ledger | Нет | F1 | Needs human verification process |
| Brief / Score / Angle / Script / ProductionPlan | Нет | Remove from F0 | No validated consumer; false precision |
| Full state machine / transition history | Нет | Remove from F0 | Existence-based flow is enough |
| Prompt pack/versioning | Нет | Defer F2 | No real prompt/provider |
| Input fingerprint | Да | Keep in package | Minimal reproducibility control |
| Separate manifest/checksum file | Нет | Remove | Package ID/fingerprint and two export hashes suffice |
| Generic LLM/repository interfaces | Нет | Remove | One implementation each |
| Human approval CLI | Нет | Defer F1 | F0 cannot publish |
| YAML configs | Нет | Remove | No changing F0 configuration |
| CLI commands | Пять | Reduce | Only executable vertical slice |
| Export files | Два | Reduce | JSON source + Markdown view |
| SQLAlchemy/Alembic/httpx/feedparser/trafilatura/RapidFuzz/Jinja2 | Нет | Remove | Controlled fixture/std library is sufficient |
| Extra ADR/architecture/editorial docs | Нет | Remove requirement | vNext already fixes decisions |

Role disagreement resolution:

- Editorial/Data roles wanted full Claim/audit structures now; Scope/Architecture roles rejected them. Resolution: source hashes and one embedded unverified mock claim now; human verification entities in F1.
- Architecture role saw future value in provider/repository seams; Python/Cost roles found no second consumer. Resolution: concrete implementations in F0, interface only when a real second implementation exists.
- Product role wanted a useful demo review; Agent-design role warned against new workflow. Resolution: one binary manual lineage/nonpublishability check, explicitly not product evidence.
- Security role preferred immutable revisions; Cost role rejected event sourcing/history. Resolution: content-addressed immutable snapshots, no generic event log.

# Отсутствующие требования

| Finding IDs | Отсутствовало | Добавлено в vNext |
|---|---|---|
| AUD-004, AUD-009 | Identity, constraints, cardinality | Content hashes, deterministic IDs, unique/FK schema |
| AUD-005 | Story Package lifecycle/source of truth | Persisted canonical `StoryPackageSnapshot` |
| AUD-007 | Encoding/order/overwrite/atomicity | Byte-level export contract |
| AUD-010 | Revisions/fingerprint | Immutable snapshot + input fingerprint |
| AUD-011 | Behavior acceptance | Test matrix + repeated E2E |
| AUD-015 | Concrete retention | Metadata and bounded plain summary only |
| AUD-016 | Input/resource/path security | Size/item/DTD/URL/path/log limits |
| AUD-026 | Date/Unicode/Windows policy | UTC/null+raw, NFC, UTF-8/LF, spaces paths |
| AUD-027 | SQLite failure behavior | FK, timeout, transactions, no auto-repair |
| AUD-R2-001, AUD-R2-002 | Exact identity preimages and raw-date revision semantics | Canonical JSON byte rules, fixed ID vectors and raw date in content hash |
| AUD-R2-003 | Enforceable schema details | Exact types/nullability/checks plus singleton creation/open validation |
| AUD-R2-004 | Mock claim derivation/cardinality | Exactly one claim with fixed text/type/status/qualifier/source |
| AUD-R2-005, AUD-R2-009 | Multi-file interruption and actionable errors | Detectable partial-set state and stable error code/action contract |
| AUD-R2-011, AUD-R2-012 | Digest representation/vector and tamper-proof reads | Fixed lowercase vector, DDL checks and identity/payload recomputation |
| AUD-R2-013 | CLI framework usage failures | `E_USAGE` with reason/help action and runner tests |

# Непроверяемые требования

| Finding IDs | Исходная формулировка | Почему непроверяема | vNext pass/fail |
|---|---|---|---|
| AUD-011 | «15 meaningful tests» | Quantity does not prove behavior | Named behavior matrix and exact outcomes |
| AUD-013 | F0 linked to product value | No hypothesis boundary | F0 validates only technical repeatability; manual lineage check |
| AUD-018 | «two own-value elements» | Easy to rename generic output | Future referenced artifact + human verdict |
| AUD-020 | «audience fit» | Audience too broad/no owner decision | Decide wedge before pilot |
| AUD-021 | Format beats own median on several metrics | Multiple comparisons/no denominator | One metric/variable/comparable cohort |
| AUD-032 | Works on clean machine | Python/prereqs/offline boundary absent | Python 3.12.x + locked environment + offline demo |

# AI Agent Interpretation Risks

| Finding IDs | Возможная формальная реализация | Защита vNext |
|---|---|---|
| AUD-001, AUD-006 | Build every enum/entity/state through production | Entity/command/dependency whitelist and non-goals |
| AUD-003 | Skip cluster or manually invent Story ID | Story creation during harvest; `--ids-only` |
| AUD-005 | Return same constant package for every Story | Fingerprint, source IDs/hashes, unknown-Story failure |
| AUD-007 | Write whichever subset of five exports is convenient | Exact two-file contract and golden bytes |
| AUD-008, AUD-025 | Install all named packages/create generic interfaces | Exact allowlist; one concrete implementation |
| AUD-011 | Create 15 trivial tests | Behavior matrix; content and failure assertions |
| AUD-023 | Build config framework and placeholders | Explicit absence of YAML/future commands |
| AUD-024 | Create nested wrapper/docs before slice | Existing root and no mandatory ADR |
| AUD-029 | Treat old §20 as operative alongside vNext | vNext explicitly normative; one Cursor prompt |
| AUD-R2-001, AUD-R2-004 | Invent implementation and matching tests for arbitrary package/claim IDs | Exact preimage bytes and fixed one-claim derivation vectors |
| AUD-R2-005 | Call two sequential atomic replaces an atomic export set | Explicit per-file boundary and injected partial-set detection |
| AUD-R2-009 | Return any non-zero error with vague stderr | Exact symbolic code, sanitized resource and recovery-action assertions |
| AUD-R2-011, AUD-R2-012 | Publish implementation-chosen vectors or trust shape-valid tampered rows | Audit-owned vector plus DDL checks and read-time recomputation |
| AUD-R2-013 | Let Typer bypass the error registry | Custom usage-error contract and exact runner assertions |

# Failure Modes

| Scenario | Proportional F0 behavior | Test |
|---|---|---|
| Same URL, changed content | New immutable Source/Story; old preserved | Integration |
| Different URLs, identical content | Separate Source/Story; no fuzzy merge | Integration |
| Same title, different events | Separate by URL+content identity | Integration |
| Multiple sources for one Story | Not merged in F0; owner decision before F1 | Acceptance review |
| Missing GUID | Accepted; GUID is not identity | Unit/integration |
| Missing date | `published_at=null` | Unit |
| Date without timezone | Do not guess; null + raw | Unit |
| Invalid URL / empty title | Whole fixture fails before writes | Integration |
| Tracking params | Remove explicit tracking keys only | Unit vectors |
| Repeat harvest | Same IDs/counts, `unchanged` summary | Integration |
| Partial DB failure/interruption | Explicit single transaction rolls back | Injected integration |
| Export interruption before replacement | Render/validate/preflight first; all old files preserved | Injected integration |
| Termination between `all` replacements | Each file remains whole; mixed set is detected as `E_EXPORT_PARTIAL`; reviewed `--force` restores pair | Injected integration |
| Repeat build/export | Same package and exact bytes; byte-identical no-op | E2E/golden |
| Fixture/source change | New immutable revision; old package remains tied to old hashes | Integration |
| Stale package | Immutable inputs + fingerprint prevent silent staleness; new revision has new Story | Integration |
| Manual export edit | Fail without `--force`; repair with `--force` | Integration |
| Incompatible schema | Fail, no auto-migration | Integration |
| Locked SQLite | Wait at most configured timeout, fail without partial write | Integration/manual |
| Corrupt SQLite | Actionable failure; no delete/recreate/repair | Manual/copied fixture DB |
| Shape/semantic DB tampering | Constraint or read validation returns `E_DB_SCHEMA`; no export/repair | Direct-SQL integration |
| Invalid CLI syntax | `[E_USAGE]` with reason and help action; no traceback | CLI runner |
| Filename collision/unsafe characters | Fixed hash IDs and fixed filenames; content never becomes path | Security test |

# External Verification Required

Проверка выполнена 13 июля 2026 года только по официальным первичным страницам. Foundation не должен хранить эти mutable values как нормативные требования.

| Область / original location | Official source | Статус на 2026-07-13 | Риск | Disposition |
|---|---|---|---|---|
| YouTube Shorts ≤3 min, §2.1 | https://support.google.com/youtube/answer/15424877 | CONFIRMED; page also adds copyright conditions omitted by original | HIGH | External platform matrix only |
| YPP thresholds, §2.2 | https://support.google.com/youtube/answer/13429240 and https://support.google.com/youtube/answer/72851 | Thresholds confirmed | HIGH | Recheck before monetization decision |
| Moldova/YPP, §2.2 | https://support.google.com/youtube/answer/7101720 and https://support.google.com/youtube/answer/13429240 | General YPP: Moldova present; expanded 500-tier list: Moldova absent. Original adjacency is misleading. | HIGH | Remove from Foundation |
| YouTube inauthentic content, §2.4 | https://support.google.com/youtube/answer/1311392 | CONFIRMED; policy explicitly covers mass-produced/repetitive and generic AI templates | HIGH | Keep only durable originality principle |
| YouTube synthetic disclosure, §2.5 | https://support.google.com/youtube/answer/14328491 | CONFIRMED, context-dependent | HIGH | Verify at publishing time |
| TikTok Creator Fund/Rewards, §2.3 | https://support.tiktok.com/en/business-and-creator/tiktok-creator-fund-us/tiktok-creator-fund-update-us and https://support.tiktok.com/en/business-and-creator/creator-rewards-program/creator-rewards-program | Replacement and ≥1 min confirmed; detailed eligibility page is locale/dynamic; Moldova availability remains `EXTERNAL_VERIFICATION_REQUIRED` | HIGH | Account/region check before strategy |
| TikTok AI label, §2.5 | https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content | CONFIRMED, context-dependent | HIGH | Verify at publishing time |
| TikTok unaudited API, §2.6 | https://developers.tiktok.com/doc/content-posting-api-get-started | CONFIRMED: unaudited clients restricted; direct-post rules are changeable | HIGH | P1 readiness record |
| Instagram publishing, §2.6 | https://developers.facebook.com/documentation/instagram-platform/content-publishing | Official page inaccessible to audit tool; `EXTERNAL_VERIFICATION_REQUIRED` | HIGH | Recheck directly before P1 |
| Telegram video API, §2.6 | https://core.telegram.org/bots/api | `sendVideo` confirmed; current size/format limits are mutable | MEDIUM | Recheck before adapter |
| Buffer limits, §2.7 | https://buffer.com/pricing | Original 3 channels/10 scheduled posts currently confirmed | HIGH | Dated budget snapshot only |
| ElevenLabs Starter, §2.7 | https://elevenlabs.io/pricing | $6 monthly currently confirmed; annual equivalence not retained | HIGH | Recheck before V1 |
| n8n Starter/Community, §2.7 | https://n8n.io/pricing/ | €20 annual-billed Starter and Community Edition currently confirmed | HIGH | Irrelevant to F0; remove |
| OpenAI/Gemini pricing/free tier, §2.7 | https://openai.com/api/pricing/ and https://ai.google.dev/gemini-api/docs/pricing | OpenAI URL redirected away from a clear API price table; Gemini free tier is model-specific. `EXTERNAL_VERIFICATION_REQUIRED` per chosen model. | HIGH | Provider decision record, not Foundation |
| Remotion license, §2.7 | https://www.remotion.dev/docs/license/pricing | Free license for individuals/companies up to 3 people currently confirmed | HIGH | Recheck before V1 |
| arXiv metadata/full text, §5.5 | https://info.arxiv.org/help/api/tou.html | Descriptive metadata CC0 confirmed; full-text rights remain item-specific | MEDIUM | F1 source policy |
| Pexels/Pixabay rights, §21 | https://www.pexels.com/legal-pages/license/ and https://pixabay.com/service/license-summary/ | General license pages confirmed; model/property/trademark rights remain asset-specific | HIGH | Asset-level evidence in F3 |

# Рекомендованный порядок исправлений

1. Accept one F0 whitelist/non-goal boundary (AUD-001, AUD-014).
2. Make the flow fixture-only and executable (AUD-002, AUD-003, AUD-006).
3. Fix identity, schema, exact claim derivation and package source-of-truth (AUD-004, AUD-005, AUD-009, AUD-010, AUD-R2-001–AUD-R2-004, AUD-R2-011, AUD-R2-012).
4. Fix exact export and error contracts (AUD-007, AUD-015, AUD-016, AUD-026, AUD-027, AUD-R2-005, AUD-R2-007, AUD-R2-009, AUD-R2-013).
5. Replace dependency alternatives and test-count proxy; remove residual provider seam (AUD-008, AUD-011, AUD-023, AUD-025, AUD-032, AUD-R2-006).
6. Separate product/editorial hypotheses and future gates (AUD-013, AUD-017–AUD-022, AUD-030–AUD-031).
7. Remove mutable platform facts and repair audit traceability/timing (AUD-012, AUD-028–AUD-029, AUD-R2-008, AUD-R2-010, AUD-R2-014).

# Go / No-Go для Foundation Sprint F0

- **Исходный `PROJECT_FOUNDATION.md`: NO-GO.** Scope, offline behavior and DoD are contradictory; autonomous implementation is unsafe.
- **`PROJECT_FOUNDATION.vNext.md`: GO after owner accepts this audit package.** Independent red-team findings are closed; no unresolved owner decision blocks the technical F0. Product/F1 decisions remain intentionally open.

Final recommendation: `READY_FOR_F0` for vNext; do not implement from the original document.
