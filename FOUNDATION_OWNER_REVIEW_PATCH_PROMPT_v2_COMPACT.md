# Owner Review Patch v2 — финализация Foundation F0

## Цель

Точечно исправить документы после Ultra-аудита и подготовить один окончательный нормативный документ для реализации F0.

Это **не новый аудит** и **не реализация проекта**. Не расширяй scope, не пиши код и не добавляй будущие компоненты.

---

# 1. Прочитай входные документы

Прочитай полностью и сопоставь:

- `PROJECT_FOUNDATION.md`
- `PROJECT_FOUNDATION.vNext.md`
- `docs/foundation-audit.md`
- `docs/foundation-change-plan.md`
- `docs/foundation-diff-summary.md`
- `docs/open-decisions.md`
- `docs/f0-minimal-scope.md`
- `docs/f0-risk-register.md`

Если часть файлов лежит в корне, используй фактический путь. Не создавай дубликаты одного документа в двух каталогах.

---

# 2. Принятые решения владельца

Эти решения не обсуждаются повторно:

- целевая машина: Windows 11, Ryzen 3 5300U, **16 GB RAM**;
- GPU и Docker для F0 не требуются;
- Python 3.12.x;
- F0 остаётся offline, deterministic, idempotent technical slice;
- F0 не проверяет аудиторию, формат, монетизацию или production readiness;
- исходный `PROJECT_FOUNDATION.md` сохраняется как исторический продуктовый источник;
- Ultra-аудит сохраняется как историческое evidence, но не как нормативная F0-спецификация;
- после этой задачи должен остаться один нормативный F0-документ.

---

# 3. Запреты

В этой задаче MUST NOT:

- писать или изменять Python-код;
- реализовывать F0;
- создавать БД, lockfile, конфигурацию или тесты;
- устанавливать зависимости;
- подключать сеть, API или внешние сервисы;
- заново проверять цены, platform rules и monetization;
- запускать новый multi-agent/Ultra-аудит;
- создавать Git commit или push;
- удалять исходные и audit-документы;
- добавлять архитектуру будущих фаз;
- создавать документы сверх списка в разделе 4.

Работай только с Markdown.

---

# 4. Итоговые документы

## 4.1. Активные

Создай или обнови:

1. `PROJECT_VISION.md`  
   Короткий ненормативный продуктовый ориентир.

2. `F0_TECHNICAL_SPEC.md`  
   **Единственная нормативная спецификация F0.**

3. `docs/f0-minimal-scope.md`  
   Краткий derived checklist.

4. `docs/open-decisions.md`  
   Только нерешённые вопросы F1/F2/content pilot.

5. `docs/f0-risk-register.md`  
   Актуальный риск-регистр.

6. `docs/foundation-owner-review.md`  
   Краткое объяснение исправлений после Ultra.

## 4.2. Исторические

Не удаляй:

- `PROJECT_FOUNDATION.md`;
- `PROJECT_FOUNDATION.vNext.md`;
- `foundation-audit.md`;
- `foundation-change-plan.md`;
- `foundation-diff-summary.md`.

В начало `PROJECT_FOUNDATION.vNext.md` и трёх audit-документов добавь banner:

```text
Status: historical audit artifact.
Superseded for F0 implementation by F0_TECHNICAL_SPEC.md.
Do not use this file as the normative Cursor implementation specification.
Owner-review summary: docs/foundation-owner-review.md.
```

Не переписывай их содержание. Исходный `PROJECT_FOUNDATION.md` не изменяй.

## 4.3. Иерархия авторитетности

Зафиксируй в `F0_TECHNICAL_SPEC.md`, `docs/f0-minimal-scope.md` и `docs/foundation-owner-review.md`:

1. `F0_TECHNICAL_SPEC.md` — единственный normative source для F0;
2. `docs/f0-minimal-scope.md` — derived non-normative checklist;
3. `PROJECT_VISION.md` — non-normative product context;
4. `docs/open-decisions.md` — будущие owner decisions;
5. `docs/f0-risk-register.md` — operational risks;
6. audit/vNext/original Foundation — historical context.

При конфликте всегда побеждает `F0_TECHNICAL_SPEC.md`.

---

# 5. PROJECT_VISION.md

Сделай документ кратким. Включи:

- mission;
- целевую аудиторию;
- JTBD;
- proof-first и anti-AI-slop позиционирование;
- связь с экспертизой автора: CRM, интеграции, автоматизация, бизнес-процессы;
- различие между technical, editorial, audience, format, monetization и lead-generation hypotheses;
- правило «автоматизировать только доказанный процесс»;
- два параллельных трека:

```text
Track A — Content Validation:
manual research → manual script → manual production → publish → measure

Track B — Technical Foundation:
F0 → F1 → F2 → F3
```

Явно укажи:

> Technical F0 MUST NOT block the manual content pilot.

Не включай SQLite DDL, hash preimages, CLI contract, тестовый matrix, цены и platform thresholds.

---

# 6. F0_TECHNICAL_SPEC.md

Создай на основе `PROJECT_FOUNDATION.vNext.md`, но исправь требования ниже.

Статус:

```text
Version: 0.6-owner-reviewed
Status: READY_FOR_F0
```

Не копируй audit narrative. Убирай дублирование. Сохрани только нормы, rationale, acceptance criteria и короткую рамку будущих фаз.

---

## OWN-001 — Hardware и ресурсный предел

Зафиксируй:

```text
Windows 11
Python 3.12.x
Ryzen 3 5300U
16 GB RAM
no GPU requirement
no Docker
single process
```

`≤512 MB peak working set` MAY быть ручным sanity target, но MUST NOT быть flaky automated gate.

Финальный implementation report должен различать:

- measured;
- estimated;
- not measured.

Запрещено придумывать измерения.

---

## OWN-002 — Direct и transitive dependencies

Нормативная формулировка:

```text
Direct runtime dependencies MUST be limited to:
- Typer
- Pydantic v2

Direct development dependencies MUST be limited to:
- pytest
- Ruff
- mypy

Transitive dependencies resolved from these direct dependencies are allowed.

No additional direct dependency MAY be added without:
1. a concrete F0 consumer;
2. an approved specification update;
3. an explanation in the implementation report.
```

Core I/O должен использовать standard library, включая при необходимости:

- `sqlite3`;
- `xml.etree.ElementTree`;
- `json`;
- `hashlib`;
- `urllib.parse`;
- `pathlib`;
- `email.utils`;
- `unicodedata`.

Dependency audit проверяет прямые зависимости проекта, а не весь transitive lock graph.

---

## OWN-003 — Disposable F0 data lifecycle

Добавь:

```text
F0 schema v1 and F0 data are disposable technical artifacts.

No forward migration from F0 schema v1 to F1 is guaranteed.

F1 MAY start from a clean database after Story identity, merge and
retention decisions are approved.

F0 MUST NOT predesign F1 migration or multi-source merge semantics.
```

Не добавляй migration framework, aliases или compatibility layer.

---

## OWN-004 — Точная нормализация текста и дат

### Encoding

Fixture MUST:

- быть UTF-8 или UTF-8 with BOM;
- удалить BOM до parse;
- отклонить другую кодировку как `E_FIXTURE_INVALID`;
- быть local regular file не больше 5 MiB;
- содержать не больше 500 items.

### RSS boundary

Поддерживается только контролируемый RSS 2.0 subset:

- root `rss`;
- `channel`;
- `item`.

Atom, unsupported root, DTD и ENTITY MUST быть отклонены до DB writes. Используется stdlib XML parser. HTML sanitizer в F0 отсутствует.

### Text extraction

Для title и description/summary:

- извлекай XML text nodes в document order;
- XML parser декодирует XML entities;
- encoded markup, являющийся текстом, сохраняется как literal text;
- HTML tags из encoded summary в F0 не удаляются.

### Общая последовательность

До NFC:

```text
CRLF → LF
CR → LF
```

### Title

В точном порядке:

1. extract text;
2. normalize newlines;
3. заменить каждый run Unicode whitespace одним ASCII space;
4. trim;
5. Unicode NFC;
6. reject if empty;
7. maximum 500 Unicode code points.

### Summary

В точном порядке:

1. extract text или empty string;
2. normalize newlines;
3. trim Unicode whitespace по краям;
4. Unicode NFC;
5. сохранить internal spaces и LF;
6. если больше 10 000 Unicode code points — отклонить весь fixture до writes.

Не обрезать данные молча.

### Forbidden controls

После XML decoding отклонить весь fixture, если title/summary содержит:

- U+0000–U+0008;
- U+000B;
- U+000C;
- U+000E–U+001F;
- U+007F.

TAB и LF разрешены в summary. В title whitespace collapsing превращает их в ASCII space.

### Dates

- absent:
  - `published_at = null`;
  - `published_at_raw = null`;
