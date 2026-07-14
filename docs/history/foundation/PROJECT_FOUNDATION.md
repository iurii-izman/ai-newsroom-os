# AI Newsroom OS — Project Foundation for Cursor

**Версия:** 0.4  
**Дата проверки:** 13 июля 2026  
**Статус:** рабочая спецификация  
**Рабочее название:** `AI Signal / AI Сигнал` — не фиксировать в коде до проверки бренда и handles.

---

## 0. Инструкция Cursor

Прочитай этот файл целиком. Он является продуктовой спецификацией, архитектурным ограничителем и backlog.

### Правила выполнения

1. Не реализуй весь конвейер сразу.
2. Начни только с раздела **Foundation Sprint F0**.
3. Перед кодом осмотри репозиторий и создай `docs/implementation-plan.md`.
4. Не подключай Docker, n8n, Remotion, TTS, web UI и публикационные API в F0.
5. Любая внешняя интеграция обязана иметь mock-режим.
6. Не добавляй URL, API-возможности и тарифы из памяти — проверяй официальную документацию.
7. Не записывай секреты в код, fixtures, логи и git.
8. После каждого шага запускай тесты.
9. Продуктовые или архитектурные изменения фиксируй через ADR.
10. После задачи дай отчёт: выполнено, изменённые файлы, проверки, решения, ограничения, следующий минимальный шаг.

---

# 1. Решение и позиционирование

Проект не должен быть фабрикой массовых AI-пересказов.

Он должен стать **редакционной операционной системой**, которая:

- обнаруживает значимые AI-события;
- объединяет материалы об одном событии;
- проверяет факты и отделяет заявления поставщика от подтверждённых результатов;
- предлагает оригинальные углы подачи;
- создаёт проверяемый сценарий и production plan;
- готовит несколько платформенных версий;
- накапливает редакционную память на основе результатов.

## 1.1. Контентное обещание

> AI без шума: что изменилось, что проверено и что можно применить в работе.

Каждый материал должен отвечать:

1. Что произошло?
2. Почему это важно именно нашей аудитории?
3. Что подтверждено источниками или тестом?
4. Что зритель может сделать сегодня?

## 1.2. Центральная сущность

Центральная сущность — не видео, а **Story Package**.

Один Story Package может породить:

- `FAST`: 30–45 секунд;
- `STANDARD`: 60–90 секунд;
- `DEEP_SHORT`: 90–180 секунд;
- Telegram-пост с источниками;
- текстовый пост или карусель;
- часть недельного дайджеста;
- запись в редакционной памяти.

---

# 2. Проверенные корректировки к концепции v0.1

## 2.1. Универсальные 60 секунд — слабое ограничение

YouTube поддерживает Shorts до трёх минут. TikTok Creator Rewards требует оригинальные ролики длительностью не менее минуты. Поэтому один мастер для всех площадок не оптимален.

## 2.2. YouTube monetization

Разделять:

- ранний уровень YPP: 500 подписчиков, 3 публичные публикации за 90 дней и 3 млн Shorts-просмотров за 90 дней либо 3 000 часов;
- рекламную монетизацию: 1 000 подписчиков и 10 млн Shorts-просмотров за 90 дней либо 4 000 часов.

Moldova входит в официальный список YPP. Доход от платформы не должен быть единственной бизнес-моделью.

## 2.3. TikTok Creator Fund устарел

Ориентир — Creator Rewards Program:

- 18+;
- личный аккаунт;
- 10 000 подписчиков;
- 100 000 просмотров за 30 дней;
- оригинальные ролики от одной минуты;
- доступность программы в регионе аккаунта.

Доступность в Moldova не считать подтверждённой, пока функция не отображается в аккаунте.

## 2.4. Массовый шаблонный контент создаёт риск

YouTube относит повторяющийся или массово произведённый контент к `inauthentic content`. AI-инструменты допустимы, но каждый материал должен содержать минимум два элемента собственной ценности:

- тест;
- демонстрацию;
- сравнение;
- расчёт;
- авторский вывод;
- практический workflow;
- оригинальную схему;
- позицию, подтверждённую доказательствами.

