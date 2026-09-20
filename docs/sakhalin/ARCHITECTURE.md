# Sakhalin Kids Studio — Architecture

## 1. Назначение

Sakhalin Kids Studio — специализированный production layer поверх OpenMontage для серийного детского образовательного YouTube-контента о Сахалине.

OpenMontage остаётся orchestration и media-production foundation.

Sakhalin Kids добавляет:

- постоянных героев;
- character continuity;
- детский editorial contract;
- русский lip-sync;
- локальную character animation;
- сахалинскую медиатеку;
- hybrid routing сцен;
- child/factual/character QA.

## 2. Архитектурный принцип

Не создавать глубокий fork.

Стремиться к следующему dependency direction:

```text
OpenMontage Core
        ^
        |
Sakhalin Kids adapters
        ^
        |
Episode pipelines / assets
```

Sakhalin-модули могут использовать OpenMontage contracts.

OpenMontage core не должен зависеть от Sakhalin-specific code.

## 3. Основные bounded contexts

### Episode Production

Отвечает за:

- research;
- episode proposal;
- script;
- scene plan;
- asset plan;
- approvals;
- compose;
- publish package.

### Character System

Отвечает за:

- character definitions;
- rig profiles;
- poses;
- actions;
- expressions;
- visemes;
- acting timelines;
- character QA.

### Media Library

Отвечает за:

- реальные фото;
- видео;
- drone footage;
- backgrounds;
- locations;
- props;
- music;
- ambient;
- provenance.

### Provider Layer

Использует OpenMontage selector/provider pattern.

Внешние модели не выбираются напрямую из screenplay.

Выбор идёт через scene router и существующие selector tools.

### QA

Разделить:

- technical QA;
- character QA;
- child-content QA;
- factual QA;
- budget QA.

## 4. Финальный cast

Допустимые постоянные персонажи:

```yaml
allowed_cast:
  - makar
  - leva
  - tikhon
  - anna
  - antoshka
```

Любой неизвестный постоянный character ID должен приводить к validation failure.

Временные персонажи выпуска допускаются только как explicit guest/non-core character и не должны автоматически становиться частью библиотеки.

## 5. Character runtime

Целевой flow:

```text
character.yaml
      |
rig profile
      |
art parts
      |
pose library
      |
action timeline
      |
dialogue audio
      |
viseme timeline
      |
acting timeline merge
      |
render package
      |
HyperFrames / Remotion
      |
MP4
```

Character runtime должен быть data-driven.

Запрещён подход:

```text
makar_renderer.py
leva_renderer.py
...
```

Вместо него:

```text
CharacterRenderer
  + CharacterSpec
  + RigProfile
  + PoseLibrary
  + Timeline
```

## 6. Rig profiles

MVP:

- `fox_cartoon` — Макар;
- `sea_lion_cartoon` — Лёва.

Следующие:

- `bear_cartoon` — Тихон;
- `seal_cartoon` — Анна;
- `seagull_cartoon` — Антошка.

Профиль задаёт:

- обязательные parts;
- pivots;
- allowed transforms;
- views;
- default poses;
- action capabilities;
- facial capabilities.

## 7. Scene model

Каждая сцена должна иметь machine-readable `type`.

Минимальный набор:

```text
character_dialogue
character_action
location_establishing
ai_cinematic
real_footage
educational_graphic
map
historical_reconstruction
fantasy_imagination
transition
```

## 8. Scene routing

Рекомендованный routing:

| Scene type | Default path |
|---|---|
| character_dialogue | local character runtime |
| character_action | local character runtime |
| location_establishing | owned footage, затем AI fallback |
| real_footage | media library |
| educational_graphic | HyperFrames/Remotion |
| map | HyperFrames/Remotion |
| ai_cinematic | OpenMontage video selector |
| historical_reconstruction | image/video selector |
| fantasy_imagination | image/video selector |
| transition | local composition runtime |

Провайдер не должен быть жёстко прописан в сценарии.

## 9. Hybrid episode

Целевая структура 4–6 минут:

- 40–50% local character animation;
- 15–25% owned real Sakhalin media;
- 10–20% generated cinematic video;
- 10–15% maps/explainers/motion graphics;
- остальное — titles/transitions.

Это ориентир, а не validation rule.

## 10. Медиа-библиотека

Предлагаемая структура:

```text
library/
  characters/
  locations/
    sakhalin/
      aniva/
      quiet-bay/
      yuzhno-sakhalinsk/
      nevelsk/
      okhotsk-sea/
      forests/
      rivers/
      ports/
      lighthouses/
      winter/
  props/
  effects/
  music/
  ambient/
  voices/
```

Каждый reusable asset должен иметь provenance metadata.

## 11. Provenance

Минимальная модель:

```yaml
id: okhotsk-sea-drone-001
type: video

source:
  kind: original_footage
  owner: internal

location:
  region: sakhalin

rights:
  status: owned

technical:
  duration_seconds: 12.4
  width: 3840
  height: 2160
```

Для generated assets дополнительно:

- provider;
- model;
- prompt reference;
- generation date;
- cost;
- episode ID.

Секреты в provenance запрещены.

## 12. Approval gates

Human approval обязателен минимум после:

1. proposal;
2. script;
3. storyboard;
4. paid/generated asset plan;
5. publish package.

Character redesign всегда требует отдельного approval.

## 13. Budget boundary

AI-провайдеры являются финансовой trust boundary.

До платного вызова:

```text
estimate
 -> validate
 -> budget policy
 -> reserve
 -> provider call
 -> reconcile
```

Никаких бесконечных retry loops.

Default:

- image retries: 3;
- video retries: 2;
- voice retries: 2.

## 14. Security invariants

1. Secrets не хранятся в Git.
2. Model output не авторизует tool calls.
3. Model output не передаётся напрямую в shell/eval.
4. Filesystem paths нормализуются и ограничиваются workspace.
5. Arbitrary URL fetch запрещён в Sakhalin-specific tools.
6. External research считается untrusted content.
7. Provider calls имеют cost limits.
8. Generated HTML/SVG не должен получать произвольный executable JS из model output.
9. Character asset writes ограничены каталогом проекта/библиотеки.
10. Все high-impact substitutions требуют explicit approval.

## 15. Runtime choice

Для character acting целевые runtimes:

### HyperFrames

Предпочтителен для:

- SVG;
- GSAP;
- timeline-driven acting;
- bespoke scene composition.

### Remotion

Предпочтителен для:

- React composition;
- reusable graphics;
- captions;
- educational cards;
- mixed video/graphics.

FFmpeg используется как post-processing/assembly layer, но не как полноценный acting runtime.

## 16. Детерминизм

Повторный render с одинаковыми:

- character assets;
- scene plan;
- dialogue audio;
- timelines;
- runtime version

должен сохранять внешний вид персонажей.

Randomness допускается только в явно объявленных effects и должна быть seedable.

## 17. Наблюдаемость

Каждый episode project должен иметь:

- decision log;
- cost log;
- asset manifest;
- provenance;
- QA reports;
- render report.

Backlot используется как production board, но его отсутствие не должно блокировать render pipeline.

## 18. Не-цели первого этапа

Не делать в Milestone 01:

- полноценный 5-минутный выпуск;
- все пять rig profiles;
- автоматическую публикацию в YouTube;
- сложный neural lip-sync;
- fine-tuning video models;
- самостоятельный web SaaS;
- arbitrary multi-agent orchestration.
