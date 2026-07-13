# OpenAI Codex — финальная стратегия плагинов и настроек

**Проект:** AI Newsroom OS / AI Shorts Machine  
**Версия:** 2.0 — Codex-only  
**Дата проверки:** 13 июля 2026  
**Среда:** OpenAI Codex в приложении ChatGPT / Codex CLI  
**Машина:** Windows 11, Ryzen 3 5300U, 16 GB RAM  
**Текущая фаза:** финализация документации и подготовка Foundation F0

---

# 1. Важное уточнение

В этом документе рассматривается **только OpenAI Codex**, доступный в приложении ChatGPT и через Codex CLI.

Не рассматриваются:

- Cursor IDE;
- Cursor Marketplace;
- VS Code-плагины Cursor;
- настройки Cursor;
- Cursor Agent;
- расширения Cursor.

Термин «Codex» далее означает coding agent OpenAI.

---

# 2. Итоговое решение

Для текущей фазы не нужен большой набор плагинов.

## Установить или подключить сейчас

| Компонент | Решение | Причина |
|---|---|---|
| Git | Обязательно | Baseline, diff, rollback, worktrees |
| `AGENTS.md` | Обязательно | Главный проектный контроль Codex |
| Project `.codex/config.toml` | Рекомендуется | Sandbox, approvals, сеть |
| Context7 | Опционально | Актуальная документация библиотек |
| GitHub integration/plugin | После создания remote | Issues, PR, CI, remote review |
| Codex Security | После появления F0-кода | Security diff scan |

## Не устанавливать сейчас

- большие methodology-плагины;
- browser automation;
- scraping-платформы;
- cloud/deployment-плагины;
- hosted database plugins;
- несколько документационных MCP;
- несколько GitHub-интеграций;
- Remotion;
- Langfuse;
- OpenAI Developers;
- Hugging Face;
- Sentry.

Главное правило:

> Плагин подключается только под существующую задачу и отключается вне её фазы.

---

# 3. Что такое плагин в Codex

Плагин Codex может включать:

- Skills — инструкции и повторяемые рабочие процедуры;
- Apps/connectors — доступ к внешним системам;
- MCP servers — дополнительные инструменты;
- Hooks — команды, запускаемые в lifecycle points;
- browser capabilities;
- templates для scheduled tasks.

Из-за этого плагин — не безобидная «подсказка». Он может:

- читать внешние данные;
- выполнять команды;
- менять файлы;
- обращаться к сети;
- выполнять write-actions во внешних сервисах;
- добавлять инструкции в контекст агента.

Перед установкой нужно проверять не название, а фактические capabilities и permissions.

---

# 4. Является ли codex-marketplace.com полным списком

Нет.

`codex-marketplace.com` — сторонний каталог для обнаружения community-плагинов. Он не является официальным реестром OpenAI и не может быть полным.

У Codex нет одного постоянного универсального списка, потому что плагины могут приходить из:

- встроенного каталога;
- OpenAI marketplace;
- workspace marketplace;
- project marketplace;
- personal marketplace;
- Git-backed marketplace;
- локальных skills и MCP-конфигураций.

## Авторитетный способ посмотреть доступное

### В приложении ChatGPT / Codex

Открыть:

```text
Codex → Plugins
```

### В Codex CLI

```text
/plugins
```

После установки плагина нужно начать новый thread/session, чтобы его skills и tools загрузились.

## Источники в порядке доверия

1. Встроенный каталог Codex.
2. Официальный репозиторий `openai/plugins`.
3. Официальный плагин поставщика.
4. Проверенный open-source community plugin.
5. Сторонний агрегатор только как поисковая витрина.

---

# 5. Что важнее плагинов

Для качества Codex в текущем проекте важнее:

1. Git baseline;
2. один нормативный `F0_TECHNICAL_SPEC.md`;
3. короткий и точный `AGENTS.md`;
4. безопасный sandbox;
5. отключённая сеть для F0 runtime/tests;
6. понятный Definition of Done;
7. отдельный review-проход;
8. минимальное число активных tools.