## 2.5. AI disclosure — поле данных, а не ручная память

Каждый пакет должен иметь:

```yaml
ai_disclosure_required: YES | NO | REVIEW
ai_disclosure_reason: "..."
```

YouTube и TikTok требуют маркировку реалистичного синтетического или существенно изменённого контента в предусмотренных случаях.

## 2.6. Автопубликация сложнее, чем кажется

- TikTok ограничивает публикации неаудированных приложений приватным режимом.
- Instagram publishing доступен профессиональным аккаунтам и поддерживает Reels.
- Telegram Bot API подходит для отправки MP4.
- YouTube требует OAuth, квоты, валидацию metadata и обработку ошибок.

В MVP публикация ручная.

## 2.7. Уточнение бюджета

- Buffer Free: 3 канала и 10 запланированных публикаций на канал.
- ElevenLabs Starter: $6 помесячно, около $5/мес при годовой оплате.
- n8n Cloud Starter: €20/мес при годовой оплате; Community Edition доступна self-hosted.
- OpenAI API не считать гарантированно бесплатным.
- Gemini Developer API имеет официальный ограниченный free tier.
- Remotion source-available, но не OSI open-source; текущая лицензия бесплатна для индивидуального автора и компании до трёх сотрудников.

## 2.8. Whisper не нужен для известного TTS-текста

Для синтетического голоса использовать timestamps TTS, forced alignment или генерацию по фразам. Whisper оставить для живого голоса и импортированного видео.

## 2.9. Универсального лучшего времени публикации нет

Время публикации — экспериментальная переменная, а не константа проекта.

---

# 3. Целевая аудитория

## 3.1. Primary audience

Русскоязычные специалисты, фрилансеры, менеджеры и предприниматели 23–42 лет, которые:

- хотят применять AI в работе;
- не успевают читать десятки источников;
- ценят ограничения и реальные тесты;
- работают с автоматизацией, CRM, данными, разработкой, документами или управлением.

## 3.2. Jobs To Be Done

### Быть в курсе

> За несколько минут понять, что реально важно, не читая десятки публикаций.

### Применять

> Увидеть конкретный рабочий сценарий и решить, стоит ли тратить время на инструмент.

### Не попасться на хайп

> Отличить проверенный результат от маркетингового обещания.

## 3.3. Авторское преимущество

Основная специализация канала должна опираться на реальную экспертизу автора:

- CRM;
- бизнес- и системный анализ;
- API и интеграции;
- n8n/Make;
- AI automation;
- процессы бизнеса.

Это сильнее общего новостного канала «про всё в AI».

---

# 4. Контентная система

## 4.1. Стартовые форматы

### `AI_SIGNAL`

Новость через последствия:

1. наблюдаемый результат;
2. что выпустили;
3. первичный источник;
4. что реально изменилось;
5. кого затрагивает;
6. что проверить.

### `TESTED_FOR_YOU`

Практический тест:

1. обещание;
2. реальная задача;
3. условия теста;
4. результат;
5. ограничение;
6. кому подходит;
7. verdict.

Это главный формат для доверия, оригинальности и будущего affiliate.

### `AI_WORKFLOW`

Объяснение процесса:

1. проблема;
2. схема;
3. инструменты;
4. критическое ограничение;
5. ожидаемый результат;
6. следующий шаг.

## 4.2. Контент-микс

| Категория | Доля |
|---|---:|
| Проверки и workflow | 40% |
| Новости с последствиями | 30% |
| Объяснения | 20% |
| Мнения и эксперименты | 10% |

## 4.3. Proof-first framework

```text
PROOF → EVENT → EVIDENCE → IMPLICATION → ACTION → BRIDGE
```

- `PROOF`: результат, интерфейс, цифра, ошибка или до/после.
- `EVENT`: что произошло без вступления.
- `EVIDENCE`: источник или тест.
- `IMPLICATION`: что меняется и для кого.
- `ACTION`: что сделать зрителю.
- `BRIDGE`: связь со следующим материалом или owned channel.

## 4.4. Запрещённые паттерны

