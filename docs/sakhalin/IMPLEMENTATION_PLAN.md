# Sakhalin Kids Studio — Implementation Plan

## Стратегия

Разработка идёт вертикальными slices.

Каждый milestone должен давать проверяемый video result.

Не реализовывать всю архитектуру до первого рабочего render proof.

---

# Milestone 00 — Repository integration

## Цель

Добавить Sakhalin Kids layer без изменения поведения существующих OpenMontage pipelines.

## Задачи

- создать каталоги `docs/sakhalin`, `tools/character/sakhalin`, `library/characters`, `schemas/sakhalin`, `tests/sakhalin`;
- добавить `pipeline_defs/sakhalin-kids.yaml`;
- проверить pipeline manifest schema;
- зарегистрировать новые tools только через существующий registry pattern;
- не менять existing provider implementations;
- добавить минимальную документацию.

## Acceptance

- существующие tests не сломаны;
- pipeline manifest валиден либо documented как draft с конкретными schema gaps;
- импорт OpenMontage не получает Sakhalin dependency;
- secrets отсутствуют.

---

# Milestone 01 — Character Runtime Proof

## Scope

Только:

- Макар;
- Лёва;
- 10–15 секунд;
- одна локация;
- один диалог.

## Сцена

Макар:

> Лёва, а почему море солёное?

Лёва:

> Хороший вопрос. Давайте разберёмся.

## Компоненты

Реализовать:

```text
character loader
rig profile loader
pose library loader
action timeline
viseme timeline
SVG renderer
HyperFrames handoff
character QA
```

## Минимальные actions

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

## Acceptance

- два персонажа одновременно;
- разные rig profiles;
- нет random redesign;
- blink видим;
- gaze видим;
- минимум один жест видим;
- рот управляется viseme timeline;
- audio sync присутствует;
- создаётся MP4;
- ffprobe проходит;
- opening/middle/end frame samples существуют;
- повторный render использует те же base assets;
- character QA не имеет blocking findings.

## Не делать

- платный AI video;
- все пять персонажей;
- полноценную episode pipeline;
- генерацию character art на лету.

---

# Milestone 02 — Russian Voice + Lip Sync

## Цель

Стабильная русская речь с достаточно естественной стилизованной артикуляцией.

## Компоненты

- dialogue manifest;
- TTS adapter через существующий OpenMontage selector;
- word timestamps;
- Russian phonemizer adapter;
- phoneme-to-viseme mapper;
- viseme smoothing;
- per-character voice profiles;
- lip-sync QA.

## Acceptance

- паузы дают REST;
- отсутствует frame-to-frame mouth chatter;
- короткие фонемы объединяются;
- audio/video drift визуально приемлем;
- target для автоматического измерения: около 150 ms или лучше;
- одинаковый input manifest воспроизводит одинаковый viseme timeline.

---

# Milestone 03 — Character Asset Library

## Цель

Перевести Макара и Лёву из тестовых SVG в production-ready reusable assets.

## Для каждого героя

Создать:

- front view;
- 3/4 view;
- side view;
- parts;
- face parts;
- visemes;
- expressions;
- poses;
- actions;
- props;
- regression frames.

## Acceptance

- character schema valid;
- colors locked;
- proportions locked;
- signature props consistent;
- comparison с reference frames проходит;
- base character никогда не перегенерируется автоматически.

---

# Milestone 04 — Sakhalin Kids Pipeline

## Stages

```text
research
proposal
script
storyboard
voices
lipsync
assets
animation
compose
qa
publish
```

## Требования

- использовать OpenMontage checkpoint protocol;
- использовать decision log;
- approval gates;
- cost tracker;
- Backlot-compatible artifacts;
- scene type routing.

## Acceptance

Из одной episode brief можно пройти pipeline до final MP4 без ручного создания промежуточных JSON/YAML файлов.

---

# Milestone 05 — Hybrid Scene Router

## Поддержать

- character_dialogue;
- character_action;
- real_footage;
- location_establishing;
- ai_cinematic;
- educational_graphic;
- map.

## Routing priority

Для `location_establishing`:

1. owned Sakhalin media;
2. approved stock;
3. generated video.

Для `character_dialogue`:

1. local character runtime;
2. никакого silent fallback на text-to-video.

## Acceptance

Scene plan детерминированно получает production path.

Provider substitution требует decision log и approval, если меняет утверждённый creative path.

---

# Milestone 06 — Full Core Cast

Добавить:

- Тихон;
- Анна;
- Антошка.

## Rig profiles

- bear_cartoon;
- seal_cartoon;
- seagull_cartoon.

## Acceptance

Каждый герой имеет:

- distinct silhouette;
- locked palette;
- voice profile;
- minimum expressions;
- minimum pose set;
- minimum action set;
- viseme set;
- character QA references.

---

# Milestone 07 — 60–120 second Integration Episode

## Требования

Минимум:

- 2–3 героя;
- 2 локации;
- character dialogue;
- real Sakhalin footage;
- одна generated cinematic сцена;
- одна educational graphic;
- music;
- ambient;
- SFX;
- subtitles.

## Acceptance

Полностью воспроизводимый production run с cost report и QA reports.

---

# Milestone 08 — Full 4–6 Minute Episode

Первый production episode.

Цель — доказать не только качество, но и операционную стоимость.

Измерить:

- число новых assets;
- число reused assets;
- AI video seconds;
- provider cost;
- render time;
- число human approvals;
- число rejected generations;
- число manual fixes.

---

# Milestone 09 — Production Optimization

После минимум трёх выпусков.

Только на основании реальных bottlenecks:

- расширять pose library;
- расширять actions;
- улучшать forced alignment;
- кешировать reusable renders;
- улучшать scene routing;
- автоматизировать Shorts derivatives;
- добавлять thumbnail pipeline.

Не оптимизировать гипотетические проблемы заранее.

---

# Quality Gates

## Technical

- schema validation;
- asset existence;
- lint;
- tests;
- render success;
- ffprobe;
- frame samples;
- audio presence;
- duration tolerance.

## Character

- identity;
- silhouette;
- palette;
- proportions;
- wardrobe;
- signature props;
- voice;
- motion readability.

## Child Content

- понятный язык;
- отсутствие длинных лекционных блоков;
- исследование через действие;
- понятный вопрос сцены;
- отсутствие опасного поведения без контекста;
- ограниченный on-screen text.

## Factual

Каждое значимое образовательное утверждение должно иметь источник в research artifact.

## Budget

Paid call не выполняется после hard limit.

---

# Suggested task breakdown for Codex

Первые задачи:

1. `SKIDS-001` — repository scaffolding.
2. `SKIDS-002` — character JSON/YAML schemas.
3. `SKIDS-003` — character loader.
4. `SKIDS-004` — rig profile contract.
5. `SKIDS-005` — pose/action contract.
6. `SKIDS-006` — viseme contract.
7. `SKIDS-007` — timeline merge.
8. `SKIDS-008` — SVG scene renderer.
9. `SKIDS-009` — HyperFrames handoff.
10. `SKIDS-010` — Character QA.
11. `SKIDS-011` — Макар fixture assets.
12. `SKIDS-012` — Лёва fixture assets.
13. `SKIDS-013` — 10–15 second render smoke test.

## Stop condition

После `SKIDS-013` остановиться и оценить video proof.

Не переходить к остальным персонажам, пока quality bar первого proof не принят.
