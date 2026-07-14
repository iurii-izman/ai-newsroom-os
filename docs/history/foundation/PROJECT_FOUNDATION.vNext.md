Status: historical audit artifact.
Superseded for F0 implementation by F0_TECHNICAL_SPEC.md.
Do not use this file as the normative Cursor implementation specification.
Owner-review summary: docs/foundation-owner-review.md.

# PROJECT_FOUNDATION.vNext.md

## Status

Версия: `0.5-audit-candidate`  
Дата: 13 июля 2026  
Статус: нормативная спецификация Foundation Sprint F0 после аудита; реализация ещё не начата.  
Оперативный документ для F0: этот файл. Исходный `PROJECT_FOUNDATION.md` сохранён как контекст и не является инструкцией для реализации F0.

Нормативные слова `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT` и `MAY` применяются только в таблицах, где рядом указан объективный способ проверки.

## Changes from previous version

- F0 — один offline-срез fixture → snapshot → SQLite → Story → mock package → JSON/Markdown.
- Убраны network, clustering/workflow, future entities, YAML и speculative interfaces; зафиксированы identity, DB, export, Windows/Unicode и error contracts.
- F0 доказывает только technical repeatability; mutable platform facts вынесены из нормы.

## Audit Traceability

| Область | Finding IDs |
|---|---|
| Scope, flow, CLI, dependencies | AUD-001, AUD-002, AUD-003, AUD-006, AUD-008, AUD-011, AUD-014, AUD-023, AUD-024, AUD-025, AUD-029, AUD-032 |
| Identity, DB, package, export, failures | AUD-004, AUD-005, AUD-007, AUD-009, AUD-010, AUD-015, AUD-016, AUD-026, AUD-027; AUD-R2-001–AUD-R2-013 |
| Editorial/product/external boundaries | AUD-012, AUD-013, AUD-017–AUD-022, AUD-028, AUD-030, AUD-031 |
| Corrected semantic trace mapping | AUD-R2-014 |

# 1. Product Vision

Локальная proof-first AI-редакция помогает русскоязычным специалистам и предпринимателям применять AI без шума:

> AI без шума: что изменилось, что подтверждено и что можно применить.

Отличие — traceable связь source → claim → вывод → применение; исходная ниша автора — CRM, интеграции и автоматизация. Автоматизируется лишь доказанный вручную процесс. F0 создаёт воспроизводимую техническую основу, не медиа-продукт или готовый контент.

# 2. Product Assumptions

| Гипотеза | Статус | Фаза проверки | Доказательство | Что не является доказательством |
|---|---|---|---|---|
| Technical repeatability/cost | Сейчас | F0 | Offline repeat, stable IDs/bytes, lineage | Classes/JSON alone |
| Editorial usefulness | Нет | F1/manual | Faster trace of every material claim | Valid mock schema |
| Audience fit | Нет | Content pilot | Repeated qualified signals in one segment | One viral post/views |
| Format fit | Нет | Exploratory pilot | Comparable cohort, one variable/metric + review | Raw post count |
| Monetization | Нет | After audience signal | Defined revenue experiment | Payout threshold/video |
| Lead generation | Нет | After audience signal | Attributed qualified response | Unattributed clicks |

Результат F0 интерпретируется только как проверка технической гипотезы. Выбор beachhead-аудитории, primary platform и pilot metric остаётся решением перед F1/content pilot (AUD-013, AUD-019, AUD-020).

# 3. Editorial Principles

| ID | Нормативное требование | Проверка |
|---|---|---|
| ED-01 | Material future claim `MUST` cite evidence; LLM/mock `MUST NOT` be a factual source. | F1 rejects missing evidence; F0 claim cites source ID. |
| ED-02 | Vendor source `MUST NOT` turn its result claim into `FACT/VERIFIED`. | Golden asserts `VENDOR_CLAIM/UNVERIFIED`. |
| ED-03 | External text `MUST` be untrusted; embedded instructions `MUST NOT` execute. | No content-driven LLM/shell/eval; malicious-title test. |
| ED-04 | Mock package `MUST NOT` be published or treated as human-verified. | Both exports assert exact mock flags/warning. |