- parseable RFC 822/2822 с explicit timezone:
  - UTC;
  - exact `YYYY-MM-DDTHH:MM:SSZ`;
  - `published_at_raw = null`;
- missing timezone, malformed или unsupported:
  - `published_at = null`;
  - `published_at_raw = trimmed NFC original string`.

MUST NOT угадывать local timezone. Microseconds не экспортируются.

Добавь нормативные test vectors для:

- Cyrillic;
- combining Unicode;
- CRLF;
- repeated title whitespace;
- multiline summary;
- absent date;
- aware date;
- naive date;
- malformed date.

---

## OWN-005 — Точная URL canonicalization

### Validation

URL MUST:

- быть trimmed absolute URL;
- использовать только `http` или `https`;
- иметь hostname;
- не иметь username/password;
- иметь valid port;
- быть не длиннее 4096 Unicode code points до canonicalization.

Ошибка отклоняет весь fixture до writes.

### Canonicalization

В точном порядке:

1. trim Unicode whitespace;
2. parse через stdlib;
3. lowercase scheme;
4. hostname → IDNA ASCII → lowercase;
5. корректно восстановить IPv6 в brackets;
6. удалить default port `80` для HTTP и `443` для HTTPS;
7. сохранить valid non-default port;
8. empty path → `/`;
9. сохранить path text и case;
10. удалить fragment;
11. разобрать query с сохранением blank values и duplicates;
12. удалить query pair, если decoded key case-insensitively:
    - начинается с `utm_`;
    - равен `fbclid`;
    - равен `gclid`;
13. сохранить исходный относительный порядок остальных query pairs;
14. детерминированно re-encode query stdlib-средствами;
15. не сортировать оставшиеся query pairs.

Rationale:

> F0 prefers a false duplicate over an incorrect semantic merge.

Нормативные vectors:

- scheme/host case;
- default/non-default port;
- empty path;
- fragment;
- duplicate keys;
- blank values;
- mixed-case tracking key;
- meaningful query order;
- IDN;
- IPv6;
- credentials rejection;
- invalid port.

---

## OWN-006 — Story без дублированного title

F0 `Story` содержит только:

```text
id
primary_source_id
```

Удалить stored `Story.title` из:

- domain contract;
- SQLite schema;
- package build logic;
- tamper-validation.

Любой Story title вычисляется как:

```text
SourceSnapshot.title referenced by Story.primary_source_id
```

Export берёт title только из immutable SourceSnapshot.

---

## OWN-007 — Export contract

### Source object

Каждый source object содержит ровно:

```json
{
  "canonical_url": "https://example.com/",
  "content_hash": "<64 lowercase hexadecimal characters>",
  "id": "src_<24 lowercase hexadecimal characters>",
  "published_at": null,
  "published_at_raw": null,
  "title": "..."
}
```

`<...>` здесь schema notation, не допустимое runtime value.

Не использовать неоднозначное поле `url`.

### Raw date

`published_at_raw` MUST присутствовать в JSON всегда: string или null.

В Markdown raw date показывается, когда она non-null, поскольку участвует в source hash.

### JSON contract

Предпочти field-contract table вместо второго byte-exact JSON source of truth.

Сохрани:

- persisted canonical payload — source of truth;
- Markdown — derived view;
- UTF-8 without BOM;
- unescaped Unicode;
- sorted object keys;
- indent 2;
- LF;
- one final LF;
- stable array order by ID;
- no current time, absolute path, SQLite row order или randomness.

### Markdown

Обязательно показывает:

- package ID;
- Story ID;
- source ID;
- canonical URL;
- content hash;
- normalized published date;
- raw date при наличии;
- единственный claim и source reference;
- exact lines:

```text
Generation mode: MOCK
Publishable: false
Warning: Demo-only package; no human verification; do not publish.
```

Не использовать `sha256...` или другой невалидный hash placeholder в нормативных runtime-примерах.

---

## OWN-008 — SQLite portability

Удалить `json_valid(payload_json)` из DDL.

Использовать:

```text
payload_json TEXT NOT NULL
bounded length CHECK
```

Полная проверка выполняется application layer:

- `json.loads`;
- Pydantic;
- schema version;
- semantic lineage;
- recomputed identities перед build/export.

Malformed или incompatible payload → `E_DB_SCHEMA`.

Не требовать SQLite JSON1.

---

## OWN-009 — Пропорциональные CLI errors