- «Привет, друзья»;
- «В этом видео мы рассмотрим»;
- пустая срочность;
- «профессия умерла» без доказательств;
- цифры без источника;
- пересказ одного заголовка;
- абстрактный CTA без связи с сюжетом;
- робот, неоновый мозг и случайный код вместо визуального доказательства.

---

# 5. Редакционная политика

## 5.1. Иерархия источников

### Tier A — первичные

Официальные блоги, release notes, документация, GitHub-релизы, model cards, научные работы, официальные страницы продукта.

### Tier B — контекст

Авторитетные технологические издания, интервью, аналитика, независимые тесты.

### Tier C — обнаружение

Reddit, Hacker News, Telegram, X, YouTube и комментарии.

Tier C может дать сигнал, но не должен быть единственным доказательством центрального факта.

## 5.2. Claim Ledger

```yaml
claims:
  - id: claim_001
    text: "Компания выпустила функцию X"
    type: FACT
    source_ids: [src_001]
    confidence: HIGH
    status: VERIFIED

  - id: claim_002
    text: "Функция сокращает работу в два раза"
    type: TEST_RESULT
    source_ids: [test_001]
    confidence: MEDIUM
    status: QUALIFIED
    qualifier: "в нашем тестовом сценарии"
```

Типы:

- `FACT`
- `VENDOR_CLAIM`
- `INFERENCE`
- `OPINION`
- `PREDICTION`
- `TEST_RESULT`

Статусы:

- `UNVERIFIED`
- `VERIFIED`
- `QUALIFIED`
- `CONFLICTED`
- `REJECTED`

## 5.3. Publication gates

Сюжет не проходит дальше, если:

- нет первичного источника или двух независимых подтверждений;
- центральное утверждение не проверено;
- нет собственной добавленной ценности;
- отсутствует визуальное доказательство;
- неясны права на материалы;
- headline обещает больше, чем доказывает сценарий;
- тема слабо соответствует аудитории.

## 5.4. Права на assets

```yaml
rights_status: OWNED | LICENSED | FAIR_USE_REVIEW | UNKNOWN
license_name: null
source_url: null
attribution_required: false
allowed_for_commercial_use: true
```

`UNKNOWN` блокирует автоматический рендер и публикацию.

## 5.5. arXiv

Metadata можно использовать по условиям API. Полный текст и иллюстрации могут быть защищены авторским правом. По умолчанию хранить metadata, ссылку, собственный краткий конспект и минимально необходимую цитату.

---

# 6. Scope MVP

## 6.1. Что строим

```text
RSS / ручной URL
→ нормализация
→ SQLite
→ дедупликация
→ Story Cluster
→ Editorial Brief
→ Claim Ledger
→ Editorial Score
→ Angle Candidates
→ Script Draft
→ Production Plan
→ Markdown + JSON export
```

## 6.2. Чего не строим до подтверждения формата

- web-панель;
- Docker-инфраструктуру;
- микросервисы;
- векторную БД;
- сложных AI-агентов;
- автогенерацию B-roll;
- автопубликацию;
- OAuth пяти платформ;
- EN-версию;
- собственный видеоредактор;
- генерацию десятков роликов в день.

## 6.3. Human Gates

1. `VERIFY_GATE`
2. `ANGLE_GATE`
3. `SCRIPT_GATE`
4. `FINAL_QA_GATE`
5. `PUBLISH_GATE`

Автоматизация предлагает, но не обходит gate.

---

# 7. Архитектура

## 7.1. Ограничения среды

Целевая машина: Windows 11, Ryzen 3 5300U, 16 GB RAM, без CUDA. Поэтому:

- Python-first;
- SQLite;
- один процесс;
- без обязательного Docker;
- тяжёлые модели через API;
- видео подключать после редакционного MVP.

## 7.2. Стек Foundation

- Python 3.12+;
- `uv`;
- Typer;
- Pydantic v2;
- SQLite;
- SQLAlchemy 2 или тонкий repository layer;
- httpx;
- feedparser;
- trafilatura как optional extractor;
- RapidFuzz;
- Jinja2;
- pytest;
- ruff;
- pyright или mypy;
- стандартный logging/JSON;
- Mock LLM.