Source tier означает близость к событию, не истинность. Claim Ledger, verification, corrections, originality, rights и approvals проектируются по ручному процессу в F1/F3 (AUD-017, AUD-018, AUD-028, AUD-031).

# 4. Foundation F0 Scope

```text
local RSS 2.0 fixture → immutable SourceSnapshot → SQLite → one Story
→ deterministic Mock StoryPackageSnapshot → JSON + Markdown
```

| ID | Нормативное требование | Проверка |
|---|---|---|
| F0-01 | F0 `MUST` run on Windows 11/Python 3.12.x/Ryzen 3 5300U/16 GB, no GPU/Docker. | Target demo; no Docker files; fixture peak ≤512 MB. |
| F0-02 | Runtime/demo/tests `MUST` make no network/API connection. | Socket guard + offline demo after install. |
| F0-03 | F0 `MUST` persist only SourceSnapshot, Story, StoryPackageSnapshot; MockClaim stays embedded. | Schema has only four §9 tables. |
| F0-04 | Unchanged rerun `MUST` preserve IDs, counts and export bytes. | Repeat E2E compares IDs/counts/SHA-256. |
| F0-05 | Package `MUST` have the sole exact mock claim and `MUST NOT` claim readiness. | Both goldens assert lineage, exact claim/flags/warning; manual trace review. |

# 5. F0 Non-Goals

| ID | Нормативное исключение | Проверка |
|---|---|---|
| NG-01 | F0 `MUST NOT` use HTTP/live RSS/manual URL. | No HTTP dependency/import; socket guard. |
| NG-02 | F0 `MUST NOT` add fuzzy dedup, clustering, merge or review queue. | CLI/schema scan. |
| NG-03 | F0 `MUST NOT` add Brief/Score/Angle/Script/ProductionPlan/Publication/Metrics/Experiment/Lesson/assets or workflow/approval state. | Code/schema/CLI scan. |
| NG-04 | F0 `MUST NOT` add real LLM, provider protocol, retry/cost or file-fixture provider. | One concrete mock generator; scan. |
| NG-05 | F0 `MUST NOT` add YAML, ORM/migrations, HTTP/feed/content/fuzzy/template libraries. | Lockfile/import audit. |
| NG-06 | F0 `MUST NOT` add UI/API/Docker/workers/n8n/TTS/video/publishing/cloud/platform adapters, nested repo wrapper or routine ADR. | Repository/dependency/process scan. |

# 6. Architecture Decisions

| ID | Решение | Проверка |
|---|---|---|
| AR-01 | Modular monolith; domain `SHOULD NOT` depend on SQLite/Typer; CLI is composition root. | Import-boundary test/review. |
| AR-02 | F0 `MUST` be synchronous and single-process. | No async/worker dependency/process. |
| AR-03 | Python `>=3.12,<3.13`, `uv`; runtime Typer/Pydantic v2; dev pytest/ruff/mypy; core I/O stdlib. Other dependency `MUST NOT` appear without F0 consumer/spec update. | Lockfile audit. |
| AR-04 | One stdlib `sqlite3` module; repository interface `MAY` appear only with a second storage consumer. | No repository protocol/ABC. |
| AR-05 | Parser supports the bounded local RSS 2.0 subset; unsupported format `MUST` fail before writes. | Atom/invalid tests: code + unchanged counts. |

# 7. Domain Model for F0

## 7.1. Объекты и владение

| Объект | Назначение | Владелец lifecycle | Хранилище | F0 use case | Проверка |
|---|---|---|---|---|---|
| `SourceSnapshot` | Immutable normalized snapshot одного RSS item | Harvest application service | `sources` | Вход и provenance | Duplicate/revision integration tests |
| `Story` | Минимальная редакционная единица, один-к-одному со snapshot в F0 | Story creation application service | `stories` | Стабильная точка package build | FK/unique tests |
| `StoryPackageSnapshot` | Persisted canonical mock payload | Package build application service | `story_packages` | Source of truth для exports | Schema/golden/rebuild tests |
| `MockClaim` | Вложенная демонстрация claim-to-source lineage | Package generator | Внутри canonical payload | Не является verified claim ledger | Schema test |

## 7.2. Поля