Стабильные project error codes сохранить для:

- `E_FIXTURE_INVALID`;
- `E_DB_SCHEMA`;
- `E_DB_LOCKED`;
- `E_DB_CORRUPT`;
- `E_STORY_NOT_FOUND`;
- `E_PACKAGE_NOT_BUILT`;
- `E_EXPORT_CONFLICT`;
- `E_EXPORT_PARTIAL`;
- `E_UNEXPECTED`.

Typer/Click syntax errors MAY использовать стандартный framework usage output и exit code.

Для missing argument, unknown command/option и invalid enum тесты проверяют:

- non-zero;
- concise usage guidance;
- no traceback.

`--help` exits 0.

Не создавать собственный parser/error framework только ради `E_USAGE`. Удалить `E_USAGE` из нормативной project error table.

---

## OWN-010 — Пропорциональная integrity validation

Перед package build и export MUST проверяться:

- source ID соответствует canonical URL + content hash;
- content hash соответствует normalized source content;
- Story ID соответствует source ID;
- Story FK существует;
- package fingerprint соответствует immutable inputs;
- package ID соответствует fingerprint;
- payload проходит JSON + Pydantic validation;
- пакет имеет ровно один normative MockClaim;
- claim ID/text/type/status/qualifier/source ID соответствуют derivation contract.

На `stories list` не требуется полная рекомпутация package graph.

Targeted direct-SQL tamper tests покрывают минимум:

1. source content/hash mismatch;
2. Story/source relation mismatch, если её можно инъецировать;
3. package fingerprint/payload mismatch;
4. modified или extra claim.

Не проектировать tamper-evident datastore.

---

## OWN-011 — Пропорциональная export recovery

MUST:

- render, validate и preflight всех requested files до replacement;
- использовать sibling temp file;
- выполнять per-file atomic `os.replace`;
- не обещать group atomicity;
- не перезаписывать differing file без `--force`;
- обнаруживать obvious mixed pair после interrupted `--format all`;
- не оставлять truncated file.

Injected failure после первого replacement SHOULD быть deterministic integration test.

Actual process-kill simulation MUST NOT требоваться.

Это edge-case hardening MUST NOT задерживать завершение после прохождения core F0 DoD. Не добавляй manifest service, filesystem transaction abstraction или workflow engine.

---

## OWN-012 — Parallel content track и timebox

Зафиксируй:

```text
Technical F0 MUST NOT block the manual content pilot.
```

Треки идут параллельно:

```text
Track A — Content Validation:
manual research → manual script → manual production → publish → measure

Track B — Technical Foundation:
F0 → F1 → F2 → F3
```

Timebox:

```text
F0 target: 2–4 focused working days.

After F0 DoD passes, further hardening requires:
- an observed failure; or
- a new owner-approved finding.

Engineering polish alone is not sufficient reason.
```

Это process constraint, не automated software test.

---

# 7. Persistence после patch

Ровно четыре таблицы:

1. `schema_meta`;
2. `sources`;
3. `stories`;
4. `story_packages`.

`stories`:

```sql
stories(
  id TEXT PRIMARY KEY,
  primary_source_id TEXT UNIQUE NOT NULL REFERENCES sources(id)
)
```

Без title.

`story_packages.payload_json` не использует JSON1.

Сохранить:

- foreign keys ON;
- explicit transactions;
- 5-second busy timeout;
- idempotent init;
- no auto-migration;
- no auto-repair;
- no delete/recreate fallback;
- validation всего fixture до writes;
- immutable source revisions.

---

# 8. CLI после patch

Оставить ровно:

```text
ai-newsroom --data-dir PATH db init
ai-newsroom --data-dir PATH harvest run --fixture FILE
ai-newsroom --data-dir PATH stories list [--ids-only]
ai-newsroom --data-dir PATH package build STORY_ID
ai-newsroom --data-dir PATH package export STORY_ID --format json|markdown|all [--force]
```

Не добавлять future placeholders.

---

# 9. Test strategy после patch

Behavior важнее количества тестов.

Обязательные области:

- text/date normalization vectors;
- URL vectors;
- identity/hash reference vector;
- invalid RSS, Atom, DTD, oversized fixture;
- repeat init/harvest/build/export;
- same URL changed content;
- different URLs same content;
- rollback;
- DB version mismatch;
- DB lock;
- Source → Story → package → claim lineage;
- JSON/Markdown goldens;
- Cyrillic/Unicode;
- path with spaces;
- no-network guard;
- manual edit conflict/force;
- targeted tamper cases;
- repeated E2E.