Cursor должен выбрать текущие совместимые версии и зафиксировать lockfile.

## 7.3. Стиль

Модульный монолит:

```text
domain
application
infrastructure
interfaces
```

Домен не зависит от n8n, конкретной LLM, Remotion и платформ публикации.

## 7.4. State Machine

```text
DISCOVERED
→ NORMALIZED
→ CLUSTERED
→ RESEARCHED
→ VERIFIED
→ SCORED
→ ANGLED
→ SCRIPTED
→ APPROVED
→ PRODUCTION_READY
→ RENDERED
→ QA_PASSED
→ SCHEDULED
→ PUBLISHED
→ MEASURED
→ LEARNED
```

Foundation реализует путь только до `PRODUCTION_READY`.

Каждый переход сохраняет timestamp, actor, reason и валидирует preconditions.

---

# 8. Основные модели

## 8.1. Source

```yaml
id: src_...
url: https://...
canonical_url: https://...
source_name: OpenAI
source_tier: A
source_type: OFFICIAL_BLOG
title: ...
author: null
published_at: ...
discovered_at: ...
language: en
summary_raw: ...
content_excerpt: ...
content_hash: sha256...
fetch_status: SUCCESS
```

## 8.2. Story

```yaml
id: story_...
canonical_event: "Компания X выпустила функцию Y"
topic: PRODUCT_RELEASE
status: CLUSTERED
source_ids: [src_001, src_002]
primary_source_id: src_001
entities: ["Company X", "Product Y"]
audience_segments: [automation, business]
first_seen_at: ...
latest_source_at: ...
```

## 8.3. Editorial Brief

```yaml
story_id: story_...
why_now: ...
what_changed: ...
what_is_not_new: ...
who_cares: ...
practical_uses: []
risks: []
open_questions: []
visual_proof_options: []
```

## 8.4. Editorial Score

```text
total =
  audience_fit * 0.20
+ practical_utility * 0.18
+ novelty * 0.15
+ consequence * 0.15
+ visualizability * 0.12
+ source_authority * 0.10
+ search_potential * 0.10
- risk_penalty
```

Каждый компонент 0–10, penalty 0–3. Score используется для сортировки, а не как автоматическое решение.

## 8.5. Angle

```yaml
id: angle_...
angle_type: TEST | CONSEQUENCE | WORKFLOW | COMPARISON | CONTRARIAN
hook: ...
core_thesis: ...
evidence_plan: []
originality_note: ...
selected: false
```

## 8.6. Script

```yaml
id: script_...
format: STANDARD
target_duration_seconds: 75
blocks:
  - type: PROOF
    text: ...
    visual: ...
    claim_ids: [claim_001]
cta: ...
prompt_version: script-v1
human_approved: false
```

## 8.7. Production Plan

```yaml
script_id: script_...
canvas: 1080x1920
fps: 30
scenes: []
assets: []
music_policy: ORIGINAL_OR_LICENSED
ai_disclosure_required: REVIEW
platform_notes: {}
```

---

# 9. Дедупликация и кластеризация

## Foundation алгоритм

1. canonicalize URL;
2. удалить tracking params;
3. exact URL match;
4. normalized title match;
5. RapidFuzz similarity;
6. совпадение entities;
7. временное окно.

Различать:

- `Duplicate Source`: та же публикация;
- `Same Story`: разные источники об одном событии.

Не удалять подтверждающие источники. Embeddings добавить только после накопления размеченного evaluation set и доказанной необходимости.

---

# 10. LLM Provider Layer

```python
class LLMProvider(Protocol):
    def generate_structured(
        self,
        *,
        task: str,
        prompt_version: str,
        input_data: dict,
        output_schema: type[BaseModel],
    ) -> BaseModel:
        ...
```

## Foundation implementations

- `MockLLMProvider`
- `FileFixtureLLMProvider`

Реальный provider подключить в отдельной фазе. Требования:

