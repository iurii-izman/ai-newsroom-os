# Open Decisions

Status: active, non-normative owner decision register for F1/F2/content pilot.  
Normative F0 source: `F0_TECHNICAL_SPEC.md`.

Ни одно из этих решений не блокирует F0. Принятые owner decisions сюда не включаются; открытые вопросы не должны быть «решены» placeholder-кодом заранее.

## DEC-001 — Identity и merge multi-source Story в F1

### Контекст

F0 намеренно создаёт одну Story на immutable SourceSnapshot. F0 schema v1 and F0 data are disposable. No migration of F0 Story IDs is required. F1 должен определить собственную stable identity и объединение нескольких публикаций, сохраняя provenance и возможность undo ошибочного merge.

### Варианты

1. Детерминированный event key из title/entities/time.
2. Случайный stable Story ID + explicit human merge/unmerge.
3. Автоматический fuzzy cluster как source of truth.

### Рекомендация

Вариант 2: stable opaque ID и human-confirmed merge; heuristics только предлагают кандидатов.

### Почему

Событийная идентичность редакционна и плохо выводится из URL/title без размеченного evaluation set. Ручное решение дешевле ошибочного автоматического merge.

### Стоимость ошибки

Высокая: смешанные события загрязнят claims и package; нестабильный ID сломает lineage/exports.

### Когда нужно решить

До реализации F1 clustering/manual merge.

### Default при откладывании

Оставлять Stories раздельными; merge не выполнять. При переходе к F1 разрешён clean database start.

## DEC-002 — Retention реального source content

### Контекст

F0 хранит только RSS metadata и bounded plain-text summary. Для fact-checking в F1 может понадобиться точный excerpt/locator, но full HTML/PDF увеличивает copyright, privacy и storage risk.

### Варианты

1. Metadata/link only.
2. Metadata + bounded excerpt + content hash/locator.
3. Полный HTML/PDF snapshot.

### Рекомендация

Вариант 2 по умолчанию; full copy только для конкретного разрешённого source/use case с retention period.

### Почему

Excerpt/hash достаточно для большинства provenance checks и значительно дешевле/безопаснее полного архивирования.

### Стоимость ошибки

Средне-высокая: слишком мало данных мешает correction/audit; слишком много создаёт rights/privacy exposure.

### Когда нужно решить

До подключения первого live source в F1.

### Default при откладывании

Metadata/link plus bounded excerpt; no full content.

## DEC-003 — Стартовый набор и способ ingestion в F1

### Контекст

Исходник предлагает 5–8 источников, RSS и manual URL, но конкретный набор, owner и failure policy не определены.

### Варианты

1. Только 3–5 официальных RSS.
2. Official RSS + manual URL для исключений.
3. Broad feeds/social discovery сразу.

### Рекомендация

Вариант 1 для первого F1 slice; manual URL добавить только после наблюдаемой потребности.

### Почему

Меньше variability, правовых допущений и network failure modes; Source Tier A даёт достаточную стартовую выборку.

### Стоимость ошибки

Средняя: слишком узкий набор пропустит сигналы; слишком широкий создаст noise и extraction scope.

### Когда нужно решить

До F1 network implementation.

### Default при откладывании

Не подключать сеть; продолжать с fixtures/manual research outside system.

## DEC-004 — Beachhead audience, primary platform и pilot metric

### Контекст

Текущая аудитория объединяет специалистов, фрилансеров, менеджеров и предпринимателей; форматы и platform metrics нельзя интерпретировать без initial wedge.

### Варианты

1. CRM/integration/automation practitioners; one primary short-video platform; qualified saves/shares or owned-channel conversion.
2. Broad Russian-speaking AI audience; multi-platform reach.
3. Business owners; lead-generation/qualified inquiries.

### Рекомендация

Вариант 1: опереться на доказуемую экспертизу автора, выбрать одну primary platform и одну primary intent metric до pilot.

### Почему

Узкий wedge уменьшает confounding и усиливает moat; multi-platform distribution можно добавить после сигнала.

### Стоимость ошибки

Средняя: неверный wedge замедлит audience learning, но исправляется дешевле, чем автоматизация общего AI-news канала.

### Когда нужно решить

До контентного pilot; технический F0 не блокирует.

### Default при откладывании

Не делать выводов о формате/аудитории и не запускать video automation.

## DEC-005 — Первый real LLM provider и data boundary

### Контекст

F0 не имеет real provider или provider interface. F2 потребует выбрать provider с учётом structured output, стоимости, региональной доступности, retention/training terms и качества на русскоязычном editorial task.

### Варианты

1. Один hosted provider с structured output.
2. Локальная CPU model.
3. Multi-provider abstraction сразу.

### Рекомендация

Вариант 1 после evaluation на human-reviewed stories; один concrete adapter. Multi-provider seam вводить только со вторым consumer. Локальная тяжёлая модель не соответствует исходной машине без отдельного доказательства.

### Почему

Реальные provider constraints должны сформировать interface; выбор по памяти/цене без evaluation ненадёжен.

### Стоимость ошибки

Высокая: data-policy violation, нестабильная схема, cost overrun или преждевременная abstraction.

### Когда нужно решить

Перед F2; повторно проверить официальные docs/pricing в этот день.

### Default при откладывании

Оставаться на deterministic mock; не создавать provider placeholders.