Изменения:

- standard Typer usage tests вместо custom `E_USAGE`;
- direct dependency audit вместо полного lock graph allowlist;
- SQLite JSON1 не требуется;
- no generic full validation on every list read;
- injected export failure SHOULD, actual process kill not required.

---

# 10. Definition of Done

Сохрани исполнимый PowerShell flow:

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

Повторить harvest/build/export и подтвердить:

- same IDs;
- same row counts;
- same JSON SHA-256;
- same Markdown SHA-256;
- no network;
- no Docker;
- no GPU requirement;
- target machine: 16 GB RAM.

---

# 11. Open decisions

Сохранить и уточнить только:

- DEC-001 — multi-source Story identity/manual merge;
- DEC-002 — retention real source content;
- DEC-003 — initial live-source set;
- DEC-004 — beachhead audience/platform/pilot metric;
- DEC-005 — first real LLM provider/data boundary.

В DEC-001 добавить:

```text
F0 schema v1 is disposable.
No migration of F0 Story IDs is required.
```

Не оставлять принятые owner decisions как open.

---

# 12. Risk register

Добавь:

```text
RSK-014
Risk: Engineering F0 delays manual content validation.
Probability: HIGH
Impact: HIGH
Early signal: No pilot videos are published while F0 expands beyond the whitelist
or continues hardening after DoD passes.
Mitigation: Timebox F0 to 2–4 focused working days; run Track A in parallel;
stop hardening after DoD unless an observed failure or owner-approved finding exists.
Owner: Project owner.
Phase: F0 and content pilot.
```

Обнови старые риски, если они ссылаются на:

- 8 GB;
- literal all-package lockfile allowlist;
- mandatory custom `E_USAGE`;
- mandatory full validation on every read;
- mandatory real process-kill simulation.

---

# 13. Reference vector

Независимо пересчитай schema-v1 reference vector после уточнения normalization.

Если значения не меняются — зафиксируй `UNCHANGED`.

Если меняются:

- исправь vector во всех активных документах;
- перечисли old/new;
- объясни точную причину;
- проверь все dependent IDs:
  - content hash;
  - source ID;
  - Story ID;
  - claim ID;
  - input fingerprint;
  - package ID.

Не изменяй identity algorithm без причины из этого prompt.

---

# 14. Consistency pass

После изменений выполни поиск по всем Markdown и проверь:

1. активные документы используют 16 GB;
2. один normative F0 source;
3. `Story.title` не хранится;
4. export использует `canonical_url`;
5. `published_at_raw` есть в export contract;
6. нет runtime hash placeholders `sha256...`;
7. DDL не использует `json_valid`;
8. нет нормативного `E_USAGE`;
9. direct/transitive dependencies различены;
10. F0 schema/data disposable;
11. text normalization имеет точный порядок;
12. URL сохраняет порядок meaningful query pairs;
13. Track A идёт параллельно;
14. RSK-014 существует;
15. open decisions не содержат принятые решения;
16. derived checklist не противоречит spec;
17. historical docs имеют banner;
18. reference vector проверен;
19. исходный `PROJECT_FOUNDATION.md` не изменён;
20. код, DB и зависимости не создавались.

---

# 15. Финальный ответ

Не начинай F0.

Ответь:

## Verdict

## Created files

## Updated files

## Authoritative document order

## Corrections applied

Сопоставь изменения с `OWN-001`–`OWN-012`.

## Consistency checks

Покажи PASS/FAIL для 20 пунктов.

## Reference vector verification

## Remaining open decisions

## Constraints confirmed

Подтверди:

- no code;
- no dependencies;
- no DB;
- no Docker;
- no API/network integration;
- original Foundation unchanged.

## Recommendation

Выбери одно:

- `READY_FOR_F0`;
- `READY_AFTER_DOCUMENT_FIX`;
- `NOT_READY_FOR_F0`.

## Next step

Только:

> Implement F0 from `F0_TECHNICAL_SPEC.md` using a separate implementation prompt.

---

# Критерий успеха

Результат успешен, если:

- полезные выводы Ultra сохранены;
- остаточные противоречия исправлены;
- F0 стал проще, а не шире;
- спецификация технически исполнима;
- normalization, identities и exports однозначны;
- SQLite portable;
- validation пропорциональна риску;
- manual content pilot не блокируется;
- Cursor получает один нормативный документ.