`SourceSnapshot`:

- `id`: `src_` + первые 24 hex SHA-256 identity digest;
- `original_url`, `canonical_url`;
- `title`: Unicode NFC, non-empty, до 500 символов;
- `summary_text`: Unicode NFC/plain text, до 10 000 символов;
- `published_at`: nullable RFC3339 UTC `Z`;
- `published_at_raw`: nullable trimmed/NFC original feed value when parsing fails or timezone is missing;
- `discovered_at`: aware UTC operational timestamp, excluded from identities and exports;
- `content_hash`: full SHA-256 canonical normalized item content.

`Story`:

- `id`: `story_` + первые 24 hex SHA-256 of `source_id`;
- `primary_source_id`: unique FK to `sources.id`;
- `title`: copied from immutable source snapshot.

`StoryPackageSnapshot`:

- `package_id`, `story_id`, `schema_version=1`;
- `generator_name=mock`, `generator_version=mock-v1`;
- `input_fingerprint` over schema/generator/story/source IDs and full content hashes;
- `payload_json`: canonical source of truth;
- `built_at`: aware UTC operational timestamp, excluded from payload and exports.

`MockClaim`:

- package содержит ровно один `MockClaim` для ровно одного source snapshot Story;
- `text`: exact string `RSS item reports: ` followed by normalized Story title;
- `id`: `claim_` + first 24 hex of SHA-256 over UTF-8 `source_id + "\n" + text + "\nVENDOR_CLAIM\nUNVERIFIED"`;
- fixed `type=VENDOR_CLAIM`, `status=UNVERIFIED`, `source_ids=[source_id]` and qualifier `Fixture metadata only; no independent or human verification.`.

## 7.3. Identity and edge cases

Canonical URL normalization is deliberately small: trim whitespace; require absolute `http`/`https`; lowercase scheme/host; remove fragment and default port; remove only `utm_*`, `fbclid` and `gclid`; sort remaining query pairs; preserve path and meaningful query values.

For every identity JSON below, canonical serialization means UTF-8, `ensure_ascii=false`, lexicographically sorted object keys, separators `,` and `:` with no insignificant whitespace, and no final LF. A “full SHA-256” is exactly 64 lowercase hexadecimal characters without prefix; an ID digest suffix is its first 24 lowercase characters. Canonical item content contains exactly normalized `title`, `summary_text`, `published_at` (string or null) and `published_at_raw` (string or null). `content_hash` is the full SHA-256 of those bytes. Source identity is `src_` plus the first 24 hex of SHA-256 over UTF-8 `canonical_url + "\n" + content_hash`. Story identity is `story_` plus the first 24 hex of SHA-256 over UTF-8 `source_id`.

The package input document uses that canonical serialization and contains exactly `schema_version=1`, `generator_name="mock"`, `generator_version="mock-v1"`, `story_id` and `sources`, where `sources` is the ID-sorted list of objects containing exactly `id` and `content_hash`. `input_fingerprint` is the full SHA-256 of those bytes. `package_id` is `pkg_` plus the first 24 hex of SHA-256 over UTF-8 bytes of literal `story-package\n` followed by the ASCII fingerprint. Claim text and ID use the exact values and preimage in §7.2. These preimages are part of schema v1 and cannot change without a schema-version change (AUD-R2-001, AUD-R2-002).

Independent schema-v1 reference vector (JSON lines have no hidden whitespace or final LF):

```text
item_json={"published_at":null,"published_at_raw":"2026-07-13 10:00","summary_text":"Кратко","title":"Тест AI"}
content_hash=e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d
canonical_url=https://example.com/news
source_id=src_58343a9a5ffae3037a3f73bf
story_id=story_55c2bc7f60628d20cb9acd4c
claim_text=RSS item reports: Тест AI
claim_id=claim_11806810946d69ba4de2ccd4
package_input_json={"generator_name":"mock","generator_version":"mock-v1","schema_version":1,"sources":[{"content_hash":"e004ecf4d7bb2bd98fe745ec7180f40a37ffb1a67ef40bfa43b5eacbbbadbc7d","id":"src_58343a9a5ffae3037a3f73bf"}],"story_id":"story_55c2bc7f60628d20cb9acd4c"}
input_fingerprint=bd9e982b780c713eaad078c3129e6ddebec56fcc6b5cba0bf951547ae31fda8f
package_id=pkg_17e9b7502f7bc00db437b993
```

