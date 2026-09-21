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

### Composition & Derivatives

Отвечает за cross-scene assembly и platform derivatives поверх уже утверждённых scene outputs.

Default path остаётся локальным и детерминированным. Hypit рассматривается как optional adapter после отдельного pilot gate, а не как новый production-state owner или character generator.

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

## 9. Semantic composition and derivatives

Целевая dependency direction для optional Hypit integration:

```text
OpenMontage episode state / approved revision
        |
Sakhalin scene router
        |
approved scene outputs + asset refs
        |
optional Hypit adapter
        |
HyperFrames / Remotion / FFmpeg
        |
review / master / vertical / teaser outputs
```

Инварианты:

- OpenMontage/Sakhalin Kids остаётся владельцем episode state, approvals, costs и artifact lineage;
- Hypit получает только schema-validated inputs и approved asset references;
- core characters всегда приходят из local Character Runtime и не перегенерируются скрыто;
- reference/viral videos могут использоваться только как источник общей format grammar при наличии необходимых прав;
- массовые почти идентичные варианты не являются целевым production mode;
- adoption возможен только после `HYPIT-P01`, pin версии/commit и license/security review.

Подробно: [HYPIT_INTEGRATION.md](HYPIT_INTEGRATION.md).

## 10. Hybrid episode

Целевая структура 4–6 минут:

- 40–50% local character animation;
- 15–25% owned real Sakhalin media;
- 10–20% generated cinematic video;
- 10–15% maps/explainers/motion graphics;
- остальное — titles/transitions.

Это ориентир, а не validation rule.

---

Production concerns (media, provenance, approvals, budget, security, runtime, determinism, observability, non-goals) — см. [PRODUCTION_ARCHITECTURE.md](PRODUCTION_ARCHITECTURE.md).
