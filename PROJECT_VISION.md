# AI Newsroom — Product Vision

Status: active, non-normative product context.  
Technical implementation requirements live only in `F0_TECHNICAL_SPEC.md`.

## Mission

Создать proof-first редакционную систему для русскоязычных людей, которые применяют AI в работе и бизнесе:

> AI без шума: что изменилось, что подтверждено и что можно применить.

Продукт не должен становиться фабрикой массовых AI-пересказов. Его ценность — прослеживаемая связь между источником, утверждением, редакционным выводом и практическим применением.

## Target Audience

Русскоязычные специалисты, фрилансеры, менеджеры и предприниматели, которым важно:

- быстро понимать значимые AI-события;
- применять инструменты в реальной работе;
- отличать проверяемый результат от vendor claim и хайпа;
- видеть ограничения, источники и практические последствия.

Исходное преимущество автора — CRM, интеграции, автоматизация, бизнес- и системный анализ и бизнес-процессы. Этот опыт задаёт более защищённую стартовую нишу, чем общий новостной канал «обо всём в AI».

## Jobs To Be Done

- **Быть в курсе:** за несколько минут понять, что действительно важно, не читая десятки публикаций.
- **Применять:** увидеть конкретный рабочий сценарий и решить, стоит ли инвестировать время.
- **Не попасться на хайп:** отделить подтверждённое, vendor claim, вывод и прогноз.

## Positioning

Proof-first означает, что материал начинается с наблюдаемого результата или доказательства и сохраняет provenance. Anti-AI-slop означает отказ от пустой срочности, недоказанных цифр, пересказа одного заголовка и декоративной автоматизации без собственной ценности.

Технический pipeline сам по себе не доказывает полезность редакционного результата.

## Hypothesis Boundaries

| Hypothesis | Что её проверяет | Что её не проверяет |
|---|---|---|
| Technical | Offline repeatability, stable identities/exports, lineage, resource fit | Наличие классов или schema-valid JSON |
| Editorial | Ручная проверка traceability, точности и экономии редакторского времени | Deterministic mock package |
| Audience | Повторяемые qualified signals в выбранном сегменте | Один viral post или общие views |
| Format | Сопоставимый manual pilot с одной primary metric | Количество автоматически созданных материалов |
| Monetization | Отдельный revenue experiment после audience signal | Platform threshold или готовность video pipeline |
| Lead generation | Атрибутируемый qualified response в одном owned destination | Неатрибутируемые переходы |

## Parallel Tracks

```text
Track A — Content Validation:
manual research → manual script → manual production → publish → measure

Track B — Technical Foundation:
F0 → F1 → F2 → F3
```

> Technical F0 MUST NOT block the manual content pilot.

Треки идут параллельно: Track A проверяет редакционную, audience и format ценность; Track B снижает технический риск и стоимость только доказанных операций.

## Governing Principle

> Автоматизировать только доказанный процесс.