| ID | Нормативное требование | Проверка |
|---|---|---|
| DM-01 | Source IDs, Story IDs, claim IDs, fingerprints and package IDs `MUST` use the exact schema-v1 preimages above and be independent of row order, current time and absolute paths. | Published unit vectors assert full preimage bytes, full hashes and truncated IDs; two isolated runs compare results. |
| DM-02 | Same canonical URL with changed normalized content `MUST` create a new immutable SourceSnapshot and Story; the old snapshot `MUST NOT` be overwritten. | Revision integration test verifies two sources/stories and preserved old hash. |
| DM-03 | Different URLs with identical content and equal titles `MUST` remain separate Stories in F0; same-story merge is deferred. | Integration test verifies two sources/stories. |
| DM-04 | Missing GUID or date `MAY` be accepted; missing timezone `MUST NOT` be guessed and yields `published_at=null` plus raw value. | Unit/integration fixtures for each case. |
| DM-05 | Invalid URL, empty title, invalid/unsupported XML or limit violation `MUST` fail the entire harvest before database writes. | Failure tests compare row counts before/after. |
| DM-06 | Each F0 package `MUST` contain exactly one claim whose text, type, status, qualifier and sole source ID are derived exactly as §7.2 defines; arbitrary or additional claims `MUST` fail validation. | Schema/generator tests compare all six values and reject zero, two or modified claims. |

F0 не имеет state machine. Существование `SourceSnapshot`, `Story` и `StoryPackageSnapshot` достаточно для команд. Ошибка оставляет предыдущее committed state без изменений. Полный workflow от verification до publication отложен (AUD-006).

# 8. CLI Contract

Общий параметр: `ai-newsroom --data-dir PATH ...`; default — `data`. Путь разрешается через `pathlib`, может содержать пробелы и Unicode.

| Команда | Success output/side effect | Ошибка | Проверка |
|---|---|---|---|
| `db init` | Создаёт/проверяет DB schema v1; повторный вызов — no-op, exit 0 | Incompatible/corrupt/locked DB: concise stderr, non-zero, без auto-repair | Integration tests |
| `harvest run --fixture PATH` | Импортирует весь валидный fixture одной transaction; печатает `items/imported/unchanged/stories`; exit 0 | Invalid/missing/oversized fixture: non-zero, no writes | Integration tests |
| `stories list [--ids-only]` | Сортировка по `story_id`; `--ids-only` печатает один ID на строку | Empty DB: exit 0 and empty output; DB error: non-zero | CLI tests |
| `package build STORY_ID` | Создаёт/находит один deterministic package с единственным F0 mock generator; печатает package ID; second run no-op | Unknown Story: non-zero, no writes | Integration tests |
| `package export STORY_ID --format json\|markdown\|all [--force]` | Экспортирует persisted package в fixed path; byte-identical existing file is success | Missing package or differing existing file without force: non-zero, no overwrite | Golden/atomicity tests |

Expected stderr begins with `[CODE]`, names only a sanitized affected path/resource and ends with the safe action below.

| Code | Condition | Safe action |
|---|---|---|
| `E_USAGE` | Missing/invalid argument, option, command or enum value | Read command help and rerun with valid syntax |
| `E_FIXTURE_INVALID` | Missing/non-regular/oversized, invalid/unsupported XML, DTD/entity, item/content/URL limit failure | Fix or replace fixture, then rerun; no rows were written |
| `E_DB_SCHEMA` | Existing DB has tampered/incompatible metadata, structure or persisted identity/payload | Select/init a supported data dir or restore a known-good copy; no auto-migration |
| `E_DB_LOCKED` | Busy timeout expires | Close the other writer and retry |
| `E_DB_CORRUPT` | SQLite reports corruption | Preserve the file and restore/diagnose a copy; no auto-repair |
| `E_STORY_NOT_FOUND` | Build Story ID is absent | Run `stories list --ids-only` and retry with an existing ID |
| `E_PACKAGE_NOT_BUILT` | Export has no persisted package for Story | Run `package build STORY_ID`, then retry |
| `E_EXPORT_CONFLICT` | Requested existing output differs and the set is not partial | Review it; rerun with explicit `--force` only to replace |
| `E_EXPORT_PARTIAL` | `all` has at least one exact expected file and at least one requested missing/differing file | Review the pair; rerun `--format all --force` to recover |
| `E_UNEXPECTED` | Unmapped internal failure | Preserve data; inspect sanitized diagnostics and report the failure |