Большое количество плагинов не увеличивает интеллект модели. Оно увеличивает:

- tool-selection noise;
- контекст;
- число конфликтующих инструкций;
- поверхность permissions;
- сетевую зависимость;
- риск случайных write-actions;
- сложность воспроизведения.

---

# 6. Плагинная стратегия по фазам

## 6.1. Сейчас: документация и подготовка F0

### Обязательные плагины

Нет.

Codex уже умеет:

- читать репозиторий;
- редактировать файлы;
- запускать команды;
- работать с Git;
- выполнять review;
- использовать sandbox;
- читать `AGENTS.md`.

### Опционально: Context7

Подключать только если доступен в текущем Codex plugin browser или как доверенный MCP.

Полезен для актуальных API:

- Python 3.12;
- `uv`;
- Pydantic v2;
- Typer;
- pytest;
- Ruff;
- mypy.

Правило использования:

```text
Use Context7 only to verify version-sensitive APIs.
Do not add dependencies or expand scope merely because another API exists.
```

Context7 не является runtime dependency проекта.

Для F0:

- агент может использовать Context7 при разработке;
- приложение и тесты не должны пользоваться сетью;
- финальный DoD выполняется offline.

Если Context7 недоступен, это не блокирует F0.

---

## 6.2. После инициализации GitHub remote

### GitHub plugin/integration

Нужен только для:

- GitHub issues;
- pull requests;
- remote code review;
- GitHub Actions;
- CI logs;
- публикации branch/PR.

Не нужен для:

- локального кодинга;
- локального diff;
- локального commit;
- выполнения F0.

### Начальные permissions

| Действие | Политика |
|---|---|
| Read repository | Разрешить |
| Read issues/PR | Разрешить |
| Read CI status/logs | Разрешить |
| Draft issue/PR text | Разрешить |
| Create issue | Только с подтверждением |
| Create PR | Только с подтверждением |
| Push branch | Только с подтверждением |
| Merge PR | Не автоматически |
| Delete branch/release | Запретить |
| Repository settings | Запретить |

Codex app уже имеет встроенную работу с Git и worktrees. Не устанавливать второй Git-assistant без наблюдаемой необходимости.

---

## 6.3. После реализации F0

### Codex Security

Это главный специальный плагин для F0.

Релевантные границы проекта:

- XML parsing;
- DTD/entity rejection;
- file-size limits;
- Unicode normalization;
- URL canonicalization;
- path handling;
- SQLite;
- export overwrite;
- error sanitization;
- network isolation.

### Порядок запуска

1. `ruff`;
2. `mypy`;
3. `pytest`;
4. полный F0 DoD;
5. обычный `/review` или `codex review`;
6. Codex Security diff scan;
7. validation найденных проблем;
8. исправление только подтверждённых findings;
9. один финальный обычный scan при необходимости.

### Не запускать пока

Deep security scan не нужен для небольшого F0.

Он оправдан позже, когда появятся:

- live network ingestion;
- секреты;
- API;
- внешние интеграции;
- публикация;
- web UI;
- существенный объём кода.

---

## 6.4. F1 — реальные источники

На старте F1 плагин не нужен.

Порядок:

```text
official RSS
→ standard-library или обычный HTTP client
→ простой extractor
→ внешний сервис только при доказанной проблеме
```

Если реальный источник невозможно нормально обрабатывать, выбрать **один** класс инструмента:

| Проблема | Возможный инструмент |
|---|---|
| Поиск релевантных материалов | Exa |
| Извлечение страницы в чистый текст | Firecrawl |
| Готовые scraping workflows | Apify |
| JS-heavy/authenticated browser | Browserbase |

Не подключать все одновременно.

Решение о таком плагине должно включать:

- конкретный source;
- наблюдаемую проблему;
- стоимость;
- retention;
- передаваемые данные;
- fallback;
- критерий удаления.

---

## 6.5. F2 — первый реальный LLM