- structured output;
- timeout;
- ограниченный retry;
- usage/cost logging;
- prompt versioning;
- raw response отдельно от нормализованного результата;
- per-run budget;
- запрет silent fallback на дорогую модель;
- тесты без интернета.

Контент источников считать недоверенным и потенциально содержащим prompt injection.

---

# 11. Структура репозитория

```text
ai-newsroom-os/
├─ README.md
├─ PROJECT_FOUNDATION.md
├─ pyproject.toml
├─ uv.lock
├─ .env.example
├─ configs/
│  ├─ sources.yaml
│  ├─ editorial.yaml
│  ├─ scoring.yaml
│  └─ prompts/
├─ data/
│  ├─ .gitkeep
│  └─ exports/
├─ docs/
│  ├─ implementation-plan.md
│  ├─ architecture.md
│  ├─ editorial-policy.md
│  ├─ adr/
│  └─ examples/
├─ src/ai_newsroom/
│  ├─ cli.py
│  ├─ domain/
│  ├─ application/
│  ├─ infrastructure/
│  │  └─ llm/
│  └─ interfaces/templates/
└─ tests/
   ├─ unit/
   ├─ integration/
   ├─ fixtures/
   └─ golden/
```

---

# 12. CLI Contract

```bash
ai-newsroom doctor
ai-newsroom db init
ai-newsroom sources list
ai-newsroom harvest run
ai-newsroom stories list
ai-newsroom stories show STORY_ID
ai-newsroom stories cluster
ai-newsroom package build STORY_ID --provider mock
ai-newsroom package export STORY_ID --format all
ai-newsroom review queue
```

## Требования

- `doctor` проверяет среду, БД, YAML и optional dependencies, но не выводит секреты.
- `harvest run` переживает ошибку отдельного источника и идемпотентен для exact duplicate.
- `package build` работает в mock-режиме.
- `package export` создаёт JSON, Markdown, claims и production plan.
- Перезапись файлов только через `--force`.

Экспорт:

```text
data/exports/<story-id>/
├─ story-package.json
├─ story-package.md
├─ claims.yaml
├─ script.md
└─ production-plan.yaml
```

---

# 13. Prompt Pack v1

Промпты хранить отдельно и версионировать.

## Brief

```text
Ты редактор доказательного русскоязычного медиа об AI для работы и бизнеса.
Используй только предоставленные источники.
Разделяй факты, заявления производителя, выводы и прогнозы.
Опиши: что произошло, что новое, что не изменилось, кому важно,
практические применения, ограничения, открытые вопросы и визуальные доказательства.
Верни только structured output.
```

## Claims

```text
Разложи материал на атомарные проверяемые утверждения.
Для каждого укажи type, source_ids, confidence, status и qualifier.
Не считай маркетинговое заявление независимым фактом.
```

## Angles

```text
Создай 5 разных углов: consequence, workflow, test, comparison, limitation.
Для каждого: hook, thesis, audience, evidence plan, original value, visual proof, risk.
Не создавай headline, который сценарий не сможет доказать.
```

## Script

```text
Структура: PROOF → EVENT → EVIDENCE → IMPLICATION → ACTION → BRIDGE.
Используй короткие произносимые предложения.
Цифры только из Claim Ledger.
Сохраняй qualifiers.
Привяжи фактические блоки к claim_id.
```

## Production Plan

```text
Приоритет визуалов:
1. собственный скринкаст;
2. официальный источник;
3. собственная схема;
4. кинетическая типографика;
5. лицензированный stock.
Для каждого внешнего asset укажи rights review.
```

---

# 14. Content Experiment: 24–30 роликов

Технический pipeline не доказывает продукт.

## Cohorts

- 8–10 `AI_SIGNAL`;
- 8–10 `TESTED_FOR_YOU`;
- 8–10 `AI_WORKFLOW`.

## Метрики

### Attention

- удержание первых секунд;
- average view duration;
- average percentage viewed;
- completion;
- rewatch, если доступен.

### Intent

- saves;
- shares;
- содержательные комментарии;
- profile visits;
- followers per 1 000 views;
- переходы в Telegram.

### Production