| ID | Нормативное требование | Проверка |
|---|---|---|
| CLI-01 | CLI `MUST` содержать ровно перечисленные F0 command groups/commands; future commands `MUST NOT` появляться как placeholders. | CLI help snapshot. |
| CLI-02 | Expected user errors `MUST` return non-zero with the mapped stable code, sanitized resource and safe next action; unexpected errors `MUST` use `E_UNEXPECTED`, preserve data and return non-zero. No traceback, secret, raw fixture body or summary is printed. | CLI failure tests assert code/action and inspect stderr/log markers. |
| CLI-03 | Every mutating command `MUST` report created/unchanged counts or resulting ID. | CLI output assertions. |
| CLI-04 | A command `MUST NOT` translate DB lock, corruption, schema mismatch, missing Story/package or export collision/partial-set conditions into a different code or silent success. | Parameterized error-contract tests assert exact code and unchanged data/files. |
| CLI-05 | Missing/unknown/invalid CLI syntax `MUST` use `[E_USAGE]`, a concise reason and help action; `--help` remains exit 0. | Typer runner tests cover missing argument, unknown option/command and invalid format enum. |

# 9. Persistence

SQLite schema v1 (types and constraints are normative):

- `schema_meta(singleton INTEGER PRIMARY KEY CHECK(singleton = 1), version INTEGER NOT NULL CHECK(version = 1))`;
- `sources(id TEXT PRIMARY KEY NOT NULL CHECK(length(id)=28 AND substr(id,1,4)='src_' AND substr(id,5) NOT GLOB '*[^0-9a-f]*'), original_url TEXT NOT NULL CHECK(length(original_url)>0), canonical_url TEXT NOT NULL CHECK(length(canonical_url)>0), title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 500), summary_text TEXT NOT NULL CHECK(length(summary_text)<=10000), published_at TEXT NULL CHECK(published_at IS NULL OR length(published_at)>0), published_at_raw TEXT NULL CHECK(published_at_raw IS NULL OR length(published_at_raw)>0), discovered_at TEXT NOT NULL CHECK(length(discovered_at)>0), content_hash TEXT NOT NULL CHECK(length(content_hash)=64 AND content_hash NOT GLOB '*[^0-9a-f]*'), UNIQUE(canonical_url, content_hash))`;
- `stories(id TEXT PRIMARY KEY NOT NULL CHECK(length(id)=30 AND substr(id,1,6)='story_' AND substr(id,7) NOT GLOB '*[^0-9a-f]*'), primary_source_id TEXT UNIQUE NOT NULL REFERENCES sources(id), title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 500))`;
- `story_packages(package_id TEXT PRIMARY KEY NOT NULL CHECK(length(package_id)=28 AND substr(package_id,1,4)='pkg_' AND substr(package_id,5) NOT GLOB '*[^0-9a-f]*'), story_id TEXT UNIQUE NOT NULL REFERENCES stories(id), schema_version INTEGER NOT NULL CHECK(schema_version=1), generator_name TEXT NOT NULL CHECK(generator_name='mock'), generator_version TEXT NOT NULL CHECK(generator_version='mock-v1'), input_fingerprint TEXT NOT NULL CHECK(length(input_fingerprint)=64 AND input_fingerprint NOT GLOB '*[^0-9a-f]*'), payload_json TEXT NOT NULL CHECK(length(payload_json) BETWEEN 2 AND 1000000 AND json_valid(payload_json)=1 AND substr(payload_json,1,1)='{'), built_at TEXT NOT NULL CHECK(length(built_at)>0))`.