### OpenAI Developers plugin

Подключать только если OpenAI выбран первым provider после evaluation.

Полезен для:

- актуальной API-документации;
- structured outputs;
- setup;
- troubleshooting;
- Agents SDK, если он реально потребуется.

Сам факт, что проект связан с AI, не является причиной установки.

### Langfuse

Подключать только после появления реальных prompt runs.

До этого нечего:

- трассировать;
- сравнивать;
- оценивать;
- версионировать.

---

## 6.6. F3/V1 — production package и видео

### Remotion

Высоко релевантен, но только после доказанного ручного формата.

До установки должны существовать:

- стабильная scene grammar;
- subtitle style;
- visual hierarchy;
- asset policy;
- один рабочий video format.

Remotion помогает реализовать renderer. Он не должен проектировать редакционный формат вместо автора.

### Figma / Canva

Подключать один инструмент, когда определён процесс:

| Инструмент | Лучше подходит |
|---|---|
| Figma | Строгая дизайн-система и повторяемые компоненты |
| Canva | Быстрые social assets и шаблоны |

### Hugging Face

Только при появлении задачи:

- сравнивать модели;
- использовать datasets;
- работать со Spaces;
- тестировать image/video generation;
- использовать hosted inference.

---

## 6.7. Production

### Sentry

После появления постоянного runtime или background jobs.

### Deployment plugin

Выбирать только после решения о платформе.

Нельзя устанавливать Cloudflare/Vercel/Netlify/AWS «для изучения» и позволять плагину фактически принять архитектурное решение.

---

# 7. Что не подключать к F0

## Методологии

Не подключать:

- Superpowers;
- Compound Engineering;
- крупные TDD workflow packs;
- multi-agent orchestration packs.

Причина: F0 уже имеет нормативную спецификацию и DoD. Дополнительная методология может:

- конкурировать с `AGENTS.md`;
- расширить scope;
- увеличить токены;
- добавить лишнюю документацию;
- изменить порядок исполнения.

## Review duplication

Не подключать одновременно:

- несколько PR-review bots;
- CodeRabbit;
- второй security scanner;
- несколько GitHub assistants.

Для F0 достаточно:

```text
Codex review
→ Codex Security diff scan
→ ручной просмотр финального diff
```

## Browser и web

Не подключать:

- Chrome extension;
- browser automation;
- Playwright MCP;
- Browserbase;
- web scraper.

F0 offline.

## Data и cloud

Не подключать:

- Supabase;
- Neon;
- PostgreSQL cloud;
- Redis;
- vector DB;
- Pinecone;
- cloud hosting;
- observability.

F0 использует локальный SQLite.

---

# 8. Лимит активных tools

Для обычного F0 thread:

```text
0–1 plugin
0–1 external MCP
```

Для review thread:

```text
Codex Security
GitHub read access при необходимости
```

Общий предел:

- максимум три активных plugin/tool bundles;
- максимум два MCP одновременно;
- один инструмент на одну функцию;
- фазовые плагины выключаются вне своей фазы.

## Хорошо

```text
F0 implementation:
- no plugin или Context7
```

```text
F0 security review:
- Codex Security
```

## Плохо

```text
Context7
+ другой docs MCP
+ Sourcegraph
+ GitHub assistant
+ browser automation
+ three scraping tools
```

---

# 9. Финальная модельная стратегия

Названия моделей и уровни усилий выбираются в UI Codex.

## Рекомендуемый default

```text
Model: 5.6 Sol
Effort: Высокий
```

Это базовый профиль для реализации F0:

- достаточно сильный reasoning;
- умеренный расход;
- подходит для кода, тестов и документации.

## Когда использовать «Очень высокий»

- первая реализация сложного вертикального slice;
- изменения identity/hash contracts;
- SQLite schema;
- сложная нормализация;
- финальный cross-file review;
- расследование нетривиального бага.

## Когда использовать «Макс.»

- единичная финальная проверка всего F0;
- сложный дефект после нескольких неудачных попыток;
- security finding с неоднозначным source-to-sink path.