- ручное время;
- стоимость;
- количество исправлений;
- время от сигнала до публикации;
- фактические ошибки.

## Go/No-Go

Автоматизацию продолжать, если:

1. опубликовано минимум 24 материала;
2. найден хотя бы один повторяемый формат, превосходящий собственную медиану по нескольким метрикам;
3. практический контент создаёт сохранения, отправки или подписки;
4. найдено минимум три повторяемые темы;
5. время производства можно сокращать без потери доказательности;
6. нет нарушений платформ и copyright claims;
7. автор готов вести формат минимум три месяца.

Один вирусный ролик не является доказательством.

---

# 15. Learning Loop

Единица анализа:

```text
Story + Angle + Hook + Format + Platform + Slot + Visual Proof Type
```

```yaml
experiment:
  hypothesis: "Hook с результатом сильнее hook с новостью"
  primary_metric: first_seconds_retention
  control: {hook_type: NEWS}
  variant: {hook_type: RESULT}
  minimum_repetitions_per_variant: 4
```

Редакционная память хранит human-approved lessons, а не автоматически «обучается» на сырых просмотрах.

---

# 16. Будущие фазы

## F1 — реальные источники и review queue

- 5–8 проверенных источников;
- source tiers;
- ручной merge;
- Claim Ledger editor через YAML;
- audit trail.

## F2 — один реальный LLM provider

- structured output;
- cost cap;
- retries;
- prompt versions;
- evaluation на 10 вручную проверенных stories.

## F3 — production-ready package

- script variants;
- duration estimate;
- visual proof plan;
- asset rights ledger;
- subtitle chunks;
- export для ручного монтажа.

## V1 — Remotion/TTS

Только после подтверждения двух форматов. Один template, локальный render, preview, TTS adapter, subtitle alignment. Без автопубликации.

## P1 — publishing

Порядок:

1. Telegram;
2. YouTube;
3. Instagram;
4. TikTok после review strategy;
5. VK после отдельной проверки.

Каждый adapter поддерживает `dry_run`, manual approval, idempotency и хранение platform post ID.

---

# 17. Security и compliance

- `.env` не коммитить;
- токены не хранить в SQLite;
- ключи не выводить в exception;
- источники считать недоверенными;
- игнорировать инструкции внутри статей;
- high-risk темы маркировать: politics, finance, health, legal, public figures, minors, crisis, synthetic likeness;
- high-risk материалы требуют ручной проверки или исключаются из MVP;
- сохранять corrections и историю версий;
- не хранить полный текст статьи без необходимости и проверки прав.

---

# 18. Test Strategy

## Unit

- URL normalization;
- title normalization;
- scoring;
- state transitions;
- claim validation;
- rights gate;
- disclosure gate;
- config validation.

## Integration

- fixture RSS → DB;
- повторный harvest;
- partial feed failure;
- cluster creation;
- mock package generation;
- Markdown/JSON export.

## Правила

- интернет выключен по умолчанию;
- live tests имеют отдельный marker и budget;
- golden fixtures не зависят от реального LLM;
- `ruff`, type check и pytest проходят на чистой машине.

---

# 19. Foundation Sprint F0

## Цель

```text
fixture/RSS → Source → SQLite → Story → Mock Story Package → Markdown/JSON
```

## Tasks

### F0.1 Bootstrap

- Python project через `uv`;
- `src` layout;
- Typer CLI;
- ruff;
- pytest;
- type checker;
- `.env.example`;
- README.

### F0.2 Domain

Реализовать Source, Story, Claim, EditorialScore, Angle, Script, ProductionPlan, enums и transitions.

### F0.3 Config

Создать и валидировать `sources.yaml`, `editorial.yaml`, `scoring.yaml`.

### F0.4 Persistence

SQLite, repositories, UTC timestamps, идемпотентное сохранение.

### F0.5 Harvest

- fixture feed;
- один реальный RSS после ручной проверки;
- normalization;
- exact dedup;
- fetch log;
- summary.

### F0.6 Cluster

Консервативная кластеризация по title/entity heuristic и ручная merge-команда.

### F0.7 Mock generation