`summary_text` uses an empty string when the feed field is absent. Schema creation inserts exactly one `(singleton=1, version=1)` row in the same transaction. The primary-key/check combination prevents a second valid singleton value; connection/open validation rejects zero rows, any extra row introduced by a tampered schema, or any version other than 1.

| ID | Нормативное требование | Проверка |
|---|---|---|
| DB-01 | Every connection `MUST` enable foreign keys and a 5-second busy timeout; writes `MUST` use explicit transactions. | Integration test checks pragmas and rollback on injected failure. |
| DB-02 | `db init` `MUST` be idempotent; every open `MUST` validate the singleton row and exact schema version; incompatible schema `MUST NOT` auto-migrate. | Init-twice, missing/surplus singleton and incompatible-version tests. |
| DB-03 | Harvest validation `MUST` finish before writes; successful source/story inserts `MUST` commit atomically. | Invalid-item and injected-write-failure tests show unchanged counts. |
| DB-04 | Corruption or lock timeout `MUST` produce actionable failure and `MUST NOT` delete, recreate or repair the database automatically. | Manual/integration error-path test against copied fixture DB. |
| DB-05 | F0 `MUST` persist only normalized feed metadata/short summary, not raw XML, full HTML, PDFs or raw LLM responses. | Schema/content inspection. |
| DB-06 | Before insert and on every read/export, IDs, hashes, payload schema, exact one-claim derivation and recomputed fingerprint/package ID `MUST` validate; mismatch `MUST` return `E_DB_SCHEMA` without export or repair. | Direct-SQL tests tamper each ID/hash/payload relation; constraints or read validation reject it. |

# 10. Export Contract

Export root:

```text
<data-dir>/exports/<story-id>/
├─ story-package.json
└─ story-package.md
```

`story-package.json` contains exactly these top-level fields in schema v1:

```json
{
  "schema_version": 1,
  "package_id": "pkg_...",
  "generation_mode": "MOCK",
  "publishable": false,
  "mock_notice": "Demo-only package; no human verification; do not publish.",
  "generator": {"name": "mock", "version": "mock-v1"},
  "input_fingerprint": "sha256...",
  "story": {"id": "story_...", "title": "..."},
  "sources": [
    {"id": "src_...", "title": "...", "url": "https://...", "published_at": null, "content_hash": "sha256..."}
  ],
  "claims": [
    {
      "id": "claim_...",
      "text": "RSS item reports: ...",
      "type": "VENDOR_CLAIM",
      "status": "UNVERIFIED",
      "source_ids": ["src_..."],
      "qualifier": "Fixture metadata only; no independent or human verification."
    }
  ]
}
```

The F0 payload contains exactly one source object matching `Story.primary_source_id` and exactly one claim matching §7.2. Markdown renders the same package ID, Story, sorted source link/hash and claim/source ID. It contains the literal lines `Generation mode: MOCK`, `Publishable: false` and `Warning: Demo-only package; no human verification; do not publish.` It is a view of persisted canonical payload, not a second source of truth.

| ID | Нормативное требование | Проверка |
|---|---|---|
| EX-01 | JSON `MUST` be UTF-8 without BOM, Unicode unescaped, keys sorted, indent 2, LF endings and one final LF. Arrays `MUST` use stable ID order. | Byte-level golden test on Windows. |
| EX-02 | Markdown `MUST` be UTF-8 without BOM with LF endings, escaped untrusted text and all three literal mock/nonpublishability lines above. | Golden/security test with exact markers, Cyrillic and Markdown control characters. |
| EX-03 | Exports `MUST NOT` contain current time, absolute paths, SQLite row order or random values. | Two isolated data directories produce identical SHA-256 files. |
| EX-04 | Export filenames and directories `MUST` derive only from validated hash IDs, never source titles/URLs. | Unsafe-title test and path inspection. |
| EX-05 | All requested files `MUST` render, validate and preflight before any replacement. Each file replacement `MUST` use a sibling temp file plus atomic `os.replace`; group atomicity is not promised. Existing differing files `MUST NOT` change without `--force`. | Pre-replace failure preserves all old bytes; collision/force tests. |
| EX-06 | A byte-identical existing export `MUST` be treated as successful no-op; a manual edit `MUST` be detected. | Export-twice and manual-edit tests. |
| EX-07 | After an interrupted `--format all`, a mixed exact/missing-or-differing pair `MUST` fail as `E_EXPORT_PARTIAL`; it `MUST NOT` be called a complete export. Recovery `MUST` require review and explicit `--force`. | Inject termination after first replace; next run detects partial set, then reviewed force rebuilds both exact files. |