Не использовать для каждого шага.

## Когда использовать «Ультра»

- независимый multi-role red-team;
- глубокий аудит перед крупным архитектурным переходом;
- F1/F2/F3 phase review, если появилось много конфликтующих решений.

Не использовать для:

- обычного кодинга;
- lint fixes;
- генерации тестовых fixtures;
- мелких рефакторингов;
- каждого commit.

## Экономный профиль

```text
Model: 5.6 Terra
Effort: Высокий
```

Допустим для:

- механических правок;
- документации;
- небольших unit tests;
- понятных bug fixes.

Основные domain, identity, persistence и security изменения лучше оставлять `5.6 Sol`.

## Не рекомендуемый core profile

Luna и более старые модели не использовать как основной исполнитель F0, если качество важнее экономии.

---

# 10. Настройки приложения ChatGPT / Codex

## General

### Prevent sleep while running

```text
ON
```

Нужно для длинных локальных задач и тестов.

### Follow-up behavior

Предпочтительно:

```text
Queue for next run / wait for current run
```

Причина: случайное сообщение не должно менять текущую реализацию в середине транзакции или тестового прохода.

Для интерактивного исследования можно временно использовать steering текущего run.

### Notifications

```text
ON for task completion
```

Полезно для длинного test/review run.

---

# 11. Sandbox и approvals

Для F0 рекомендуется:

```text
sandbox_mode = workspace-write
approval_policy = on-request
network_access = false
```

Codex сможет:

- читать проект;
- менять файлы в workspace;
- запускать тесты;
- работать с Git локально.

Он должен запрашивать approval для выхода за workspace или сетевого доступа.

## Не использовать

```text
danger-full-access
--dangerously-bypass-approvals-and-sandbox
--yolo
```

## Read-only профиль

Для аудита документации и финального review:

```text
sandbox_mode = read-only
approval_policy = on-request
```

## Auto-review approvals

Automatic approval review использует дополнительные model calls.

Для минимизации токенов оставить:

```text
approvals_reviewer = user
```

Использовать auto-review только если поток ручных approvals реально мешает.

---

# 12. Рекомендуемый user config

Файл:

```text
~/.codex/config.toml
```

На Windows путь зависит от Codex home; открыть его безопаснее через Codex Settings.

Минимальная база:

```toml
model_reasoning_effort = "high"
model_verbosity = "medium"

approval_policy = "on-request"
sandbox_mode = "workspace-write"
allow_login_shell = false

project_doc_max_bytes = 32768

[sandbox_workspace_write]
network_access = false
```

## Пояснения

- `model_reasoning_effort = "high"` — стабильный default;
- для сложных thread выбрать более высокий effort в UI;
- `model_verbosity = "medium"` — отчёты достаточны, но не перегружены;
- `on-request` — безопасный баланс;
- `workspace-write` — Codex может реализовывать F0;
- сеть выключена;
- login shell отключён для меньшей неявности;
- 32 KiB достаточно для короткого `AGENTS.md`.

Не задавать вручную:

- model context window;
- auto compact threshold;
- custom provider;
- OpenAI base URL;
- telemetry;
- network proxy;

если нет конкретной причины.

---

# 13. Project config для F0

Файл:

```text
<repo>/.codex/config.toml
```

Project-scoped config загружается только для trusted project.

Рекомендуемый вариант:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false
```

Не хранить в project config:

- API keys;
- provider auth;
- пользовательские токены;
- GitHub token;
- секреты;
- machine-specific absolute paths.

## Перед trust

Сначала:

1. прочитать repository;
2. проверить `.codex/config.toml`;
3. проверить hooks;
4. проверить `AGENTS.md`;
5. проверить plugins/MCP;
6. только потом помечать project trusted.

---

# 14. Профили

Профили удобны, чтобы не менять настройки вручную.

## 14.1. Audit profile

```toml
approval_policy = "on-request"
sandbox_mode = "read-only"
model_reasoning_effort = "xhigh"
model_verbosity = "high"
```

Использование:

- foundation review;
- security triage;
- diff review;
- документационный аудит.

## 14.2. F0 implementation profile

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_reasoning_effort = "high"
model_verbosity = "medium"

[sandbox_workspace_write]
network_access = false
```