Provider protocol, mock provider, fixture response, schema validation.

### F0.8 Export

JSON, Markdown, claims YAML, script и production plan.

### F0.9 Tests

Минимум 15 содержательных тестов и один end-to-end fixture test.

## Definition of Done

```bash
uv sync
uv run ai-newsroom doctor
uv run ai-newsroom db init
uv run ai-newsroom harvest run --fixture tests/fixtures/feeds/sample.xml
uv run ai-newsroom stories list
uv run ai-newsroom package build STORY_ID --provider mock
uv run ai-newsroom package export STORY_ID --format all
uv run pytest
```

Все команды работают на чистой машине без Docker и внешнего API.

---

# 20. Первый запрос для Cursor

```text
Прочитай PROJECT_FOUNDATION.md целиком.

Не реализуй весь проект. Выполни только Foundation Sprint F0.

Сначала:
1. исследуй текущий репозиторий;
2. создай docs/implementation-plan.md;
3. создай ADR по модульному монолиту и SQLite;
4. покажи список создаваемых и изменяемых файлов;
5. проверь, что решение работает на 16 GB RAM без Docker.

Затем реализуй вертикальный срез:
fixture RSS → SQLite → Story → Mock Story Package → JSON/Markdown export.

Требования:
- Python + uv;
- Typer;
- Pydantic;
- SQLite;
- mock LLM;
- no network in tests;
- минимум 15 тестов;
- выполнить Definition of Done F0;
- не подключать TTS, Remotion, n8n, web UI и publishing APIs.

После реализации запусти проверки и дай отчёт:
## Выполнено
## Изменённые файлы
## Проверки
## Принятые решения
## Ограничения
## Следующий минимальный шаг
```

---

# 21. Официальные источники

Проверено 13 июля 2026. Перед конкретной интеграцией проверять повторно.

## YouTube

- https://support.google.com/youtube/answer/15424877
- https://support.google.com/youtube/answer/12779649
- https://support.google.com/youtube/answer/72851
- https://support.google.com/youtube/answer/13429240
- https://support.google.com/youtube/answer/7101720
- https://support.google.com/youtube/answer/1311392
- https://support.google.com/youtube/answer/14328491
- https://support.google.com/youtube/answer/13486873

## TikTok

- https://support.tiktok.com/en/business-and-creator/creator-rewards-program/creator-rewards-program
- https://support.tiktok.com/en/business-and-creator/tiktok-creator-fund-us/tiktok-creator-fund-update-us
- https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content
- https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- https://developers.tiktok.com/doc/content-posting-api-get-started

## Instagram / Meta

- https://developers.facebook.com/documentation/instagram-platform/overview
- https://developers.facebook.com/documentation/instagram-platform/content-publishing
- https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login
- https://creators.instagram.com/original-content-guidelines

## Telegram

- https://core.telegram.org/bots/api
- https://telegram.org/blog/monetization-for-channels

## Tools и APIs

- https://n8n.io/pricing/
- https://elevenlabs.io/pricing
- https://buffer.com/pricing
- https://www.remotion.dev/docs/license
- https://www.remotion.dev/docs/pricing
- https://openai.com/api/pricing/
- https://ai.google.dev/gemini-api/docs/pricing
- https://docs.anthropic.com/en/docs/about-claude/pricing
- https://api-docs.deepseek.com/quick_start/pricing

## Assets и research

- https://www.pexels.com/license/
- https://pixabay.com/service/license-summary/
- https://info.arxiv.org/help/api/tou.html
- https://info.arxiv.org/help/api/index.html

---

# 22. Финальный критерий

Проект успешен не тогда, когда автоматически создаёт много видео.

Он успешен, когда повторяемо создаёт материалы, которые:

1. основаны на проверяемых источниках;
2. содержат собственную ценность;
3. узнаваемы;
4. удерживают целевую аудиторию;
5. приводят к сохранениям, подпискам и доверию;
6. становятся быстрее и дешевле без деградации качества;
7. формируют редакционную память, которую сложно скопировать.

> Автоматизировать следует только доказанный процесс.