Operational timestamps may vary in SQLite and logs. IDs, canonical payload and exported bytes are strictly deterministic.

# 11. Testing

Required behavior matrix replaces the arbitrary test-count target (AUD-011).

| Area | Required cases | Test type | Pass criterion |
|---|---|---|---|
| URL/content identity | tracking params, fragment, invalid URL, same URL changed content, different URL same content | Unit + integration | Exact expected IDs/counts |
| Dates | UTC offset, missing date, missing timezone | Unit | RFC3339 Z or documented null/raw |
| RSS boundary | valid single/multi item, empty, invalid XML, DTD/entity, Atom, oversized | Integration | Exact error code/action; failures write nothing |
| Persistence | init twice, repeat harvest, FK, rollback, incompatible version, busy timeout | Integration | No orphan/partial/implicit migration |
| Package | unknown Story, build twice, exact one-claim derivation, source/claim lineage, mock flags | Integration | Same package ID/payload; arbitrary/extra claim rejected |
| Export | JSON/Markdown golden, literal markers, repeat, edit collision, force, interruption after first replace | Golden + integration | Exact bytes; per-file atomicity; partial pair detected/recovered |
| Environment | no network, Unicode/spaces path, no Docker, dependency allowlist | Integration + manual | Offline green run on target |
| End-to-end | fresh data dir through all F0 commands twice | Integration | Same IDs/counts/export hashes |

| ID | Нормативное требование | Проверка |
|---|---|---|
| T-01 | Automated tests `MUST` block outbound sockets and `MUST NOT` depend on current time, absolute paths, SQLite implicit order or live services. | Network guard plus isolated repeated test run. |
| T-02 | Golden files `MUST` be reviewed artifacts and `MUST` include meaningful lineage/content assertions, not only schema validity. | Test review checks fixed package/source/claim IDs and warning text. |
| T-03 | `ruff`, `mypy` and `pytest` `MUST` pass from the locked environment. | `uv run ruff check .`, `uv run mypy src`, `uv run pytest`. |
| T-04 | At least one manual review `MUST` confirm that a reader can trace the mock claim to the exact source ID/hash and cannot mistake the package for publishable content. | Signed demo checklist with binary pass/fail; it is not a product-success claim. |

# 12. Security and Safety

| ID | Нормативное требование | Проверка |
|---|---|---|
| SEC-01 | Fixture `MUST` be a local regular file no larger than 5 MiB and no more than 500 items; DTD/entity declarations `MUST` be rejected before XML parse. | Boundary/security fixtures; failures write nothing. |
| SEC-02 | Titles/summaries `MUST` have control characters removed, Unicode normalized and length limits enforced; they `MUST NOT` influence commands, imports or paths. | Malicious fixture test. |
| SEC-03 | URLs `MUST` use only `http` or `https`; generated Markdown `MUST` escape untrusted labels. | URL validation and Markdown injection tests. |
| SEC-04 | F0 `MUST NOT` require, read or log secrets; raw fixture bodies and summaries `MUST NOT` be dumped to logs on failure. | Environment/log inspection with marker values. |
| SEC-05 | Database/export errors `MUST NOT` trigger destructive cleanup or silent fallback. Each export file remains whole; a process stop between two replacements may leave a mixed pair, which `MUST` be detected as `E_EXPORT_PARTIAL` on the next `all` export. | DB failures preserve baseline counts; export injection proves no truncated file, detectable mixed pair and explicit-force recovery. |

There are no assets, synthetic media, publishing or public-figure generation in F0. Rights ledger, correction/takedown workflow, AI disclosure, personal data policy and platform policy gates are required before their first real consumer, not as placeholders now (AUD-015, AUD-016, AUD-028).

# 13. Definition of Done

## 13.1. Automated acceptance

From repository root:

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