## 14.3. Final review profile

```toml
approval_policy = "on-request"
sandbox_mode = "read-only"
model_reasoning_effort = "xhigh"
model_verbosity = "high"
```

Для review лучше новый thread, чтобы реализационный контекст и самооправдание агента не влияли на проверку.

## 14.4. F1 network profile

Создавать только в F1.

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true
```

При включении сети использовать allowlist/proxy policy, если доступно, вместо unrestricted network.

---

# 15. AGENTS.md — главный контроль проекта

Codex читает `AGENTS.md` перед началом работы.

Размещение:

```text
<repo>/AGENTS.md
```

Не превращать его в копию всей спецификации.

## Рекомендуемый `AGENTS.md`

```markdown
# AI Newsroom OS — Codex instructions

## Authority

- `F0_TECHNICAL_SPEC.md` is the sole normative F0 specification.
- `docs/f0-minimal-scope.md` is a derived checklist.
- Historical foundation and audit files are non-normative.
- If documents conflict, `F0_TECHNICAL_SPEC.md` wins.

## Scope

Implement Foundation F0 only.
Do not create future commands, entities, providers, network ingestion,
UI, API, Docker, video, publishing or placeholder abstractions.

## Environment

- Windows 11
- Python 3.12.x
- `uv`
- 16 GB RAM
- no GPU requirement
- no Docker
- no network during runtime, tests or F0 demo

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
- Never delete or recreate an existing database automatically.
- Never overwrite a differing export without explicit `--force`.
- Never run destructive Git commands.
- Never expose secrets or raw fixture bodies in logs.

## Stop conditions

