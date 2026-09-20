# Sakhalin Kids Studio — стартовый бриф для OpenCode

## Цель

Развивать отдельный production layer для детского образовательного YouTube-канала о Сахалине поверх OpenMontage.

OpenCode является основным coding agent для этого репозитория.

Перед работой всегда читать `AGENTS.md`.

## Финальная команда

Постоянные core characters:

- `makar` — Макар, лисёнок, главный исследователь.
- `leva` — Лёва, сивуч, спокойный напарник и голос здравого смысла.
- `tikhon` — Тихон, медвежонок, лес и безопасность.
- `anna` — Анна, нерпа, море и подводный мир.
- `antoshka` — Антошка, чайка-путешественник и собиратель историй.

Новые постоянные персонажи не создаются без отдельного решения проекта.

## Архитектурный принцип

Не переписывать OpenMontage.

Sakhalin Kids должен оставаться тонким специализированным слоем:

```text
OpenMontage Core
        ^
        |
Sakhalin Kids adapters
        ^
        |
Episodes / assets
```

Использовать существующие OpenMontage contracts, registry, selectors, checkpoints, artifacts, cost tracking и render runtimes.

Sakhalin-specific logic не должна проникать в OpenMontage core без доказанной необходимости.

## Основные директории

Целевая структура:

```text
pipeline_defs/sakhalin-kids.yaml
skills/pipelines/sakhalin-kids/
styles/sakhalin-kids.yaml
tools/character/sakhalin/
library/characters/
library/locations/
schemas/sakhalin/
tests/sakhalin/
docs/sakhalin/
```

## Производственная стратегия

Не строить сериал как набор независимых text-to-video генераций.

Основные герои должны быть повторно используемыми детерминированными ассетами:

```text
character spec
-> rig profile
-> pose library
-> action timeline
-> dialogue audio
-> viseme timeline
-> acting timeline
-> renderer
```

Генеративное видео использовать только там, где оно даёт реальную производственную ценность:

- establishing shots;
- природа;
- море;
- реконструкции;
- фантазийные сцены;
- сложные cinematic inserts.

Обычный диалог постоянных героев должен идти через local character runtime.

## Первый implementation cycle

Выполнять:

`SKIDS-001 -> SKIDS-013`

Не переходить к полному сериалу до принятия первого proof.

### Target

10–15 секунд.

Персонажи:

- Макар;
- Лёва.

Локация:

- берег моря.

Диалог:

> Макар: «Лёва, а почему море солёное?»
>
> Лёва: «Хороший вопрос. Давайте разберёмся.»

### Proof должен показать

1. два разных персонажа одновременно;
2. два rig profiles;
3. reusable character assets;
4. стабильный внешний вид;
5. blink;
6. gaze;
7. минимум один gesture на героя;
8. два voice profiles;
9. русский viseme timeline;
10. lip-sync;
11. acting и mouth animation работают независимо;
12. итоговый MP4;
13. повторный render не меняет identity героев.

## Порядок задач

### SKIDS-001 — scaffold

Создать минимальные каталоги и contracts.

Не добавлять лишние abstractions.

### SKIDS-002 — schemas

Добавить schemas для:

- CharacterSpec;
- RigProfile;
- Pose;
- Action;
- VisemeTimeline.

### SKIDS-003 — character loader

Безопасно загружать и валидировать character manifests.

### SKIDS-004 — rig profile contract

Первоначально:

- `fox_cartoon`;
- `sea_lion_cartoon`.

### SKIDS-005 — pose/action contract

Минимум:

Макар:
- idle;
- blink;
- look;
- point;
- talk.

Лёва:
- idle;
- blink;
- look;
- think;
- talk.

### SKIDS-006 — viseme contract

Поддержать:

```text
REST
A
E
O
U
MBP
FV
SH
L
S
```

### SKIDS-007 — timeline merge

Объединить:

- body;
- head;
- eyes;
- gesture;
- mouth.

Mouth track не должен переписывать acting.

### SKIDS-008 — SVG scene renderer

Собрать детерминированную сцену из reusable assets.

### SKIDS-009 — runtime handoff

Подключить HyperFrames или Remotion через существующие OpenMontage conventions.

Не изобретать отдельный video framework.

### SKIDS-010 — Character QA

Проверять минимум:

- identity;
- required parts;
- palette lock;
- scale;
- viseme support;
- expected actions.

### SKIDS-011 — Макар fixtures

Минимальные SVG assets, достаточные для proof.

### SKIDS-012 — Лёва fixtures

Минимальные SVG assets, достаточные для proof.

### SKIDS-013 — render smoke test

Собрать тестовую сцену до MP4.

После этого остановиться и провести визуальную оценку.

## Не делать в первом цикле

- все пять production rigs;
- полноценный 4–6 минутный выпуск;
- платный AI-video;
- neural lip-sync;
- автоматическую публикацию;
- собственный SaaS;
- fine-tuning моделей;
- отдельный renderer для каждого персонажа.

## Ограничения по коду

- каждый authored source file ≤400 строк;
- одна основная ответственность на файл;
- не создавать generic dumping grounds;
- сохранять dependency direction;
- не ломать public interfaces OpenMontage;
- предпочитать data-driven contracts.

## Безопасность

Обязательные правила:

- не коммитить `.env`, API keys, tokens, credentials;
- не помещать секреты в prompts, manifests или logs;
- model output считать untrusted data;
- не исполнять model output напрямую как shell/eval/code;
- ограничивать filesystem writes workspace-каталогом;
- валидировать provider responses;
- ограничивать retries и стоимость;
- платные вызовы выполнять только после budget policy;
- high-impact действия не должны зависеть только от решения модели.

## Проверки перед завершением задачи

Запустить всё доступное и относящееся к изменению:

- formatting/lint;
- type/static checks;
- targeted tests;
- relevant contract tests;
- render smoke test, если затронут renderer;
- ffprobe для видео;
- frame sampling;
- secret scan;
- authored file line-count check.

Не писать PASS, если проверка фактически не запускалась.

## Документы проекта

Читать по необходимости:

- `AGENTS.md`
- `docs/sakhalin/ARCHITECTURE.md`
- `docs/sakhalin/IMPLEMENTATION_PLAN.md`
- `docs/sakhalin/CHARACTER_FORMAT.md`
- `docs/sakhalin/LIPSYNC.md`
- `pipeline_defs/sakhalin-kids.yaml`

## Формат отчёта OpenCode

После задачи кратко сообщить:

1. что реализовано;
2. какие файлы изменены;
3. какие проверки запущены;
4. их результат;
5. что осталось;
6. какой следующий SKIDS task.

Не расширять scope автоматически.