The official fixture contains exactly one valid RSS item, including Cyrillic text. The automated end-to-end test repeats harvest/build/export and checks unchanged counts, IDs and bytes.

## 13.2. Completion gates

| ID | Нормативное требование | Проверка |
|---|---|---|
| DOD-01 | Every command above `MUST` exit 0 on a fresh Windows data directory after dependency installation. | Captured command log. |
| DOD-02 | The full runtime/demo/test path `MUST` pass with network disabled and without Docker, GPU or external API. | Offline target-machine run and environment review. |
| DOD-03 | The second complete run `MUST` produce no new rows and identical export SHA-256 values. | E2E assertion and command summary. |
| DOD-04 | All behavior rows in section 11 `MUST` have passing evidence; test count alone `MUST NOT` satisfy DoD. | Coverage checklist linked to test names. |
| DOD-05 | A manual lineage/nonpublishability review `MUST` pass; both files `MUST` expose literal mock/nonpublishability markers; product, format and monetization hypotheses `MUST NOT` be marked validated. | Signed binary checklist, exact-marker assertions and final report wording. |

# 14. Future Phases

- **F1 — real sources and human editorial pilot:** decide source set/retention/Story merge identity; add bounded network ingestion, manual merge, evidence locators, Claim review and the first necessary human gate.
- **F2 — one real LLM provider:** choose provider/data boundary; add one concrete adapter, structured output, budget/retry controls and evaluation on human-reviewed stories.
- **F3 — production-ready package:** add validated angle/script/production plan, originality evidence, asset rights and disclosure review.
- **V1 — video:** one proven format, local rendering/TTS only after manual evidence.
- **P1 — publishing:** manual-first; adapters and current platform policies only after separate verification.

Each phase begins from a new, owner-approved scope. Future entity tables, protocols and adapters are not pre-created in F0.

# 15. External Assumptions

F0 has no dependency on monetization thresholds, platform duration limits, publishing APIs, regional availability, pricing/free tiers, asset libraries or video-tool licensing.

| ID | Нормативное требование | Проверка |
|---|---|---|
| EXT-01 | Before a future integration decision, changing external facts `MUST` be rechecked against an official primary source and recorded with URL, exact date, scope and owner. | Phase readiness review rejects an undated/unofficial assumption. |
| EXT-02 | Changing prices, quotas, program thresholds and regional availability `MUST NOT` be treated as permanent Foundation requirements. | Foundation review contains no numeric external platform/tool assumptions. |
| EXT-03 | If an official primary source is inaccessible or ambiguous, the item `MUST` be marked `EXTERNAL_VERIFICATION_REQUIRED` rather than inferred from memory. | External-assumption record review. |

Audit snapshot and official links checked on 13 July 2026 are in `docs/foundation-audit.md`; they are evidence for the audit, not normative F0 requirements (AUD-012).

# 16. Open Decisions

There are no unresolved owner decisions that block F0 under this specification. Decisions required before F1/F2 are maintained in `docs/open-decisions.md`:

- Story identity and merge policy for multi-source stories;
- source set and ingestion boundary;
- source-content retention;
- initial editorial wedge/platform/pilot metric;
- real LLM provider and data-handling boundary.

# 17. Cursor Execution Prompt

```text
Read PROJECT_FOUNDATION.vNext.md and docs/f0-minimal-scope.md completely.
Treat PROJECT_FOUNDATION.vNext.md as the normative F0 specification; use the old
PROJECT_FOUNDATION.md only as non-normative product context.

Inspect the existing repository root. Implement Foundation Sprint F0 only.
Do not create a nested project directory. Do not implement placeholders or future
entities, commands, states, adapters, configs, providers, UI, video or publishing.
Use only the dependency allowlist in Architecture Decision AR-03.

Before editing, present a short file-level plan. Then implement the exact offline
vertical slice and CLI contract. Tests must block the network. Run every command in
Definition of Done, including a repeated end-to-end run, and report exact results.

If a requirement conflicts with an exclusion, the exclusion wins. If completion
would require scope not whitelisted in F0, stop and report the conflict instead of
inventing an abstraction or silently expanding scope.

Final report:
## Implemented
## Changed files
## Verification results
## Requirement deviations
## Known limitations
## One next step
```