Stop and report instead of guessing when:
- the specification conflicts with itself;
- completion requires a non-goal;
- a new direct dependency appears necessary;
- a destructive action would be required;
- a test cannot be made deterministic.
```

## Размер

Оставлять `AGENTS.md` значительно меньше стандартного лимита 32 KiB.

Большие детали должны жить в `F0_TECHNICAL_SPEC.md`, а не дублироваться.

## Проверка загрузки

В новом Codex thread попросить:

```text
Summarize the active project instructions and identify the sole normative F0 document.
Do not modify files.
```

Если ответ неверный — не начинать реализацию.

---

# 16. Локальные skills вместо сторонних methodology plugins

Официальная модель Codex:

- Skill — рабочая процедура;
- Plugin — способ распространять skills и connectors.

Пока workflow нужен только этому репозиторию, лучше использовать local skills.

## Skill 1 — F0 Scope Guardian

Задачи:

- читать нормативный spec;
- сравнивать diff с whitelist/non-goals;
- выявлять лишние dependencies;
- искать future placeholders;
- выдавать PASS/FAIL.

## Skill 2 — F0 Quality Gate

Задачи:

- Ruff;
- mypy;
- pytest;
- полный DoD;
- повторный E2E;
- сравнение IDs/counts/hashes;
- итоговая таблица.

## Skill 3 — F0 Diff Review

Задачи:

- review только текущего Git diff;
- requirement mapping;
- missing tests;
- accidental scope expansion;
- без автоматического исправления.

## Skill 4 — Documentation Authority Check

Задачи:

- проверять иерархию документов;
- искать противоречивые active instructions;
- проверять historical banners;
- не менять product vision.

## Когда создавать

Не до финализации `F0_TECHNICAL_SPEC.md`.

После стабилизации можно создать один-два local skill. Не нужно сразу создавать plugin package.

---

# 17. Subagents

Codex поддерживает subagents, но для F0 их использовать ограниченно.

## Полезный сценарий

После реализации:

- основной agent завершил работу;
- независимый read-only subagent проверяет diff;
- другой security-oriented review выполняется отдельно.

## Не использовать

- несколько subagents одновременно реализуют одни и те же файлы;
- один пишет schema, другой параллельно меняет identity contract;
- swarm для маленького F0;
- автоматическое «голосование» без единого нормативного spec.

Для F0 последовательность лучше параллелизма.

---

# 18. Hooks

Hooks могут выполняться автоматически.

На F0:

```text
No custom hooks initially.
```

Позже допустим безопасный post-task hook, который только:

- запускает formatting/lint;
- не меняет внешние системы;
- не использует сеть;
- не выполняет commit/push;
- не удаляет файлы.

Любой plugin hook проверить до enable.

---

# 19. MCP policy

Перед подключением MCP проверить:

- кто оператор;
- какие tools exposed;
- read/write actions;
- auth;
- network destination;
- какие данные уходят наружу;
- где хранится token;
- можно ли ограничить tools;
- можно ли установить approval mode per tool.

## Для F0

Разрешён максимум один documentation MCP.

Не подключать MCP с:

- shell write;
- filesystem write;
- browser control;
- external database write;
- deployment;
- broad GitHub write.

---

# 20. Git baseline

До реализации F0:

```powershell
git init
git add .
git commit -m "docs: establish F0 foundation baseline"
```

Перед commit проверить:

- `.env` исключён;
- `.demo-f0/` исключён;
- SQLite files исключены;
- exports/runtime data исключены;
- temporary files исключены;
- historical docs имеют корректный status;
- `F0_TECHNICAL_SPEC.md` финален;
- `AGENTS.md` указывает на него.

Рекомендуемый workflow:

```text
main
└── feat/f0-foundation
```

Codex app может использовать worktree для отдельного thread, но для маленького F0 достаточно одной feature branch.

---

# 21. Рекомендуемый рабочий процесс F0

## Thread 1 — план

Режим:

```text
5.6 Sol
Очень высокий
read-only
```

Задача:

- прочитать spec;
- проверить repo;
- составить минимальный file plan;
- не писать код.

## Thread 2 — реализация

Режим:

```text
5.6 Sol
Высокий
workspace-write
network off
```

Задача:

- реализовать F0;
- запускать тесты итеративно;
- не расширять scope.

## Thread 3 — независимый review

Режим:

```text
5.6 Sol
Очень высокий
read-only
```

Задача:

- review diff;
- сверка с spec;
- искать пропуски;
- не оправдывать решения предыдущего thread.

## Thread 4 — fix verified findings

Режим:

```text
5.6 Sol
Высокий
workspace-write
network off
```

## Thread 5 — security

Codex Security:

- diff scan;
- validation;
- fix только подтверждённых findings.

## Thread 6 — финальный DoD

Чистый новый thread:

- выполнить команды;
- не менять код без отдельного finding;
- зафиксировать результаты.

---

# 22. Plugin admission checklist

Community plugin допускается только после ответа на вопросы.

## Provenance

- автор известен;
- официальный repository существует;
- license указана;
- история commits реальна;
- upstream соответствует marketplace entry.

## Content

Проверить:

- plugin manifest;
- skills;
- MCP config;
- hooks;
- scripts;
- agents;
- permissions.

## Security

- shell access;
- filesystem write;
- network;
- secrets;
- GitHub write;
- deployment;
- destructive actions;
- token storage;
- telemetry.

## Scope

- решает текущую проблему;
- нет дубля;
- можно выключить;
- есть removal condition;
- plugin не меняет архитектуру проекта скрыто.

## Решение

```text
ALLOW
ALLOW WITH RESTRICTIONS
DEFER
REJECT
```

---

# 23. Registry установленных инструментов

После первой реальной установки создать:

```text
docs/codex-tooling-registry.md
```

Поля:

| Поле | Содержание |
|---|---|
| Name | Название |
| Type | Plugin / Skill / MCP / App |
| Source | Official/community |
| Version/ref | Версия |
| Purpose | Текущая задача |
| Permissions | Read/write/network/auth |
| Scope | User/project |
| Enabled phases | F0/F1/... |
| Installed | Дата |
| Reviewed | Дата |
| Removal condition | Когда удалить |
| Owner | Кто утвердил |

Не создавать registry с фиктивными записями до фактической установки.

---

# 24. Финальная матрица

## Сейчас

| Компонент | Решение |
|---|---|
| `AGENTS.md` | Создать |
| `.codex/config.toml` | Создать |
| Git baseline | Создать |
| Context7 | Опционально |
| Другие плагины | Не устанавливать |

## После GitHub remote

| Компонент | Решение |
|---|---|
| GitHub plugin/integration | Read-first, write with confirmation |

## После F0 code

| Компонент | Решение |
|---|---|
| Codex Security | Diff scan |
| Deep scan | Нет |

## F1

| Компонент | Решение |
|---|---|
| Scraping/search plugin | Только при наблюдаемой проблеме, выбрать один |

## F2

| Компонент | Решение |
|---|---|
| OpenAI Developers | Только если выбран OpenAI |
| Langfuse | После реальных traces |

## V1

| Компонент | Решение |
|---|---|
| Remotion | После доказанного формата |
| Figma или Canva | Выбрать один |
| Hugging Face | По отдельному use case |

---

# 25. Точная рекомендация для текущего момента

## Сделать сейчас

1. Дождаться финального `F0_TECHNICAL_SPEC.md`.
2. Создать Git baseline.
3. Создать короткий `AGENTS.md`.
4. Создать project `.codex/config.toml`.
5. Убедиться, что network выключен.
6. Поставить default:
   - `5.6 Sol`;
   - effort `Высокий`.
7. Для финального planning thread выбрать `Очень высокий`.
8. Context7 подключить только если доступен и реально нужен.
9. Не ставить другие плагины до появления кода.
10. После F0 использовать Codex Security.

## Не делать сейчас

- не устанавливать пакет marketplace-плагинов;
- не подключать browser;
- не давать GitHub write до baseline;
- не использовать Ultra для реализации;
- не включать unrestricted network;
- не включать danger full access;
- не создавать plugin package из project workflow;
- не автоматизировать commit/push.

---

# 26. Источники

Официальная документация OpenAI:

- Codex plugins:  
  https://developers.openai.com/codex/plugins

- Build plugins:  
  https://developers.openai.com/codex/plugins/build

- Codex skills:  
  https://developers.openai.com/codex/skills

- Codex configuration basics:  
  https://developers.openai.com/codex/config-basic

- Codex configuration reference:  
  https://developers.openai.com/codex/config-reference

- Codex advanced configuration:  
  https://developers.openai.com/codex/config-advanced

- Agent approvals and security:  
  https://developers.openai.com/codex/agent-approvals-security

- `AGENTS.md`:  
  https://developers.openai.com/codex/guides/agents-md

- MCP:  
  https://developers.openai.com/codex/mcp

- Hooks:  
  https://developers.openai.com/codex/hooks

- Subagents:  
  https://developers.openai.com/codex/subagents

- Codex Security plugin:  
  https://developers.openai.com/codex/security/plugin

- OpenAI plugins repository:  
  https://github.com/openai/plugins

Сторонний каталог, только для discovery:

- https://www.codex-marketplace.com/plugins

---

# 27. Итог

Оптимальная конфигурация F0:

```text
OpenAI Codex only

Model:
5.6 Sol / Высокий
Очень высокий для planning и final review

Sandbox:
workspace-write
on-request approvals
network off
no danger-full-access

Project:
Git baseline
F0_TECHNICAL_SPEC.md
short AGENTS.md
project .codex/config.toml

Plugins:
Context7 optional
GitHub after remote
Codex Security after implementation
nothing else during F0
```

Это максимизирует качество не количеством плагинов, а:

- ясностью authority;
- сильной моделью;
- достаточным effort;
- чистыми threads;
- независимым review;
- безопасным sandbox;
- минимальной tool surface;
- строгим F0 scope.
